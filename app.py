# app.py

import os, math, json
import hashlib, hmac, base64
from datetime import date

import streamlit as st
import pandas as pd
import requests
from streamlit_option_menu import option_menu


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


def inject_fitness_ui():
    st.markdown(r"""
    <style>
    :root{
      --bg0:#0b1020;
      --bg1:#0e1630;
      --card: rgba(255,255,255,0.06);
      --stroke: rgba(255,255,255,0.10);
      --txt: rgba(255,255,255,0.92);
      --muted: rgba(226,232,240,0.72);
      --pink:#ff4fd8;
      --purple:#8b5cf6;
      --cyan:#22d3ee;
      --green:#22c55e;
      --r16: 16px;
      --r20: 20px;
      --shadow: 0 18px 45px rgba(0,0,0,0.40);
    }

    html, body, [data-testid="stAppViewContainer"]{
      background:
        radial-gradient(900px 700px at 80% 10%, rgba(139,92,246,0.18) 0%, transparent 62%),
        radial-gradient(900px 700px at 10% 30%, rgba(255,79,216,0.12) 0%, transparent 62%),
        radial-gradient(900px 700px at 60% 90%, rgba(34,211,238,0.10) 0%, transparent 62%),
        linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%) !important;
      color: var(--txt) !important;
    }

    .block-container{
      max-width: 1100px;
      padding-top: 60px;
      padding-bottom: 90px;
    }

    /* Layout helpers */
    .fm-row{ display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .fm-title{ font-weight: 900; letter-spacing:-0.02em; }
    .fm-sub{ color: var(--muted); font-size: 12px; font-weight: 650; }
    .fm-big{ font-size: 32px; font-weight: 950; letter-spacing:-0.04em; }
    .fm-chip{
      display:inline-flex; align-items:center; gap:6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      color: rgba(255,255,255,0.88);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .fm-divider{
      height:1px; background: rgba(255,255,255,0.08);
      margin: 10px 0;
    }

    /* Cards */
    .fm-card{
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 18px 45px rgba(0,0,0,0.40);
      backdrop-filter: blur(12px);
    }
    .fm-card + .fm-card{ margin-top: 14px; }

    .fm-mini{ border-radius: 18px; padding: 14px 14px; }

    .fm-accent-pink{
      border-color: rgba(255,79,216,0.22);
      box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,79,216,0.10);
      background: linear-gradient(180deg, rgba(255,79,216,0.12), rgba(255,255,255,0.05));
    }
    .fm-accent-purple{
      border-color: rgba(139,92,246,0.22);
      box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(139,92,246,0.10);
      background: linear-gradient(180deg, rgba(139,92,246,0.12), rgba(255,255,255,0.05));
    }
    .fm-accent-cyan{
      border-color: rgba(34,211,238,0.22);
      box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(34,211,238,0.10);
      background: linear-gradient(180deg, rgba(34,211,238,0.10), rgba(255,255,255,0.05));
    }
    .fm-accent-green{
      border-color: rgba(34,197,94,0.22);
      box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(34,197,94,0.10);
      background: linear-gradient(180deg, rgba(34,197,94,0.10), rgba(255,255,255,0.05));
    }

    /* Inputs */
    input, textarea, div[data-baseweb="select"] > div{
      background: rgba(255,255,255,0.06) !important;
      border: 1px solid rgba(255,255,255,0.10) !important;
      border-radius: 14px !important;
      color: var(--txt) !important;
      font-weight: 650 !important;
    }

    /* Buttons */
    .stButton > button, div[data-testid="stFormSubmitButton"] button{
      border-radius: 999px !important;
      font-weight: 900 !important;
      border: 1px solid rgba(255,255,255,0.10) !important;
    }
    .stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] button{
      background: linear-gradient(135deg, rgba(255,79,216,0.92), rgba(139,92,246,0.92)) !important;
      color: #0b1020 !important;
      border: none !important;
      box-shadow: 0 16px 34px rgba(0,0,0,0.35);
    }

    /* Sidebar brand */
    .sb-brand{
      display:flex;
      align-items:center;
      gap:12px;
      padding: 12px 12px;
      margin: 6px 0 12px 0;
      border-radius: 18px;
      background: linear-gradient(135deg, rgba(255,79,216,0.12), rgba(139,92,246,0.12));
      border: 1px solid rgba(255,255,255,0.10);
      box-shadow: 0 18px 46px rgba(0,0,0,0.45);
    }
    .sb-logo{
      width:44px;height:44px;
      border-radius: 14px;
      background: linear-gradient(135deg, rgba(255,79,216,0.92), rgba(139,92,246,0.92));
      display:flex;align-items:center;justify-content:center;
      font-weight: 950;
      color: #0b1020;
    }
    .sb-title .sb-name{
      font-size: 18px;
      font-weight: 950;
      color: rgba(255,255,255,0.92);
      line-height: 1.05;
    }
    .sb-title .sb-sub{
      font-size: 12px;
      font-weight: 650;
      color: rgba(226,232,240,0.70);
      margin-top: 2px;
    }

    /* ===== Tabla FitMacro (dark) + scroll independiente ===== */
    .fm-table-card{
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 18px;
      padding: 10px;
      box-shadow: 0 18px 45px rgba(0,0,0,0.40);
      backdrop-filter: blur(12px);
    }
    .fm-table-scroll{
      overflow-x: auto;
      overflow-y: hidden;
      -webkit-overflow-scrolling: touch;
      border-radius: 14px;
    }
    .fm-table-scroll::-webkit-scrollbar{ height: 10px; }
    .fm-table-scroll::-webkit-scrollbar-track{ background: rgba(255,255,255,0.06); border-radius: 999px; }
    .fm-table-scroll::-webkit-scrollbar-thumb{ background: rgba(255,255,255,0.16); border-radius: 999px; }

    .fm-table-scroll table{
      width: 100%;
      min-width: 820px;
      border-collapse: separate !important;
      border-spacing: 0 !important;
      overflow: hidden !important;
      border-radius: 14px !important;
    }
    .fm-table-scroll thead th{
      background: linear-gradient(135deg, rgba(255,79,216,0.55), rgba(139,92,246,0.55)) !important;
      color: rgba(255,255,255,0.92) !important;
      font-weight: 900 !important;
      padding: 12px 12px !important;
      border: none !important;
      text-align: left !important;
    }
    .fm-table-scroll tbody td{
      background: rgba(255,255,255,0.06) !important;
      color: rgba(255,255,255,0.90) !important;
      font-weight: 650 !important;
      padding: 12px 12px !important;
      border: none !important;
    }
    .fm-table-scroll tbody tr:nth-child(even) td{ background: rgba(255,255,255,0.045) !important; }
    .fm-table-scroll tbody tr:hover td{
      background: rgba(34,211,238,0.10) !important;
      transition: background 0.12s ease;
    }

    /* ===== DASHBOARD: Totales mini-cards (HTML) ===== */
    .fm-metric-label{
      font-size: 12px;
      font-weight: 800;
      color: rgba(226,232,240,0.82);
      display:flex;
      align-items:center;
      gap:6px;
      margin-bottom: 6px;
    }
    .fm-metric-value{
      font-size: 34px;
      font-weight: 950;
      letter-spacing: -0.04em;
      color: rgba(255,255,255,0.92);
      line-height: 1.05;
    }

    /* ===== DASHBOARD: Progress rows (HTML) ===== */
    .fm-progress-row{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:14px;
    }
    .fm-progress-left{ flex: 1; min-width: 0; }
    .fm-progress-right{
      width: 160px;
      text-align:right;
      flex: 0 0 auto;
    }
    .fm-progress-title{
      font-weight: 900;
      color: rgba(255,255,255,0.92);
      margin-bottom: 6px;
    }
    .fm-progress-sub{
      color: rgba(226,232,240,0.72);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .fm-bar{
      height: 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.10);
      border: 1px solid rgba(255,255,255,0.10);
      overflow: hidden;
    }
    .fm-bar > span{
      display:block;
      height: 100%;
      width: 0%;
      border-radius: 999px;
      background: rgba(139,92,246,0.85);
    }
    .fm-rem-caption{
      color: rgba(226,232,240,0.72);
      font-size: 12px;
      font-weight: 800;
      margin-bottom: 4px;
    }
    .fm-rem-value{
      font-size: 32px;
      font-weight: 950;
      letter-spacing:-0.04em;
      color: rgba(255,255,255,0.92);
      line-height: 1.05;
    }

    /* Per-macro bar colors */
    .fm-bar.pink > span{ background: rgba(255,79,216,0.90); }
    .fm-bar.purple > span{ background: rgba(139,92,246,0.90); }
    .fm-bar.cyan > span{ background: rgba(34,211,238,0.90); }
    .fm-bar.green > span{ background: rgba(34,197,94,0.90); }

    /* ===== Secciones en una sola "card" (evita cards vacías) ===== */
    .fm-section{
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 18px 45px rgba(0,0,0,0.40);
      backdrop-filter: blur(12px);
      margin: 14px 0;
    }
    
    .fm-section-title{
      font-size: 20px;
      font-weight: 950;
      letter-spacing:-0.02em;
      margin: 0 0 10px 0;
    }
    
    .fm-grid-4{
      display:grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }
    
    @media (max-width: 900px){
      .fm-grid-4{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    
    .fm-progress-stack{
      display:flex;
      flex-direction:column;
      gap: 12px;
    }

/* =========================
   MOBILE UPGRADE (Dashboard)
   ========================= */
@media (max-width: 900px){
  /* Menos “aire” arriba: se siente más app */
  .block-container{
    padding-top:56px !important;
  }

  /* Títulos un pelín más compactos en móvil */
  h1, h2, h3{
    letter-spacing: -0.02em !important;
  }
}

    /* ===== HERO (cabecera dashboard) ===== */
    .fm-hero{
      position: relative;
      border-radius: 22px;
      padding: 16px 16px;
      border: 1px solid rgba(255,255,255,0.10);
      background:
        radial-gradient(900px 400px at 15% 20%, rgba(255,79,216,0.16) 0%, transparent 55%),
        radial-gradient(900px 500px at 85% 30%, rgba(34,211,238,0.12) 0%, transparent 60%),
        linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.04));
      box-shadow: 0 18px 45px rgba(0,0,0,0.45);
      overflow: hidden;
    }
    
    .fm-hero:after{
      content:"";
      position:absolute;
      inset:-2px;
      background: linear-gradient(135deg, rgba(255,79,216,0.10), rgba(139,92,246,0.08), rgba(34,211,238,0.08));
      filter: blur(18px);
      opacity: 0.8;
      pointer-events:none;
    }
    
    .fm-hero-inner{
      position: relative;
      display:flex;
      align-items:flex-start;
      justify-content:space-between;
      gap: 12px;
      z-index: 2;
    }
    
    .fm-hero-title{
      font-size: 24px;
      font-weight: 950;
      letter-spacing: -0.03em;
      margin: 0;
      color: rgba(255,255,255,0.95);
    }
    
    .fm-hero-sub{
      margin-top: 6px;
      font-size: 12px;
      font-weight: 750;
      color: rgba(226,232,240,0.75);
    }
    
    .fm-hero-pills{
      display:flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content:flex-end;
    }
    
    .fm-pill{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap: 6px;
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      color: rgba(255,255,255,0.92);
      font-size: 12px;
      font-weight: 900;
      white-space: nowrap;
    }
    
    .fm-pill.hot{
      background: linear-gradient(135deg, rgba(255,79,216,0.92), rgba(139,92,246,0.92));
      border: none;
      color: #0b1020;
      box-shadow: 0 12px 28px rgba(0,0,0,0.35);
    }
    
    /* En móvil: hero más “apretado” y bonito */
    @media (max-width: 900px){
      .fm-hero{
        padding: 14px 14px;
        border-radius: 20px;
      }
      .fm-hero-title{
        font-size: 22px;
      }
      .fm-hero-pills{
        justify-content:flex-start;
      }
    }

    /* ===== Medidas corporales (cards) ===== */
    .fm-measure-card{
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 16px;
      padding: 12px 12px;
      margin: 10px 0;
    }
    .fm-measure-title{
      font-size: 12px;
      font-weight: 900;
      color: rgba(226,232,240,0.82);
      margin-bottom: 6px;
    }


    /* =========================
       Medidas corporales: mantener 3 columnas en móvil (swipe)
       ========================= */
    .measures-wrap [data-testid="stHorizontalBlock"]{
      gap: 14px;
    }
    
    /* En móvil: NO apilar, permitir scroll horizontal */
    @media (max-width: 900px){
      .measures-wrap [data-testid="stHorizontalBlock"]{
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        -webkit-overflow-scrolling: touch !important;
        padding-bottom: 6px;
      }
    
      /* Cada "columna" tendrá ancho fijo para que quepan 3 con swipe */
      .measures-wrap [data-testid="stHorizontalBlock"] > div{
        flex: 0 0 auto !important;
        width: 280px !important; /* ajusta 260-320 si quieres */
      }
    
      /* Cards más compactas en móvil */
      .measures-wrap .fm-measure-card{
        margin: 6px 0 !important;
        padding: 10px 10px !important;
        border-radius: 14px !important;
      }
    
      /* Imagen: limita altura para no comerse la pantalla */
      .measures-wrap img{
        max-height: 420px !important;
        object-fit: contain !important;
      }
    }

    /* =========================
       Compactar inputs en MÓVIL (solo dentro de Tabs)
       ========================= */
    @media (max-width: 900px){
    
      /* reduce espacio entre “bloques” dentro de tabs */
      .stTabs [data-testid="stVerticalBlock"] > div{
        margin-bottom: -10px !important;
        padding-bottom: 0px !important;
      }
    
      /* reduce margen del texto/labels dentro de tabs */
      .stTabs [data-testid="stMarkdownContainer"] p{
        margin: 0 0 4px 0 !important;
        line-height: 1.15 !important;
      }
    
      /* number input: menos aire */
      .stTabs [data-testid="stNumberInput"]{
        margin: 0 !important;
      }
    
      /* input más bajito */
      .stTabs [data-testid="stNumberInput"] input{
        padding-top: 8px !important;
        padding-bottom: 8px !important;
        min-height: 40px !important;
      }
    
      /* botones +/− más compactos */
      .stTabs [data-testid="stNumberInput"] button{
        height: 40px !important;
        min-height: 40px !important;
      }
    }

    /* =========================
       Bottom Nav (Instagram-like)
       ========================= */
    .block-container{
      /* ya lo tienes, pero lo reforzamos para que no tape contenido */
      padding-bottom: 110px !important;
    }

    .fm-bottom-nav{
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 9999;
      padding: 10px 12px 18px 12px;
      background: rgba(11,16,32,0.86);
      backdrop-filter: blur(14px);
      border-top: 1px solid rgba(255,255,255,0.10);
    }

    .fm-bottom-nav .fm-inner{
      max-width: 1100px;
      margin: 0 auto;
      border-radius: 22px;
      padding: 10px 10px;
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.04));
      border: 1px solid rgba(255,255,255,0.10);
      box-shadow: 0 18px 45px rgba(0,0,0,0.45);
    }

    /* option-menu tweaks */
    .fm-bottom-nav ul{
      display:flex !important;
      justify-content: space-between !important;
      align-items:center !important;
      gap: 6px !important;
    }

    .fm-bottom-nav li{
      flex: 1 1 0 !important;
      min-width: 0 !important;
    }

    .fm-bottom-nav a{
      border-radius: 999px !important;
      padding: 10px 10px !important;
      text-align:center !important;
      font-weight: 950 !important;
      color: rgba(255,255,255,0.80) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      background: rgba(255,255,255,0.04) !important;
    }

    .fm-bottom-nav a:hover{
      background: rgba(255,255,255,0.07) !important;
      border-color: rgba(255,255,255,0.12) !important;
    }

    /* seleccionado */
    .fm-bottom-nav .nav-link.active{
      background: linear-gradient(135deg, rgba(139,92,246,0.42), rgba(34,211,238,0.24)) !important;
      border-color: rgba(255,255,255,0.16) !important;
      color: rgba(255,255,255,0.92) !important;
      box-shadow: 0 12px 28px rgba(0,0,0,0.35) !important;
    }

    /* HOME (primer botón) más grande + rosita */
    .fm-bottom-nav li:nth-child(1) a{
      transform: translateY(-6px);
      padding: 13px 10px !important;
      background: linear-gradient(135deg, rgba(255,79,216,0.92), rgba(139,92,246,0.92)) !important;
      color: #0b1020 !important;
      border: none !important;
      box-shadow: 0 18px 38px rgba(0,0,0,0.45) !important;
    }

    .fm-bottom-nav li:nth-child(1) a .icon{
      filter: drop-shadow(0 8px 18px rgba(0,0,0,0.35));
    }

    /* reduce texto/iconos */
    .fm-bottom-nav .nav-link span{
      font-size: 16px !important;
      font-weight: 950 !important;
    }

    /* (Opcional) ocultar sidebar si quieres look app total */
    /* section[data-testid="stSidebar"]{ display:none; } */





    </style>
    """, unsafe_allow_html=True)

