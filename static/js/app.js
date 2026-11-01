/**
 * GatherFlow AI — app.js
 * Complete single-page application controller
 * All API interactions, UI state management, and event handlers
 */

'use strict';

/* ══════════════════════════════════════════════
   STATE
   ══════════════════════════════════════════════ */
const state = {
  sessionId: null,
  currentUser: null,
  currentEventId: null,
  currentEvent: null,
  events: [],
  blueprint: null,
  budgetItems: [],
  tasks: [],
  vendors: [],
  currentRescueId: null,
  aiConnected: false,
  language: 'en',
};

/* ══════════════════════════════════════════════
   MULTILINGUAL & I18N SUPPORT
   ══════════════════════════════════════════════ */
const i18n = {
  en: {
    btn_evaluator: "⚡ Enter as Evaluator",
    btn_demo: "🌟 Load Demo Event (Judges)",
    btn_guest: "Guest Sandbox",
    hero_title: "GenAI Event Intelligence & Autonomous Planning Studio",
    hero_sub: "Plan fail-safe weddings, community celebrations, and corporate galas with Google Gemini 3.8-Flash, ChromaDB semantic retrieval, and 100% deterministic financial mathematical precision.",
    btn_enter_studio: "▶ Enter Studio",
    eval_card_title: "🔒 Evaluator & Planner Access",
    eval_card_desc: "Authenticate using the official evaluator passcode to generate a cryptographically random session token with HTTP-only cookies and strict record ownership isolation.",
    eval_passcode_label: "Evaluator Passcode",
    eval_passcode_hint: "Official evaluator passcode configured on the server.",
    btn_eval_submit: "⚡ Enter as Evaluator (1-Click)",
    btn_demo_submit: "🌟 Load Demo Showcase Event (Judges)",
    btn_guest_submit: "👤 Continue as Guest (Sandboxed)",
    ai_card_title: "✦ AI Engine Status",
    ai_card_desc: "Gemini 3.8-Flash is configured server-side and ready for autonomous blueprint synthesis, budget intelligence, Plan Rescue, and ChromaDB semantic search.",
    btn_guest_full: "👤 Continue as Guest (Sandboxed)",
    guide_title: "How to Use GatherFlow AI",
    guide_sub: "Four autonomous pillars that take you from initial vision to stress-free event execution",
    step1_title: "Define Event & Vision",
    step1_desc: "Enter your celebration type, planned budget, guest headcount, cultural customs, and venue preferences. GatherFlow sets up an isolated workspace.",
    step2_title: "Generate AI Blueprint",
    step2_desc: "Gemini 3.8-Flash automatically plans theme concepts, phase milestones, prioritized checklists, and Next Best Actions (NBA) with real-time health scoring.",
    step3_title: "Budget & What-If Studio",
    step3_desc: "Track Estimated vs. Quoted vs. Committed vs. Paid costs. Simulate guest surges or budget cuts with 100% deterministic arithmetic.",
    step4_title: "Vector Search & Plan Rescue",
    step4_desc: "Discover your vendors using scoped ChromaDB vector search. When disruptions strike, generate and apply an adaptive Plan Rescue in 1 click.",
    sidebar_events: "Your Events",
    sidebar_no_events: "No events yet",
    btn_new_event: "+ New Event",
    btn_load_demo: "🌟 Load Demo Event",
    tab_home: "Home & Guide",
    tab_blueprint: "Blueprint",
    tab_budget: "Budget Studio",
    tab_timeline: "Timeline",
    tab_vendors: "Vendors",
    tab_rescue: "Plan Rescue",
    btn_settings: "⚙ Settings",
    page_title_select: "Select or Create an Event",
    nav_home: "🏠 Home & Guide",
    nav_exit: "🚪 Exit",
    studio_awaits_title: "Your Planning Studio Awaits",
    studio_awaits_sub: "Create a new event or select one from the sidebar to start planning with AI.",
    btn_create_first: "+ Create Your First Event",
    btn_demo_center: "🌟 Load Demo Showcase (Judges)"
  },
  hi: {
    btn_evaluator: "⚡ मूल्यांकक के रूप में प्रवेश करें",
    btn_demo: "🌟 डेमो इवेंट लोड करें (जज)",
    btn_guest: "अतिथि सैंडबॉक्स",
    hero_title: "GenAI इवेंट इंटेलिजेंस और स्वायत्त योजना स्टूडियो",
    hero_sub: "Google Gemini 3.8-Flash, ChromaDB सिमेंटिक रिट्रीवल और 100% सटीक वित्तीय गणितीय सटीकता के साथ शादियों और आयोजनों की योजना बनाएं।",
    btn_enter_studio: "▶ स्टूडियो में प्रवेश करें",
    eval_card_title: "🔒 मूल्यांकक और योजनाकार पहुंच",
    eval_card_desc: "HTTP-केवल कुकीज़ और सख्त रिकॉर्ड स्वामित्व अलगाव के साथ यादृच्छिक सत्र टोकन उत्पन्न करने के लिए आधिकारिक पासकोड से प्रमाणित करें।",
    eval_passcode_label: "मूल्यांकक पासकोड",
    eval_passcode_hint: "सर्वर पर कॉन्फ़िगर किया गया आधिकारिक पासकोड।",
    btn_eval_submit: "⚡ मूल्यांकक के रूप में प्रवेश करें (1-क्लिक)",
    btn_demo_submit: "🌟 डेमो शोकेस इवेंट लोड करें (जज)",
    btn_guest_submit: "👤 अतिथि के रूप में जारी रखें (सैंडबॉक्स)",
    ai_card_title: "✦ एआई इंजन स्थिति",
    ai_card_desc: "Gemini 3.8-Flash सर्वर-साइड कॉन्फ़िगर है और ब्लूप्रिंट संश्लेषण, बजट बुद्धिमत्ता और प्लान रेस्क्यू के लिए तैयार है।",
    btn_guest_full: "👤 अतिथि के रूप में जारी रखें (सैंडबॉक्स)",
    guide_title: "GatherFlow AI का उपयोग कैसे करें",
    guide_sub: "चार स्वायत्त स्तंभ जो आपको प्रारंभिक दृष्टि से तनाव-मुक्त आयोजन निष्पादन तक ले जाते हैं",
    step1_title: "इवेंट और विज़न को परिभाषित करें",
    step1_desc: "उत्सव का प्रकार, बजट, अतिथियों की संख्या और स्थान की प्राथमिकताएं दर्ज करें।",
    step2_title: "एआई ब्लूप्रिंट उत्पन्न करें",
    step2_desc: "Gemini 3.8-Flash स्वचालित रूप से थीम अवधारणाओं, मील के पत्थर और प्राथमिकताओं की योजना बनाता है।",
    step3_title: "बजट और विश्लेषण स्टूडियो",
    step3_desc: "अनुमानित बनाम उद्धृत लागत ट्रैक करें और 100% अंकगणित के साथ सिमुलेशन करें।",
    step4_title: "वेक्टर खोज और प्लान रेस्क्यू",
    step4_desc: "ChromaDB वेक्टर खोज से विक्रेताओं को खोजें और व्यवधान होने पर 1 क्लिक में प्लान रेस्क्यू लागू करें।",
    sidebar_events: "आपके इवेंट",
    sidebar_no_events: "अभी कोई इवेंट नहीं",
    btn_new_event: "+ नया इवेंट",
    btn_load_demo: "🌟 डेमो इवेंट लोड करें",
    tab_home: "होम और गाइड",
    tab_blueprint: "ब्लूप्रिंट",
    tab_budget: "बजट स्टूडियो",
    tab_timeline: "समयरेखा",
    tab_vendors: "विक्रेता",
    tab_rescue: "प्लान रेस्क्यू",
    btn_settings: "⚙ सेटिंग्स",
    page_title_select: "इवेंट चुनें या बनाएं",
    nav_home: "🏠 होम और गाइड",
    nav_exit: "🚪 बाहर निकलें",
    studio_awaits_title: "आपका प्लानिंग स्टूडियो तैयार है",
    studio_awaits_sub: "एक नया इवेंट बनाएं या एआई के साथ योजना शुरू करने के लिए साइडबार से चुनें।",
    btn_create_first: "+ अपना पहला इवेंट बनाएं",
    btn_demo_center: "🌟 डेमो शोकेस लोड करें (जज)"
  },
  es: {
    btn_evaluator: "⚡ Entrar como Evaluador",
    btn_demo: "🌟 Cargar Evento Demo (Jueces)",
    btn_guest: "Sandbox de Invitado",
    hero_title: "Inteligencia GenAI y Estudio de Planificación Autónoma",
    hero_sub: "Planifique bodas, celebraciones y galas con Google Gemini 3.8-Flash, búsqueda semántica ChromaDB y precisión financiera 100% determinista.",
    btn_enter_studio: "▶ Entrar al Estudio",
    eval_card_title: "🔒 Acceso de Evaluador y Planificador",
    eval_card_desc: "Autentíquese con el código de evaluador para generar un token de sesión seguro con cookies HTTP-only.",
    eval_passcode_label: "Código de Evaluador",
    eval_passcode_hint: "Código oficial configurado en el servidor.",
    btn_eval_submit: "⚡ Entrar como Evaluador (1 Clic)",
    btn_demo_submit: "🌟 Cargar Evento Demo (Jueces)",
    btn_guest_submit: "👤 Continuar como Invitado",
    ai_card_title: "✦ Estado del Motor de IA",
    ai_card_desc: "Gemini 3.8-Flash está configurado en el servidor y listo para sintetizar planos, análisis de presupuestos y Plan Rescue.",
    btn_guest_full: "👤 Continuar como Invitado",
    guide_title: "Cómo usar GatherFlow AI",
    guide_sub: "Cuatro pilares autónomos desde la visión inicial hasta la ejecución sin estrés",
    step1_title: "Definir Evento y Visión",
    step1_desc: "Ingrese tipo de celebración, presupuesto, invitados y preferencias de lugar.",
    step2_title: "Generar Plan con IA",
    step2_desc: "Gemini 3.8-Flash genera conceptos de tema, hitos y listas de tareas priorizadas.",
    step3_title: "Estudio de Presupuesto y Simulación",
    step3_desc: "Supervise costos y simule variaciones con aritmética 100% determinista.",
    step4_title: "Búsqueda Vectorial y Plan Rescue",
    step4_desc: "Descubra proveedores con ChromaDB y aplique rescate de plan ante imprevistos en 1 clic.",
    sidebar_events: "Sus Eventos",
    sidebar_no_events: "Sin eventos aún",
    btn_new_event: "+ Nuevo Evento",
    btn_load_demo: "🌟 Cargar Evento Demo",
    tab_home: "Inicio y Guía",
    tab_blueprint: "Plan Maestro",
    tab_budget: "Presupuesto",
    tab_timeline: "Cronograma",
    tab_vendors: "Proveedores",
    tab_rescue: "Plan Rescue",
    btn_settings: "⚙ Configuración",
    page_title_select: "Seleccionar o Crear Evento",
    nav_home: "🏠 Inicio y Guía",
    nav_exit: "🚪 Salir",
    studio_awaits_title: "Su Estudio de Planificación le Espera",
    studio_awaits_sub: "Cree un nuevo evento o seleccione uno de la barra lateral para comenzar con IA.",
    btn_create_first: "+ Crear Primer Evento",
    btn_demo_center: "🌟 Cargar Evento Demo (Jueces)"
  },
  fr: {
    btn_evaluator: "⚡ Entrer comme Évaluateur",
    btn_demo: "🌟 Charger Événement Démo",
    btn_guest: "Mode Invité",
    hero_title: "Intelligence Événementielle GenAI & Studio de Planification",
    hero_sub: "Planifiez mariages et événements avec Google Gemini 3.8-Flash, ChromaDB et une précision mathématique 100% déterministe.",
    btn_enter_studio: "▶ Entrer dans le Studio",
    eval_card_title: "🔒 Accès Évaluateur & Organisateur",
    eval_card_desc: "Authentifiez-vous avec le code évaluateur pour générer une session sécurisée avec cookies HTTP-only.",
    eval_passcode_label: "Code Évaluateur",
    eval_passcode_hint: "Code officiel configuré sur le serveur.",
    btn_eval_submit: "⚡ Entrer comme Évaluateur (1-Clic)",
    btn_demo_submit: "🌟 Charger Événement Démo",
    btn_guest_submit: "👤 Continuer comme Invité",
    ai_card_title: "✦ État du Moteur IA",
    ai_card_desc: "Gemini 3.8-Flash est configuré côté serveur et prêt pour la synthèse de plans et Plan Rescue.",
    btn_guest_full: "👤 Continuer comme Invité",
    guide_title: "Comment utiliser GatherFlow AI",
    guide_sub: "Quatre piliers autonomes de la vision initiale à la réalisation sans stress",
    step1_title: "Définir l'Événement",
    step1_desc: "Indiquez type de célébration, budget, nombre d'invités et préférences.",
    step2_title: "Générer le Plan IA",
    step2_desc: "Gemini 3.8-Flash planifie les jalons, les thèmes et les actions prioritaires.",
    step3_title: "Studio Budgétaire",
    step3_desc: "Suivez les coûts et simulez des scénarios avec calculs déterministes.",
    step4_title: "Recherche Vectorielle & Plan Rescue",
    step4_desc: "Trouvez des prestataires via ChromaDB et appliquez un sauvetage en 1 clic.",
    sidebar_events: "Vos Événements",
    sidebar_no_events: "Aucun événement",
    btn_new_event: "+ Nouvel Événement",
    btn_load_demo: "🌟 Charger Démo",
    tab_home: "Accueil & Guide",
    tab_blueprint: "Plan Directeur",
    tab_budget: "Budget",
    tab_timeline: "Planning",
    tab_vendors: "Prestataires",
    tab_rescue: "Plan Rescue",
    btn_settings: "⚙ Paramètres",
    page_title_select: "Sélectionner ou Créer un Événement",
    nav_home: "🏠 Accueil",
    nav_exit: "🚪 Quitter",
    studio_awaits_title: "Votre Studio de Planification Attend",
    studio_awaits_sub: "Créez un événement ou sélectionnez-en un pour commencer avec l'IA.",
    btn_create_first: "+ Créer Premier Événement",
    btn_demo_center: "🌟 Charger Démo (Juges)"
  },
  de: {
    btn_evaluator: "⚡ Als Evaluator beitreten",
    btn_demo: "🌟 Demo-Event laden (Juroren)",
    btn_guest: "Gast-Sandbox",
    hero_title: "GenAI Event-Intelligenz & Autonomes Planungsstudio",
    hero_sub: "Planen Sie Hochzeiten und Großevents mit Google Gemini 3.8-Flash, ChromaDB und 100% deterministischer Finanzmathematik.",
    btn_enter_studio: "▶ Studio betreten",
    eval_card_title: "🔒 Evaluator- & Planer-Zugang",
    eval_card_desc: "Authentifizieren Sie sich mit dem Evaluator-Passcode für eine sichere Sitzung mit HTTP-only Cookies.",
    eval_passcode_label: "Evaluator-Passcode",
    eval_passcode_hint: "Offizieller Passcode auf dem Server konfiguriert.",
    btn_eval_submit: "⚡ Als Evaluator beitreten (1-Klick)",
    btn_demo_submit: "🌟 Demo-Event laden (Juroren)",
    btn_guest_submit: "👤 Als Gast fortfahren",
    ai_card_title: "✦ KI-Engine Status",
    ai_card_desc: "Gemini 3.8-Flash ist serverseitig konfiguriert und bereit für Bauplan-Synthese und Plan Rescue.",
    btn_guest_full: "👤 Als Gast fortfahren",
    guide_title: "So nutzen Sie GatherFlow AI",
    guide_sub: "Vier autonome Säulen von der ersten Vision bis zur stressfreien Durchführung",
    step1_title: "Event definieren",
    step1_desc: "Geben Sie Art, Budget, Gästezahl und Veranstaltungsort ein.",
    step2_title: "KI-Bauplan generieren",
    step2_desc: "Gemini 3.8-Flash plant Meilensteine und priorisierte Checklisten automatisch.",
    step3_title: "Budget & Simulation",
    step3_desc: "Verfolgen Sie Kosten mit 100% deterministischer Arithmetik.",
    step4_title: "Vektorsuche & Plan Rescue",
    step4_desc: "Dienstleister via ChromaDB finden und bei Störungen Plan Rescue in 1 Klick aktivieren.",
    sidebar_events: "Ihre Events",
    sidebar_no_events: "Noch keine Events",
    btn_new_event: "+ Neues Event",
    btn_load_demo: "🌟 Demo-Event laden",
    tab_home: "Home & Guide",
    tab_blueprint: "Bauplan",
    tab_budget: "Budget",
    tab_timeline: "Zeitplan",
    tab_vendors: "Dienstleister",
    tab_rescue: "Plan Rescue",
    btn_settings: "⚙ Einstellungen",
    page_title_select: "Event auswählen oder erstellen",
    nav_home: "🏠 Home",
    nav_exit: "🚪 Beenden",
    studio_awaits_title: "Ihr Planungsstudio ist bereit",
    studio_awaits_sub: "Erstellen Sie ein neues Event oder wählen Sie eines aus der Seitenleiste.",
    btn_create_first: "+ Erstes Event erstellen",
    btn_demo_center: "🌟 Demo laden (Juroren)"
  },
  zh: {
    btn_evaluator: "⚡ 评估员登录",
    btn_demo: "🌟 加载演示活动 (评委)",
    btn_guest: "访客沙盒",
    hero_title: "GenAI 活动智能与自主策划工作室",
    hero_sub: "借助 Google Gemini 3.8-Flash、ChromaDB 语义检索和 100% 确定性金融计算，策划无懈可击的婚礼和庆典。",
    btn_enter_studio: "▶ 进入工作室",
    eval_card_title: "🔒 评估员与策划者访问",
    eval_card_desc: "使用官方评估员密码进行身份验证，生成具有安全 HTTP-only Cookie 的隔离会话。",
    eval_passcode_label: "评估员密码",
    eval_passcode_hint: "服务器上配置的官方评估员密码。",
    btn_eval_submit: "⚡ 一键以评估员身份进入",
    btn_demo_submit: "🌟 加载演示展示活动 (评委)",
    btn_guest_submit: "👤 以访客身份继续",
    ai_card_title: "✦ AI 引擎状态",
    ai_card_desc: "Gemini 3.8-Flash 已在服务端配置就绪，随时可进行蓝图生成、预算智能与应急救援 (Plan Rescue)。",
    btn_guest_full: "👤 以访客身份继续",
    guide_title: "如何使用 GatherFlow AI",
    guide_sub: "四大自主支柱，带您从初步设想走向无忧活动执行",
    step1_title: "定义活动与愿景",
    step1_desc: "输入庆祝类型、计划预算、宾客人数与场地偏好。",
    step2_title: "生成 AI 蓝图",
    step2_desc: "Gemini 3.8-Flash 自动规划主题概念、阶段里程碑与优先检查清单。",
    step3_title: "预算与情景模拟",
    step3_desc: "以 100% 确定性算法跟踪预估与实际费用并进行情景模拟。",
    step4_title: "向量搜索与计划救援",
    step4_desc: "通过 ChromaDB 发现供应商并在突发状况时一键应用救援方案。",
    sidebar_events: "您的活动",
    sidebar_no_events: "暂无活动",
    btn_new_event: "+ 新建活动",
    btn_load_demo: "🌟 加载演示活动",
    tab_home: "首页与指南",
    tab_blueprint: "活动蓝图",
    tab_budget: "预算工作室",
    tab_timeline: "时间线",
    tab_vendors: "供应商",
    tab_rescue: "计划救援",
    btn_settings: "⚙ 设置",
    page_title_select: "选择或创建活动",
    nav_home: "🏠 首页与指南",
    nav_exit: "🚪 退出",
    studio_awaits_title: "您的策划工作室已准备就绪",
    studio_awaits_sub: "创建新活动或从侧边栏选择一个活动以开始 AI 策划。",
    btn_create_first: "+ 创建您的第一个活动",
    btn_demo_center: "🌟 加载演示展示 (评委)"
  },
  ar: {
    btn_evaluator: "⚡ دخول كمقيّم",
    btn_demo: "🌟 تحميل حدث تجريبي (للحكام)",
    btn_guest: "وضع الضيف",
    hero_title: "ذكاء تخطيط الفعاليات الاصطناعي والاستوديو الذاتي",
    hero_sub: "خطط لحفلات الزفاف والفعاليات بثقة مع Google Gemini 3.8-Flash وبحث ChromaDB الدلالي وحسابات مالية دقيقة 100%.",
    btn_enter_studio: "▶ دخول الاستوديو",
    eval_card_title: "🔒 وصول المقيّم والمنظم",
    eval_card_desc: "تسجيل الدخول برمز المقيّم الرسمي لإنشاء جلسة آمنة مع كوكيز HTTP-only.",
    eval_passcode_label: "رمز مرور المقيّم",
    eval_passcode_hint: "الرمز الرسمي المضبوط في الخادم.",
    btn_eval_submit: "⚡ دخول كمقيّم (بنقرة واحدة)",
    btn_demo_submit: "🌟 تحميل الحدث التجريبي (للحكام)",
    btn_guest_submit: "👤 المتابعة كضيف",
    ai_card_title: "✦ حالة محرك الذكاء الاصطناعي",
    ai_card_desc: "Gemini 3.8-Flash مضبوط في الخادم وجاهز لتوليد المخططات وحسابات الميزانية وخطة الإنقاذ.",
    btn_guest_full: "👤 المتابعة كضيف",
    guide_title: "كيفية استخدام GatherFlow AI",
    guide_sub: "أربعة أركان تنقلك من الرؤية الأولية إلى التنفيذ الخالي من الإجهاد",
    step1_title: "تحديد الحدث والرؤية",
    step1_desc: "أدخل نوع الفعالية، الميزانية، عدد الضيوف، والتفضيلات.",
    step2_title: "توليد مخطط الذكاء الاصطناعي",
    step2_desc: "يقوم Gemini 3.8-Flash بتخطيط المفاهيم والمراحل وقوائم المهام تلقائيًا.",
    step3_title: "استوديو الميزانية والمحاكاة",
    step3_desc: "تتبع التكاليف ومحاكاة السيناريوهات بحسابات قطعية 100%.",
    step4_title: "البحث الشعاعي وإنقاذ الخطة",
    step4_desc: "اكتشف الموردين عبر ChromaDB وطبق خطة الإنقاذ بنقرة واحدة عند الطوارئ.",
    sidebar_events: "فعالياتك",
    sidebar_no_events: "لا توجد فعاليات بعد",
    btn_new_event: "+ حدث جديد",
    btn_load_demo: "🌟 تحميل حدث تجريبي",
    tab_home: "الرئيسية والدليل",
    tab_blueprint: "المخطط العام",
    tab_budget: "استوديو الميزانية",
    tab_timeline: "الجدول الزمني",
    tab_vendors: "الموردون",
    tab_rescue: "إنقاذ الخطة",
    btn_settings: "⚙ الإعدادات",
    page_title_select: "اختر أو أنشئ حدثاً",
    nav_home: "🏠 الرئيسية",
    nav_exit: "🚪 خروج",
    studio_awaits_title: "استوديو التخطيط بانتظارك",
    studio_awaits_sub: "أنشئ حدثاً جديداً أو اختر من الشريط الجانبي لبدء التخطيط مع الذكاء الاصطناعي.",
    btn_create_first: "+ أنشئ حدثك الأول",
    btn_demo_center: "🌟 تحميل العرض التجريبي (للحكام)"
  }
};

