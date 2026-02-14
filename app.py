# app.py
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


def inject_black_theme():
    st.markdown("""
    <style>

    /* =========================
       FITMACRO PRO THEME
       ========================= */

    :root{
        --bg: #dce3ed;
        --bg2: #d4efe3;

        --panel: #ffffff;
        --panel-soft: #f4f7fb;

        --stroke: rgba(15,23,42,0.18);
        --stroke-soft: rgba(15,23,42,0.08);

        --txt: #0f172a;
        --muted: #334155;

        --green: #16a34a;
        --green2: #22c55e;
        --blue: #2563eb;

        --radius: 18px;
    }

    /* ===== Fondo ===== */

    html, body, [data-testid="stAppViewContainer"]{
        background:
            radial-gradient(1000px 700px at 10% 10%, rgba(34,197,94,0.18) 0%, transparent 60%),
            radial-gradient(900px 600px at 90% 15%, rgba(37,99,235,0.16) 0%, transparent 60%),
            linear-gradient(180deg, var(--bg) 0%, #eef2f9 100%) !important;
        color: var(--txt) !important;
    }

    .block-container{
        max-width: 1180px;
        padding-top: 18px;
        padding-bottom: 60px;
    }

    /* ===== Sidebar ===== */

    [data-testid="stSidebar"] > div{
        background: rgba(255,255,255,0.92) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid var(--stroke-soft) !important;
    }

    /* ===== Tipografía ===== */

    h1{
        font-size: 44px !important;
        font-weight: 900 !important;
        letter-spacing: -0.04em;
        color: var(--txt) !important;
    }

    h2, h3{
        font-weight: 800 !important;
        color: var(--txt) !important;
    }

    p, label, .stCaption, .stMarkdown{
        color: var(--muted) !important;
    }

    /* ===== Inputs ===== */

    input, textarea{
        background: var(--panel-soft) !important;
        border: 1px solid var(--stroke) !important;
        border-radius: 14px !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div{
        background: var(--panel-soft) !important;
        border: 1px solid var(--stroke) !important;
        border-radius: 14px !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] span{
        color: #000000 !important;
    }

    /* ===== BOTONES UNIFICADOS ===== */

    .stButton > button,
    div[data-testid="stFormSubmitButton"] button,
    button[kind="primary"]{

        background: linear-gradient(
            135deg,
            var(--green) 0%,
            var(--green2) 45%,
            var(--blue) 100%
        ) !important;

        color: #ffffff !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px;

        box-shadow: 0 12px 28px rgba(37,99,235,0.25);
        transition: all 0.15s ease-in-out;
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover{
        transform: translateY(-1px);
        filter: brightness(1.05);
        box-shadow: 0 16px 36px rgba(22,163,74,0.28);
    }

    .stButton > button:active,
    div[data-testid="stFormSubmitButton"] button:active{
        transform: translateY(0px);
    }

    button:disabled{
        background: linear-gradient(135deg,#94a3b8 0%,#cbd5e1 100%) !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }

    /* ===== MÉTRICAS ===== */

    div[data-testid="stMetric"]{
        background: var(--panel);
        border: 1px solid var(--stroke-soft);
        border-radius: var(--radius);
        padding: 18px;
        box-shadow: 0 18px 46px rgba(15,23,42,0.12);
        position: relative;
        overflow: hidden;
    }

    div[data-testid="stMetric"]::before{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(900px 220px at 15% 0%, rgba(34,197,94,0.28) 0%, transparent 65%),
            radial-gradient(900px 220px at 85% 0%, rgba(37,99,235,0.22) 0%, transparent 65%);
        pointer-events: none;
    }

    div[data-testid="stMetric"] label{
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 13px !important;
    }

    div[data-testid="stMetricValue"]{
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 36px !important;
    }

    /* ===== TABLAS ===== */

    div[data-testid="stDataFrame"]{
        background: linear-gradient(
            180deg,
            rgba(34,197,94,0.18) 0%,
            rgba(37,99,235,0.15) 100%
        ) !important;

        border: 1px solid var(--stroke-soft) !important;
        border-radius: var(--radius) !important;
        box-shadow: 0 18px 40px rgba(15,23,42,0.12);
    }

    div[data-testid="stDataFrame"] td,
    div[data-testid="stDataFrame"] th{
        color: #000000 !important;
        font-weight: 600 !important;
        background: transparent !important;
    }

    /* ===== PROGRESS ===== */

    div[data-testid="stProgress"]{
        background: rgba(15,23,42,0.12) !important;
        border-radius: 999px !important;
    }

    div[data-testid="stProgress"] > div > div{
        background: linear-gradient(
            90deg,
            var(--green) 0%,
            var(--green2) 45%,
            var(--blue) 100%
        ) !important;
    }

    /* ===== FIT CARD (para gráficos Altair) ===== */

    .fit-card{
        background: linear-gradient(
            180deg,
            rgba(34,197,94,0.18) 0%,
            rgba(37,99,235,0.15) 100%
        );
        padding: 18px;
        border-radius: var(--radius);
        border: 1px solid var(--stroke-soft);
        box-shadow: 0 18px 40px rgba(15,23,42,0.12);
    }
    
    /* ===== HERO BANNER ===== */
    
    .hero-banner{
        display: flex;
        align-items: center;
        gap: 18px;
    
        background: linear-gradient(
            135deg,
            rgba(34,197,94,0.25) 0%,
            rgba(37,99,235,0.22) 100%
        );
    
        padding: 22px 26px;
        border-radius: 20px;
        margin-bottom: 28px;
    
        box-shadow: 0 20px 50px rgba(15,23,42,0.15);
    }
    
    .hero-logo{
        width: 60px;
        height: 60px;
    
        border-radius: 50%;
        background: linear-gradient(135deg,#16a34a,#2563eb);
    
        display: flex;
        align-items: center;
        justify-content: center;
    
        font-weight: 900;
        font-size: 22px;
        color: white;
    }
    
    .hero-text h1{
        margin: 0;
        font-size: 34px !important;
    }
    
    .hero-text p{
        margin: 0;
        font-size: 14px;
        opacity: 0.8;
    }

    /* =========================
       SIDEBAR PREMIUM
       ========================= */
    
    [data-testid="stSidebar"] > div{
      padding-top: 18px !important;
      padding-bottom: 18px !important;
    }
    
    /* Header brand */
    .sb-brand{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 12px;
      margin: 6px 8px 14px 8px;
      border-radius: 18px;
      background: linear-gradient(
          135deg,
          rgba(34,197,94,0.18) 0%,
          rgba(37,99,235,0.16) 100%
      );
      border: 1px solid rgba(15,23,42,0.08);
      box-shadow: 0 14px 30px rgba(15,23,42,0.10);
    }
    
    .sb-logo{
      width: 44px;
      height: 44px;
      border-radius: 14px;
      background: linear-gradient(135deg,#16a34a,#2563eb);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      color: #fff;
      letter-spacing: 0.5px;
    }
    
    .sb-title .sb-name{
      font-size: 18px;
      font-weight: 900;
      color: #0f172a;
      line-height: 1.05;
    }
    .sb-title .sb-sub{
      font-size: 12px;
      font-weight: 650;
      color: rgba(15,23,42,0.60);
      margin-top: 2px;
    }
    
    /* Inputs en sidebar: más “card” */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div{
      background: rgba(255,255,255,0.96) !important;
      border: 1px solid rgba(15,23,42,0.18) !important;
      border-radius: 14px !important;
    }
    
    /* Radio nav como pills */
    [data-testid="stSidebar"] div[role="radiogroup"]{
      margin: 8px 6px 0 6px;
      padding: 10px;
      border-radius: 18px;
      background: rgba(255,255,255,0.60);
      border: 1px solid rgba(15,23,42,0.08);
    }
    
    /* Cada opción */
    [data-testid="stSidebar"] div[role="radiogroup"] label{
      border-radius: 14px !important;
      padding: 10px 12px !important;
      margin: 6px 0 !important;
      transition: all .15s ease;
    }
    
    /* Hover */
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover{
      background: rgba(37,99,235,0.10) !important;
      transform: translateY(-1px);
    }
    
    /* Texto de opciones */
    [data-testid="stSidebar"] div[role="radiogroup"] label p{
      font-weight: 750 !important;
      color: #0f172a !important;
    }
    
    /* “seleccionado”: Streamlit marca con input checked, lo estilizamos */
    [data-testid="stSidebar"] div[role="radiogroup"] input:checked + div{
      background: linear-gradient(
          135deg,
          rgba(22,163,74,0.18) 0%,
          rgba(37,99,235,0.14) 100%
      ) !important;
      border-radius: 14px !important;
      border: 1px solid rgba(15,23,42,0.08) !important;
    }
    
    /* Tip al fondo */
    .sb-tip{
      margin: 14px 10px 0 10px;
      padding: 12px 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.60);
      border: 1px solid rgba(15,23,42,0.08);
      color: rgba(15,23,42,0.65);
      font-weight: 650;
      font-size: 12px;
    }

    /* Botón flotante Fit */
    
    .fit-fab{
        position: fixed;
        bottom: 20px;
        right: 20px;
    
        width: 60px;
        height: 60px;
    
        border-radius: 20px;
    
        background: linear-gradient(135deg,#16a34a,#2563eb);
        color: white;
    
        display: flex;
        align-items: center;
        justify-content: center;
    
        font-size: 26px;
        font-weight: 900;
    
        box-shadow: 0 18px 40px rgba(15,23,42,0.25);
        z-index: 9999;
        cursor: pointer;
    }

    /* =========================
       DATAFRAME FIT STYLE
       ========================= */
    
    /* Contenedor general */
    div[data-testid="stDataFrame"]{
        background: linear-gradient(
            180deg,
            rgba(34,197,94,0.18) 0%,
            rgba(37,99,235,0.15) 100%
        ) !important;
    
        border-radius: 18px !important;
        border: 1px solid rgba(15,23,42,0.10) !important;
        box-shadow: 0 20px 40px rgba(15,23,42,0.12);
        padding: 6px;
    }
    
    /* Header */
    div[data-testid="stDataFrame"] th{
        background: rgba(15,23,42,0.85) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: none !important;
    }
    
    /* Celdas */
    div[data-testid="stDataFrame"] td{
        background: rgba(255,255,255,0.65) !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    /* Hover fila */
    div[data-testid="stDataFrame"] tr:hover td{
        background: rgba(37,99,235,0.15) !important;
        transition: background 0.15s ease;
    }


    </style>
    """, unsafe_allow_html=True)