# =========================
# UI helpers (Hero)
# =========================
def fm_hero(title: str, subtitle: str = "", pills=None):
    import textwrap
    pills = pills or []

    pills_html = "".join([f'<span class="fm-pill">{p}</span>' for p in pills])

    hero_html = textwrap.dedent(f"""
    <div class="fm-hero">
      <div class="fm-hero-inner">
        <div>
          <div class="fm-hero-title">{title}</div>
          {"<div class='fm-hero-sub'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        <div class="fm-hero-pills">
          {pills_html}
        </div>
      </div>
    </div>
    """).strip()

    st.markdown(hero_html, unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


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
    if "auth_ok" not in st.session_state:
        st.session_state["auth_ok"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = ""

    users = _get_users()

    if st.session_state.get("user_id") and st.session_state["user_id"] not in users:
        st.session_state["auth_ok"] = False
        st.session_state["user_id"] = ""

    if st.session_state["auth_ok"]:
        return

    if not users:
        st.error("No hay usuarios configurados en secrets.toml ([users]).")
        st.stop()

    has_dialog = hasattr(st, "dialog")

    def login_form():
        st.markdown("### 🔐 Iniciar sesión")
        st.caption("Selecciona usuario e introduce contraseña.")

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
inject_fitness_ui()

# =========================
# USDA FoodData Central (FDC) helpers
# =========================
FDC_BASE = "https://api.nal.usda.gov/fdc/v1"

def _fdc_key() -> str:
    # Usa tu key real en secrets; fallback a DEMO_KEY para pruebas
    return st.secrets.get("FDC_API_KEY", "v9pKcIdiVPg2mrWKcmMNgcdTUr4bqgLavV9Gb4TD")

def fdc_search_generic_foods(query: str, page_size: int = 8, include_fndds: bool = False):
    """
    Devuelve lista de foods.
    - Por defecto SOLO básicos: Foundation + SR Legacy
    - Opcional: incluir Survey (FNDDS) = platos preparados
    """
    q = (query or "").strip()
    if not q:
        return []

    url = f"{FDC_BASE}/foods/search"
    params = {"api_key": _fdc_key()}

    data_types = ["Foundation", "SR Legacy"]
    if include_fndds:
        data_types.append("Survey (FNDDS)")

    payload = {
        "query": q,
        "pageSize": int(page_size),
        "dataType": data_types,
        "sortBy": "dataType.keyword",
        "sortOrder": "asc",
    }

    r = requests.post(url, params=params, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json() or {}
    foods = data.get("foods", []) or []

    # --- Ranking local: prioriza ingredientes y penaliza platos ---
    good_tokens = [
        "raw", "breast", "meat", "thigh", "drumstick", "wing",
        "skinless", "boneless", "uncooked", "plain",
        "chicken", "turkey", "beef", "pork", "fish",
        "potato", "rice", "oat", "egg", "milk", "yogurt"
    ]
    bad_tokens = [
        "soup", "stew", "with", "sauce", "gravy", "fried", "breaded",
        "style", "recipe", "sandwich", "pizza", "burger", "taco",
        "rice with", "casserole", "fricassee"
    ]

    def score_food(f):
        desc = str(f.get("description", "")).lower()
        dt = str(f.get("dataType", "")).lower()

        score = 0
        # preferimos foundation/sr legacy
        if "foundation" in dt:
            score += 50
        if "sr legacy" in dt:
            score += 40
        if "fndds" in dt:
            score -= 20

        # tokens buenos/malos por descripción
        for t in good_tokens:
            if t in desc:
                score += 3
        for t in bad_tokens:
            if t in desc:
                score -= 4

        # penaliza descripciones muy largas típicas de platos
        if len(desc) > 60:
            score -= 5

        return score

    foods.sort(key=score_food, reverse=True)
    return foods

def fdc_get_macros_per_100g(fdc_id: int):
    """
    Lee detalle del alimento y extrae kcal/prote/carb/fat (por 100g típicamente).
    """
    url = f"{FDC_BASE}/food/{int(fdc_id)}"
    params = {"api_key": _fdc_key()}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    food = r.json() or {}

    # Nutrientes vienen en foodNutrients
    # Buscamos por nombre estándar (puede variar un poco según dataset)
    nutrients = food.get("foodNutrients", []) or []

    def pick(names):
        for n in nutrients:
            name = str(n.get("nutrient", {}).get("name", "")).lower()
            if any(x in name for x in names):
                val = n.get("amount", None)
                unit = n.get("nutrient", {}).get("unitName", "")
                if val is None:
                    continue
                return float(val), str(unit)
        return 0.0, ""

    kcal, _ = pick(["energy"])  # normalmente "Energy"
    protein, _ = pick(["protein"])
    fat, _ = pick(["total lipid", "fat"])
    carbs, _ = pick(["carbohydrate", "carb"])

    # Ojo: algunos entries podrían no traer alguno => 0.0
    return {
        "name": food.get("description", "Alimento"),
        "calories": float(kcal),
        "protein": float(protein),
        "carbs": float(carbs),
        "fat": float(fat),
    }

def fdc_tag(food: dict) -> str:
    """
    Etiqueta simple para UI:
    - 🧪 Ingrediente: foundation / sr legacy o desc tipo 'raw/breast/meat'
    - 🍲 Plato: fndds o desc tipo soup/stew/with sauce...
    """
    desc = str(food.get("description", "")).lower()
    dt = str(food.get("dataType", "")).lower()

    if "fndds" in dt:
        return "🍲 Plato"

    # heurística rápida
    if any(x in desc for x in ["soup", "stew", "with sauce", "gravy", "style", "recipe"]):
        return "🍲 Plato"

    return "🧪 Ingrediente"




require_login()

uid = st.session_state["user_id"]

# =========================
# SESSION UI STATE (fecha + dialogs)
# =========================
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = date.today()

def _set_date(d: date):
    st.session_state["selected_date"] = d

selected_date = st.session_state["selected_date"]
selected_date_str = selected_date.isoformat()

if "food_popup_open" not in st.session_state:
    st.session_state["food_popup_open"] = False

if "profile_popup_open" not in st.session_state:
    st.session_state["profile_popup_open"] = False

# =========================
# NAV STATE
# =========================
if "goto_page" not in st.session_state:
    st.session_state["goto_page"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "📊 Dashboard"

if "menu_open" not in st.session_state:
    st.session_state["menu_open"] = False

# Atajos internos (si algún botón pone goto_page)
if st.session_state["goto_page"]:
    st.session_state["page"] = st.session_state["goto_page"]
    st.session_state["goto_page"] = None


def _go(target_page: str):
    """Cambia de página y cierra popups."""
    st.session_state["page"] = target_page
    st.session_state["food_popup_open"] = False
    st.session_state["profile_popup_open"] = False

# =========================
# POPUPS (Comidas / Perfil)
# =========================
def _open_foods():
    st.session_state["food_popup_open"] = True

def _open_profile():
    st.session_state["profile_popup_open"] = True


# Popup: Comidas
if st.session_state.get("food_popup_open", False):
    @st.dialog("🍽️ Comidas", width="small")
    def _dlg_foods():
        st.caption("Elige qué quieres hacer 👇")

        if st.button("🍽 Registro", type="primary", use_container_width=True):
            st.session_state["food_popup_open"] = False
            _go("🍽 Registro")
            st.rerun()

        if st.button("➕ Añadir alimento", use_container_width=True):
            st.session_state["food_popup_open"] = False
            _go("➕ Añadir alimento")
            st.rerun()

        if st.button("👨‍🍳 Chef IA", use_container_width=True):
            st.session_state["food_popup_open"] = False
            _go("👨‍🍳 Chef IA")
            st.rerun()

        st.divider()
        if st.button("✖️ Cerrar", use_container_width=True):
            st.session_state["food_popup_open"] = False
            st.rerun()

    _dlg_foods()


# Popup: Perfil (fecha + logout)
if st.session_state.get("profile_popup_open", False):
    @st.dialog("👤 Perfil", width="small")
    def _dlg_profile():
        st.caption(f"Sesión: **{st.session_state['user_id']}**")

        d = st.date_input("📅 Día", value=st.session_state["selected_date"])
        if d != st.session_state["selected_date"]:
            st.session_state["selected_date"] = d
            st.toast("Fecha actualizada ✅")
            st.rerun()

        st.divider()

        if st.button("🚪 Cerrar sesión", type="primary", use_container_width=True):
            st.session_state["auth_ok"] = False
            st.session_state["user_id"] = ""
            st.session_state["profile_popup_open"] = False
            st.rerun()

        if st.button("✖️ Cerrar", use_container_width=True):
            st.session_state["profile_popup_open"] = False
            st.rerun()

    _dlg_profile()


# =========================
# BOTTOM NAV (Instagram-like)
# =========================
def render_bottom_nav():
    st.markdown('<div class="fm-bottom-nav"><div class="fm-inner">', unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["🏠", "🍽️", "🎯", "🏋️", "👤"],
        icons=["house-fill", "egg-fried", "bullseye", "activity", "person-circle"],
        orientation="horizontal",
        key="fm_bottom_nav",
        styles={
            "container": {"padding": "0px", "background-color": "transparent"},
            "icon": {"font-size": "18px"},
            "nav-link": {"padding": "10px 10px", "margin": "0px", "border-radius": "999px"},
            "nav-link-selected": {"border-radius": "999px"},
        },
    )

    st.markdown("</div></div>", unsafe_allow_html=True)

    # helper: navega SOLO si cambia
    def nav_to(p):
        if st.session_state.get("page") != p:
            _go(p)
            st.rerun()

    if selected == "🏠":
        nav_to("📊 Dashboard")

    elif selected == "🍽️":
        _open_foods()
        st.rerun()

    elif selected == "🎯":
        nav_to("🎯 Objetivos")

    elif selected == "🏋️":
        nav_to("🏋️ Rutina IA")

    elif selected == "👤":
        _open_profile()
        st.rerun()



# =========================
# Sync bottom nav -> page (ANTES de renderizar option_menu)
# =========================
page_to_tab = {
    "📊 Dashboard": "🏠",
    "🍽 Registro": "🍽️",
    "➕ Añadir alimento": "🍽️",
    "👨‍🍳 Chef IA": "🍽️",
    "🤖 IA Alimento": "🍽️",
    "🎯 Objetivos": "🎯",
    "🏋️ Rutina IA": "🏋️",
}

desired_tab = page_to_tab.get(st.session_state.get("page", "📊 Dashboard"), "🏠")
if st.session_state.get("fm_bottom_nav") != desired_tab:
    st.session_state["fm_bottom_nav"] = desired_tab

# =========================
# CURRENT PAGE
# =========================
render_bottom_nav()

page = st.session_state["page"]

# ==========================================================
# PÁGINA: DASHBOARD
# ==========================================================
if page == "📊 Dashboard":
    import altair as alt
    import streamlit.components.v1 as components
    import textwrap

    # --- Objetivos (ANTES del hero, para poder mostrarlos arriba) ---
    uid = st.session_state["user_id"]
    target_kcal = float(get_setting("target_deficit_calories", 1800, user_id=uid))
    target_p = float(get_setting("target_protein", 120, user_id=uid))
    target_c = float(get_setting("target_carbs", 250, user_id=uid))
    target_f = float(get_setting("target_fat", 60, user_id=uid))

    # --- Hero (cabecera móvil pro) ---
    hero_html = textwrap.dedent(f"""
    <div class="fm-hero">
      <div class="fm-hero-inner">
        <div>
          <div class="fm-hero-title">📊 Dashboard</div>
        </div>
        <div class="fm-hero-pills">
          <span class="fm-pill">🎯 Obj: {target_kcal:.0f} kcal</span>
          <span class="fm-pill hot">⚡ Dale duro</span>
        </div>
      </div>
    </div>
    """).strip()
    st.markdown(hero_html, unsafe_allow_html=True)

    # Acciones rápidas (móvil-friendly)
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Añadir comida", type="primary", use_container_width=True):
            st.session_state["goto_page"] = "🍽 Registro"
            st.rerun()
    with c2:
        if st.button("🎯 Cambiar objetivos", use_container_width=True):
            st.session_state["goto_page"] = "🎯 Objetivos"
            st.rerun()

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- Datos del día ---
    rows = list_entries_by_date(selected_date_str, st.session_state["user_id"])

    total_kcal = sum(float(r["calories"]) for r in rows) if rows else 0.0
    total_protein = sum(float(r["protein"]) for r in rows) if rows else 0.0
    total_carbs = sum(float(r["carbs"]) for r in rows) if rows else 0.0
    total_fat = sum(float(r["fat"]) for r in rows) if rows else 0.0

    # --- CSS SOLO para el iframe (dashboard) ---
    DASH_CSS = """
    <style>
      :root{
        --card: rgba(255,255,255,0.06);
        --stroke: rgba(255,255,255,0.10);
        --txt: rgba(255,255,255,0.92);
        --muted: rgba(226,232,240,0.72);
      }
      body{
        margin:0;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial;
        color: var(--txt);
        background: transparent;
      }
      .fm-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.40);
        backdrop-filter: blur(12px);
      }
      .fm-mini{ border-radius: 18px; padding: 14px; }

      .fm-accent-pink{
        border-color: rgba(255,79,216,0.22);
        box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,79,216,0.10);
        background: linear-gradient(180deg, rgba(255,79,216,0.12), rgba(255,255,255,0.05));
      }
      .fm-accent-purple{
        border-color: rgba(139,92,246,0.22);
        box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(139,92,246,0.10);
        background: linear-gradient(180deg, rgba(139,92,246,0.12), rgba(255,255,255,0.05));
      }
      .fm-accent-cyan{
        border-color: rgba(34,211,238,0.22);
        box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(34,211,238,0.10);
        background: linear-gradient(180deg, rgba(34,211,238,0.10), rgba(255,255,255,0.05));
      }
      .fm-accent-green{
        border-color: rgba(34,197,94,0.22);
        box-shadow: 0 18px 45px rgba(0,0,0,0.40), 0 0 0 1px rgba(34,197,94,0.10);
        background: linear-gradient(180deg, rgba(34,197,94,0.10), rgba(255,255,255,0.05));
      }

      .fm-section{
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.40);
        backdrop-filter: blur(12px);
        margin: 14px 0;
      }
      .fm-section-title{
        font-size: 20px;
        font-weight: 950;
        letter-spacing:-0.02em;
        margin: 0 0 10px 0;
      }

      .fm-grid-4{
        display:grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
      }
      @media (max-width: 900px){
        .fm-grid-4{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }

      .fm-metric-label{
        font-size: 12px;
        font-weight: 800;
        color: rgba(226,232,240,0.82);
        display:flex;
        align-items:center;
        gap:6px;
        margin-bottom: 6px;
      }
      .fm-metric-value{
        font-size: 34px;
        font-weight: 950;
        letter-spacing: -0.04em;
        color: rgba(255,255,255,0.92);
        line-height: 1.05;
      }

      .fm-progress-stack{
        display:flex;
        flex-direction:column;
        gap: 12px;
      }
      .fm-progress-row{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:14px;
      }
      .fm-progress-left{ flex: 1; min-width: 0; }
      .fm-progress-right{ width: 160px; text-align:right; flex: 0 0 auto; }

      .fm-progress-title{
        font-weight: 900;
        color: rgba(255,255,255,0.92);
        margin-bottom: 6px;
      }
      .fm-progress-sub{
        color: rgba(226,232,240,0.72);
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 10px;
      }

      .fm-bar{
        height: 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.10);
        overflow: hidden;
      }
      .fm-bar > span{
        display:block;
        height: 100%;
        width: 0%;
        border-radius: 999px;
      }
      .fm-bar.pink > span{ background: rgba(255,79,216,0.90); }
      .fm-bar.purple > span{ background: rgba(139,92,246,0.90); }
      .fm-bar.cyan > span{ background: rgba(34,211,238,0.90); }
      .fm-bar.green > span{ background: rgba(34,197,94,0.90); }

      .fm-rem-caption{
        color: rgba(226,232,240,0.72);
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 4px;
      }
      .fm-rem-value{
        font-size: 32px;
        font-weight: 950;
        letter-spacing:-0.04em;
        color: rgba(255,255,255,0.92);
        line-height: 1.05;
      }

      /* ✅ Quita borde blanco del embed de Altair dentro del iframe */
      .vega-embed, .vega-embed details, .vega-embed summary{
        color: rgba(255,255,255,0.90) !important;
      }
      .vega-embed{
        border: none !important;
        background: transparent !important;
      }
    </style>
    """

    # Helper: renderizar charts dentro de la card (iframe)
    def chart_in_card(title: str, chart, height: int = 360, subtitle: str = ""):
        chart_html = chart.to_html()
        subtitle_html = f'<div class="fm-progress-sub">{subtitle}</div>' if subtitle else ""
        html = f"""
        {DASH_CSS}
        <div class="fm-section">
          <div class="fm-section-title">{title}</div>
          {subtitle_html}
          <div style="border-radius:14px; overflow:hidden;">
            {chart_html}
          </div>
        </div>
        """
        components.html(html, height=height, scrolling=False)

    # ===== TOTALES DEL DÍA (iframe con CSS dentro) =====
    totales_html = textwrap.dedent(f"""
    {DASH_CSS}
    <div class="fm-section">
      <div class="fm-section-title">📌 Totales del día</div>

      <div class="fm-grid-4">
        <div class="fm-card fm-mini fm-accent-pink">
          <div class="fm-metric-label">🔥 Calorías</div>
          <div class="fm-metric-value">{total_kcal:.0f} kcal</div>
        </div>

        <div class="fm-card fm-mini fm-accent-purple">
          <div class="fm-metric-label">🥩 Proteína</div>
          <div class="fm-metric-value">{total_protein:.1f} g</div>
        </div>

        <div class="fm-card fm-mini fm-accent-cyan">
          <div class="fm-metric-label">🍚 Carbs</div>
          <div class="fm-metric-value">{total_carbs:.1f} g</div>
        </div>

        <div class="fm-card fm-mini fm-accent-green">
          <div class="fm-metric-label">🥑 Grasas</div>
          <div class="fm-metric-value">{total_fat:.1f} g</div>
        </div>
      </div>
    </div>
    """).strip()
    components.html(totales_html, height=270, scrolling=False)

    # ===== PROGRESO (iframe con CSS dentro) =====
    def clamp01(x: float) -> float:
        return 0.0 if x < 0 else 1.0 if x > 1 else x

    def mk_progress_html(label, value, goal, unit, accent_cls, bar_color_cls):
        goal = float(goal) if goal else 0.0
        value = float(value) if value else 0.0
        ratio = 0.0 if goal <= 0 else clamp01(value / goal)
        remaining = goal - value
        tag = "Restante" if remaining >= 0 else "Exceso"

        pct = int(round(ratio * 100.0))
        left_txt = (
            f"{value:.0f}{unit} / {goal:.0f}{unit}"
            if unit.strip() == "kcal"
            else f"{value:.1f}{unit} / {goal:.1f}{unit}"
        )
        rem_txt = (
            f"{abs(remaining):.0f}{unit}"
            if unit.strip() == "kcal"
            else f"{abs(remaining):.1f}{unit}"
        )

        return textwrap.dedent(f"""
        <div class="fm-card fm-mini {accent_cls}">
          <div class="fm-progress-row">
            <div class="fm-progress-left">
              <div class="fm-progress-title">{label} · {left_txt}</div>
              <div class="fm-bar {bar_color_cls}"><span style="width:{pct}%"></span></div>
            </div>
            <div class="fm-progress-right">
              <div class="fm-rem-caption">{tag}</div>
              <div class="fm-rem-value">{rem_txt}</div>
            </div>
          </div>
        </div>
        """).strip()

    progress_html = "".join([
        mk_progress_html("🔥 Calorías", total_kcal, target_kcal, " kcal", "fm-accent-pink", "pink"),
        mk_progress_html("🥩 Proteína", total_protein, target_p, " g", "fm-accent-purple", "purple"),
        mk_progress_html("🍚 Carbs", total_carbs, target_c, " g", "fm-accent-cyan", "cyan"),
        mk_progress_html("🥑 Grasas", total_fat, target_f, " g", "fm-accent-green", "green"),
    ])

    progreso_html = textwrap.dedent(f"""
    {DASH_CSS}
    <div class="fm-section">
      <div class="fm-section-title">🎯 Progreso del día</div>
      <div class="fm-progress-sub">Objetivo vs consumido y cuánto te queda.</div>
      <div class="fm-progress-stack">
        {progress_html}
      </div>
    </div>
    """).strip()
    components.html(progreso_html, height=550, scrolling=False)

    # ===== HISTÓRICO =====
    hist = daily_totals_last_days(30, user_id=uid)
    hist_df = pd.DataFrame(hist, columns=["date", "calories", "protein", "carbs", "fat"])

    # ===== CHART: Últimos 30 días =====
    if hist_df.empty:
        st.info("Aún no hay histórico para este usuario. Registra comidas y aquí verás la evolución 💪")
    else:
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        hist_df = hist_df.sort_values("date")

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

        hist_df["kcal_7d"] = hist_df["calories"].rolling(7, min_periods=1).mean()
        last7 = float(hist_df["kcal_7d"].iloc[-1])
        diff = last7 - float(target_kcal)

        chart_in_card(
            "📈 Últimos 30 días",
            kcal_chart,
            height=420,
            subtitle=f"📌 Media móvil (7 días): {last7:.0f} kcal · Diferencia vs objetivo: {diff:+.0f} kcal"
        )

    # ===== CHART: Macros recientes (14 días) =====
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

        chart_in_card(
            "🥗 Macros recientes (14 días)",
            macros_chart,
            height=380
        )

# ==========================================================
# PÁGINA: REGISTRO  (MULTI-AÑADIDO / “CARRITO”)
# ==========================================================
elif page == "🍽 Registro":
    fm_hero(
        "🍽 Registro",
        subtitle=f"Día: {selected_date_str}",
        pills=["🧺 Multi-añadido", "⚡ Rápido"]
    )

    # -------------------------
    # Estado / feedback
    # -------------------------
    if "pending_entries" not in st.session_state:
        st.session_state["pending_entries"] = []  # lista de items pendientes

    if st.session_state.get("_just_added", False):
        last_ids = st.session_state.get("_last_add_ids", [])
        if isinstance(last_ids, list) and last_ids:
            st.success(f"✅ Añadidas {len(last_ids)} entradas al registro")
        else:
            last_id = st.session_state.get("_last_add_id", "")
            if last_id:
                st.success(f"✅ Entrada guardada (id={last_id})")
        st.session_state["_just_added"] = False

    # -------------------------
    # DEBUG (lo dejas igual)
    # -------------------------
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

    # -------------------------
    # Datos base
    # -------------------------
    categories = list_categories()
    if not categories:
        st.error("No hay categorías. Revisa la pestaña foods.")
        st.stop()

    # Construye un map global nombre -> food (para calcular macros y para guardar)
    # (Tu app asume nombres únicos; si hay duplicados, habría que usar id)
    food_map = {}
    for c in categories:
        for f in list_foods_by_category(c):
            food_map[f["name"]] = f

    # -------------------------
    # UI: carrito (añadir varios)
    # -------------------------
    st.markdown('<div class="fm-card fm-accent-cyan">', unsafe_allow_html=True)
    st.markdown("## 🧺 Añadir varios (rápido)")
    st.caption("Vas metiendo alimentos a la lista y luego los vuelcas todos al registro con un solo botón.")

    colA, colB = st.columns([2, 2])
    with colA:
        category = st.selectbox("Categoría", categories, key="reg_category_cart")
    with colB:
        foods_in_cat = list_foods_by_category(category)
        if not foods_in_cat:
            st.warning("Esa categoría no tiene alimentos.")
            st.stop()
        food = st.selectbox("Alimento", foods_in_cat, format_func=lambda x: x["name"], key="reg_food_cart")

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        grams = float(
            st.number_input(
                "Gramos",
                min_value=1.0,
                step=1.0,
                value=100.0,
                format="%.0f",
                key="reg_grams_cart",
            )
        )
    with col2:
        meal = st.selectbox(
            "Comida",
            ["Desayuno", "Almuerzo", "Merienda", "Cena"],
            index=0,
            key="reg_meal_cart",
        )
    with col3:
        st.write("")
        st.write("")

    # Preview macros del item actual (solo visual, no guarda)
    try:
        _m = scale_macros(food, grams)
        st.caption(
            f"Preview: **{food['name']}** — {grams:.0f} g · "
            f"{_m['calories']:.0f} kcal · P {_m['protein']:.1f} · C {_m['carbs']:.1f} · G {_m['fat']:.1f}"
        )
    except Exception:
        pass

    b1, b2, b3 = st.columns([2, 2, 2])
    with b1:
        add_to_list = st.button("➕ Añadir a la lista", type="primary", use_container_width=True, key="btn_add_to_list")
    with b2:
        clear_list = st.button("🧹 Vaciar lista", use_container_width=True, key="btn_clear_list")
    with b3:
        pending_n = len(st.session_state["pending_entries"])
        commit_disabled = pending_n == 0
        commit = st.button(
            f"✅ Añadir al registro ({pending_n})",
            disabled=commit_disabled,
            type="primary",
            use_container_width=True,
            key="btn_commit_list",
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # -------------------------
    # Acciones: añadir / vaciar / guardar
    # -------------------------
    if add_to_list:
        try:
            item = {
                "meal": str(meal),
                "name": str(food["name"]),
                "grams": float(grams),
            }
            st.session_state["pending_entries"].append(item)
            st.toast("Añadido a la lista ✅")
            st.rerun()
        except Exception as e:
            st.error("No pude añadir el item a la lista.")
            st.exception(e)

    if clear_list:
        st.session_state["pending_entries"] = []
        st.toast("Lista vaciada 🧹")
        st.rerun()

    if commit and st.session_state["pending_entries"]:
        try:
            new_ids = []
            for it in st.session_state["pending_entries"]:
                nm = str(it.get("name", "")).strip()
                gr = float(it.get("grams", 0))
                ml = str(it.get("meal", "")).strip()

                if not nm or nm not in food_map:
                    continue
                if gr <= 0:
                    continue
                if ml not in ["Desayuno", "Almuerzo", "Merienda", "Cena"]:
                    ml = "Almuerzo"

                base_food = food_map[nm]
                macros = scale_macros(base_food, gr)

                entry = {
                    "user_id": st.session_state["user_id"],
                    "entry_date": selected_date_str,
                    "meal": ml,
                    "name": nm,
                    "grams": float(gr),
                    **macros,
                }

                new_id = add_entry(entry)
                new_ids.append(new_id)

            st.cache_data.clear()

            # feedback
            st.session_state["_just_added"] = True
            st.session_state["_last_add_ids"] = new_ids
            if new_ids:
                st.session_state["_last_add_id"] = new_ids[-1]

            # limpia carrito
            st.session_state["pending_entries"] = []
            st.rerun()

        except Exception as e:
            st.error("❌ Error guardando el lote en Google Sheets")
            st.exception(e)

    # -------------------------
    # Mostrar pendientes (carrito)
    # -------------------------
    pending = st.session_state.get("pending_entries", [])
    if pending:
        st.markdown('<div class="fm-card fm-accent-purple">', unsafe_allow_html=True)
        st.markdown("## 🧾 Pendientes por añadir")

        # Tabla simple
        pend_df = pd.DataFrame(pending, columns=["meal", "name", "grams"])
        pend_df = pend_df.rename(columns={"meal": "Comida", "name": "Alimento", "grams": "Gramos"})
        pend_df["Gramos"] = pd.to_numeric(pend_df["Gramos"], errors="coerce").fillna(0).round(0).astype(int)

        st.dataframe(pend_df, use_container_width=True, hide_index=True)

        # Totales del carrito (opcional pero útil)
        tot = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for it in pending:
            nm = str(it.get("name", ""))
            gr = float(it.get("grams", 0))
            if nm in food_map and gr > 0:
                mm = scale_macros(food_map[nm], gr)
                tot["calories"] += float(mm.get("calories", 0))
                tot["protein"] += float(mm.get("protein", 0))
                tot["carbs"] += float(mm.get("carbs", 0))
                tot["fat"] += float(mm.get("fat", 0))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 kcal (pendientes)", f"{tot['calories']:.0f}")
        c2.metric("🥩 P (pendientes)", f"{tot['protein']:.1f} g")
        c3.metric("🍚 C (pendientes)", f"{tot['carbs']:.1f} g")
        c4.metric("🥑 G (pendientes)", f"{tot['fat']:.1f} g")

        st.caption("Nota: si quieres borrar un pendiente, lo más limpio es vaciar lista y volver a añadir (luego lo mejoramos con botones por fila).")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ======================================================
    # REGISTRO DEL DÍA (TU TABLA ACTUAL: intacta)
    # ======================================================
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

        df_tbl = df_view.copy()

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
        )

        table_html = styler.to_html()

        st.markdown(
            f"""<div class="fm-table-card"><div class="fm-table-scroll">{table_html}</div></div>""",
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

            # Reusar el food_map global (ya lo hemos construido arriba)
            base_food = food_map.get(row["name"])
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

    # --- Medidas corporales guardadas (opcional) ---
    # --- Medidas corporales guardadas (desde JSON) ---
    raw_bm = get_setting("body_metrics_json", "{}", user_id=uid)
    try:
        bm = json.loads(raw_bm) if raw_bm else {}
    except Exception:
        bm = {}

    measures = bm.get("measures_cm", {}) or {}
    saved_neck = float(measures.get("neck", 40))
    saved_shoulders = float(measures.get("shoulders", 117))
    saved_chest = float(measures.get("chest", 102))
    saved_waist = float(measures.get("waist", 90))
    saved_hip = float(measures.get("hip", 93))
    saved_arm_l = float(measures.get("arm_l", 34))
    saved_arm_r = float(measures.get("arm_r", 34))
    saved_thigh_l = float(measures.get("thigh_l", 65))
    saved_thigh_r = float(measures.get("thigh_r", 65))
    saved_calf_l = float(measures.get("calf_l", 40))
    saved_calf_r = float(measures.get("calf_r", 40))
    
    fm_hero(
        "🎯 Objetivos",
        subtitle="Calcula y guarda tus objetivos diarios.",
        pills=["🧮 Calculadora", "💾 Guarda perfil"]
    )

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

    # =========================
    # 📏 Medidas corporales (UI tipo captura)
    # =========================
    st.markdown("### 📏 Medidas corporales")
    compact_mode = st.toggle("📱 Modo móvil compacto (recomendado en móvil)", value=True)
    
    with st.expander("Abrir / editar medidas", expanded=True):

        # Helper: input más estrecho + menos espacio vertical (móvil)
        def measure_input(title, min_v, max_v, default_v, key):
            st.caption(title)
            c_val, c_pad = st.columns([2.4, 1])  # <- aquí controlas la “línea azul”
            with c_val:
                v = st.number_input(
                    title,
                    min_value=float(min_v),
                    max_value=float(max_v),
                    value=float(default_v),
                    step=0.5,
                    key=key,
                    label_visibility="collapsed"
                )

            return v

        
        if compact_mode:
            # =========================
            # 📱 MODO COMPACTO (tabs)
            # =========================
            tabL, tabC, tabR = st.tabs(["⬅️ Medidas (I)", "🧍‍♂️ Foto", "➡️ Medidas (D)"])
    
            with tabC:
                img_path = os.path.join("assets", "body.png")
                if os.path.exists(img_path):
                    st.image(img_path, width=220)
                else:
                    st.info("Pon una imagen en `assets/body.png` para ver el muñeco aquí 🙂")
                st.caption("Consejo: mide siempre en las mismas condiciones para que los cambios sean comparables.")
    
            with tabL:
                neck_cm   = measure_input("Cuello (cm)", 20, 60, saved_neck, "m_neck")
                arm_l_cm  = measure_input("Brazo (I) (cm)", 15, 60, saved_arm_l, "m_arm_l")
                chest_cm  = measure_input("Pecho (cm)", 50, 160, saved_chest, "m_chest")
                thigh_l_cm= measure_input("Muslo (I) (cm)", 30, 110, saved_thigh_l, "m_thigh_l")
                calf_l_cm = measure_input("Pantorrilla (I) (cm)", 20, 70, saved_calf_l, "m_calf_l")
    
            with tabR:
                shoulders_cm = measure_input("Hombros (cm)", 60, 200, saved_shoulders, "m_shoulders")
                arm_r_cm     = measure_input("Brazo (D) (cm)", 15, 60, saved_arm_r, "m_arm_r")
                waist_cm     = measure_input("Cintura (cm)", 40, 200, saved_waist, "m_waist")
                hip_cm       = measure_input("Cadera (cm)", 60, 220, saved_hip, "m_hip")
                thigh_r_cm   = measure_input("Muslo (D) (cm)", 30, 110, saved_thigh_r, "m_thigh_r")
                calf_r_cm    = measure_input("Pantorrilla (D) (cm)", 20, 70, saved_calf_r, "m_calf_r")
    
        else:
            # =========================
            # 🖥️ MODO PC (3 columnas)
            # =========================
            colL, colC, colR = st.columns([1.1, 1.3, 1.1], gap="large")
    
            with colC:
                img_path = os.path.join("assets", "body.png")
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.info("Pon una imagen en `assets/body.png` para ver el muñeco aquí 🙂")
                st.caption("Consejo: mide siempre en las mismas condiciones para que los cambios sean comparables.")
    
            with colL:
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Cuello (cm)</div>', unsafe_allow_html=True)
                neck_cm = st.number_input("Cuello", 20.0, 60.0, float(saved_neck), 0.5, key="m_neck", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Brazo (I) (cm)</div>', unsafe_allow_html=True)
                arm_l_cm = st.number_input("Brazo Izquierdo", 15.0, 60.0, float(saved_arm_l), 0.5, key="m_arm_l", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Pecho (cm)</div>', unsafe_allow_html=True)
                chest_cm = st.number_input("Pecho", 50.0, 160.0, float(saved_chest), 0.5, key="m_chest", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Muslo (I) (cm)</div>', unsafe_allow_html=True)
                thigh_l_cm = st.number_input("Muslo Izquierdo", 30.0, 110.0, float(saved_thigh_l), 0.5, key="m_thigh_l", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Pantorrilla (I) (cm)</div>', unsafe_allow_html=True)
                calf_l_cm = st.number_input("Pantorrilla Izquierda", 20.0, 70.0, float(saved_calf_l), 0.5, key="m_calf_l", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
            with colR:
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Hombros (cm)</div>', unsafe_allow_html=True)
                shoulders_cm = st.number_input("Hombros", 60.0, 200.0, float(saved_shoulders), 0.5, key="m_shoulders", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Brazo (D) (cm)</div>', unsafe_allow_html=True)
                arm_r_cm = st.number_input("Brazo Derecho", 15.0, 60.0, float(saved_arm_r), 0.5, key="m_arm_r", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Cintura (cm)</div>', unsafe_allow_html=True)
                waist_cm = st.number_input("Cintura", 40.0, 200.0, float(saved_waist), 0.5, key="m_waist", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Cadera (cm)</div>', unsafe_allow_html=True)
                hip_cm = st.number_input("Cadera", 60.0, 220.0, float(saved_hip), 0.5, key="m_hip", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Muslo (D) (cm)</div>', unsafe_allow_html=True)
                thigh_r_cm = st.number_input("Muslo Derecho", 30.0, 110.0, float(saved_thigh_r), 0.5, key="m_thigh_r", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
    
                st.markdown('<div class="fm-measure-card"><div class="fm-measure-title">Pantorrilla (D) (cm)</div>', unsafe_allow_html=True)
                calf_r_cm = st.number_input("Pantorrilla Derecha", 20.0, 70.0, float(saved_calf_r), 0.5, key="m_calf_r", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)


        st.markdown('</div>', unsafe_allow_html=True)

        # =========================
        # Métricas clave (IMC + ratios + estimaciones)
        # =========================
        # IMC
        h_m = float(height) / 100.0 if float(height) > 0 else 0.0
        bmi = (float(weight) / (h_m ** 2)) if h_m > 0 else 0.0

        # Cintura/altura
        whtr = (float(waist_cm) / float(height)) if float(height) > 0 else 0.0

        # Cintura/cadera
        whr = (float(waist_cm) / float(hip_cm)) if float(hip_cm) > 0 else 0.0

        # % Grasa US Navy (estimación). Si sexo=F usa cadera.
        def _navy_bodyfat(sex_local: str, height_cm: float, neck: float, waist: float, hip: float) -> float:
            # protege contra logs invalidos
            if height_cm <= 0:
                return 0.0
            sex_local = (sex_local or "M").upper().strip()

            try:
                if sex_local == "M":
                    x = waist - neck
                    if x <= 0:
                        return 0.0
                    bf = 495.0 / (1.0324 - 0.19077 * math.log10(x) + 0.15456 * math.log10(height_cm)) - 450.0
                else:
                    x = waist + hip - neck
                    if x <= 0:
                        return 0.0
                    bf = 495.0 / (1.29579 - 0.35004 * math.log10(x) + 0.22100 * math.log10(height_cm)) - 450.0
                # clamp razonable
                return float(max(0.0, min(70.0, bf)))
            except Exception:
                return 0.0

        bodyfat_pct = _navy_bodyfat(sex, float(height), float(neck_cm), float(waist_cm), float(hip_cm))
        fat_kg = float(weight) * (bodyfat_pct / 100.0)
        lbm_kg = float(weight) - fat_kg
        ffmi = (lbm_kg / (h_m ** 2)) if h_m > 0 else 0.0

        st.divider()
        st.markdown("#### 📌 Métricas clave (estimadas)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📏 IMC", f"{bmi:.1f}")
        m2.metric("🧪 % grasa (Navy)", f"{bodyfat_pct:.1f}%")
        m3.metric("💪 Masa magra", f"{lbm_kg:.1f} kg")
        m4.metric("🏋️ FFMI", f"{ffmi:.1f}")

        r1, r2 = st.columns(2)
        r1.metric("📐 Cintura/Altura", f"{whtr:.2f}")
        r2.metric("📐 Cintura/Cadera", f"{whr:.2f}")


    
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

        
        # =========================
        # Guardar medidas + métricas en 1 sola key (evita rate limit)
        # =========================
        def _ss(key, fallback):
            v = st.session_state.get(key, None)
            return float(v) if v is not None else float(fallback)

        neck_cm_v = _ss("m_neck", saved_neck)
        shoulders_cm_v = _ss("m_shoulders", saved_shoulders)
        chest_cm_v = _ss("m_chest", saved_chest)
        waist_cm_v = _ss("m_waist", saved_waist)
        hip_cm_v = _ss("m_hip", saved_hip)
        arm_l_cm_v = _ss("m_arm_l", saved_arm_l)
        arm_r_cm_v = _ss("m_arm_r", saved_arm_r)
        thigh_l_cm_v = _ss("m_thigh_l", saved_thigh_l)
        thigh_r_cm_v = _ss("m_thigh_r", saved_thigh_r)
        calf_l_cm_v = _ss("m_calf_l", saved_calf_l)
        calf_r_cm_v = _ss("m_calf_r", saved_calf_r)

        # Métricas clave
        h_m = float(height) / 100.0 if float(height) > 0 else 0.0
        bmi_v = (float(weight) / (h_m ** 2)) if h_m > 0 else 0.0
        whtr_v = (waist_cm_v / float(height)) if float(height) > 0 else 0.0
        whr_v = (waist_cm_v / hip_cm_v) if hip_cm_v > 0 else 0.0

        def _navy_bodyfat(sex_local: str, height_cm: float, neck: float, waist: float, hip: float) -> float:
            if height_cm <= 0:
                return 0.0
            sex_local = (sex_local or "M").upper().strip()
            try:
                if sex_local == "M":
                    x = waist - neck
                    if x <= 0:
                        return 0.0
                    bf = 495.0 / (1.0324 - 0.19077 * math.log10(x) + 0.15456 * math.log10(height_cm)) - 450.0
                else:
                    x = waist + hip - neck
                    if x <= 0:
                        return 0.0
                    bf = 495.0 / (1.29579 - 0.35004 * math.log10(x) + 0.22100 * math.log10(height_cm)) - 450.0
                return float(max(0.0, min(70.0, bf)))
            except Exception:
                return 0.0

        bodyfat_pct_v = _navy_bodyfat(sex, float(height), neck_cm_v, waist_cm_v, hip_cm_v)
        fat_kg_v = float(weight) * (bodyfat_pct_v / 100.0)
        lbm_kg_v = float(weight) - fat_kg_v
        ffmi_v = (lbm_kg_v / (h_m ** 2)) if h_m > 0 else 0.0

        body_metrics = {
            "measures_cm": {
                "neck": neck_cm_v,
                "shoulders": shoulders_cm_v,
                "chest": chest_cm_v,
                "waist": waist_cm_v,
                "hip": hip_cm_v,
                "arm_l": arm_l_cm_v,
                "arm_r": arm_r_cm_v,
                "thigh_l": thigh_l_cm_v,
                "thigh_r": thigh_r_cm_v,
                "calf_l": calf_l_cm_v,
                "calf_r": calf_r_cm_v,
            },
            "metrics": {
                "bmi": bmi_v,
                "bodyfat_percent": bodyfat_pct_v,
                "fat_kg": fat_kg_v,
                "lbm_kg": lbm_kg_v,
                "ffmi": ffmi_v,
                "whtr": whtr_v,
                "whr": whr_v,
            }
        }

        # ✅ UNA sola llamada a Google Sheets
        set_setting("body_metrics_json", json.dumps(body_metrics, ensure_ascii=False), user_id=uid)

        
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
    fm_hero(
        "🍽️ Gestión de alimentos",
        subtitle="Añade, edita o borra alimentos de tu base de datos.",
        pills=["➕ Añadir", "✏️ Editar", "🗑️ Borrar"]
    )
    
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

    fm_hero(
        "👨‍🍳 Chef IA",
        subtitle="Nutrición + menús + platos con tus alimentos.",
        pills=["🤖 Chat", "🍽️ Menús", "🥘 Platos"]
    )
    
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

    if "chef_mode" not in st.session_state:
        st.session_state["chef_mode"] = "none"

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

    cats = list_categories()
    food_map = {}
    for c in cats:
        for f in list_foods_by_category(c):
            food_map[f["name"]] = f
    allowed = list(food_map.keys())

    mode = st.session_state.get("chef_mode", "Menus")

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
        realista = st.toggle("✅ Menú coherente (porciones realistas)", value=True, key="menu_realista")


        
        if st.button("✨ Generar menú", type="primary", use_container_width=True):
            context = f"""
            Objetivo diario: {kcal_obj} kcal; Proteína {prot_obj}g; Carbs {carb_obj}g; Grasas {fat_obj}g.
            Preferencia: {pref}.
            
            Genera un menú de 4 comidas: Desayuno, Almuerzo, Merienda, Cena.
            REGLAS DE COHERENCIA (obligatorio):
            - Porciones realistas, evita cantidades absurdas.
            - Cereales/avena/muesli: máximo 60 g por ración (ideal 30–50 g).
            - Fruta típica: 80–200 g por ración.
            - Lácteo/bebida en desayuno si existe en mis alimentos (leche, yogur, queso fresco, bebida vegetal).
            - Legumbres (lentejas/garbanzos): preferible en Almuerzo. En Cena solo si la cena es ligera o no hay otra opción.
            - Cena: prioriza proteína + verduras/ensalada o carbs moderados. Evita comidas pesadas.
            - No repitas el mismo alimento en más de 2 comidas.
            - Usa SOLO alimentos de la lista permitida.
            Devuelve JSON válido con la estructura: {{ "meals":[{{"meal":"Desayuno","items":[{{"name":"...","grams":123}}]}}] }}.
            """.strip()
            raw = generate_menu_json(context, allowed_food_names=allowed)

            try:
                menu = json.loads(raw)
            except json.JSONDecodeError:
                st.error("La IA devolvió un formato raro. Vuelve a generar.")
                st.code(raw)
                st.stop()

            # ===== Ajuste automático: si el menú se queda corto, subir gramos =====
            MIN_KCAL_RATIO = 0.92  # mínimo 92% del objetivo
            MAX_KCAL_RATIO = 1.05  # máximo 105% del objetivo
            STEP_G = 25.0          # incremento por iteración
            MAX_ITERS = 80         # límite de iteraciones para no colgar
            
            def menu_totals(menu_obj: dict) -> dict:
                t = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
                for meal in menu_obj.get("meals", []) or []:
                    for it in meal.get("items", []) or []:
                        nm = str(it.get("name", "")).strip()
                        g = float(it.get("grams", 0) or 0)
                        if nm in food_map and g > 0:
                            m = scale_macros(food_map[nm], g)
                            t["calories"] += float(m["calories"])
                            t["protein"] += float(m["protein"])
                            t["carbs"] += float(m["carbs"])
                            t["fat"] += float(m["fat"])
                return t
            
            def pick_best_booster(allowed_names: list[str]) -> str | None:
                """
                Elige un alimento "fácil" para subir kcal sin volverse loco:
                - Primero carbs (arroz, pan, cereales, pasta, patata…)
                - Si no hay, grasa (aceite, frutos secos)
                - Si no hay, proteína (pollo/pavo/atun/huevos)
                """
                carbs_kw = ["arroz", "pasta", "fideo", "noodle", "pan", "cereal", "cereales", "avena", "patata", "platano", "uva", "kiwi"]
                fat_kw   = ["aceite", "nuez", "almendra", "cacahu", "mantequilla", "aguacate"]
                prot_kw  = ["pollo", "pavo", "atun", "huevo", "yogur", "queso", "carne", "pesc"]
            
                def score(nm: str) -> int:
                    n = nm.lower()
                    s = 0
                    if any(k in n for k in carbs_kw): s += 30
                    if any(k in n for k in fat_kw):   s += 20
                    if any(k in n for k in prot_kw):  s += 10
                    # también valora densidad calórica por 100g
                    if nm in food_map:
                        try:
                            s += int(float(food_map[nm]["calories"]) / 10.0)  # kcal/100g -> +0..50
                        except Exception:
                            pass
                    return s
            
                cands = [n for n in allowed_names if n in food_map]
                if not cands:
                    return None
                cands.sort(key=score, reverse=True)
                return cands[0]
            
            def boost_menu_to_target(menu_obj: dict, kcal_target: float) -> dict:
                if kcal_target <= 0:
                    return menu_obj
            
                booster = pick_best_booster(allowed)
                if booster is None:
                    return menu_obj
            
                # intentamos subir principalmente en Almuerzo/Cena para coherencia
                meal_order = ["Almuerzo", "Cena", "Desayuno", "Merienda"]
            
                for _ in range(MAX_ITERS):
                    t = menu_totals(menu_obj)
                    if t["calories"] >= kcal_target * MIN_KCAL_RATIO:
                        break
            
                    # elige a qué comida añadir el booster
                    chosen_meal = None
                    for mn in meal_order:
                        for m in menu_obj.get("meals", []) or []:
                            if str(m.get("meal", "")).strip() == mn:
                                chosen_meal = m
                                break
                        if chosen_meal:
                            break
            
                    if chosen_meal is None:
                        break
            
                    # si el booster ya está en esa comida, sube gramos, si no, lo añade
                    items = chosen_meal.get("items", []) or []
                    found = False
                    for it in items:
                        if str(it.get("name", "")).strip() == booster:
                            it["grams"] = float(it.get("grams", 0) or 0) + STEP_G
                            found = True
                            break
                    if not found:
                        items.append({"name": booster, "grams": STEP_G})
                        chosen_meal["items"] = items
            
                    
            
                return menu_obj
            
            menu = boost_menu_to_target(menu, float(kcal_obj))


            
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

    elif mode == "platos":
        st.subheader("🥘 Generador de platos")
        st.caption("Combina alimentos de tu base, calcula macros automáticamente y guarda el plato como nuevo alimento.")

        if not allowed:
            st.info("No hay alimentos disponibles en tu base para crear un plato.")
            st.stop()

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

                    st.session_state["dish_items"] = [{"name": allowed[0], "grams": 100.0}]
                    st.rerun()


# ==========================================================
# PÁGINA: RUTINA IA
# ==========================================================
elif page == "🏋️ Rutina IA":
    fm_hero(
        "🏋️ Rutina IA",
        subtitle="Rutina personalizada según tu material, nivel y objetivos.",
        pills=["📱 Mobile", "📈 Progresiva"]
    )
    import json
    from ai_groq import generate_workout_plan_json



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


# ==========================================================
# PÁGINA: IA ALIMENTO (genéricos)
# ==========================================================
elif page == "🤖 IA Alimento":
    fm_hero(
        "🤖 IA Alimento",
        subtitle="Busca un alimento y guárdalo por 100g desde USDA FoodData Central.",
        pills=["🧪 Básicos", "🍲 Platos"]
    )

    # -------------------------
    # Estado estable
    # -------------------------
    if "ai_food_results" not in st.session_state:
        st.session_state["ai_food_results"] = []
    if "ai_food_last_query" not in st.session_state:
        st.session_state["ai_food_last_query"] = ""
    if "ai_food_selected_fdcid" not in st.session_state:
        st.session_state["ai_food_selected_fdcid"] = None
    if "ai_food_macros_preview" not in st.session_state:
        st.session_state["ai_food_macros_preview"] = None
    if "ai_food_search_now" not in st.session_state:
        st.session_state["ai_food_search_now"] = False

    def _clear_ai_state():
        st.session_state["ai_food_results"] = []
        st.session_state["ai_food_selected_fdcid"] = None
        st.session_state["ai_food_macros_preview"] = None

    # -------------------------
    # UI
    # -------------------------
    st.markdown('<div class="fm-card fm-accent-cyan">', unsafe_allow_html=True)

    q = st.text_input(
        "Nombre del alimento",
        placeholder="Ej: patata, arroz, pollo...",
        key="ai_food_query"
    )

    # Toggle pro: básicos vs platos
    only_basics = st.toggle("✅ Solo alimentos básicos (recomendado)", value=True, key="ai_food_only_basics")
    include_fndds = not only_basics  # si no son básicos, permitimos platos

    col1, col2 = st.columns([2, 1])
    with col1:
        category = st.text_input("Categoría para guardarlo", value="Genericos", key="ai_food_category")
    with col2:
        # ✅ Botón que activa la flag + rerun (esto arregla el “no hace nada”)
        if st.button("🔎 Buscar", type="primary", use_container_width=True, key="btn_ai_food_search"):
            st.session_state["ai_food_search_now"] = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # -------------------------
    # Buscar (solo cuando toca)
    # -------------------------
    if st.session_state.get("ai_food_search_now", False):
        st.session_state["ai_food_search_now"] = False

        q_clean = (q or "").strip()
        if not q_clean:
            st.warning("Escribe un alimento para buscar.")
        else:
            try:
                # ✅ feedback visual (parece que “no pasa nada” sin esto)
                with st.spinner("Consultando USDA FoodData Central…"):
                    foods = fdc_search_generic_foods(q_clean, page_size=8, include_fndds=include_fndds)

                st.session_state["ai_food_results"] = foods
                st.session_state["ai_food_last_query"] = q_clean
                st.toast("Búsqueda OK ✅")

                # Reset selección/preview al buscar nuevo
                st.session_state["ai_food_selected_fdcid"] = None
                st.session_state["ai_food_macros_preview"] = None

                # ✅ fuerza refresco para pintar resultados ya
                st.rerun()

            except requests.HTTPError as e:
                code = getattr(e.response, "status_code", None)
                if code == 403:
                    st.error("403: API key inválida o sin permisos. Revisa `FDC_API_KEY` en secrets.")
                elif code == 429:
                    st.error("429: demasiadas peticiones (rate limit). Espera un poco y reintenta.")
                else:
                    st.error("Error HTTP al buscar en USDA (FDC).")
                st.exception(e)

            except requests.Timeout as e:
                st.error("Timeout conectando con USDA (FDC). Reintenta.")
                st.exception(e)

            except Exception as e:
                st.error("No pude buscar en la base USDA (FDC). Revisa tu conexión o API key.")
                st.exception(e)

    foods = st.session_state.get("ai_food_results", [])

    if not foods:
        st.info("Busca algo arriba para ver resultados.")
        st.stop()

    # -------------------------
    # Resultados + selección
    # -------------------------
    st.markdown('<div class="fm-card fm-accent-purple">', unsafe_allow_html=True)
    st.subheader("Resultados")
    st.caption(f"Query: **{st.session_state.get('ai_food_last_query','')}**")

    options = []
    for f in foods:
        desc = f.get("description", "Food")
        dt = f.get("dataType", "")
        fdc_id = f.get("fdcId", "")
        tag = fdc_tag(f)  # (la función ya la tienes definida fuera)
        options.append({"fdcId": fdc_id, "label": f"{tag} · {desc}  ·  {dt}  ·  id={fdc_id}"})

    # índice por defecto: si ya había selección, la mantenemos
    current_id = st.session_state.get("ai_food_selected_fdcid")
    idx = 0
    if current_id is not None:
        for i, opt in enumerate(options):
            if int(opt["fdcId"]) == int(current_id):
                idx = i
                break

    picked = st.selectbox(
        "Elige el alimento correcto",
        options,
        index=idx,
        format_func=lambda x: x["label"],
        key="ai_food_pick",
    )

    # Si cambia el picked, limpia preview para recalcular solo una vez
    if st.session_state.get("ai_food_selected_fdcid") != int(picked["fdcId"]):
        st.session_state["ai_food_selected_fdcid"] = int(picked["fdcId"])
        st.session_state["ai_food_macros_preview"] = None

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # -------------------------
    # Preview macros (cacheado)
    # -------------------------
    st.markdown('<div class="fm-card fm-accent-green">', unsafe_allow_html=True)
    st.subheader("Macros (por 100g)")

    if st.session_state.get("ai_food_macros_preview") is None:
        try:
            with st.spinner("Leyendo macros del alimento…"):
                macros = fdc_get_macros_per_100g(int(st.session_state["ai_food_selected_fdcid"]))
            st.session_state["ai_food_macros_preview"] = macros

        except requests.HTTPError as e:
            code = getattr(e.response, "status_code", None)
            if code == 403:
                st.error("403: API key inválida. Revisa `FDC_API_KEY` en secrets.")
            elif code == 429:
                st.error("429: rate limit. Espera y reintenta.")
            else:
                st.error("Error HTTP leyendo detalles del alimento (FDC).")
            st.exception(e)
            st.stop()

        except Exception as e:
            st.error("No pude leer los detalles del alimento (FDC).")
            st.exception(e)
            st.stop()

    macros = st.session_state.get("ai_food_macros_preview") or {}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔥 kcal", f"{float(macros.get('calories', 0)):.0f}")
    with c2:
        st.metric("🥩 Prote", f"{float(macros.get('protein', 0)):.1f} g")
    with c3:
        st.metric("🍚 Carbs", f"{float(macros.get('carbs', 0)):.1f} g")
    with c4:
        st.metric("🥑 Grasas", f"{float(macros.get('fat', 0)):.1f} g")

    st.caption("Fuente: USDA FoodData Central.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # -------------------------
    # Guardar en tu base
    # -------------------------
    st.markdown('<div class="fm-card fm-accent-pink">', unsafe_allow_html=True)
    st.subheader("Guardar en tu base")

    default_name = str(macros.get("name", "")).strip()
    nn = st.text_input(
        "Nombre final (puedes editarlo)",
        value=default_name.title(),
        key="ai_food_final_name"
    )

    if st.button("✅ Añadir a mi base", type="primary", use_container_width=True, key="btn_ai_food_save"):
        try:
            final_name = (nn or "").strip()
            final_cat = (category or "Genericos").strip()

            if not final_name:
                st.error("Pon un nombre válido.")
            else:
                add_food({
                    "name": final_name,
                    "category": final_cat,
                    "calories": float(macros.get("calories", 0.0)),
                    "protein": float(macros.get("protein", 0.0)),
                    "carbs": float(macros.get("carbs", 0.0)),
                    "fat": float(macros.get("fat", 0.0)),
                })
                st.cache_data.clear()
                st.success("Alimento añadido ✅")

                # opcional: limpiar estado para nueva búsqueda
                # _clear_ai_state()
                # st.rerun()

        except Exception as e:
            st.error("Error guardando el alimento en Google Sheets.")
            st.exception(e)

    st.markdown("</div>", unsafe_allow_html=True)