function setLanguage(lang) {
  if (!i18n[lang]) lang = 'en';
  state.language = lang;
  try {
    localStorage.setItem('gatherflow_lang', lang);
  } catch {}

  // Sync selectors
  const homeSel = document.getElementById('lang-selector-home');
  const appSel = document.getElementById('lang-selector-app');
  if (homeSel) homeSel.value = lang;
  if (appSel) appSel.value = lang;

  // RTL support for Arabic
  document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';

  const dict = i18n[lang] || i18n.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.innerHTML = dict[key];
    }
  });
}

function initLanguageSelectors() {
  const homeSel = document.getElementById('lang-selector-home');
  const appSel = document.getElementById('lang-selector-app');

  const onLangChange = (e) => {
    setLanguage(e.target.value);
  };

  homeSel?.addEventListener('change', onLangChange);
  appSel?.addEventListener('change', onLangChange);

  let savedLang = 'en';
  try {
    savedLang = localStorage.getItem('gatherflow_lang') || 'en';
  } catch {}
  setLanguage(savedLang);
}

/* ══════════════════════════════════════════════
   API HELPERS
   ══════════════════════════════════════════════ */
async function api(method, path, body = null, timeoutMs = 75000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Ensures HTTP-only session cookies are sent and received
    signal: controller.signal,
  };
  if (state.sessionId) {
    opts.headers['X-Session-Id'] = state.sessionId;
  }
  if (body) opts.body = JSON.stringify(body);

  try {
    const resp = await fetch(path, opts);
    clearTimeout(timeoutId);
    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try { const j = await resp.json(); detail = j.detail || detail; } catch {}
      throw new Error(detail);
    }
    if (resp.status === 204) return null;
    return resp.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw err;
  }
}