# ---------------------------
# App init
# ---------------------------
st.set_page_config(page_title="Calculadora de calorías y macros", layout="wide")
inject_black_theme()

# ===== SIDEBAR APP STYLE =====

st.sidebar.markdown("""
<div class="sb-brand">
  <div class="sb-logo">FM</div>
  <div class="sb-title">
    <div class="sb-name">FitMacro</div>
    <div class="sb-sub">Fitness macros tracker</div>
  </div>
</div>
""", unsafe_allow_html=True)


USER_ID = st.sidebar.text_input(
    "👤 Usuario",
    value=st.session_state.get("user_id", "moi")
)

st.session_state["user_id"] = (
    USER_ID.strip() if USER_ID else "default_user"
)

selected_date = st.sidebar.date_input(
    "📅 Día",
    value=date.today()
)

selected_date_str = selected_date.isoformat()

page = st.sidebar.radio(
    "",
    ["📊 Dashboard", "🍽 Registro", "➕ Añadir alimento", "🎯 Objetivos", "🧠 Coach IA"],
    label_visibility="collapsed",
    key="nav"
)

st.sidebar.markdown("""
<div class="sb-tip">⚡ Usa el mismo usuario para mantener el histórico.</div>
""", unsafe_allow_html=True)



# Bootstrap BD (una vez)
@st.cache_resource
def _bootstrap():
    init_db()
    seed_foods_if_empty(FOODS)

