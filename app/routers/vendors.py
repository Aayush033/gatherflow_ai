import sqlite3
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_deps import get_current_user_dep, verify_event_ownership
from app.database import get_db
from app.schemas import VendorCreate, VendorOut, VendorUpdate

router = APIRouter(prefix="/api/events/{event_id}/vendors", tags=["Vendor Organiser"])


def verify_budget_item_belongs_to_event(cursor: sqlite3.Cursor, budget_item_id: str | None, event_id: str) -> None:
    if not budget_item_id:
        return
    cursor.execute("SELECT id FROM budget_items WHERE id = ? AND event_id = ?", (budget_item_id, event_id))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Linked budget item does not belong to this event"
        )


def sync_linked_budget_item(cursor: sqlite3.Cursor, budget_item_id: str | None, event_id: str) -> None:
    if not budget_item_id:
        return
    # Recalculate committed amount from confirmed vendors linked to this item
    cursor.execute(
        "SELECT quotation_amount FROM vendors WHERE linked_budget_item_id = ? AND event_id = ? AND status = 'confirmed'",
        (budget_item_id, event_id),
    )
    confirmed_rows = cursor.fetchall()
    total_committed = sum(float(r["quotation_amount"] or 0.0) for r in confirmed_rows)

    # Recalculate quoted amount from all vendors linked to this item
    cursor.execute(
        "SELECT quotation_amount FROM vendors WHERE linked_budget_item_id = ? AND event_id = ?",
        (budget_item_id, event_id),
    )
    all_rows = cursor.fetchall()
    total_quoted = max([float(r["quotation_amount"] or 0.0) for r in all_rows], default=0.0)

    new_status = "committed" if total_committed > 0 else ("quoted" if total_quoted > 0 else "planned")
    cursor.execute(
        """
        UPDATE budget_items
        SET committed_amount = ?, quoted_amount = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND event_id = ?
    """,
        (total_committed, total_quoted, new_status, budget_item_id, event_id),
    )


@router.get("", response_model=list[VendorOut])
def list_vendors(event_id: str, current_user: dict = Depends(get_current_user_dep)):
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE event_id = ? ORDER BY category ASC, name ASC", (event_id,))
        return [VendorOut(**dict(r)) for r in cursor.fetchall()]


@router.get("/semantic-search")
def semantic_search_vendors(
    event_id: str, q: str, category: str | None = None, current_user: dict = Depends(get_current_user_dep)
):
    """
    Approximate text similarity search across user vendors saved for this specific event.
    Returns empty list if no matching user records exist.
    """
    verify_event_ownership(event_id, current_user["id"])
    try:
        from app.vector_db import search_vendors_text_similarity

        return search_vendors_text_similarity(query=q, event_id=event_id, category=category, n_results=5)
    except Exception:
        return []


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor(event_id: str, vendor_in: VendorCreate, current_user: dict = Depends(get_current_user_dep)):
    verify_event_ownership(event_id, current_user["id"])
    vendor_id = f"vnd_{uuid.uuid4().hex[:8]}"

    with get_db() as conn:
        cursor = conn.cursor()

        # Enforce cross-event boundary on linked budget items
        verify_budget_item_belongs_to_event(cursor, vendor_in.linked_budget_item_id, event_id)

        cursor.execute(
            """
        INSERT INTO vendors (
            id, event_id, name, category, contact_person, contact_phone,
            contact_email, quotation_amount, status, follow_up_date,
            notes, linked_budget_item_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                vendor_id,
                event_id,
                vendor_in.name,
                vendor_in.category,
                vendor_in.contact_person,
                vendor_in.contact_phone,
                vendor_in.contact_email,
                vendor_in.quotation_amount,
                vendor_in.status,
                vendor_in.follow_up_date,
                vendor_in.notes,
                vendor_in.linked_budget_item_id,
            ),
        )

        # Recalculate linked budget item
        if vendor_in.linked_budget_item_id:
            sync_linked_budget_item(cursor, vendor_in.linked_budget_item_id, event_id)

        cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        created_dict = dict(cursor.fetchone())

        # Index in ChromaDB (scoped to this event and user)
        try:
            from app.vector_db import index_user_vendor

            index_user_vendor(created_dict, event_id=event_id, user_id=current_user["id"])
        except Exception:
            pass

        return VendorOut(**created_dict)


@router.patch("/{vendor_id}", response_model=VendorOut)
def update_vendor(
    event_id: str, vendor_id: str, vendor_update: VendorUpdate, current_user: dict = Depends(get_current_user_dep)
):
    verify_event_ownership(event_id, current_user["id"])
    update_data = vendor_update.model_dump(exclude_unset=True)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE id = ? AND event_id = ?", (vendor_id, event_id))
        existing_row = cursor.fetchone()
        if not existing_row:
            raise HTTPException(status_code=404, detail="Vendor not found")
        old_linked_id = existing_row["linked_budget_item_id"]

        # If linked_budget_item_id is being changed, verify it belongs to this event
        if "linked_budget_item_id" in update_data:
            verify_budget_item_belongs_to_event(cursor, update_data["linked_budget_item_id"], event_id)

        if update_data:
            clauses = [f"{k} = ?" for k in update_data.keys()]
            clauses.append("updated_at = CURRENT_TIMESTAMP")
            values = list(update_data.values())
            values.extend([vendor_id, event_id])
            cursor.execute(f"UPDATE vendors SET {', '.join(clauses)} WHERE id = ? AND event_id = ?", values)

        cursor.execute("SELECT * FROM vendors WHERE id = ? AND event_id = ?", (vendor_id, event_id))
        vendor_row = cursor.fetchone()
        vendor_dict = dict(vendor_row)
        new_linked_id = vendor_dict.get("linked_budget_item_id")

        # Synchronize budget item commitments and quotations
        if old_linked_id and old_linked_id != new_linked_id:
            sync_linked_budget_item(cursor, old_linked_id, event_id)
        if new_linked_id:
            sync_linked_budget_item(cursor, new_linked_id, event_id)

        try:
            from app.vector_db import index_user_vendor

            index_user_vendor(vendor_dict, event_id=event_id, user_id=current_user["id"])
        except Exception:
            pass

        return VendorOut(**vendor_dict)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(event_id: str, vendor_id: str, current_user: dict = Depends(get_current_user_dep)):
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE id = ? AND event_id = ?", (vendor_id, event_id))
        vendor_row = cursor.fetchone()
        if not vendor_row:
            raise HTTPException(status_code=404, detail="Vendor not found")

        linked_bgt_id = vendor_row["linked_budget_item_id"]
        cursor.execute("DELETE FROM vendors WHERE id = ? AND event_id = ?", (vendor_id, event_id))

        # Synchronize budget item after deletion to remove stale commitments
        if linked_bgt_id:
            sync_linked_budget_item(cursor, linked_bgt_id, event_id)

    try:
        from app.vector_db import delete_user_vendor

        delete_user_vendor(vendor_id)
    except Exception:
        pass