const GET    = (p)       => api('GET', p);
const POST   = (p, b)    => api('POST', p, b);
const PATCH  = (p, b)    => api('PATCH', p, b);
const DELETE = (p)       => api('DELETE', p);

/* ══════════════════════════════════════════════
   TOAST NOTIFICATIONS
   ══════════════════════════════════════════════ */
function toast(message, type = 'info', duration = 4000) {
  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), duration);
}

/* ══════════════════════════════════════════════
   LOADING SCREEN
   ══════════════════════════════════════════════ */
function hideLoading() {
  const ls = document.getElementById('loading-screen');
  ls.style.opacity = '0';
  ls.style.transition = 'opacity 0.5s ease';
  setTimeout(() => ls.classList.add('hidden'), 500);
}

function showScreen(id) {
  ['loading-screen', 'setup-screen', 'app-screen'].forEach(s => {
    const el = document.getElementById(s);
    if (el) el.classList.toggle('hidden', s !== id);
  });
  if (id === 'loading-screen') {
    document.getElementById('loading-screen').classList.remove('hidden');
  }
}

/* ══════════════════════════════════════════════
   SESSION / AUTH
   ══════════════════════════════════════════════ */
function getStoredSession() {
  return sessionStorage.getItem('gf_session') || localStorage.getItem('gf_session');
}
function storeSession(id, persist = false) {
  state.sessionId = id;
  sessionStorage.setItem('gf_session', id);
  if (persist) localStorage.setItem('gf_session', id);
}

async function initSession() {
  try {
    const me = await GET('/api/auth/me');
    if (me && me.id) {
      state.currentUser = me;
      return true;
    }
  } catch {}
  return false;
}

async function loginAsEvaluator(passcode = 'gatherflow-evaluator') {
  const data = await POST('/api/auth/evaluator-login', { passcode: (passcode || 'gatherflow-evaluator').trim() });
  state.currentUser = data;
  return data;
}

async function loginAsGuest() {
  const data = await GET('/api/auth/me');
  state.currentUser = data;
  return data;
}

/* ══════════════════════════════════════════════
   AI HEALTH & STATUS
   ══════════════════════════════════════════════ */
async function checkAiHealth() {
  try {
    const h = await GET('/api/health');
    const aiData = h?.ai || h?.generative_ai || {};
    // Key is configured on the server via .env — AI is Online and ready
    const isOnline = aiData.key_configured === true || aiData.connected === true;
    updateAiStatusIndicator(isOnline, aiData.model || 'gemini-3.8-flash');
    state.aiConnected = isOnline;
    return isOnline;
  } catch {
    updateAiStatusIndicator(false, '');
    return false;
  }
}

function updateAiStatusIndicator(connected, model) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('ai-status-label');
  const homeBadge = document.getElementById('home-ai-status-badge');
  if (dot) dot.className = 'status-dot ' + (connected ? 'connected' : 'error');
  if (label) label.textContent = connected ? 'AI: Online' : 'AI: Offline';
  if (homeBadge) {
    if (connected) {
      homeBadge.style.background = 'rgba(16,185,129,0.15)';
      homeBadge.style.color = '#10b981';
      homeBadge.style.borderColor = 'rgba(16,185,129,0.3)';
      homeBadge.innerHTML = '&#128994; Online';
    } else {
      homeBadge.style.background = 'rgba(239,68,68,0.15)';
      homeBadge.style.color = '#ef4444';
      homeBadge.style.borderColor = 'rgba(239,68,68,0.3)';
      homeBadge.innerHTML = '&#128308; Offline';
    }
  }
}

/* ══════════════════════════════════════════════
   SETUP & HOME SCREEN
   ══════════════════════════════════════════════ */
let setupScreenInitialized = false;

function initSetupScreen() {
  if (setupScreenInitialized) return;
  setupScreenInitialized = true;

  // Evaluator Login Buttons
  const evalSubmitBtn = document.getElementById('btn-login-evaluator-submit');
  const evalQuickBtn  = document.getElementById('btn-home-quick-eval');
  const evalStatusDiv = document.getElementById('eval-login-status');
  const evalPasscode  = document.getElementById('eval-passcode-input');
  
  // Guest Buttons
  const guestSubmitBtn = document.getElementById('btn-login-guest-submit');
  const guestTopBtn    = document.getElementById('btn-home-guest');
  const skipBtn        = document.getElementById('btn-skip-setup');

  const handleEvaluatorLogin = async () => {
    const code = evalPasscode?.value.trim() || 'gatherflow-evaluator';
    if (evalSubmitBtn) { evalSubmitBtn.disabled = true; evalSubmitBtn.textContent = '⏳ Authenticating...'; }
    if (evalQuickBtn) { evalQuickBtn.disabled = true; }
    setStatus(evalStatusDiv, 'loading', 'Authenticating evaluator session...');

    try {
      const user = await loginAsEvaluator(code);
      setStatus(evalStatusDiv, 'success', `✓ Verified evaluator session (${user.name}). Launching studio...`);
      toast(`Welcome, ${user.name}! Official Evaluator Mode active.`, 'success');
      setTimeout(() => enterApp(), 750);
    } catch (e) {
      setStatus(evalStatusDiv, 'error', `Authentication failed: ${e.message}`);
      toast('Invalid evaluator passcode.', 'error');
    } finally {
      if (evalSubmitBtn) { evalSubmitBtn.disabled = false; evalSubmitBtn.textContent = '⚡ Enter as Evaluator (1-Click)'; }
      if (evalQuickBtn) { evalQuickBtn.disabled = false; }
    }
  };

  evalSubmitBtn?.addEventListener('click', handleEvaluatorLogin);
  evalQuickBtn?.addEventListener('click', handleEvaluatorLogin);

  const handleGuestLogin = async () => {
    if (guestSubmitBtn) { guestSubmitBtn.disabled = true; }
    try {
      const user = await loginAsGuest();
      toast(`Entered as ${user.name}. Isolated sandbox ready.`, 'info');
      await enterApp();
    } catch (e) {
      toast(`Guest session error: ${e.message}`, 'error');
    } finally {
      if (guestSubmitBtn) { guestSubmitBtn.disabled = false; }
    }
  };

  guestSubmitBtn?.addEventListener('click', handleGuestLogin);
  guestTopBtn?.addEventListener('click', handleGuestLogin);
  skipBtn?.addEventListener('click', handleGuestLogin);
  document.getElementById('btn-home-resume')?.addEventListener('click', enterApp);

  // Demo Showcase Event triggers for Judges & Evaluators
  document.getElementById('btn-home-demo')?.addEventListener('click', loadDemoShowcaseEvent);
  document.getElementById('btn-login-demo-submit')?.addEventListener('click', loadDemoShowcaseEvent);
  document.getElementById('btn-sidebar-demo')?.addEventListener('click', loadDemoShowcaseEvent);
  document.getElementById('btn-demo-event-center')?.addEventListener('click', loadDemoShowcaseEvent);
}