_bootstrap()

st.markdown("""
<div class="hero-banner">
    <div class="hero-logo">FM</div>
    <div class="hero-text">
        <h1>FitMacro</h1>
        <p>Controla tus macros. Domina tu progreso.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="fit-fab">+</div>
""", unsafe_allow_html=True)



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

    target_kcal = float(get_setting("target_deficit_calories", 1800))
    target_p = float(get_setting("target_protein", 120))
    target_c = float(get_setting("target_carbs", 250))
    target_f = float(get_setting("target_fat", 60))

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
        styler = (
            df_view.style
            .set_table_styles([
                # Contenedor
                {"selector": "table", "props": [
                    ("border-collapse", "separate"),
                    ("border-spacing", "0"),
                    ("border-radius", "16px"),
                    ("overflow", "hidden"),
                    ("width", "100%"),
                    ("box-shadow", "0 18px 40px rgba(15,23,42,0.12)"),
                ]},
                # Header
                {"selector": "thead th", "props": [
                    ("background", "linear-gradient(135deg, rgba(22,163,74,0.85), rgba(37,99,235,0.85))"),
                    ("color", "white"),
                    ("font-weight", "800"),
                    ("border", "none"),
                    ("padding", "12px 12px"),
                ]},
                # Celdas
                {"selector": "tbody td", "props": [
                    ("background", "rgba(255,255,255,0.72)"),
                    ("color", "#0f172a"),
                    ("font-weight", "650"),
                    ("border", "none"),
                    ("padding", "12px 12px"),
                ]},
                # Hover
                {"selector": "tbody tr:hover td", "props": [
                    ("background", "rgba(37,99,235,0.14)"),
                ]},
            ])
        )
        
        st.dataframe(styler, use_container_width=True, hide_index=True)


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
    saved_sex = str(get_setting("sex", "M")).upper().strip()
    saved_age = float(get_setting("age", 25))
    saved_weight = float(get_setting("weight", 70))
    saved_height = float(get_setting("height", 175))
    saved_activity = float(get_setting("activity", 1.55))
    saved_deficit = float(get_setting("deficit_pct", 20))

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

        set_setting("sex", str(sex))
        set_setting("age", str(age))
        set_setting("weight", str(weight))
        set_setting("height", str(height))
        set_setting("activity", str(activity))
        set_setting("deficit_pct", str(deficit_pct))

        set_setting("target_maintenance", str(maintenance))
        set_setting("target_deficit_calories", str(deficit_kcal))
        set_setting("target_protein", str(protein_g))
        set_setting("target_carbs", str(carbs_g))
        set_setting("target_fat", str(fat_g))

        st.cache_data.clear()
        st.success("Perfil y objetivos guardados ✅")
        st.rerun()

    st.divider()

    target_maint = get_setting("target_maintenance")
    target_def = get_setting("target_deficit_calories")
    target_p = get_setting("target_protein")
    target_c = get_setting("target_carbs")
    target_f = get_setting("target_fat")

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
# PÁGINA: COACH IA
# ==========================================================
elif page == "🧠 Coach IA":
    import json
    from ai_groq import chat_answer, generate_menu_json

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

    st.subheader("🗨️ Chat de nutrición")
    for m in st.session_state.chat_history:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.write(m["content"])

    st.divider()

    colA, colB = st.columns([6, 1])
    with colA:
        st.text_input("Escribe tu pregunta de nutrición…", key="coach_prompt", on_change=send_coach)
    with colB:
        st.button("Enviar", type="primary", on_click=send_coach)

    st.divider()
    st.subheader("🍽️ Generador de menú (según tus alimentos)")

    cats = list_categories()
    food_map = {}
    for c in cats:
        for f in list_foods_by_category(c):
            food_map[f["name"]] = f
    allowed = list(food_map.keys())

    target_def = float(get_setting("target_deficit_calories", 2000))
    target_p = float(get_setting("target_protein", 120))
    target_c = float(get_setting("target_carbs", 250))
    target_f = float(get_setting("target_fat", 60))

    kcal_obj = st.number_input("Objetivo kcal (día)", min_value=800.0, max_value=6000.0, value=target_def, step=50.0, key="menu_kcal")
    prot_obj = st.number_input("Proteína objetivo (g)", min_value=0.0, max_value=400.0, value=target_p, step=5.0, key="menu_p")
    carb_obj = st.number_input("Carbs objetivo (g)", min_value=0.0, max_value=800.0, value=target_c, step=10.0, key="menu_c")
    fat_obj  = st.number_input("Grasas objetivo (g)", min_value=0.0, max_value=300.0, value=target_f, step=5.0, key="menu_f")

    pref = st.selectbox("Preferencia", ["Equilibrado", "Alta proteína", "Baja grasa", "Bajo carb"], key="menu_pref")

    if st.button("✨ Generar menú", type="primary"):
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






















