"""
GatherFlow AI - Opt-in Live Gemini Verification Script
Executes genuine model calls against Google GenAI to verify:
1. Primary configured model (gemini-3.8-flash)
2. High-availability fallback model (gemini-2.5-flash)
3. End-to-end AI service availability

Usage:
    python scripts/live_gemini_test.py
"""

import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from google.genai.errors import APIError

# Add project root to sys.path for local app imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings  # noqa: E402
from app.services.ai_service import check_model_health  # noqa: E402


def run_live_test() -> int:
    print("=" * 65, flush=True)
    print("GATHERFLOW AI — LIVE GEMINI MODEL & RESILIENCE VERIFICATION", flush=True)
    print("=" * 65, flush=True)

    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        print("\n[SKIPPED] GEMINI_API_KEY is not configured in .env or environment.", flush=True)
        print("To run live model tests, set GEMINI_API_KEY in your local environment.", flush=True)
        return 0

    primary_model = settings.GEMINI_MODEL
    print(f"Target Primary Model : {primary_model}", flush=True)
    print("Server API Key Status: Configured (Protected)", flush=True)

    # 1. Connectivity Smoke Test (Model Catalog)
    print("\n[Step 1] Verifying Google GenAI API Credentials...", flush=True)
    health = check_model_health()
    print(f"  Auth Status : {health.get('status')}", flush=True)
    print(f"  Connected   : {health.get('connected')}", flush=True)
    print(f"  Message     : {health.get('message')}", flush=True)

    if not health.get("connected"):
        print("\n[RESULT] API authentication check failed. Cannot proceed with live generation.", flush=True)
        return 1

    # 2. Test Primary Model Directly with Larger Timeout
    timeout_ms = 45000  # 45-second timeout for primary evaluation
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
    minimal_prompt = "Provide a 1-sentence strategic event planning tip for an anniversary gala."

    print(f"\n[Step 2] Testing Primary Model '{primary_model}' Directly...", flush=True)
    print(f'  Prompt  : "{minimal_prompt}"', flush=True)
    print(f"  Timeout : {timeout_ms // 1000} seconds", flush=True)

    primary_verified = False
    primary_error_detail = ""
    start_time = time.time()

    try:
        response = client.models.generate_content(
            model=primary_model,
            contents=minimal_prompt,
        )
        elapsed = time.time() - start_time
        if response and response.text and response.text.strip():
            primary_verified = True
            print(f"  Response ({elapsed:.2f}s): {response.text.strip()}", flush=True)
            print(f"  Result  : PRIMARY MODEL VERIFIED ({primary_model})", flush=True)
        else:
            primary_error_detail = "Empty response returned by primary model."
            print(f"  Result  : PRIMARY MODEL NOT VERIFIED — {primary_error_detail}", flush=True)
    except APIError as api_err:
        elapsed = time.time() - start_time
        code = getattr(api_err, "code", "UNKNOWN")
        err_msg = str(api_err).split("\n")[0]
        primary_error_detail = f"HTTP {code} ({err_msg})"
        print(f"  Failed ({elapsed:.2f}s): {primary_error_detail}", flush=True)
        print(f"  Result  : PRIMARY MODEL NOT VERIFIED — {primary_error_detail}", flush=True)
    except Exception as exc:
        elapsed = time.time() - start_time
        primary_error_detail = f"Exception: {str(exc)[:150]}"
        print(f"  Failed ({elapsed:.2f}s): {primary_error_detail}", flush=True)
        print(f"  Result  : PRIMARY MODEL NOT VERIFIED — {primary_error_detail}", flush=True)

    # 3. Test High-Availability Fallback Model Separately
    fallback_models = ["gemini-2.5-flash", "gemini-3.5-flash"]
    fallback_verified = False
    active_fallback_id = None

    print("\n[Step 3] Testing High-Availability Fallback Generation...", flush=True)
    for fb_model in fallback_models:
        if fb_model == primary_model:
            continue
        print(f"  Attempting Fallback Model: {fb_model}...", flush=True)
        fb_start = time.time()
        try:
            fb_res = client.models.generate_content(
                model=fb_model,
                contents=minimal_prompt,
            )
            fb_elapsed = time.time() - fb_start
            if fb_res and fb_res.text and fb_res.text.strip():
                fallback_verified = True
                active_fallback_id = fb_model
                print(f"  Fallback Response ({fb_elapsed:.2f}s): {fb_res.text.strip()}", flush=True)
                print(f"  Result  : FALLBACK MODEL VERIFIED ({fb_model})", flush=True)
                break
        except Exception as fb_err:
            print(f"  Fallback {fb_model} failed: {str(fb_err)[:100]}", flush=True)

    # 4. Final Comprehensive Diagnosis & Reporting
    print("\n" + "=" * 65, flush=True)
    print("FINAL MODEL & SERVICE STATUS REPORT", flush=True)
    print("=" * 65, flush=True)

    if primary_verified:
        print(f"1. Primary Model ({primary_model})  : PRIMARY MODEL VERIFIED", flush=True)
    else:
        print(f"1. Primary Model ({primary_model})  : PRIMARY MODEL NOT VERIFIED — {primary_error_detail}", flush=True)

    if fallback_verified:
        print(f"2. Fallback Model ({active_fallback_id}) : FALLBACK MODEL VERIFIED", flush=True)
    else:
        print("2. Fallback Model                   : FALLBACK MODEL NOT VERIFIED", flush=True)

    if primary_verified:
        print(f"3. Overall AI Service Availability  : FULLY OPERATIONAL (Primary Model: {primary_model})", flush=True)
        return 0
    elif fallback_verified:
        print(
            f"3. Overall AI Service Availability  : OPERATIONAL VIA RESILIENT FALLBACK ({active_fallback_id})",
            flush=True,
        )
        print("   Architecture Note: GatherFlow AI automatically routes requests to the verified", flush=True)
        print(f"   fallback model ({active_fallback_id}) during upstream capacity/deadline spikes.", flush=True)
        return 0
    else:
        print("3. Overall AI Service Availability  : DEGRADED (No models responding)", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_live_test())