function setStatus(el, type, msg) {
  if (!el) return;
  el.className = `setup-status ${type}`;
  el.textContent = msg;
  el.classList.remove('hidden');
}

/* ══════════════════════════════════════════════
   HOME & APP SCREEN TRANSITIONS
   ══════════════════════════════════════════════ */
function showHomeScreen() {
  showScreen('setup-screen');
  initSetupScreen();
  updateHomeUserStatus();
}

function updateHomeUserStatus() {
  const banner = document.getElementById('home-resume-banner');
  const nameEl = document.getElementById('home-user-name');
  if (state.currentUser) {
    if (nameEl) nameEl.textContent = state.currentUser.name || 'Planner';
    if (banner) banner.classList.remove('hidden');
  } else {
    if (banner) banner.classList.add('hidden');
  }
}

async function logoutUser() {
  try {
    await POST('/api/auth/logout', {});
  } catch {}
  state.currentUser = null;
  state.currentEventId = null;
  state.currentEvent = null;
  state.events = [];
  toast('Signed out successfully. Return to Home Portal.', 'info');
  showHomeScreen();
}

async function loadDemoShowcaseEvent() {
  toast('Loading Evaluator Demo Showcase...', 'info');
  try {
    if (!state.currentUser) {
      await loginAsEvaluator();
    }
    const demoEvent = await POST('/api/events/demo-showcase', {});
    toast(`Loaded showcase: "${demoEvent.title}"!`, 'success');
    await enterApp();
    await loadEvents();
    if (demoEvent && demoEvent.id) {
      selectEvent(demoEvent.id);
    }
  } catch (e) {
    toast(`Could not load demo event: ${e.message}`, 'error');
  }
}

async function enterApp() {
  showScreen('app-screen');
  updateUserChip();
  try {
    await checkAiHealth();
  } catch (err) {
    // Graceful degradation when network/offline
  }
  await loadEvents();
}

function updateUserChip() {
  const u = state.currentUser;
  const nameEl = document.getElementById('user-name-display');
  if (nameEl && u) nameEl.textContent = u.name || u.email || 'User';
}

/* ══════════════════════════════════════════════
   EVENTS (SIDEBAR LIST)
   ══════════════════════════════════════════════ */
async function loadEvents() {
  try {
    state.events = await GET('/api/events');
    renderEventList();
    if (state.currentEventId) {
      const exists = state.events.find(e => e.id === state.currentEventId);
      if (exists) selectEvent(state.currentEventId);
    }
  } catch (e) {
    console.error('loadEvents:', e);
  }
}

const EVENT_ICONS = { wedding: '💍', birthday: '🎂', community: '🎉', custom: '✨' };

function renderEventList() {
  const list = document.getElementById('event-list-sidebar');
  if (!list) return;
  if (!state.events.length) {
    list.innerHTML = '<li class="event-list-empty">No events yet</li>';
    return;
  }
  list.innerHTML = state.events.map(ev => `
    <li class="event-item ${ev.id === state.currentEventId ? 'active' : ''}"
        data-event-id="${ev.id}" role="listitem" aria-label="${ev.title}">
      <span class="event-item-icon">${EVENT_ICONS[ev.event_type] || '📅'}</span>
      <span class="event-item-name">${escHtml(ev.title)}</span>
    </li>`).join('');

  list.querySelectorAll('.event-item').forEach(li => {
    li.addEventListener('click', () => selectEvent(li.dataset.eventId));
  });
}

async function selectEvent(eventId) {
  state.currentEventId = eventId;
  state.currentEvent = state.events.find(e => e.id === eventId) || null;
  renderEventList(); // highlight active

  const title = document.getElementById('page-title');
  if (title && state.currentEvent) title.textContent = state.currentEvent.title;

  document.getElementById('no-event-panel')?.classList.add('hidden');
  document.getElementById('event-workspace')?.classList.remove('hidden');

  await loadBlueprint();
}

/* ══════════════════════════════════════════════
   TAB NAVIGATION
   ══════════════════════════════════════════════ */
