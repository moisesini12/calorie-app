# app.py


import hashlib, hmac, base64

import streamlit as st
import pandas as pd

from datetime import date

from db_gsheets import (
    init_db, seed_foods_if_empty,
    list_categories, list_foods_by_category, add_food,
    add_entry, list_entries_by_date, daily_totals_last_days,
    set_setting, get_setting,
    list_all_foods, update_food, delete_food_by_id,
    update_entry, delete_entry_by_id
)
from core import scale_macros, calculate_goals
from your_foods import FOODS


# ✅ SIEMPRE lo primero (y SOLO una vez)
st.set_page_config(
    page_title="FitMacro",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_black_theme():
    st.markdown(r"""
    <style>
    /* =========================
       FITMACRO — DARK PRO (FIX WHITE BANDS)
       ========================= */

    :root{
        --bg0:#0b1220;
        --bg1:#0f1b2e;

        --glass: rgba(255,255,255,0.10);
        --glass2: rgba(255,255,255,0.07);

        --stroke: rgba(255,255,255,0.16);
        --stroke2: rgba(255,255,255,0.10);

        --txt: rgba(255,255,255,0.92);
        --muted: rgba(226,232,240,0.72);

        --g:#22c55e;
        --b:#60a5fa;

        --r16: 16px;
        --r18: 18px;
        --r22: 22px;
    }

    /* ====== HARD RESET: QUITAR FONDOS BLANCOS EN TODA LA CADENA ====== */
    html, body{
        background: transparent !important;
        color: var(--txt) !important;
    }

    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main,
    section.main > div,
    .block-container{
        background: transparent !important;
    }

    html, body{
      min-height: 100%;
      background: transparent !important;
    }
    
    /* Fondo FIJO que nunca “se corta” al hacer scroll */
    body::before{
      content:"";
      position: fixed;
      inset: 0;
      z-index: -1;
      background:
        radial-gradient(1100px 750px at 12% 12%, rgba(34,197,94,0.18) 0%, transparent 60%),
        radial-gradient(1000px 700px at 88% 12%, rgba(96,165,250,0.18) 0%, transparent 60%),
        radial-gradient(900px 650px at 60% 85%, rgba(96,165,250,0.10) 0%, transparent 60%),
        linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%);
    }

    /* Evita “cortes” raros de sombras */
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main,
    section.main > div,
    .block-container{
        overflow: visible !important;
    }

    .block-container{
        max-width: 1180px;
        padding-top: 18px !important;
        padding-bottom: 56px !important;
    }

    /* ===== TIPOGRAFÍA ===== */
    h1{
        font-size: 44px !important;
        font-weight: 950 !important;
        letter-spacing: -0.04em;
        color: var(--txt) !important;
    }
    h2,h3{
        font-weight: 900 !important;
        color: var(--txt) !important;
    }
    p,label,.stCaption,.stMarkdown{
        color: var(--muted) !important;
    }

    /* ===== INPUTS ===== */
    input, textarea, div[data-baseweb="select"] > div{
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 14px !important;
        color: var(--txt) !important;
        font-weight: 650 !important;
    }
    div[data-baseweb="select"] span{
        color: var(--txt) !important;
    }

    /* ===== BOTONES (MAIN) ===== */
    [data-testid="stAppViewContainer"] .stButton > button,
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button{
        background: linear-gradient(135deg, var(--g), var(--b)) !important;
        color: #06101c !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 10px 18px !important;
        font-weight: 900 !important;
        box-shadow:
            0 14px 34px rgba(34,197,94,0.14),
            0 14px 34px rgba(96,165,250,0.12) !important;
        transition: all .15s ease;
    }
    [data-testid="stAppViewContainer"] .stButton > button:hover{
        transform: translateY(-1px);
        filter: brightness(1.04);
    }
    button:disabled{
        opacity: .55 !important;
        box-shadow: none !important;
    }

    /* ===== MÉTRICAS (GLASS PRO, GLOW CONTROLADO) ===== */
    div[data-testid="stMetric"]{
        background: linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.08)) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 22px !important;
        padding: 18px !important;
        backdrop-filter: blur(14px);
        box-shadow:
            0 0 0 1px rgba(255,255,255,0.03),
            0 10px 28px rgba(0,0,0,0.35) !important;
    }
    div[data-testid="stMetric"] label{
        color: rgba(226,232,240,0.78) !important;
        font-weight: 800 !important;
        font-size: 13px !important;
    }
    div[data-testid="stMetricValue"]{
        color: #fff !important;
        font-weight: 950 !important;
        font-size: 36px !important;
    }

    /* ===== PROGRESS ===== */
    [data-testid="stProgress"] > div{
        background: rgba(255,255,255,0.10) !important;
        border-radius: 999px !important;
    }

    /* ===== VEGA/ALTAIR: quita fondos blancos ===== */
    .vega-embed, .vega-embed details, .vega-embed summary{
        background: transparent !important;
    }
    .vega-embed .chart-wrapper{
        background: transparent !important;
    }
    /* algunos renders meten un div blanco alrededor */
    [data-testid="stVegaLiteChart"], 
    [data-testid="stVegaLiteChart"] > div,
    [data-testid="stVegaLiteChart"] svg,
    [data-testid="stVegaLiteChart"] canvas{
        background: transparent !important;
    }

    /* ===== SIDEBAR BASE ===== */
    [data-testid="stSidebar"] > div{
        background: rgba(10,14,22,0.72) !important;
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }

    /* Mantén visible el “brand card” que tú pintas con markdown (.sb-brand) */
    .sb-brand{
        display:flex;
        align-items:center;
        gap:12px;
        padding:12px 12px;
        margin:8px 10px 14px 10px;
        border-radius:18px;
        background: linear-gradient(135deg, rgba(34,197,94,0.16), rgba(96,165,250,0.14));
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 18px 46px rgba(0,0,0,0.35);
    }
    .sb-logo{
        width:44px;height:44px;
        border-radius:14px;
        background: linear-gradient(135deg, #16a34a, #2563eb);
        display:flex;align-items:center;justify-content:center;
        font-weight:900;color:#fff;
    }
    .sb-title .sb-name{
        font-size:18px;font-weight:900;color:#eaf0ff;line-height:1.1;
    }
    .sb-title .sb-sub{
        font-size:12px;font-weight:650;color:rgba(234,240,255,0.70);
    }

    /* Inputs sidebar */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div{
        background: rgba(255,255,255,0.06) !important;
        color: #eaf0ff !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 14px !important;
    }

    /* ===== EXPANDERS SIDEBAR (ESTABLES) ===== */
    [data-testid="stSidebar"] [data-testid="stExpander"]{
        margin: 10px 10px !important;
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details{
        border: none !important;
        background: transparent !important;
    }

    /* Header del expander */
    [data-testid="stSidebar"] [data-testid="stExpander"] details > summary{
        background: linear-gradient(135deg, rgba(34,197,94,0.92), rgba(37,99,235,0.92)) !important;
        color: #07121f !important;
        border-radius: 999px !important;
        padding: 10px 14px !important;
        font-weight: 950 !important;
        border: none !important;
        box-shadow: 0 16px 40px rgba(0,0,0,0.28) !important;
        list-style: none !important;
    }
    [data-testid="stSidebar"] summary::-webkit-details-marker{
        display:none !important;
    }

    /* CUERPO (clave para que NO “salgan” fuera los botones) */
    [data-testid="stSidebar"] [data-testid="stExpanderDetails"]{
        margin-top: 10px !important;
        padding: 10px !important;
        border-radius: 18px !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        overflow: hidden !important; /* <- importante: encierra los botones dentro */
    }

    /* Botones nav dentro del expander */
    [data-testid="stSidebar"] [data-testid="stExpanderDetails"] .stButton > button{
        width: 100% !important;
        border-radius: 999px !important;
        padding: 10px 14px !important;
        font-weight: 850 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        background: rgba(255,255,255,0.06) !important;
        color: #eaf0ff !important;
        box-shadow: none !important;
        margin: 6px 0 !important;
        transition: all .12s ease;
    }
    [data-testid="stSidebar"] [data-testid="stExpanderDetails"] .stButton > button[kind="primary"]{
        background: linear-gradient(135deg, rgba(34,197,94,0.28), rgba(37,99,235,0.24)) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpanderDetails"] .stButton > button:hover{
        transform: translateY(-1px);
        filter: brightness(1.03);
    }

    /* =========================
       REGISTRO TABLE CARD (scroll + no cortada)
       ========================= */
    
    .fit-table-card{
      border-radius: 22px;
      border: 1px solid rgba(255,255,255,0.10);
      background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.06));
      box-shadow: 0 18px 40px rgba(0,0,0,0.35);
      overflow: hidden;          /* 🔥 clave: recorta por las curvas */
      padding: 0 !important;     /* 🔥 sin margen interno */
    }
    
    /* IMPORTANTE: padding abajo para que NO “muerda” el borde redondo */
    .fit-table-scroll{
      width: 100%;
      overflow-x: auto;          /* scroll lateral si hace falta */
      overflow-y: hidden;
      padding: 0 !important;     /* 🔥 sin margen interno */
      margin: 0 !important;
    }
    
    /* Fuerza a que haya scroll si faltan px */
    .fit-table-scroll table{
      width: 100% !important;
      min-width: 100% !important;
      border-collapse: separate !important;
      border-spacing: 0 !important;
      margin: 0 !important;
    }

    
        /* Evita que el Styler meta cosas raras */
    .fit-table-scroll thead th,
    .fit-table-scroll tbody td{
      border: none !important;
    }

    
    /* Scrollbar (opcional, pro) */
    .fit-table-scroll::-webkit-scrollbar{
      height: 10px;
    }
    .fit-table-scroll::-webkit-scrollbar-track{
      background: rgba(255,255,255,0.08);
      border-radius: 999px;
    }
    .fit-table-scroll::-webkit-scrollbar-thumb{
      background: rgba(255,255,255,0.18);
      border-radius: 999px;
    }
    .fit-table-scroll::-webkit-scrollbar-thumb:hover{
      background: rgba(255,255,255,0.26);
    }

    .fit-table-scroll thead th:first-child{ border-top-left-radius: 22px; }
    .fit-table-scroll thead th:last-child{  border-top-right-radius: 22px; }
    .fit-table-scroll tbody tr:last-child td:first-child{ border-bottom-left-radius: 22px; }
    .fit-table-scroll tbody tr:last-child td:last-child{  border-bottom-right-radius: 22px; }



    /* ===== Floating Action Button (evita el "+" suelto) ===== */
    .fit-fab{
      position: fixed;
      right: 22px;
      bottom: 22px;
      width: 54px;
      height: 54px;
      border-radius: 999px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size: 26px;
      font-weight: 900;
      color: #07121f;
      background: linear-gradient(135deg,#22c55e,#60a5fa);
      box-shadow: 0 18px 40px rgba(0,0,0,0.35);
      cursor: pointer;
      z-index: 9999;
      user-select: none;
    }

    /* ===== TOP APP HEADER ===== */
    .app-header{
      display:flex;
      align-items:center;
      gap:16px;
      margin: 6px 0 22px 0;
      padding:18px 22px;
      border-radius:24px;
      border:1px solid rgba(255,255,255,0.12);
      background: linear-gradient(135deg, rgba(34,197,94,0.14), rgba(96,165,250,0.14));
      box-shadow: 0 12px 36px rgba(0,0,0,0.30);
      overflow: hidden;
    }
    
    .app-logo{
      width:56px;
      height:56px;
      border-radius:18px;
      background: linear-gradient(135deg,#22c55e,#3b82f6);
      display:flex;
      align-items:center;
      justify-content:center;
      font-weight:900;
      font-size:20px;
      color:white;
      flex: 0 0 auto;
    }
    
    .app-title{ line-height: 1.05; }
    .app-name{
      font-size:26px;
      font-weight:900;
      letter-spacing:-0.02em;
      color: rgba(255,255,255,0.95);
    }
    .app-sub{
      font-size:13px;
      color: rgba(226,232,240,0.75);
      margin-top: 4px;
    }

    .block-container{
      max-width:1180px;
      padding-top: 64px !important;   /* ⬅️ antes tenías 8/34… aquí está la clave */
      padding-bottom:56px;
      overflow: visible !important;
    }




    </style>
    """, unsafe_allow_html=True)









# ---------------------------
# Auth
# ---------------------------
def _verify_password(password: str, stored: str) -> bool:
    """
    stored format: pbkdf2_sha256$iterations$salt_b64$hash_b64
    """
    try:
        algo, iters_s, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(hash_b64.encode())
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iters,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def _get_users() -> dict:
    return dict(st.secrets.get("users", {}))


def require_login() -> None:
    # Estado
    if "auth_ok" not in st.session_state:
        st.session_state["auth_ok"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = ""

    users = _get_users()

    # 🔒 Limpia user_id inválido (evita "****" o users que ya no existen)
    if st.session_state.get("user_id") and st.session_state["user_id"] not in users:
        st.session_state["auth_ok"] = False
        st.session_state["user_id"] = ""

    # Ya logueado
    if st.session_state["auth_ok"]:
        return

    if not users:
        st.error("No hay usuarios configurados en secrets.toml ([users]).")
        st.stop()

    has_dialog = hasattr(st, "dialog")

    def login_form():
        st.markdown("### 🔐 Iniciar sesión")
        st.caption("Selecciona usuario e introduce contraseña.")

        # contador para resetear input sin tocar el state del widget
        if "_login_pwd_n" not in st.session_state:
            st.session_state["_login_pwd_n"] = 0

        user = st.selectbox("Usuario", list(users.keys()), key="_login_user")

        pwd_key = f"_login_pwd_{st.session_state['_login_pwd_n']}"
        pwd = st.text_input("Contraseña", type="password", key=pwd_key)

        c1, c2 = st.columns([1, 1])
        with c1:
            ok = st.button("Entrar", type="primary", use_container_width=True)
        with c2:
            if st.button("Limpiar", use_container_width=True):
                st.session_state["_login_pwd_n"] += 1
                st.rerun()

        if ok:
            if _verify_password(pwd, users.get(user, "")):
                st.session_state["auth_ok"] = True
                st.session_state["user_id"] = user
                st.session_state["_login_pwd_n"] += 1
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")
                st.session_state["_login_pwd_n"] += 1
                st.rerun()

    if has_dialog:
        @st.dialog("Acceso a FitMacro", width="small")
        def _dlg():
            login_form()

        _dlg()
        st.stop()
    else:
        st.markdown("<div style='max-width:420px;margin:60px auto;'>", unsafe_allow_html=True)
        login_form()
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()




# ---------------------------
# App init
# ---------------------------
inject_black_theme()
require_login()

# ===== TOP HEADER (MAIN) =====
st.markdown("""
<div class="app-header">
    <div class="app-logo">FM</div>
    <div class="app-title">
        <div class="app-name">FitMacro</div>
        <div class="app-sub">Fitness macros intelligence</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== SIDEBAR BRAND =====
st.sidebar.markdown("""
<div class="sb-brand">
  <div class="sb-logo">FM</div>
  <div class="sb-title">
    <div class="sb-name">FitMacro</div>
    <div class="sb-sub">Fitness macros tracker</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.caption(f"👤 Sesión: **{st.session_state['user_id']}**")

if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
    st.session_state["auth_ok"] = False
    st.session_state["user_id"] = ""
    st.rerun()

selected_date = st.sidebar.date_input("📅 Día", value=date.today())
selected_date_str = selected_date.isoformat()

# =========================
# SIDEBAR NAV (UNA SOLA SELECCIÓN)
# =========================
if "nav" not in st.session_state:
    st.session_state["nav"] = "📊 Dashboard"

def _set_nav(v: str):
    st.session_state["nav"] = v

def nav_btn(label: str, value: str, key: str):
    """Botón de navegación (se usa dentro de expander)."""
    active = (st.session_state.get("nav") == value)
    st.button(
        label,
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary",
        on_click=_set_nav,
        args=(value,),
    )

# --- Navegación controlada (para atajos "Ir a ...") ---
if "goto_page" not in st.session_state:
    st.session_state["goto_page"] = None

if st.session_state["goto_page"]:
    st.session_state["nav"] = st.session_state["goto_page"]
    st.session_state["goto_page"] = None

# =========================
# MENÚ POR SECCIONES (4 EXPANDERS)
# =========================
page = st.session_state["nav"]

GROUPS = {
    "PRINCIPAL": {
        "icon": "📊",
        "pages": [
            ("📊 Dashboard", "📊 Dashboard", "nav_dash"),
        ]
    },
    "NUTRICIÓN": {
        "icon": "🍽️",
        "pages": [
            ("🍽 Registro", "🍽 Registro", "nav_reg"),
            ("👨‍🍳 Chef IA", "👨‍🍳 Chef IA", "nav_chef"),
            ("➕ Añadir alimento", "➕ Añadir alimento", "nav_foods"),
        ]
    },
    "ENTRENAMIENTO": {
        "icon": "🏋️",
        "pages": [
            ("🏋️ Rutina IA", "🏋️ Rutina IA", "nav_rutina"),
        ]
    },
    "PERFIL": {
        "icon": "⚙️",
        "pages": [
            ("🎯 Objetivos", "🎯 Objetivos", "nav_obj"),
        ]
    },
}

def group_for_page(p: str) -> str:
    for gname, g in GROUPS.items():
        for _, value, _ in g["pages"]:
            if value == p:
                return gname
    return "PRINCIPAL"

active_group = group_for_page(page)

# Render de los 4 expanders
for gname in ["PRINCIPAL", "NUTRICIÓN", "ENTRENAMIENTO", "PERFIL"]:
    g = GROUPS[gname]
    title = f"{g['icon']} {gname.title()}"
    expanded = (gname == active_group)

    with st.sidebar.expander(title, expanded=expanded):
        # 🔥 IMPORTANTE: NO envolver con <div> custom aquí dentro
        # porque rompe el DOM del expander en Streamlit.
        for label, value, key in g["pages"]:
            nav_btn(label, value, key)

# Página final (por claridad)
page = st.session_state["nav"]

# (Si tienes el FAB, déjalo aquí)
st.markdown("""<div class="fit-fab">+</div>""", unsafe_allow_html=True)



# ==========================================================
# PÁGINA: DASHBOARD
# ==========================================================
if page == "📊 Dashboard":
    import altair as alt

    st.subheader("📊 Dashboard")
    st.caption(f"Día: {selected_date_str}")
    st.divider()

    rows = list_entries_by_date(selected_date_str, st.session_state["user_id"])

    total_kcal = sum(float(r["calories"]) for r in rows) if rows else 0.0
    total_protein = sum(float(r["protein"]) for r in rows) if rows else 0.0
    total_carbs = sum(float(r["carbs"]) for r in rows) if rows else 0.0
    total_fat = sum(float(r["fat"]) for r in rows) if rows else 0.0

    # ===== GRID METRICS (fit style) =====

    cL, cR = st.columns(2)
    
    with cL:
        st.metric("🔥 Calorías", f"{total_kcal:.0f} kcal")
        st.metric("🥩 Proteína", f"{total_protein:.1f} g")
    
    with cR:
        st.metric("🍚 Carbs", f"{total_carbs:.1f} g")
        st.metric("🥑 Grasas", f"{total_fat:.1f} g")
    st.divider()

    # ===== PROGRESO =====
    st.subheader("🎯 Progreso del día")
    st.caption("Objetivo vs consumido y cuánto te queda.")

    uid = st.session_state["user_id"]
    target_kcal = float(get_setting("target_deficit_calories", 1800, user_id=uid))
    target_p = float(get_setting("target_protein", 120, user_id=uid))
    target_c = float(get_setting("target_carbs", 250, user_id=uid))
    target_f = float(get_setting("target_fat", 60, user_id=uid))


    def clamp01(x: float) -> float:
        return 0.0 if x < 0 else 1.0 if x > 1 else x

    def progress_row(label: str, value: float, goal: float, unit: str = ""):
        goal = float(goal) if goal else 0.0
        value = float(value) if value else 0.0
        ratio = 0.0 if goal <= 0 else clamp01(value / goal)
        remaining = goal - value

        left, right = st.columns([5, 2])
        with left:
            st.markdown(f"**{label}**  ·  {value:.0f}{unit} / {goal:.0f}{unit}")
            st.progress(ratio)
        with right:
            if goal <= 0:
                st.caption("sin objetivo")
            else:
                st.metric("Restante" if remaining >= 0 else "Exceso", f"{abs(remaining):.0f}{unit}")

    progress_row("🔥 Calorías", total_kcal, target_kcal, " kcal")
    progress_row("🥩 Proteína", total_protein, target_p, " g")
    progress_row("🍚 Carbs", total_carbs, target_c, " g")
    progress_row("🥑 Grasas", total_fat, target_f, " g")

    st.divider()

    # ===== HISTÓRICO EN CARD DEGRADADA =====
    # ===== HISTÓRICO + INSIGHTS (multiusuario) =====
    uid = st.session_state["user_id"]

    hist = daily_totals_last_days(30, user_id=uid)  # [(date, kcal, p, c, f), ...]
    hist_df = pd.DataFrame(hist, columns=["date", "calories", "protein", "carbs", "fat"])

    # Card contenedora
    st.markdown('<div class="fit-card">', unsafe_allow_html=True)

    topL, topR = st.columns([3, 2], vertical_alignment="top")

    with topL:
        st.subheader("📈 Últimos 30 días")
        if hist_df.empty:
            st.info("Aún no hay histórico para este usuario. Registra comidas y aquí verás la evolución 💪")
        else:
            hist_df["date"] = pd.to_datetime(hist_df["date"])
            hist_df = hist_df.sort_values("date")

            # Kcal chart con objetivo
            target_kcal_line = pd.DataFrame({
                "date": hist_df["date"],
                "Objetivo": [target_kcal] * len(hist_df),
                "Consumido": hist_df["calories"].astype(float),
            }).melt("date", var_name="serie", value_name="kcal")

            kcal_chart = (
                alt.Chart(target_kcal_line)
                .mark_line()
                .encode(
                    x=alt.X("date:T", title=""),
                    y=alt.Y("kcal:Q", title="kcal"),
                    color=alt.Color("serie:N", legend=alt.Legend(orient="top")),
                    tooltip=["date:T", "serie:N", "kcal:Q"]
                )
                .properties(height=220)
            )
            st.altair_chart(kcal_chart, use_container_width=True)

            # Mini resumen: media 7 días
            hist_df["kcal_7d"] = hist_df["calories"].rolling(7, min_periods=1).mean()
            last7 = float(hist_df["kcal_7d"].iloc[-1])
            diff = last7 - float(target_kcal)

            st.caption(f"📌 Media móvil (7 días): **{last7:.0f} kcal** · Diferencia vs objetivo: **{diff:+.0f} kcal**")

    with topR:
        st.subheader("🧾 Resumen rápido")
        st.caption("Hoy + lo que te queda para cumplir el objetivo.")

        rem_kcal = float(target_kcal) - float(total_kcal)
        rem_p = float(target_p) - float(total_protein)
        rem_c = float(target_c) - float(total_carbs)
        rem_f = float(target_f) - float(total_fat)

        def badge(label, val, unit):
            # positivo = te queda, negativo = te pasaste
            tag = "Restante" if val >= 0 else "Exceso"
            st.metric(f"{label} ({tag})", f"{abs(val):.0f}{unit}" if unit == " kcal" else f"{abs(val):.1f}{unit}")

        b1, b2 = st.columns(2)
        with b1:
            badge("🔥 kcal", rem_kcal, " kcal")
            badge("🥩 P", rem_p, " g")
        with b2:
            badge("🍚 C", rem_c, " g")
            badge("🥑 G", rem_f, " g")

        st.divider()
        st.caption("Atajos")
        cA, cB = st.columns(2)
        with cA:
            if st.button("➕ Ir a Registro", type="primary"):
                st.session_state["goto_page"] = "🍽 Registro"
                st.rerun()

        with cB:
            if st.button("🎯 Ir a Objetivos", type="primary"):
                st.session_state["goto_page"] = "🎯 Objetivos"
                st.rerun()


    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ===== MACROS (stacked) últimos 14 días =====
    st.subheader("🥗 Macros recientes (14 días)")
    if hist_df.empty:
        st.caption("Aquí aparecerán tus macros cuando tengas datos.")
    else:
        df14 = hist_df.tail(14).copy()
        df14["date"] = pd.to_datetime(df14["date"])
        long_macros = df14.melt("date", value_vars=["protein", "carbs", "fat"], var_name="macro", value_name="g")

        macros_chart = (
            alt.Chart(long_macros)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title=""),
                y=alt.Y("g:Q", title="gramos"),
                color=alt.Color("macro:N", legend=alt.Legend(orient="top")),
                tooltip=["date:T", "macro:N", "g:Q"]
            )
            .properties(height=220)
        )
        st.altair_chart(macros_chart, use_container_width=True)




# ==========================================================
# PÁGINA: REGISTRO
# ==========================================================
elif page == "🍽 Registro":
    st.subheader("🍽 Registro")
    st.caption(f"Día: {selected_date_str}")
    st.divider()

    # Mensaje persistente post-rerun (para que no “parpadee”)
    if st.session_state.get("_just_added", False):
        last_id = st.session_state.get("_last_add_id", "")
        st.success(f"✅ Entrada guardada (id={last_id})")
        st.session_state["_just_added"] = False

    # DEBUG (DENTRO de Registro, con indent correcto)
    with st.expander("🛠️ DEBUG Sheets (solo para ti)", expanded=False):
        import db_gsheets
        try:
            sh = db_gsheets._sh()
            ws = db_gsheets._ws(db_gsheets.TAB_ENTRIES)

            st.write("**Sheet ID (secrets):**", db_gsheets.SHEET_ID)
            st.write("**Spreadsheet title:**", sh.title)
            st.write("**Worksheet title:**", ws.title)
            st.write("**Worksheets disponibles:**", [w.title for w in sh.worksheets()])

            header = ws.row_values(1)
            st.write("**Header entries:**", header)

            all_vals = ws.get_all_values()
            st.write("**Filas totales (get_all_values):**", len(all_vals))

            if len(all_vals) >= 2:
                st.write("**Última fila:**", all_vals[-1])
            else:
                st.write("**Última fila:** (vacío, solo headers)")

        except Exception as e:
            st.error("Fallo leyendo debug de Sheets")
            st.exception(e)

    categories = list_categories()
    if not categories:
        st.error("No hay categorías. Revisa la pestaña foods.")
        st.stop()

    colA, colB = st.columns([2, 2])
    with colA:
        category = st.selectbox("Categoría", categories, key="reg_category")
    with colB:
        foods_in_cat = list_foods_by_category(category)
        if not foods_in_cat:
            st.warning("Esa categoría no tiene alimentos.")
            st.stop()
        food = st.selectbox("Alimento", foods_in_cat, format_func=lambda x: x["name"], key="reg_food")

        # FORM de alta
    with st.form("add_entry_form", clear_on_submit=False):
    
        grams = float(
            st.number_input(
                "Gramos consumidos",
                min_value=1.0,
                step=1.0,
                value=100.0,
                format="%.0f",
                key="reg_grams"
            )
        )
    
        meal = st.radio(
            "Comida",
            ["Desayuno", "Almuerzo", "Merienda", "Cena"],
            horizontal=False,
            key="reg_meal"
        )
    
        add_btn = st.form_submit_button("Añadir al registro")
    
        if add_btn:
            try:
                macros = scale_macros(food, grams)
                entry = {
                    "user_id": st.session_state["user_id"],
                    "entry_date": selected_date_str,
                    "meal": meal,
                    "name": food["name"],
                    "grams": float(grams),
                    **macros
                }
    
                new_id = add_entry(entry)
    
                st.cache_data.clear()
                st.session_state["_just_added"] = True
                st.session_state["_last_add_id"] = new_id
                st.rerun()
    
            except Exception as e:
                st.error("❌ Error guardando la entrada en Google Sheets")
                st.exception(e)


    # Lectura del día (siempre, después del form)
    st.subheader("Registro")
    rows = list_entries_by_date(selected_date_str, st.session_state["user_id"])
    df = pd.DataFrame(rows, columns=["id", "meal", "name", "grams", "calories", "protein", "carbs", "fat"])

    if df.empty:
        st.info("Aún no hay entradas en este día.")
    else:
        df_view = df.drop(columns=["id"]).rename(columns={
            "meal": "Comida",
            "name": "Alimento",
            "grams": "Gramos",
            "calories": "Calorías",
            "protein": "Proteínas",
            "carbs": "Carbohidratos",
            "fat": "Grasas"
        })
        # ----- TABLA BONITA (HTML) -----
        df_tbl = df_view.copy()
        
        # Formato numérico
        for col in ["Gramos", "Calorías"]:
            if col in df_tbl.columns:
                df_tbl[col] = pd.to_numeric(df_tbl[col], errors="coerce").fillna(0).round(0).astype(int)
        
        for col in ["Proteínas", "Carbohidratos", "Grasas"]:
            if col in df_tbl.columns:
                df_tbl[col] = pd.to_numeric(df_tbl[col], errors="coerce").fillna(0).round(1)
                
        styler = (
            df_tbl.style
            .hide(axis="index")
            .format({
                "Gramos": "{:.0f}",
                "Calorías": "{:.0f}",
                "Proteínas": "{:.1f}",
                "Carbohidratos": "{:.1f}",
                "Grasas": "{:.1f}",
            })
            .set_table_styles([
                {"selector": "table", "props": [
                    ("width", "100%"),
                    ("border-collapse", "separate"),
                    ("border-spacing", "0"),
                    ("border-radius", "18px"),
                    ("overflow", "hidden"),
                    ("box-shadow", "0 18px 40px rgba(15,23,42,0.12)"),
                    ("border", "1px solid rgba(15,23,42,0.10)"),
                ]},
                {"selector": "thead th", "props": [
                    ("background", "linear-gradient(135deg, rgba(22,163,74,0.85), rgba(37,99,235,0.85))"),
                    ("color", "white"),
                    ("font-weight", "800"),
                    ("padding", "12px 12px"),
                    ("border", "none"),
                    ("text-align", "left"),
                ]},
                {"selector": "tbody td", "props": [
                    ("background", "rgba(255,255,255,0.75)"),
                    ("color", "#0f172a"),
                    ("font-weight", "650"),
                    ("padding", "12px 12px"),
                    ("border", "none"),
                ]},
                {"selector": "tbody tr:nth-child(even) td", "props": [
                    ("background", "rgba(255,255,255,0.62)"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background", "rgba(37,99,235,0.14)"),
                ]},
            ])
        )
                
        table_html = styler.to_html()
        
        st.markdown(
            f"""<div class="fit-table-card"><div class="fit-table-scroll">{table_html}</div></div>""",
            unsafe_allow_html=True
        )





        st.subheader("Totales")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("🔥 Calorías", f"{df['calories'].sum():.0f} kcal")
        with c2:
            st.metric("🥩 Proteína", f"{df['protein'].sum():.1f} g")
        with c3:
            st.metric("🍚 Carbohidratos", f"{df['carbs'].sum():.1f} g")
        with c4:
            st.metric("🥑 Grasas", f"{df['fat'].sum():.1f} g")

    # Tendencia (aunque el día esté vacío, puede haber histórico)
        
    
        # Editor/Borrado (solo si hay filas)
        if not df.empty:
            st.subheader("✏️ Editar / 🗑️ Borrar entrada")
    
            options = [{
                "id": int(r["id"]),
                "label": f"{r['meal']} — {r['name']} — {float(r['grams']):.0f} g"
            } for _, r in df.iterrows()]
    
            selected_opt = st.selectbox(
                "Selecciona una entrada",
                options,
                format_func=lambda x: x["label"],
                key="entry_select_edit"
            )
    
            selected_id = int(selected_opt["id"])
            row = df[df["id"] == selected_id].iloc[0]
    
            colE1, colE2, colE3 = st.columns([2, 1, 1])
            with colE1:
                meals = ["Desayuno", "Almuerzo", "Merienda", "Cena"]
                current_meal = row["meal"] if row["meal"] in meals else meals[0]
                new_meal = st.selectbox("Comida", meals, index=meals.index(current_meal), key=f"meal_edit_{selected_id}")
            with colE2:
                new_grams = st.number_input("Gramos", min_value=1.0, step=1.0, value=float(row["grams"]), key=f"grams_edit_{selected_id}")
            with colE3:
                st.write("")
                st.write("")
    
            # Mapa de alimentos para recalcular macros
            if "food_map" not in st.session_state:
                m = {}
                for c in list_categories():
                    for f in list_foods_by_category(c):
                        m[f["name"]] = f
                st.session_state["food_map"] = m
    
            base_food = st.session_state["food_map"].get(row["name"])
            if base_food is None:
                st.error("No encuentro este alimento en la base de datos (quizá lo borraste).")
            else:
                if st.button("Guardar cambios", type="primary", key=f"save_entry_{selected_id}"):
                    macros = scale_macros(base_food, float(new_grams))
                    update_entry(
                        selected_id,
                        grams=float(new_grams),
                        calories=float(macros["calories"]),
                        protein=float(macros["protein"]),
                        carbs=float(macros["carbs"]),
                        fat=float(macros["fat"]),
                        meal=new_meal
                    )
                    st.cache_data.clear()
                    st.success("Entrada actualizada ✅")
                    st.rerun()
    
                st.warning("⚠️ Borrar elimina la entrada (no se puede deshacer).")
                confirm_del = st.checkbox("Confirmo que quiero borrar esta entrada", key=f"confirm_del_{selected_id}")
                if st.button("Borrar entrada", disabled=not confirm_del, key=f"del_entry_{selected_id}"):
                    delete_entry_by_id(selected_id)
                    st.cache_data.clear()
                    st.success("Entrada borrada ✅")
                    st.rerun()


# ==========================================================
# PÁGINA: OBJETIVOS
# ==========================================================
elif page == "🎯 Objetivos":
    uid = st.session_state["user_id"]
    
    saved_sex = str(get_setting("sex", "M", user_id=uid)).upper().strip()
    saved_age = float(get_setting("age", 25, user_id=uid))
    saved_weight = float(get_setting("weight", 70, user_id=uid))
    saved_height = float(get_setting("height", 175, user_id=uid))
    saved_activity = float(get_setting("activity", 1.55, user_id=uid))
    saved_deficit = float(get_setting("deficit_pct", 20, user_id=uid))


    st.subheader("🎯 Objetivos")
    st.caption("Calcula y guarda tus objetivos diarios.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        sex = st.selectbox("Sexo", ["M", "F"], index=0 if saved_sex == "M" else 1)
        age = st.number_input("Edad (años)", min_value=1.0, max_value=120.0, value=float(saved_age), step=1.0)
        weight = st.number_input("Peso (kg)", min_value=1.0, max_value=400.0, value=float(saved_weight), step=0.5)
        height = st.number_input("Altura (cm)", min_value=50.0, max_value=250.0, value=float(saved_height), step=1.0)

    with col2:
        activity_options = [
            "Sedentaria (1.2)",
            "Ligera (1.375)",
            "Moderada (1.55)",
            "Alta (1.725)",
            "Muy alta (1.9)",
        ]
        activity_values = [1.2, 1.375, 1.55, 1.725, 1.9]
        try:
            activity_index = activity_values.index(saved_activity)
        except ValueError:
            activity_index = activity_values.index(1.55)

        activity_label = st.selectbox("Actividad física", activity_options, index=activity_index)
        activity = float(activity_label.split("(")[-1].strip(")"))
        deficit_pct = st.slider("% Déficit (0-30)", 0, 30, int(saved_deficit))

    if st.button("Calcular y guardar objetivos", type="primary"):
        maintenance, deficit_kcal, protein_g, carbs_g, fat_g = calculate_goals(
            sex=sex,
            age=float(age),
            weight=float(weight),
            height=float(height),
            activity=float(activity),
            deficit_pct=float(deficit_pct),
        )

        set_setting("sex", str(sex), user_id=uid)
        set_setting("age", str(age), user_id=uid)
        set_setting("weight", str(weight), user_id=uid)
        set_setting("height", str(height), user_id=uid)
        set_setting("activity", str(activity), user_id=uid)
        set_setting("deficit_pct", str(deficit_pct), user_id=uid)
        
        set_setting("target_maintenance", str(maintenance), user_id=uid)
        set_setting("target_deficit_calories", str(deficit_kcal), user_id=uid)
        set_setting("target_protein", str(protein_g), user_id=uid)
        set_setting("target_carbs", str(carbs_g), user_id=uid)
        set_setting("target_fat", str(fat_g), user_id=uid)


        st.cache_data.clear()
        st.success("Perfil y objetivos guardados ✅")
        st.rerun()

    st.divider()

    target_maint = get_setting("target_maintenance", user_id=uid)
    target_def = get_setting("target_deficit_calories", user_id=uid)
    target_p = get_setting("target_protein", user_id=uid)
    target_c = get_setting("target_carbs", user_id=uid)
    target_f = get_setting("target_fat", user_id=uid)


    if all([target_maint, target_def, target_p, target_c, target_f]):
        st.subheader("📌 Tus objetivos guardados")
        a, b, c, d, e = st.columns(5)
        a.metric("⚡ Mantenimiento", f"{float(target_maint):.0f} kcal")
        b.metric("🎯 Déficit", f"{float(target_def):.0f} kcal")
        c.metric("🥩 Proteína", f"{float(target_p):.0f} g")
        d.metric("🍚 Carbs", f"{float(target_c):.0f} g")
        e.metric("🥑 Grasas", f"{float(target_f):.0f} g")
    else:
        st.info("Aún no has guardado objetivos. Rellena los datos y pulsa el botón.")


# ==========================================================
# PÁGINA: AÑADIR ALIMENTO
# ==========================================================
elif page == "➕ Añadir alimento":
    st.subheader("Gestión de alimentos")
    st.caption("Aquí puedes añadir alimentos nuevos, editar los existentes o borrarlos de la base de datos.")

    mode = st.radio("Modo", ["➕ Añadir", "✏️ Editar", "🗑️ Borrar"], horizontal=True, key="food_mode")
    all_foods = list_all_foods()

    if mode == "➕ Añadir":
        with st.form("add_food_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nombre del alimento")
                category = st.text_input("Categoría", value="Carbohidratos")
            with col2:
                calories = st.number_input("Kcal por 100g", min_value=0.0, value=100.0, step=1.0)
                protein = st.number_input("Proteína por 100g", min_value=0.0, value=0.0, step=0.1)
                carbs = st.number_input("Carbs por 100g", min_value=0.0, value=0.0, step=0.1)
                fat = st.number_input("Grasas por 100g", min_value=0.0, value=0.0, step=0.1)

            save_food_btn = st.form_submit_button("Guardar alimento")
            if save_food_btn:
                try:
                    nn = name.strip()
                    nc = category.strip()
                    if not nn:
                        st.error("Falta el nombre del alimento.")
                    elif not nc:
                        st.error("Falta la categoría.")
                    else:
                        add_food({
                            "name": nn,
                            "category": nc,
                            "calories": float(calories),
                            "protein": float(protein),
                            "carbs": float(carbs),
                            "fat": float(fat),
                        })
                        st.cache_data.clear()
                        st.success("Alimento guardado ✅")
                        st.rerun()
                except Exception as e:
                    st.error("❌ Error guardando el alimento en Google Sheets")
                    st.exception(e)

    elif mode == "✏️ Editar":
        if not all_foods:
            st.info("No hay alimentos para editar.")
        else:
            selected = st.selectbox(
                "Selecciona alimento",
                all_foods,
                format_func=lambda f: f"{f['category']} — {f['name']}"
            )

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Nombre", value=selected["name"])
                new_category = st.text_input("Categoría", value=selected["category"])
            with col2:
                new_calories = st.number_input("Kcal por 100g", min_value=0.0, value=float(selected["calories"]), step=1.0)
                new_protein = st.number_input("Proteína por 100g", min_value=0.0, value=float(selected["protein"]), step=0.1)
                new_carbs = st.number_input("Carbs por 100g", min_value=0.0, value=float(selected["carbs"]), step=0.1)
                new_fat = st.number_input("Grasas por 100g", min_value=0.0, value=float(selected["fat"]), step=0.1)

            if st.button("Guardar cambios", type="primary"):
                nn = new_name.strip()
                nc = new_category.strip()
                if not nn:
                    st.error("El nombre no puede estar vacío.")
                elif not nc:
                    st.error("La categoría no puede estar vacía.")
                else:
                    update_food(selected["id"], {
                        "name": nn,
                        "category": nc,
                        "calories": float(new_calories),
                        "protein": float(new_protein),
                        "carbs": float(new_carbs),
                        "fat": float(new_fat),
                    })
                    st.cache_data.clear()
                    st.success("Cambios guardados ✅")
                    st.rerun()

    else:  # 🗑️ Borrar
        if not all_foods:
            st.info("No hay alimentos para borrar.")
        else:
            selected = st.selectbox(
                "Selecciona alimento a borrar",
                all_foods,
                format_func=lambda f: f"{f['category']} — {f['name']}"
            )
            st.warning("⚠️ Esto lo borra de la base de datos. No se puede deshacer.")
            confirm = st.checkbox(f"Confirmo que quiero borrar: {selected['name']}")
            if st.button("Borrar alimento", disabled=not confirm):
                delete_food_by_id(selected["id"])
                st.cache_data.clear()
                st.success("Alimento borrado ✅")
                st.rerun()


# ==========================================================
# PÁGINA: CHEF IA
# ==========================================================
elif page == "👨‍🍳 Chef IA":
    import json
    from ai_groq import chat_answer, generate_menu_json

    uid = st.session_state["user_id"]

    # ---------------------------
    # Chat
    # ---------------------------
    def send_coach():
        prompt = st.session_state.get("coach_prompt", "").strip()
        if not prompt:
            return
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        answer = chat_answer(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.session_state.coach_prompt = ""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "Eres un asistente de nutrición. Sé claro, práctico y breve."}
        ]

    st.subheader("👨‍🍳 Chef IA")
    st.caption("Nutrición + menú + platos con tus alimentos (optimizado para móvil).")

    # Chat arriba (siempre)
    for m in st.session_state.chat_history:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.write(m["content"])

    st.divider()

    colA, colB = st.columns([6, 1])
    with colA:
        st.text_input("Pregúntale al Chef IA…", key="coach_prompt", on_change=send_coach)
    with colB:
        st.button("Enviar", type="primary", on_click=send_coach)

    st.divider()

    # ---------------------------
    # Selector móvil: Menús vs Platos
    # ---------------------------
    if "chef_mode" not in st.session_state:
        st.session_state["chef_mode"] = "none"  # al entrar: no mostrar nada


    b1, b2 = st.columns(2)
    with b1:
        if st.button("🥘 Generador de platos", use_container_width=True):
            st.session_state["chef_mode"] = "platos"
            st.rerun()
    with b2:
        if st.button("🍽️ Generador de menús", use_container_width=True):
            st.session_state["chef_mode"] = "menus"
            st.rerun()

    st.divider()

    # ---------------------------
    # Datos comunes para ambos generadores
    # ---------------------------
    cats = list_categories()
    food_map = {}
    for c in cats:
        for f in list_foods_by_category(c):
            food_map[f["name"]] = f
    allowed = list(food_map.keys())

    mode = st.session_state.get("chef_mode", "Menus")



    # ==========================================================
    # 🍽️ GENERADOR DE MENÚS
    # ==========================================================
    if mode == "menus":
        st.subheader("🍽️ Generador de menú")
        st.caption("Te genera un menú de 4 comidas usando SOLO tus alimentos.")

        if not allowed:
            st.info("No hay alimentos disponibles en tu base de datos.")
            st.stop()

        target_def = float(get_setting("target_deficit_calories", 2000, user_id=uid))
        target_p = float(get_setting("target_protein", 120, user_id=uid))
        target_c = float(get_setting("target_carbs", 250, user_id=uid))
        target_f = float(get_setting("target_fat", 60, user_id=uid))

        kcal_obj = st.number_input("Objetivo kcal (día)", min_value=800.0, max_value=6000.0, value=target_def, step=50.0, key="menu_kcal")
        prot_obj = st.number_input("Proteína objetivo (g)", min_value=0.0, max_value=400.0, value=target_p, step=5.0, key="menu_p")
        carb_obj = st.number_input("Carbs objetivo (g)", min_value=0.0, max_value=800.0, value=target_c, step=10.0, key="menu_c")
        fat_obj  = st.number_input("Grasas objetivo (g)", min_value=0.0, max_value=300.0, value=target_f, step=5.0, key="menu_f")

        pref = st.selectbox("Preferencia", ["Equilibrado", "Alta proteína", "Baja grasa", "Bajo carb"], key="menu_pref")

        if st.button("✨ Generar menú", type="primary", use_container_width=True):
            context = (
                f"Objetivo diario: {kcal_obj} kcal; Proteína {prot_obj}g; Carbs {carb_obj}g; Grasas {fat_obj}g. "
                f"Preferencia: {pref}. "
                "Crea un menú de 4 comidas (Desayuno, Almuerzo, Merienda, Cena)."
            )
            raw = generate_menu_json(context, allowed_food_names=allowed)

            try:
                menu = json.loads(raw)
            except json.JSONDecodeError:
                st.error("La IA devolvió un formato raro. Vuelve a generar.")
                st.code(raw)
                st.stop()

            totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

            for meal in menu.get("meals", []):
                st.markdown(f"### {meal.get('meal','Comida')}")
                for item in meal.get("items", []):
                    name = item.get("name")
                    grams = float(item.get("grams", 0))
                    if name not in food_map or grams <= 0:
                        continue
                    macros = scale_macros(food_map[name], grams)
                    totals["calories"] += macros["calories"]
                    totals["protein"] += macros["protein"]
                    totals["carbs"] += macros["carbs"]
                    totals["fat"] += macros["fat"]
                    st.write(f"- **{name}** — {grams:.0f} g · {macros['calories']:.0f} kcal")

            st.success(
                f"Total menú: {totals['calories']:.0f} kcal · P {totals['protein']:.0f} · C {totals['carbs']:.0f} · G {totals['fat']:.0f}"
            )

    # ==========================================================
    # 🥘 GENERADOR DE PLATOS (plato combinado)
    # ==========================================================
    elif mode == "platos":
        st.subheader("🥘 Generador de platos")
        st.caption("Combina alimentos de tu base, calcula macros automáticamente y guarda el plato como nuevo alimento.")

        if not allowed:
            st.info("No hay alimentos disponibles en tu base para crear un plato.")
            st.stop()

        # Estado para ir añadiendo ingredientes
        if "dish_items" not in st.session_state:
            st.session_state["dish_items"] = [{"name": allowed[0], "grams": 100.0}]

        with st.expander("➕ Construir plato", expanded=True):

            dish_name = st.text_input("Nombre del plato", value=st.session_state.get("dish_name", "Plato casero"), key="dish_name")
            dish_category = st.text_input("Categoría (para guardarlo)", value=st.session_state.get("dish_category", "Platos"), key="dish_category")

            st.divider()

            c_add, c_del = st.columns(2)
            with c_add:
                if st.button("➕ Añadir ingrediente", use_container_width=True):
                    st.session_state["dish_items"].append({"name": allowed[0], "grams": 100.0})
                    st.rerun()
            with c_del:
                if st.button("➖ Quitar último", use_container_width=True, disabled=len(st.session_state["dish_items"]) <= 1):
                    st.session_state["dish_items"].pop()
                    st.rerun()

            st.divider()

            total_grams = 0.0
            totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

            for i, it in enumerate(st.session_state["dish_items"]):
                st.markdown(f"**Ingrediente {i+1}**")

                # Asegurar consistencia si cambió allowed
                if it.get("name") not in allowed:
                    it["name"] = allowed[0]

                sel_name = st.selectbox(
                    "Alimento",
                    allowed,
                    index=allowed.index(it["name"]),
                    key=f"dish_food_{i}"
                )
                sel_grams = float(
                    st.number_input(
                        "Gramos",
                        min_value=1.0,
                        step=1.0,
                        value=float(it.get("grams", 100.0)),
                        key=f"dish_grams_{i}"
                    )
                )

                it["name"] = sel_name
                it["grams"] = sel_grams

                macros = scale_macros(food_map[sel_name], sel_grams)
                total_grams += sel_grams
                totals["calories"] += float(macros["calories"])
                totals["protein"] += float(macros["protein"])
                totals["carbs"] += float(macros["carbs"])
                totals["fat"] += float(macros["fat"])

                st.caption(
                    f"{sel_grams:.0f} g · {macros['calories']:.0f} kcal · "
                    f"P {macros['protein']:.1f} · C {macros['carbs']:.1f} · G {macros['fat']:.1f}"
                )
                st.divider()

            st.markdown("### Totales del plato")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("🔥 kcal", f"{totals['calories']:.0f}")
                st.metric("🥩 Proteína", f"{totals['protein']:.1f} g")
            with m2:
                st.metric("🍚 Carbs", f"{totals['carbs']:.1f} g")
                st.metric("🥑 Grasas", f"{totals['fat']:.1f} g")

            st.caption(f"Peso total: **{total_grams:.0f} g**")

            # Por 100g (para guardar como alimento)
            if total_grams > 0:
                per100 = {
                    "calories": totals["calories"] / total_grams * 100.0,
                    "protein": totals["protein"] / total_grams * 100.0,
                    "carbs": totals["carbs"] / total_grams * 100.0,
                    "fat": totals["fat"] / total_grams * 100.0,
                }
            else:
                per100 = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

            st.markdown("### Por 100g (se guardará así en tu base)")
            p1, p2 = st.columns(2)
            with p1:
                st.metric("🔥 kcal/100g", f"{per100['calories']:.0f}")
                st.metric("🥩 P/100g", f"{per100['protein']:.1f} g")
            with p2:
                st.metric("🍚 C/100g", f"{per100['carbs']:.1f} g")
                st.metric("🥑 G/100g", f"{per100['fat']:.1f} g")

            st.divider()

            if st.button("💾 Guardar plato como alimento", type="primary", use_container_width=True):
                nn = dish_name.strip()
                nc = dish_category.strip() or "Platos"

                if not nn:
                    st.error("Pon un nombre al plato.")
                elif total_grams <= 0:
                    st.error("El plato debe tener gramos totales > 0.")
                else:
                    add_food({
                        "name": nn,
                        "category": nc,
                        "calories": float(per100["calories"]),
                        "protein": float(per100["protein"]),
                        "carbs": float(per100["carbs"]),
                        "fat": float(per100["fat"]),
                    })
                    st.cache_data.clear()
                    st.success("Plato guardado como alimento ✅")

                    # Reset rápido
                    st.session_state["dish_items"] = [{"name": allowed[0], "grams": 100.0}]
                    st.rerun()


# ==========================================================
# PÁGINA: RUTINA IA
# ==========================================================
elif page == "🏋️ Rutina IA":
    import json
    from ai_groq import generate_workout_plan_json

    st.subheader("🏋️ Rutina IA")
    st.caption("Crea una rutina personalizada según tu material, nivel y objetivos. Optimizado para móvil 📱")
    st.divider()

    uid = st.session_state["user_id"]

    # --- Cargar perfil guardado (si existe) ---
    saved_profile_raw = get_setting("workout_profile_json", default="{}", user_id=uid)
    try:
        saved_profile = json.loads(saved_profile_raw) if saved_profile_raw else {}
    except Exception:
        saved_profile = {}

    # --- Objetivos nutrición (de tu app) ---
    target_kcal = float(get_setting("target_deficit_calories", 1800, user_id=uid))
    target_p = float(get_setting("target_protein", 120, user_id=uid))
    target_c = float(get_setting("target_carbs", 250, user_id=uid))
    target_f = float(get_setting("target_fat", 60, user_id=uid))

    # ====== UI MOBILE-FIRST: inputs en vertical ======
    with st.expander("🧬 Tu perfil (guardar)", expanded=True):
        equipment = st.text_area(
            "Material disponible (separa por comas)",
            value=saved_profile.get("equipment", "mancuernas ajustables, banda elástica"),
            height=70,
            key="wk_equipment"
        )

        col1, col2 = st.columns(2)
        with col1:
            level = st.selectbox(
                "Nivel",
                ["Principiante", "Intermedio", "Avanzado"],
                index=["Principiante", "Intermedio", "Avanzado"].index(saved_profile.get("level", "Principiante")),
                key="wk_level"
            )
            days = st.selectbox(
                "Días/semana",
                [2, 3, 4, 5, 6],
                index=[2, 3, 4, 5, 6].index(int(saved_profile.get("days", 3))),
                key="wk_days"
            )
        with col2:
            minutes = st.selectbox(
                "Minutos por sesión",
                [20, 30, 40, 45, 60, 75],
                index=[20, 30, 40, 45, 60, 75].index(int(saved_profile.get("minutes", 45))),
                key="wk_minutes"
            )
            goal = st.selectbox(
                "Objetivo principal",
                ["Perder grasa", "Ganar músculo", "Recomposición", "Mejorar rendimiento", "Salud general"],
                index=["Perder grasa", "Ganar músculo", "Recomposición", "Mejorar rendimiento", "Salud general"].index(saved_profile.get("goal", "Recomposición")),
                key="wk_goal"
            )

        st.markdown("**Capacidades (aprox.)**")
        c1, c2, c3 = st.columns(3)
        with c1:
            pushups = st.number_input("Flexiones seguidas", min_value=0, max_value=200, value=int(saved_profile.get("pushups", 10)), step=1, key="wk_pushups")
        with c2:
            squats = st.number_input("Sentadillas seguidas", min_value=0, max_value=300, value=int(saved_profile.get("squats", 25)), step=1, key="wk_squats")
        with c3:
            plank_sec = st.number_input("Plancha (segundos)", min_value=0, max_value=600, value=int(saved_profile.get("plank_sec", 30)), step=5, key="wk_plank")

        focus = st.text_input(
            "Foco (opcional): ej. glúteos, abs, espalda…",
            value=saved_profile.get("focus", "glúteos y abs"),
            key="wk_focus"
        )

        limitations = st.text_input(
            "Lesiones/limitaciones (opcional)",
            value=saved_profile.get("limitations", ""),
            key="wk_limits"
        )

        colS1, colS2 = st.columns(2)
        with colS1:
            if st.button("💾 Guardar perfil", type="primary", use_container_width=True):
                profile = {
                    "equipment": equipment.strip(),
                    "level": level,
                    "days": int(days),
                    "minutes": int(minutes),
                    "goal": goal,
                    "pushups": int(pushups),
                    "squats": int(squats),
                    "plank_sec": int(plank_sec),
                    "focus": focus.strip(),
                    "limitations": limitations.strip(),
                }
                set_setting("workout_profile_json", json.dumps(profile, ensure_ascii=False), user_id=uid)
                st.success("Perfil guardado ✅")
                st.rerun()
        with colS2:
            if st.button("🧹 Reset perfil", use_container_width=True):
                set_setting("workout_profile_json", "{}", user_id=uid)
                st.success("Perfil reseteado ✅")
                st.rerun()

    st.divider()

    # ====== Generación rutina ======
    st.subheader("✨ Generar rutina")
    st.caption("La rutina se adapta a tu perfil y se alinea con tus objetivos de nutrición.")

    # Botón grande (móvil)
    if st.button("⚡ Generar rutina personalizada", type="primary", use_container_width=True):
        # Recolectar contexto
        profile = {
            "equipment": st.session_state.get("wk_equipment", "").strip(),
            "level": st.session_state.get("wk_level", "Principiante"),
            "days": int(st.session_state.get("wk_days", 3)),
            "minutes": int(st.session_state.get("wk_minutes", 45)),
            "goal": st.session_state.get("wk_goal", "Recomposición"),
            "pushups": int(st.session_state.get("wk_pushups", 10)),
            "squats": int(st.session_state.get("wk_squats", 25)),
            "plank_sec": int(st.session_state.get("wk_plank", 30)),
            "focus": st.session_state.get("wk_focus", "").strip(),
            "limitations": st.session_state.get("wk_limits", "").strip(),
        }

        nutrition_context = (
            f"Objetivos nutrición (diarios): {target_kcal} kcal; "
            f"Proteína {target_p}g; Carbs {target_c}g; Grasas {target_f}g."
        )

        ctx = (
            f"Perfil entrenamiento:\n"
            f"- Nivel: {profile['level']}\n"
            f"- Días/semana: {profile['days']}\n"
            f"- Duración: {profile['minutes']} min\n"
            f"- Material: {profile['equipment'] or 'ninguno'}\n"
            f"- Capacidades: flexiones {profile['pushups']}, sentadillas {profile['squats']}, plancha {profile['plank_sec']}s\n"
            f"- Objetivo: {profile['goal']}\n"
            f"- Foco: {profile['focus'] or 'equilibrado'}\n"
            f"- Limitaciones: {profile['limitations'] or 'ninguna'}\n\n"
            f"{nutrition_context}\n\n"
            f"Preferencias: rutina razonable, progresiva, segura. Formato claro para móvil."
        )

        raw = generate_workout_plan_json(ctx)

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            st.error("La IA devolvió un formato raro. Reintenta.")
            st.code(raw)
            st.stop()

        # Guardar temporal en session (para botón Guardar)
        st.session_state["last_workout_plan"] = plan
        st.success("Rutina generada ✅ (revisa abajo)")
        st.rerun()

    st.divider()

    # ====== Mostrar rutina generada o guardada ======
    saved_plan_raw = get_setting("workout_plan_json", default="", user_id=uid)
    plan = st.session_state.get("last_workout_plan")

    if plan is None and saved_plan_raw:
        try:
            plan = json.loads(saved_plan_raw)
        except Exception:
            plan = None

    if not plan:
        st.info("Aún no hay rutina. Genera una y guarda la que te guste.")
    else:
        # Cabecera
        st.markdown(f"## 🗓️ {plan.get('plan_name','Rutina personalizada')}")
        st.caption(plan.get("summary", ""))

        # Guardar / borrar
        cA, cB = st.columns(2)
        with cA:
            if st.button("💾 Guardar rutina", type="primary", use_container_width=True):
                set_setting("workout_plan_json", json.dumps(plan, ensure_ascii=False), user_id=uid)
                st.success("Rutina guardada ✅")
                st.rerun()
        with cB:
            if st.button("🗑️ Borrar rutina guardada", use_container_width=True):
                set_setting("workout_plan_json", "", user_id=uid)
                st.success("Rutina borrada ✅")
                st.rerun()

        st.divider()

        # Calendario semanal (mobile friendly: expander por día)
        st.subheader("📅 Plan semanal")

        for d in plan.get("weekly_schedule", []):
            day = d.get("day", "Día")
            focus = d.get("focus", "")
            dur = d.get("duration_min", "")
            title = f"{day} — {focus}" if focus else day

            sess = d.get("session", {}) or {}

            # Card + expander para móvil
            st.markdown('<div class="wk-card">', unsafe_allow_html=True)
            with st.expander(f"▶️ {title}", expanded=False):
                st.markdown(
                    f"""
                    <div class="wk-title">
                      <h4>{title}</h4>
                      <span class="wk-chip">⏱️ {dur} min</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Warmup
                warm = sess.get("warmup", []) or []
                if warm:
                    st.markdown('<div class="wk-sec">', unsafe_allow_html=True)
                    st.markdown('<div class="wk-sec-title">🔥 Calentamiento</div>', unsafe_allow_html=True)
                    st.markdown("<ul class='wk-list'>" + "".join([f"<li>{x}</li>" for x in warm]) + "</ul>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # Main
                main = sess.get("main", []) or []
                if main:
                    st.markdown('<div class="wk-sec">', unsafe_allow_html=True)
                    st.markdown('<div class="wk-sec-title">🏋️ Principal</div>', unsafe_allow_html=True)

                    for ex in main:
                        ex_name = ex.get("exercise", "Ejercicio")
                        sets = ex.get("sets", 3)
                        reps = ex.get("reps", "8-12")
                        rest = ex.get("rest_sec", 90)
                        note = str(ex.get("notes", "")).strip()

                        st.markdown(
                            f"""
                            <div class="wk-ex">
                              <b>{ex_name}</b><br>
                              <span class="wk-chip">Series: {sets}</span>
                              <span class="wk-chip">Reps: {reps}</span>
                              <span class="wk-chip">Descanso: {rest}s</span>
                              {"<div class='wk-note'>📝 " + note + "</div>" if note else ""}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("</div>", unsafe_allow_html=True)

                # Finisher
                fin = sess.get("finisher_optional", []) or []
                if fin:
                    st.markdown('<div class="wk-sec">', unsafe_allow_html=True)
                    st.markdown('<div class="wk-sec-title">⚡ Finisher (opcional)</div>', unsafe_allow_html=True)
                    st.markdown("<ul class='wk-list'>" + "".join([f"<li>{x}</li>" for x in fin]) + "</ul>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # Cooldown
                cool = sess.get("cooldown", []) or []
                if cool:
                    st.markdown('<div class="wk-sec">', unsafe_allow_html=True)
                    st.markdown('<div class="wk-sec-title">🧘 Vuelta a la calma</div>', unsafe_allow_html=True)
                    st.markdown("<ul class='wk-list'>" + "".join([f"<li>{x}</li>" for x in cool]) + "</ul>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # Progresión
        st.subheader("📈 Progresión (4 semanas)")
        for w in plan.get("progression_4_weeks", []):
            st.markdown('<div class="wk-card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="wk-title">
                  <h4>Semana {w.get('week','?')}</h4>
                  <span class="wk-chip">📌 Progresión</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            notes = str(w.get("notes", "")).strip()
            rule = str(w.get("rule", "")).strip()

            if notes:
                st.markdown(f"- {notes}")
            if rule:
                st.caption(rule)

            st.markdown("</div>", unsafe_allow_html=True)


        nt = plan.get("nutrition_ties", {}) or {}
        st.subheader("🍽️ Nutrición (alineada con tu FitMacro)")

        td = nt.get("training_days", {}) or {}
        rd = nt.get("rest_days", {}) or {}

        # Entreno
        st.markdown('<div class="wk-card">', unsafe_allow_html=True)
        st.markdown("<div class='wk-title'><h4>🏋️ Días de entreno</h4><span class='wk-chip'>Fuel</span></div>", unsafe_allow_html=True)
        st.markdown(f"- Proteína sugerida: **{td.get('protein_g_hint', int(target_p))} g** (objetivo actual: {int(target_p)} g)")
        pre = str(td.get("preworkout_hint","")).strip()
        post = str(td.get("postworkout_hint","")).strip()
        if pre: st.markdown(f"- Pre: {pre}")
        if post: st.markdown(f"- Post: {post}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Descanso
        st.markdown('<div class="wk-card">', unsafe_allow_html=True)
        st.markdown("<div class='wk-title'><h4>🛌 Días de descanso</h4><span class='wk-chip'>Recovery</span></div>", unsafe_allow_html=True)
        st.markdown(f"- Proteína sugerida: **{rd.get('protein_g_hint', int(target_p))} g**")
        hint = str(rd.get("hint","")).strip()
        if hint: st.markdown(f"- {hint}")
        st.markdown("</div>", unsafe_allow_html=True)

































































