function initTabs() {
  document.querySelectorAll('.nav-tab[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
}

async function switchTab(tab) {
  document.querySelectorAll('.nav-tab').forEach(b => {
    const active = b.dataset.tab === tab;
    b.classList.toggle('active', active);
    b.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.tab-panel').forEach(p => {
    const active = p.id === `tab-${tab}`;
    p.classList.toggle('active', active);
    if (active) p.removeAttribute('hidden');
    else p.setAttribute('hidden', '');
  });

  if (!state.currentEventId) return;
  switch (tab) {
    case 'blueprint': await loadBlueprint(); break;
    case 'budget':    await loadBudget(); break;
    case 'timeline':  await loadTasks(); break;
    case 'vendors':   await loadVendors(); break;
  }
}

/* ══════════════════════════════════════════════
   BLUEPRINT TAB
   ══════════════════════════════════════════════ */
async function loadBlueprint() {
  if (!state.currentEventId) return;
  try {
    state.blueprint = await GET(`/api/events/${state.currentEventId}/blueprint`);
    renderBlueprint(state.blueprint);
  } catch (e) {
    toast(`Blueprint load failed: ${e.message}`, 'error');
  }
}

function renderBlueprint(bp) {
  if (!bp) return;
  renderHealthCard(bp.health);
  renderNBA(bp.next_best_action);
  renderStats(bp);
  renderPlanConcept(bp.plan);
}

function renderHealthCard(health) {
  if (!health) return;
  const score = health.health_score;
  const circle = document.getElementById('ring-fill-circle');
  if (circle) {
    const circ = 2 * Math.PI * 32;
    const offset = circ - (circ * score / 100);
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = score >= 80 ? 'var(--success)' : score >= 50 ? 'var(--warning)' : 'var(--danger)';
  }
  document.getElementById('health-score-value').textContent = score;
  const badge = document.getElementById('health-status-badge');
  badge.textContent = health.health_status;
  badge.className = 'health-status-badge ' + (score >= 80 ? '' : score >= 50 ? 'warning' : 'danger');

  const alertsEl = document.getElementById('health-alerts');
  alertsEl.innerHTML = health.alert_messages.length
    ? health.alert_messages.map(a => `<li>${escHtml(a)}</li>`).join('')
    : '<li style="color:var(--success)">All systems nominal.</li>';
}

function renderNBA(nba) {
  if (!nba) return;
  document.getElementById('nba-title').textContent = nba.title;
  document.getElementById('nba-description').textContent = nba.description;
  const urgBadge = document.getElementById('nba-urgency');
  urgBadge.textContent = nba.urgency;
  urgBadge.className = `urgency-badge ${nba.urgency}`;
  const btn = document.getElementById('btn-nba-action');
  if (btn && nba.action_url) {
    btn.onclick = () => {
      const tab = nba.action_url.replace('#', '');
      switchTab(tab);
    };
  }
}

function renderStats(bp) {
  const bs = bp.budget_summary;
  const ts = bp.task_summary;
  const h  = bp.health;
  const cur = bs?.currency || '';

  const used = bs?.total_committed || 0;
  const planned = bs?.planned_budget || 0;
  const pct = planned > 0 ? ((used / planned) * 100).toFixed(0) : 0;

  document.getElementById('stat-budget-val').textContent =
    `${cur} ${fmtNum(used)} (${pct}%)`;
  document.getElementById('stat-tasks-val').textContent =
    `${ts?.progress_percentage?.toFixed(0) || 0}% (${ts?.completed_tasks || 0}/${ts?.total_tasks || 0})`;
  document.getElementById('stat-days-val').textContent =
    h?.days_to_event != null ? `${h.days_to_event} days` : '--';

  // Vendors confirmed — count from vendors if available
  const confirmed = state.vendors.filter(v => v.status === 'confirmed').length;
  document.getElementById('stat-vendors-val').textContent =
    state.vendors.length ? `${confirmed} / ${state.vendors.length}` : '--';
}

function renderPlanConcept(plan) {
  const el = document.getElementById('plan-concept-content');
  if (!plan || !plan.concept) {
    el.innerHTML = '<p class="muted">No plan generated yet. Click <strong>Regenerate</strong> to ask Gemini for ideas.</p>';
    document.getElementById('milestones-list').innerHTML = '<p class="muted">Generate a plan to see milestones.</p>';
    document.getElementById('risks-content').innerHTML = '<p class="muted">--</p>';
    return;
  }

  el.innerHTML = `
    <div class="ai-badge">✦ Generated by Gemini</div>
    <h4>${formatAiMarkdown(plan.theme_details || '')}</h4>
    <p>${formatAiMarkdown(plan.concept || '')}</p>`;

  // Milestones
  let milestones = [];
  try { milestones = JSON.parse(plan.timeline_milestones_json || '[]'); } catch {}
  const mEl = document.getElementById('milestones-list');
  mEl.innerHTML = milestones.length
    ? milestones.map(m => `
      <div class="milestone-item">
        <div>
          <div class="milestone-phase">${escHtml(m.phase || '')}</div>
          <div class="milestone-timeframe">${escHtml(m.timeframe || '')}</div>
          <div class="milestone-desc">${escHtml(m.description || '')}</div>
        </div>
      </div>`).join('')
    : '<p class="muted">No milestones available.</p>';

  // Risks & Contingencies
  let risks = [], contingencies = [];
  try { risks = JSON.parse(plan.risks_json || '[]'); } catch {}
  try { contingencies = JSON.parse(plan.contingencies_json || '[]'); } catch {}
  document.getElementById('risks-content').innerHTML = `
    <div class="risks-section">
      <h5>Risks</h5>
      <ul>${(risks.length ? risks : ['No risks listed.']).map(r => `<li>${escHtml(r)}</li>`).join('')}</ul>
    </div>
    <div class="risks-section">
      <h5>Contingencies</h5>
      <ul>${(contingencies.length ? contingencies : ['No contingencies listed.']).map(c => `<li>${escHtml(c)}</li>`).join('')}</ul>
    </div>`;
}

document.getElementById('btn-regenerate-plan')?.addEventListener('click', async () => {
  if (!state.currentEventId) { toast('Select an event first.', 'warning'); return; }
  const btn = document.getElementById('btn-regenerate-plan');
  btn.textContent = '⏳ Generating...'; btn.disabled = true;
  try {
    await POST(`/api/events/${state.currentEventId}/plan/generate`, {});
    await loadBlueprint();
    toast('Plan regenerated by Gemini!', 'success');
  } catch (e) {
    toast(`Plan generation failed: ${e.message}`, 'error');
  } finally {
    btn.textContent = '↻ Regenerate'; btn.disabled = false;
  }
});

/* ══════════════════════════════════════════════
   BUDGET TAB
   ══════════════════════════════════════════════ */
async function loadBudget() {
  if (!state.currentEventId) return;
  try {
    state.budgetItems = await GET(`/api/events/${state.currentEventId}/budget/items`);
    const summary = await GET(`/api/events/${state.currentEventId}/budget/summary`);
    renderBudgetSummary(summary);
    renderBudgetTable(state.budgetItems);
  } catch (e) {
    toast(`Budget load failed: ${e.message}`, 'error');
  }
}

function renderBudgetSummary(s) {
  if (!s) return;
  const cur = s.currency || '';
  const pct = s.planned_budget > 0 ? ((s.total_committed / s.planned_budget) * 100).toFixed(1) : 0;
  const el = document.getElementById('budget-summary-block');
  el.innerHTML = `
    <div class="budget-row"><span class="label">Planned Budget</span><span class="value">${cur} ${fmtNum(s.planned_budget)}</span></div>
    <div class="budget-row"><span class="label">Total Estimated</span><span class="value">${cur} ${fmtNum(s.total_estimated)}</span></div>
    <div class="budget-row"><span class="label">Total Quoted</span><span class="value">${cur} ${fmtNum(s.total_quoted)}</span></div>
    <div class="budget-row"><span class="label">Total Committed</span><span class="value ${s.is_over_budget ? 'over-budget' : ''}">${cur} ${fmtNum(s.total_committed)}</span></div>
    <div class="budget-row"><span class="label">Total Actual Paid</span><span class="value">${cur} ${fmtNum(s.total_actual)}</span></div>
    <div class="budget-row"><span class="label">Remaining (Committed)</span><span class="value ${s.is_over_budget ? 'over-budget' : 'on-track'}">${cur} ${fmtNum(s.remaining_from_committed)}</span></div>
    <div class="budget-row"><span class="label">Budget Usage</span><span class="value ${pct > 100 ? 'over-budget' : pct > 90 ? '' : 'on-track'}">${pct}%</span></div>
    ${s.alerts.length ? `<div style="margin-top:.5rem">${s.alerts.map(a => `<div style="font-size:.8rem;color:var(--warning)">⚠ ${escHtml(a)}</div>`).join('')}</div>` : ''}`;
}

function renderBudgetTable(items) {
  const tbody = document.getElementById('budget-table-body');
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="table-empty">No budget items yet. Click Add Item to start.</td></tr>';
    return;
  }
  const cur = state.currentEvent?.currency || '';
  tbody.innerHTML = items.map(item => `
    <tr>
      <td>${escHtml(item.category)}</td>
      <td>${escHtml(item.item_name)}</td>
      <td>${cur} ${fmtNum(item.estimated_amount)}</td>
      <td>${cur} ${fmtNum(item.quoted_amount)}</td>
      <td>${cur} ${fmtNum(item.committed_amount)}</td>
      <td>${cur} ${fmtNum(item.actual_amount)}</td>
      <td><span class="status-badge status-${item.status}">${item.status}</span></td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="openBudgetModal('${item.id}')" aria-label="Edit budget item">Edit</button>
        <button class="btn btn-danger btn-sm" onclick="deleteBudgetItem('${item.id}')" aria-label="Delete budget item">Del</button>
      </td>
    </tr>`).join('');
}

/* Budget Modal */
function openBudgetModal(itemId = null) {
  const item = itemId ? state.budgetItems.find(i => i.id === itemId) : null;
  document.getElementById('budget-item-modal-title').textContent = item ? 'Edit Budget Item' : 'Add Budget Item';
  document.getElementById('bi-id').value      = item?.id || '';
  document.getElementById('bi-category').value= item?.category || '';
  document.getElementById('bi-name').value    = item?.item_name || '';
  document.getElementById('bi-estimated').value= item?.estimated_amount || 0;
  document.getElementById('bi-quoted').value  = item?.quoted_amount || 0;
  document.getElementById('bi-committed').value= item?.committed_amount || 0;
  document.getElementById('bi-actual').value  = item?.actual_amount || 0;
  document.getElementById('bi-status').value  = item?.status || 'planned';
  document.getElementById('bi-notes').value   = item?.notes || '';
  document.getElementById('budget-item-error').classList.add('hidden');
  openModal('modal-budget-item');
}
window.openBudgetModal = openBudgetModal;

document.getElementById('btn-add-budget-item')?.addEventListener('click', () => openBudgetModal());

document.getElementById('budget-item-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('bi-id').value;
  const errEl = document.getElementById('budget-item-error');
  const payload = {
    category: document.getElementById('bi-category').value.trim(),
    item_name: document.getElementById('bi-name').value.trim(),
    estimated_amount: parseFloat(document.getElementById('bi-estimated').value) || 0,
    quoted_amount: parseFloat(document.getElementById('bi-quoted').value) || 0,
    committed_amount: parseFloat(document.getElementById('bi-committed').value) || 0,
    actual_amount: parseFloat(document.getElementById('bi-actual').value) || 0,
    status: document.getElementById('bi-status').value,
    notes: document.getElementById('bi-notes').value.trim(),
  };
  try {
    if (id) {
      await PATCH(`/api/events/${state.currentEventId}/budget/items/${id}`, payload);
      toast('Budget item updated.', 'success');
    } else {
      await POST(`/api/events/${state.currentEventId}/budget/items`, payload);
      toast('Budget item added.', 'success');
    }
    closeModal('modal-budget-item');
    await loadBudget();
  } catch (err) {
    errEl.textContent = err.message; errEl.classList.remove('hidden');
  }
});

async function deleteBudgetItem(id) {
  if (!confirm('Delete this budget item?')) return;
  try {
    await DELETE(`/api/events/${state.currentEventId}/budget/items/${id}`);
    toast('Budget item deleted.', 'info');
    await loadBudget();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}
window.deleteBudgetItem = deleteBudgetItem;

/* Budget Scenario */
document.getElementById('scenario-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const resultEl = document.getElementById('scenario-result');
  const btn = document.getElementById('btn-run-scenario');
  btn.disabled = true; btn.textContent = '⏳ Analyzing...';
  try {
    const result = await POST(`/api/events/${state.currentEventId}/budget/scenario`, {
      guest_count_delta: parseInt(document.getElementById('scenario-guest-delta').value) || 0,
      budget_delta_percent: parseFloat(document.getElementById('scenario-budget-delta').value) || 0,
      additional_expense: parseFloat(document.getElementById('scenario-extra-cost').value) || 0,
    });
    const cur = state.currentEvent?.currency || '';
    const feasible = result.is_feasible;
    resultEl.className = `scenario-result ${feasible ? 'feasible' : 'infeasible'}`;

    // Parse deterministic analysis lines into clean structured list items
    const analysisLines = (result.deterministic_analysis || '')
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean);

    // Format AI Advice cleanly with paragraphs
    let aiAdviceHtml = '';
    if (result.ai_tradeoff_advice) {
      const paragraphs = result.ai_tradeoff_advice
        .split('\n\n')
        .map(p => p.trim())
        .filter(Boolean);
      aiAdviceHtml = `
        <div class="scenario-ai-card">
          <div class="scenario-ai-header">
            <span class="ai-badge">&#10022; Strategic AI Evaluation (Gemini 3.8-Flash)</span>
          </div>
          <div class="scenario-ai-body">
            ${paragraphs.map(p => `<p>${escHtml(p).replace(/\n/g, '<br>')}</p>`).join('')}
          </div>
        </div>
      `;
    }

    resultEl.innerHTML = `
      <div class="scenario-header">
        <div class="scenario-feasibility-tag ${feasible ? 'tag-feasible' : 'tag-infeasible'}">
          ${feasible ? '✓ Feasible Scenario' : '⚠ Deficit Detected'}
        </div>
        <div class="scenario-variance-val ${feasible ? 'on-track' : 'over-budget'}">
          ${feasible ? '+' : ''}${cur} ${fmtNum(result.projected_variance)} Net Balance
        </div>
      </div>

      <div class="scenario-stats-grid">
        <div class="scenario-stat-card">
          <span class="label">Projected Budget</span>
          <span class="val">${cur} ${fmtNum(result.projected_budget)}</span>
          <small class="sub">Baseline: ${cur} ${fmtNum(result.original_budget)}</small>
        </div>
        <div class="scenario-stat-card">
          <span class="label">Projected Guests</span>
          <span class="val">${result.projected_guest_count}</span>
          <small class="sub">Original: ${result.original_guest_count}</small>
        </div>
        <div class="scenario-stat-card">
          <span class="label">Cost Impact</span>
          <span class="val ${result.projected_cost_impact > 0 ? 'over-budget' : ''}">
            ${result.projected_cost_impact >= 0 ? '+' : ''}${cur} ${fmtNum(result.projected_cost_impact)}
          </span>
          <small class="sub">Guest &amp; Expense Impact</small>
        </div>
        <div class="scenario-stat-card">
          <span class="label">Feasibility</span>
          <span class="val ${feasible ? 'on-track' : 'over-budget'}">
            ${feasible ? 'Surplus' : 'Deficit'}
          </span>
          <small class="sub">${feasible ? 'Within Limits' : 'Requires Trimming'}</small>
        </div>
      </div>

      <div class="scenario-breakdown">
        <h5>Detailed Deterministic Calculations</h5>
        <ul>
          ${analysisLines.map(line => `<li>${escHtml(line)}</li>`).join('')}
        </ul>
      </div>

      ${aiAdviceHtml}
    `;
    resultEl.classList.remove('hidden');
  } catch (err) {
    resultEl.className = 'scenario-result infeasible';
    resultEl.textContent = `Error: ${err.message}`;
    resultEl.classList.remove('hidden');
  } finally {
    btn.disabled = false; btn.textContent = '⚡ Run What-If';
  }
});

/* ══════════════════════════════════════════════
   TIMELINE TAB
   ══════════════════════════════════════════════ */
async function loadTasks() {
  if (!state.currentEventId) return;
  try {
    state.tasks = await GET(`/api/events/${state.currentEventId}/tasks`);
    renderTaskList();
  } catch (e) {
    toast(`Tasks load failed: ${e.message}`, 'error');
  }
}

function renderTaskList() {
  const statusFilter   = document.getElementById('task-filter-status')?.value || '';
  const priorityFilter = document.getElementById('task-filter-priority')?.value || '';
  let tasks = state.tasks;
  if (statusFilter)   tasks = tasks.filter(t => t.status === statusFilter);
  if (priorityFilter) tasks = tasks.filter(t => t.priority === priorityFilter);

  // Progress bar
  const total = state.tasks.length;
  const done  = state.tasks.filter(t => t.status === 'completed').length;
  const pct   = total ? Math.round((done / total) * 100) : 0;
  const fill  = document.getElementById('task-progress-fill');
  const label = document.getElementById('task-progress-label');
  if (fill)  { fill.style.width = pct + '%'; fill.setAttribute('aria-valuenow', pct); }
  if (label) label.textContent = `${pct}% Complete (${done}/${total})`;

  const container = document.getElementById('task-list-container');
  if (!tasks.length) {
    container.innerHTML = '<p class="muted" style="padding:1.5rem">No tasks match the current filter.</p>';
    return;
  }
  container.innerHTML = tasks.map(task => {
    const overdue = task.is_overdue;
    const classes = ['task-item', overdue ? 'overdue' : '', task.status === 'completed' ? 'completed' : ''].filter(Boolean).join(' ');
    const due = task.due_date ? `Due: ${task.due_date}` : '';
    const days = task.days_remaining != null ? `(${task.days_remaining < 0 ? Math.abs(task.days_remaining) + 'd overdue' : task.days_remaining + 'd left'})` : '';
    return `
      <div class="${classes}" role="listitem">
        <input type="checkbox" class="task-checkbox" ${task.status === 'completed' ? 'checked' : ''}
          onchange="toggleTaskStatus('${task.id}', this.checked)" aria-label="Mark task complete" />
        <div class="task-info">
          <div class="task-title-text">${escHtml(task.title)}</div>
          <div class="task-meta">
            <span class="status-badge status-${task.status}">${task.status.replace('_', ' ')}</span>
            <span class="priority-${task.priority}">${task.priority}</span>
            <span>${escHtml(task.category)}</span>
            ${due ? `<span ${overdue ? 'class="task-overdue-tag"' : ''}>${due} ${days}</span>` : ''}
            ${task.assignee ? `<span>👤 ${escHtml(task.assignee)}</span>` : ''}
          </div>
        </div>
        <div class="task-actions">
          <button class="btn btn-ghost btn-sm" onclick="openTaskModal('${task.id}')" aria-label="Edit task">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deleteTask('${task.id}')" aria-label="Delete task">Del</button>
        </div>
      </div>`;
  }).join('');
}

async function toggleTaskStatus(taskId, checked) {
  try {
    await PATCH(`/api/events/${state.currentEventId}/tasks/${taskId}`, {
      status: checked ? 'completed' : 'todo'
    });
    await loadTasks();
  } catch (e) {
    toast(`Update failed: ${e.message}`, 'error');
  }
}
window.toggleTaskStatus = toggleTaskStatus;

function openTaskModal(taskId = null) {
  const task = taskId ? state.tasks.find(t => t.id === taskId) : null;
  document.getElementById('task-modal-title').textContent = task ? 'Edit Task' : 'New Task';
  document.getElementById('task-id').value        = task?.id || '';
  document.getElementById('task-title').value     = task?.title || '';
  document.getElementById('task-category').value  = task?.category || 'General';
  document.getElementById('task-assignee').value  = task?.assignee || '';
  document.getElementById('task-due').value       = task?.due_date?.slice(0,10) || '';
  document.getElementById('task-priority').value  = task?.priority || 'medium';
  document.getElementById('task-status').value    = task?.status || 'todo';
  document.getElementById('task-notes').value     = task?.notes || '';
  document.getElementById('task-error').classList.add('hidden');
  openModal('modal-task');
}
window.openTaskModal = openTaskModal;

document.getElementById('btn-add-task')?.addEventListener('click', () => openTaskModal());

document.getElementById('task-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('task-id').value;
  const errEl = document.getElementById('task-error');
  const payload = {
    title: document.getElementById('task-title').value.trim(),
    category: document.getElementById('task-category').value.trim(),
    assignee: document.getElementById('task-assignee').value.trim() || null,
    due_date: document.getElementById('task-due').value || null,
    priority: document.getElementById('task-priority').value,
    status: document.getElementById('task-status').value,
    notes: document.getElementById('task-notes').value.trim(),
  };
  try {
    if (id) {
      await PATCH(`/api/events/${state.currentEventId}/tasks/${id}`, payload);
      toast('Task updated.', 'success');
    } else {
      await POST(`/api/events/${state.currentEventId}/tasks`, payload);
      toast('Task added.', 'success');
    }
    closeModal('modal-task');
    await loadTasks();
  } catch (err) {
    errEl.textContent = err.message; errEl.classList.remove('hidden');
  }
});

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return;
  try {
    await DELETE(`/api/events/${state.currentEventId}/tasks/${id}`);
    toast('Task deleted.', 'info');
    await loadTasks();
  } catch (e) { toast(`Delete failed: ${e.message}`, 'error'); }
}
window.deleteTask = deleteTask;

document.getElementById('task-filter-status')?.addEventListener('change', renderTaskList);
document.getElementById('task-filter-priority')?.addEventListener('change', renderTaskList);

/* ══════════════════════════════════════════════
   VENDORS TAB
   ══════════════════════════════════════════════ */
async function loadVendors() {
  if (!state.currentEventId) return;
  try {
    state.vendors = await GET(`/api/events/${state.currentEventId}/vendors`);
    renderVendorTable(state.vendors);
  } catch (e) {
    toast(`Vendors load failed: ${e.message}`, 'error');
  }
}

function renderVendorTable(vendors) {
  const tbody = document.getElementById('vendor-table-body');
  if (!vendors.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No vendors yet. Add your first vendor.</td></tr>';
    return;
  }
  const cur = state.currentEvent?.currency || '';
  tbody.innerHTML = vendors.map(v => `
    <tr>
      <td>${escHtml(v.name)}</td>
      <td>${escHtml(v.category)}</td>
      <td>${v.contact_person ? escHtml(v.contact_person) : '--'}${v.contact_phone ? `<br><small>${escHtml(v.contact_phone)}</small>` : ''}</td>
      <td>${cur} ${fmtNum(v.quotation_amount)}</td>
      <td><span class="status-badge status-${v.status}">${v.status}</span></td>
      <td>${v.follow_up_date ? v.follow_up_date.slice(0,10) : '--'}</td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="openVendorModal('${v.id}')" aria-label="Edit vendor">Edit</button>
        <button class="btn btn-danger btn-sm" onclick="deleteVendor('${v.id}')" aria-label="Delete vendor">Del</button>
      </td>
    </tr>`).join('');
}

function openVendorModal(vendorId = null) {
  const v = vendorId ? state.vendors.find(x => x.id === vendorId) : null;
  document.getElementById('vendor-modal-title').textContent = v ? 'Edit Vendor' : 'Add Vendor';
  document.getElementById('vendor-id').value              = v?.id || '';
  document.getElementById('vendor-name').value            = v?.name || '';
  document.getElementById('vendor-category').value        = v?.category || '';
  document.getElementById('vendor-contact-person').value  = v?.contact_person || '';
  document.getElementById('vendor-phone').value           = v?.contact_phone || '';
  document.getElementById('vendor-email').value           = v?.contact_email || '';
  document.getElementById('vendor-quotation').value       = v?.quotation_amount || 0;
  document.getElementById('vendor-status').value          = v?.status || 'enquiry';
  document.getElementById('vendor-followup').value        = v?.follow_up_date?.slice(0,10) || '';
  document.getElementById('vendor-notes').value           = v?.notes || '';
  document.getElementById('vendor-error').classList.add('hidden');
  openModal('modal-vendor');
}
window.openVendorModal = openVendorModal;

document.getElementById('btn-add-vendor')?.addEventListener('click', () => openVendorModal());

document.getElementById('vendor-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('vendor-id').value;
  const errEl = document.getElementById('vendor-error');
  const payload = {
    name: document.getElementById('vendor-name').value.trim(),
    category: document.getElementById('vendor-category').value.trim(),
    contact_person: document.getElementById('vendor-contact-person').value.trim() || null,
    contact_phone: document.getElementById('vendor-phone').value.trim() || null,
    contact_email: document.getElementById('vendor-email').value.trim() || null,
    quotation_amount: parseFloat(document.getElementById('vendor-quotation').value) || 0,
    status: document.getElementById('vendor-status').value,
    follow_up_date: document.getElementById('vendor-followup').value || null,
    notes: document.getElementById('vendor-notes').value.trim(),
  };
  try {
    if (id) {
      await PATCH(`/api/events/${state.currentEventId}/vendors/${id}`, payload);
      toast('Vendor updated.', 'success');
    } else {
      await POST(`/api/events/${state.currentEventId}/vendors`, payload);
      toast('Vendor added.', 'success');
    }
    closeModal('modal-vendor');
    await loadVendors();
  } catch (err) {
    errEl.textContent = err.message; errEl.classList.remove('hidden');
  }
});

async function deleteVendor(id) {
  if (!confirm('Delete this vendor?')) return;
  try {
    await DELETE(`/api/events/${state.currentEventId}/vendors/${id}`);
    toast('Vendor deleted.', 'info');
    await loadVendors();
  } catch (e) { toast(`Delete failed: ${e.message}`, 'error'); }
}
window.deleteVendor = deleteVendor;

/* ══════════════════════════════════════════════
   CHROMADB SEMANTIC VENDOR DISCOVERY
   ══════════════════════════════════════════════ */
async function searchVendorsSemantic() {
  if (!state.currentEventId) {
    toast('Please select an event first.', 'warning');
    return;
  }
  const input = document.getElementById('vendor-semantic-input');
  const catSelect = document.getElementById('vendor-semantic-category');
  const resultsEl = document.getElementById('vendor-semantic-results');
  const btn = document.getElementById('btn-vendor-semantic-search');
  const q = input?.value.trim();
  if (!q) {
    toast('Please enter natural language search terms for vector search.', 'warning');
    return;
  }
  const category = catSelect?.value || '';
  btn.disabled = true;
  btn.textContent = '⏳ Searching Vectors...';
  try {
    const url = `/api/events/${state.currentEventId}/vendors/semantic-search?q=${encodeURIComponent(q)}${category ? '&category=' + encodeURIComponent(category) : ''}`;
    const results = await GET(url);
    if (!results || !results.length) {
      resultsEl.innerHTML = '<p class="muted">No matching suppliers found in ChromaDB vector collection.</p>';
      resultsEl.classList.remove('hidden');
      return;
    }
    resultsEl.innerHTML = `
      <div style="font-weight:600;margin-bottom:0.75rem;font-size:0.9rem;color:var(--text-primary)">
        ⚡ ChromaDB Vector Recommendations (${results.length}):
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));gap:0.75rem;">
        ${results.map(r => `
          <div style="background:rgba(255,255,255,0.04);border:1px solid var(--border-color);border-radius:8px;padding:0.75rem 1rem;display:flex;flex-direction:column;justify-content:space-between;">
            <div>
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <strong style="color:var(--primary);font-size:0.95rem;">${escHtml(r.name)}</strong>
                <span class="status-badge" style="background:rgba(99,102,241,0.2);color:#a5b4fc;font-size:0.75rem;">${escHtml(r.category)}</span>
              </div>
              <p style="font-size:0.82rem;color:var(--text-muted);margin:0.4rem 0 0.6rem;line-height:1.4;">${escHtml(r.description)}</p>
              ${r.metadata?.price_range ? `<span style="font-size:0.75rem;color:var(--text-secondary);margin-right:0.5rem;">Tier: <b>${escHtml(r.metadata.price_range)}</b></span>` : ''}
              ${r.metadata?.city ? `<span style="font-size:0.75rem;color:var(--text-secondary);">City: <b>${escHtml(r.metadata.city)}</b></span>` : ''}
            </div>
            <div style="margin-top:0.75rem;display:flex;gap:0.5rem;align-items:center;">
              <button class="btn btn-primary btn-sm" onclick="quickAddVendor('${escHtml(r.name.replace(/'/g, "\\'"))}', '${escHtml(r.category)}')">+ Add to Event</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    resultsEl.classList.remove('hidden');
  } catch (err) {
    toast(`Vector search error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Search Vectors';
  }
}

function quickAddVendor(name, category) {
  openVendorModal();
  document.getElementById('vendor-name').value = name;
  document.getElementById('vendor-category').value = category;
  document.getElementById('vendor-notes').value = 'Discovered via ChromaDB semantic vector search';
}
window.quickAddVendor = quickAddVendor;

document.getElementById('btn-vendor-semantic-search')?.addEventListener('click', searchVendorsSemantic);
document.getElementById('vendor-semantic-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    searchVendorsSemantic();
  }
});

/* ══════════════════════════════════════════════
   PLAN RESCUE TAB
   ══════════════════════════════════════════════ */
document.getElementById('rescue-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!state.currentEventId) { toast('Select an event first.', 'warning'); return; }
  const btn = document.getElementById('btn-rescue-submit');
  btn.disabled = true; btn.textContent = '⏳ Gemini is analyzing...';
  const panel = document.getElementById('rescue-proposal-panel');
  panel.classList.add('hidden');
  try {
    const payload = {
      scenario_type: document.getElementById('rescue-scenario-type').value,
      description:   document.getElementById('rescue-description').value.trim(),
      target_budget: parseFloat(document.getElementById('rescue-new-budget').value) || null,
      new_guest_count: parseInt(document.getElementById('rescue-new-guests').value) || null,
    };
    const proposal = await POST(`/api/events/${state.currentEventId}/rescue/propose`, payload);
    state.currentRescueId = proposal.rescue_id;
    renderRescueProposal(proposal);
    panel.classList.remove('hidden');
    toast('Rescue plan generated!', 'success');
  } catch (err) {
    toast(`Rescue failed: ${err.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '🚨 Generate Rescue Plan';
  }
});

function renderRescueProposal(p) {
  document.getElementById('rescue-proposal-id').textContent = `ID: ${p.rescue_id}`;
  const el = document.getElementById('rescue-proposal-content');

  const budgetRows = (p.proposed_budget_adjustments || []).map(b =>
    `<li><strong>${escHtml(b.category)} — ${escHtml(b.item_name)}:</strong> ${escHtml(b.current_estimate.toLocaleString())} → ${escHtml(b.proposed_estimate.toLocaleString())} <em>(${escHtml(b.adjustment_reason)})</em></li>`
  ).join('');
  const taskRows = (p.proposed_task_actions || []).map(t =>
    `<li><span class="status-badge status-${t.action === 'add' ? 'quoted' : t.action === 'delete' ? 'rejected' : 'in_progress'}">${t.action}</span> <strong>${escHtml(t.title)}</strong> — ${escHtml(t.priority)} priority${t.notes ? ' — ' + escHtml(t.notes) : ''}</li>`
  ).join('');
  const actions = (p.immediate_actions || []).map(a => `<li>${escHtml(a)}</li>`).join('');

  el.innerHTML = `
    <div class="rescue-proposal-section">
      <h4>Situation Summary</h4>
      <p>${formatAiMarkdown(p.situation_summary || '')}</p>
    </div>
    <div class="rescue-proposal-section">
      <h4>Tradeoffs &amp; Impact</h4>
      <p>${formatAiMarkdown(p.tradeoffs_and_impact || '')}</p>
    </div>
    ${budgetRows ? `<div class="rescue-proposal-section"><h4>Proposed Budget Adjustments</h4><ul>${budgetRows}</ul></div>` : ''}
    ${taskRows   ? `<div class="rescue-proposal-section"><h4>Proposed Task Changes</h4><ul>${taskRows}</ul></div>` : ''}
    ${actions    ? `<div class="rescue-proposal-section"><h4>Immediate Actions</h4><ul>${actions}</ul></div>` : ''}`;
}

document.getElementById('btn-apply-rescue')?.addEventListener('click', async () => {
  if (!state.currentRescueId) return;
  const btn = document.getElementById('btn-apply-rescue');
  btn.disabled = true; btn.textContent = '⏳ Applying...';
  try {
    await POST(`/api/events/${state.currentEventId}/rescue/apply`, {
      rescue_id: state.currentRescueId,
      apply_event_updates: document.getElementById('apply-event-updates').checked,
      apply_budget_adjustments: document.getElementById('apply-budget-adj').checked,
      apply_task_actions: document.getElementById('apply-task-actions').checked,
    });
    toast('Plan Rescue applied successfully!', 'success');
    await loadBlueprint();
  } catch (e) {
    toast(`Apply failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '✓ Apply Plan Rescue';
  }
});

/* ══════════════════════════════════════════════
   COPILOT
   ══════════════════════════════════════════════ */
function openCopilot() {
  const drawer = document.getElementById('copilot-drawer');
  const overlay = document.getElementById('copilot-overlay');
  drawer.removeAttribute('hidden');
  overlay.classList.remove('hidden');
  document.getElementById('copilot-input')?.focus();
}
function closeCopilot() {
  const drawer = document.getElementById('copilot-drawer');
  const overlay = document.getElementById('copilot-overlay');
  drawer.setAttribute('hidden', '');
  overlay.classList.add('hidden');
}

document.getElementById('btn-open-copilot')?.addEventListener('click', openCopilot);
document.getElementById('btn-close-copilot')?.addEventListener('click', closeCopilot);
document.getElementById('copilot-overlay')?.addEventListener('click', closeCopilot);

document.getElementById('copilot-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('copilot-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  appendCopilotMsg(msg, 'user');
  const loadingEl = appendCopilotLoading();

  try {
    const result = await POST(`/api/events/${state.currentEventId}/copilot/chat`, { message: msg });
    loadingEl.remove();
    appendCopilotMsg(result.reply || 'No response from AI.', 'bot');
    if (result.suggested_actions?.length) {
      const actionsEl = document.createElement('div');
      actionsEl.className = 'copilot-msg bot';
      actionsEl.innerHTML = `<span class="msg-avatar">🤖</span><div class="msg-bubble" style="font-size:.8rem">
        ${result.suggested_actions.map(a => `<div style="margin-bottom:.25rem">→ ${escHtml(a)}</div>`).join('')}
      </div>`;
      document.getElementById('copilot-messages').appendChild(actionsEl);
    }
  } catch (err) {
    loadingEl.remove();
    appendCopilotMsg(`Sorry, AI is unavailable: ${err.message}`, 'bot');
  }
  scrollCopilotToBottom();
});

function appendCopilotMsg(text, role) {
  const msgs = document.getElementById('copilot-messages');
  const el = document.createElement('div');
  el.className = `copilot-msg ${role}`;
  const content = role === 'bot' ? formatAiMarkdown(text) : escHtml(text);
  el.innerHTML = `<span class="msg-avatar">${role === 'bot' ? '🤖' : '👤'}</span><div class="msg-bubble">${content}</div>`;
  msgs.appendChild(el);
  scrollCopilotToBottom();
  return el;
}

function appendCopilotLoading() {
  const msgs = document.getElementById('copilot-messages');
  const el = document.createElement('div');
  el.className = 'copilot-msg bot loading';
  el.innerHTML = `<span class="msg-avatar">🤖</span><div class="msg-bubble">
    <span class="copilot-loading-dot"></span>
    <span class="copilot-loading-dot"></span>
    <span class="copilot-loading-dot"></span>
  </div>`;
  msgs.appendChild(el);
  scrollCopilotToBottom();
  return el;
}

function scrollCopilotToBottom() {
  const msgs = document.getElementById('copilot-messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

/* ══════════════════════════════════════════════
   NEW EVENT MODAL
   ══════════════════════════════════════════════ */
function openNewEventModal() {
  document.getElementById('new-event-form')?.reset();
  document.getElementById('new-event-error').classList.add('hidden');
  // Set min date to today
  const today = new Date().toISOString().slice(0,10);
  document.getElementById('ne-date').min = today;
  openModal('modal-new-event');
}

document.getElementById('btn-new-event')?.addEventListener('click', openNewEventModal);
document.getElementById('btn-new-event-center')?.addEventListener('click', openNewEventModal);

document.getElementById('new-event-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const errEl = document.getElementById('new-event-error');
  const btn = document.getElementById('btn-create-event-submit');
  btn.disabled = true; btn.textContent = '⏳ Creating...';

  const payload = {
    title:      document.getElementById('ne-title').value.trim(),
    event_type: document.getElementById('ne-type').value,
    date:       document.getElementById('ne-date').value,
    time_details: document.getElementById('ne-time').value.trim() || null,
    location:   document.getElementById('ne-location').value.trim(),
    guest_count: parseInt(document.getElementById('ne-guests').value),
    budget:     parseFloat(document.getElementById('ne-budget').value),
    currency:   document.getElementById('ne-currency').value,
    theme:      document.getElementById('ne-theme').value.trim() || null,
    cultural_preferences: document.getElementById('ne-cultural').value.trim() || null,
    priorities_constraints: document.getElementById('ne-constraints').value.trim() || null,
  };

  try {
    const ev = await POST('/api/events', payload);
    state.events.unshift(ev);
    closeModal('modal-new-event');
    if (ev.plan_status === 'unplanned') {
      toast(`Event "${ev.title}" saved. ${ev.plan_warning || 'Click "↻ Regenerate" in Blueprint to retry AI planning.'}`, 'info');
    } else {
      toast(`Event "${ev.title}" created with AI Blueprint!`, 'success');
    }
    renderEventList();
    await selectEvent(ev.id);
  } catch (err) {
    errEl.textContent = err.message; errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false; btn.textContent = '✨ Create & Generate AI Plan';
  }
});

/* ══════════════════════════════════════════════
   SETTINGS MODAL
   ══════════════════════════════════════════════ */
async function refreshSettingsModalStatus() {
  const statusEl = document.getElementById('settings-status');
  const badgeEl = document.getElementById('settings-connection-badge');
  if (badgeEl) {
    badgeEl.innerHTML = '<span class="status-dot"></span> Checking live status...';
  }
  try {
    const h = await GET('/api/health');
    const ai = h?.ai || h?.generative_ai || {};
    if (ai.connected) {
      if (badgeEl) badgeEl.innerHTML = '<span class="status-dot connected"></span> <strong style="color:var(--success)">Connected &amp; Verified</strong>';
      setStatus(statusEl, 'success', `✓ Live connection active with ${ai.model || 'gemini-3.8-flash'} via server .env`);
      updateAiStatusIndicator(true, ai.model || 'gemini-3.8-flash');
    } else if (ai.status === 'quota_exhausted') {
      if (badgeEl) badgeEl.innerHTML = '<span class="status-dot error"></span> <strong style="color:var(--warning)">Quota Exhausted (429)</strong>';
      setStatus(statusEl, 'warning', `⚠ Account quota reached for ${ai.model || 'gemini-3.8-flash'} (HTTP 429). The app operates in offline/deterministic mode.`);
      updateAiStatusIndicator(false, 'Quota Limit');
    } else if (ai.key_configured) {
      if (badgeEl) badgeEl.innerHTML = '<span class="status-dot connected"></span> <strong style="color:var(--success)">Online &bull; Loaded from .env</strong>';
      setStatus(statusEl, 'success', `✓ Gemini 3.8-Flash is securely loaded from server .env. Click "Test Live Connection" to perform an instant smoke check.`);
      updateAiStatusIndicator(true, ai.model || 'gemini-3.8-flash');
    } else {
      if (badgeEl) badgeEl.innerHTML = '<span class="status-dot error"></span> <span style="color:var(--text-muted)">Unconfigured</span>';
      setStatus(statusEl, 'warning', 'No API key configured in server environment (.env).');
      updateAiStatusIndicator(false, 'Offline');
    }
  } catch (e) {
    if (badgeEl) badgeEl.innerHTML = '<span class="status-dot error"></span> <span style="color:var(--danger)">Unavailable</span>';
    setStatus(statusEl, 'error', `Could not reach health check: ${e.message}`);
  }
}

document.getElementById('btn-open-settings')?.addEventListener('click', async () => {
  openModal('modal-settings');
  await refreshSettingsModalStatus();
});

// Dedicated on-demand test connection button (uses server-side .env key)
document.getElementById('btn-test-settings')?.addEventListener('click', async () => {
  const btn = document.getElementById('btn-test-settings');
  const statusEl = document.getElementById('settings-status');

  btn.disabled = true;
  btn.textContent = '⏳ Testing...';
  setStatus(statusEl, 'loading', 'Sending smoke test to Gemini 3.8-Flash via server key...');

  try {
    const res = await POST('/api/health/verify-ai', {});
    const ai = res?.ai || res?.generative_ai || {};
    if (ai.connected) {
      setStatus(statusEl, 'success', `✓ Verified! Model ${ai.model} responded successfully.`);
      state.aiConnected = true;
      updateAiStatusIndicator(true, ai.model);
      toast('Live Gemini connectivity verified!', 'success');
    } else if (ai.status === 'quota_exhausted') {
      setStatus(statusEl, 'warning', `⚠ Key is valid, but account quota reached (HTTP 429). Calculations remain 100% active in deterministic mode.`);
      state.aiConnected = false;
      updateAiStatusIndicator(false, 'Quota Limit');
    } else if (ai.status === 'timeout') {
      setStatus(statusEl, 'warning', `⚠ ${ai.message || 'Connection check timed out.'}`);
      state.aiConnected = false;
      updateAiStatusIndicator(false, 'Timeout');
    } else {
      setStatus(statusEl, 'error', `✕ Smoke test failed: ${ai.message || 'No response'}`);
      state.aiConnected = false;
      updateAiStatusIndicator(false, 'Offline');
    }
  } catch (e) {
    setStatus(statusEl, 'error', `Smoke test error: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Test Live Connection';
    const badgeEl = document.getElementById('settings-connection-badge');
    if (badgeEl) {
      if (state.aiConnected) {
        badgeEl.innerHTML = '<span class="status-dot connected"></span> <strong style="color:var(--success)">Connected &amp; Verified</strong>';
      } else {
        badgeEl.innerHTML = '<span class="status-dot error"></span> <strong style="color:var(--warning)">Offline / Limited</strong>';
      }
    }
  }
});

/* ══════════════════════════════════════════════
   MODAL HELPERS
   ══════════════════════════════════════════════ */
function openModal(id) {
  document.getElementById(id)?.classList.remove('hidden');
}
function closeModal(id) {
  document.getElementById(id)?.classList.add('hidden');
}

// Close buttons via data-modal attribute
document.querySelectorAll('[data-modal]').forEach(btn => {
  btn.addEventListener('click', () => closeModal(btn.dataset.modal));
});
document.querySelectorAll('.modal-close').forEach(btn => {
  btn.addEventListener('click', () => {
    const modal = btn.closest('.modal-overlay');
    if (modal) modal.classList.add('hidden');
  });
});
// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.add('hidden');
  });
});
// ESC key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => m.classList.add('hidden'));
    closeCopilot();
  }
});

/* ══════════════════════════════════════════════
   SIDEBAR TOGGLE
   ══════════════════════════════════════════════ */
document.getElementById('btn-sidebar-toggle')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.toggle('collapsed');
});
// Topbar hamburger — reopen collapsed sidebar
document.getElementById('btn-sidebar-open')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.remove('collapsed');
});

/* ══════════════════════════════════════════════
   UTILITIES
   ══════════════════════════════════════════════ */
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');
}
function formatAiMarkdown(str) {
  if (str == null) return '';
  let s = escHtml(str);
  // Bold **text** -> <strong>text</strong>
  s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text* -> <em>text</em>
  s = s.replace(/(^|[^\*])\*([^\*\n]+)\*([^\*]|$)/g, '$1<em>$2</em>$3');
  // Bullet items starting with * or -
  s = s.replace(/^[*-•]\s+(.+)$/gm, '<div style="margin-left:0.5rem; margin-bottom:0.25rem;">• $1</div>');
  // Numbered list items
  s = s.replace(/^(\d+)\.\s+(.+)$/gm, '<div style="margin-left:0.5rem; margin-bottom:0.25rem;">$1. $2</div>');
  // Line breaks
  s = s.replace(/\n\n+/g, '<br><br>').replace(/\n/g, '<br>');
  return s;
}
function fmtNum(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

/* ══════════════════════════════════════════════
   BOOTSTRAP
   ══════════════════════════════════════════════ */
async function main() {
  // Show brief loading animation
  await new Promise(r => setTimeout(r, 600));

  await initSession();

  hideLoading();

  // Initialize multilingual selector
  initLanguageSelectors();

  // Always land on the Home Portal first:
  // Shows 1-click Evaluator Login, Guest Sandbox, AI Status, and 4-Step Interactive Guide!
  showHomeScreen();

  document.getElementById('btn-topbar-home')?.addEventListener('click', showHomeScreen);
  document.getElementById('btn-sidebar-home')?.addEventListener('click', showHomeScreen);
  document.getElementById('btn-topbar-logout')?.addEventListener('click', logoutUser);

  initTabs();
}

main().catch(console.error);
