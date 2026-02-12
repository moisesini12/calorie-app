# app.py
# app.py
import streamlit as st
import pandas as pd
USER_ID = "default_user"


def inject_black_theme():
    st.markdown("""
    <style>

    /* ===== FITNESS PRO MINIMAL (BLACK) ===== */
    :root{
      --bg: #000000;
      --panel: rgba(255,255,255,0.04);
      --panel-2: rgba(255,255,255,0.06);
      --stroke: rgba(255,255,255,0.08);
      --stroke-2: rgba(255,255,255,0.12);
      --txt: rgba(255,255,255,0.92);
      --muted: rgba(255,255,255,0.60);
      --muted2: rgba(255,255,255,0.40);
      --accent: #39ff14; /* verde gym: cambia si quieres */
      --radius: 18px;
    }
    
    /* Fondo total negro */
    html, body, [data-testid="stAppViewContainer"]{
      background: var(--bg) !important;
      color: var(--txt) !important;
    }
    
    /* Contenedor principal: menos ancho para “app” y no web random */
    .block-container{
      max-width: 1100px;
      padding-top: 28px;
      padding-bottom: 60px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"]{
      background: var(--bg) !important;
      border-right: 1px solid var(--stroke) !important;
    }
    
    /* Tipografía: más pro */
    h1{
      font-size: 44px !important;
      letter-spacing: -0.03em;
    }
    h2, h3{
      letter-spacing: -0.02em;
    }
    p, label, .stCaption, .stMarkdown{
      color: var(--muted) !important;
    }
    
    /* “Tarjetas” estilo glass */
    div[data-testid="stMetric"]{
      background: var(--panel) !important;
      border: 1px solid var(--stroke) !important;
      border-radius: var(--radius) !important;
      padding: 18px 18px !important;
      box-shadow: 0 8px 30px rgba(0,0,0,0.35);
      backdrop-filter: blur(10px);
    }
    
    /* Metric label y value más limpios */
    div[data-testid="stMetric"] label{
      color: var(--muted) !important;
      font-size: 13px !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"]{
      font-size: 34px !important;
      font-weight: 700 !important;
      color: var(--txt) !important;
    }
    
    /* Botones: “pill” pro + borde sutil */
    .stButton > button{
      background: var(--panel) !important;
      border: 1px solid var(--stroke-2) !important;
      border-radius: 999px !important;
      color: var(--txt) !important;
      padding: 10px 16px !important;
      transition: all .15s ease;
    }
    .stButton > button:hover{
      transform: translateY(-1px);
      border-color: rgba(57,255,20,0.35) !important;
      box-shadow: 0 8px 26px rgba(57,255,20,0.08);
    }
    .stButton > button:active{
      transform: translateY(0px);
    }
    
    /* Inputs y select: panel oscuro */
    input, textarea{
      background: var(--panel) !important;
      border: 1px solid var(--stroke) !important;
      border-radius: 14px !important;
      color: var(--txt) !important;
    }
    div[data-baseweb="select"] > div{
      background: var(--panel) !important;
      border: 1px solid var(--stroke) !important;
      border-radius: 14px !important;
    }
    
    /* Divider / HR */
    hr{
      border: none !important;
      height: 1px !important;
      background: var(--stroke) !important;
    }
    
    /* Dataframe “card” */
    div[data-testid="stDataFrame"]{
      background: var(--panel) !important;
      border: 1px solid var(--stroke) !important;
      border-radius: var(--radius) !important;
      overflow: hidden;
    }
    
    /* Tabs más pro */
    div[role="tablist"] button{
      background: var(--panel) !important;
      border: 1px solid var(--stroke) !important;
      color: var(--muted) !important;
      border-radius: 999px !important;
      padding: 8px 14px !important;
    }
    div[role="tablist"] button[aria-selected="true"]{
      color: var(--txt) !important;
      border-color: rgba(57,255,20,0.35) !important;
    }
    
    /* Progress bar (verde accent) */
    div[data-testid="stProgress"] > div > div{
      background-color: var(--accent) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar{ width: 8px; }
    ::-webkit-scrollbar-track{ background: var(--bg); }
    ::-webkit-scrollbar-thumb{
      background: rgba(255,255,255,0.12);
      border-radius: 999px;
    }

    /* TARJETAS METRIC ESTILO FITNESS PRO */
    div[data-testid="stMetric"] {
        background: #0b0b0b !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 0 0 1px #111 inset;
    }


    
    </style>
    """, unsafe_allow_html=True)

inject_black_theme()



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
from your_foods import FOODS  # tu lista gigante original para cargar la BD la primera vez


st.set_page_config(page_title="Calculadora de calorías y macros", layout="wide")

USER_ID = st.sidebar.text_input("👤 Usuario", value=st.session_state.get("user_id", "moi"))
st.session_state["user_id"] = USER_ID


@st.cache_resource
def _bootstrap():
    init_db()
    seed_foods_if_empty(FOODS)

_bootstrap()


st.title("Calculadora de calorías y macros")

selected_date = st.sidebar.date_input("📅 Día", value=date.today())
selected_date_str = selected_date.isoformat()

page = st.sidebar.radio(
    "",
    ["📊 Dashboard", "🍽 Registro", "🎯 Objetivos", "➕ Añadir alimento", "🧠 Coach IA"],
    label_visibility="collapsed"
)


# ======================
# TAB 0: DASHBOARD
# ======================
if page == "📊 Dashboard":

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
                if remaining >= 0:
                    st.metric("Restante", f"{remaining:.0f}{unit}")
                else:
                    st.metric("Exceso", f"{abs(remaining):.0f}{unit}")
    
    progress_row("🔥 Calorías", total_kcal, target_kcal, " kcal")
    progress_row("🥩 Proteína", total_protein, target_p, " g")
    progress_row("🍚 Carbs", total_carbs, target_c, " g")
    progress_row("🥑 Grasas", total_fat, target_f, " g")



# =========================
# TAB 1: REGISTRO
# =========================
elif page == "🍽 Registro":
    # --- TODO: aquí va TODO lo del registro (incluye df, totales, editar/borrar...) ---
    categories = list_categories()
    if not categories:
        st.error("No hay categorías. Revisa la tabla foods.")
        st.stop()

    colA, colB = st.columns([2, 2])
    with colA:
        category = st.selectbox("Categoría", categories)
    with colB:
        foods_in_cat = list_foods_by_category(category)
        food = st.selectbox("Alimento", foods_in_cat, format_func=lambda x: x["name"])

    col1, col2, col3 = st.columns(3)
    with col1:
        grams = st.number_input("Gramos consumidos", min_value=1.0, step=1.0, value=100.0)
    with col2:
        meal = st.radio(
            "Comida",
            ["Desayuno", "Almuerzo", "Merienda", "Cena"],
            horizontal=True,
            key="meal_add"
)

    with col3:
        st.write("")
        st.write("")
        add_btn = st.button("Añadir al registro")

    if add_btn:
        macros = scale_macros(food, grams)
        entry = {
            "user_id": USER_ID,   # 👈 NUEVO
            "entry_date": selected_date_str,
            "meal": meal,
            "name": food["name"],
            "grams": float(grams),
            **macros
}
        add_entry(entry)
        st.success("Añadido ✅")
        st.rerun()




    st.subheader("Registro")
    rows = list_entries_by_date(selected_date_str, USER_ID)



    df = pd.DataFrame(rows, columns=["id","meal","name","grams","calories","protein","carbs","fat"])

    df_view = df.drop(columns=["id"]).rename(columns={
        "meal": "Comida",
        "name": "Alimento",
        "grams": "Gramos",
        "calories": "Calorías",
        "protein": "Proteínas",
        "carbs": "Carbohidratos",
        "fat": "Grasas"
})
 

    st.dataframe(df_view, use_container_width=True)

    target_def = get_setting("target_deficit_calories")
    target_p = get_setting("target_protein")
    target_c = get_setting("target_carbs")
    target_f = get_setting("target_fat")

    targets_ok = all(x not in (None, "") for x in [target_def, target_p, target_c, target_f])


    if not df.empty:
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

# --- Objetivos vs Consumo ---
    if not df.empty:
        st.subheader("🎯 Objetivos vs Consumo")

    if not targets_ok:
        st.info("Calcula y guarda objetivos en la pestaña 🧮 Objetivos para ver esta comparación.")
    else:
        consumed = {
            "Calorías": float(df["calories"].sum()),
            "Proteína": float(df["protein"].sum()),
            "Carbohidratos": float(df["carbs"].sum()),
            "Grasas": float(df["fat"].sum()),
        }
        targets = {
            "Calorías": float(target_def),   # usamos déficit como objetivo diario
            "Proteína": float(target_p),
            "Carbohidratos": float(target_c),
            "Grasas": float(target_f),
        }

        comp_df = pd.DataFrame({
            "Consumido": consumed,
            "Objetivo": targets
        })

        st.bar_chart(comp_df)

        st.subheader("📏 Progreso del día")

        def progress(label, value, goal, unit=""):
            ratio = 0 if goal <= 0 else min(value / goal, 1.0)
            st.write(f"**{label}:** {value:.1f}{unit} / {goal:.1f}{unit}")
            st.progress(ratio)

        progress("🔥 Calorías (déficit)", consumed["Calorías"], targets["Calorías"], " kcal")
        progress("🥩 Proteína", consumed["Proteína"], targets["Proteína"], " g")
        progress("🍚 Carbohidratos", consumed["Carbohidratos"], targets["Carbohidratos"], " g")
        progress("🥑 Grasas", consumed["Grasas"], targets["Grasas"], " g")



    st.subheader("📊 Tendencia (últimos 30 días)")
    history = daily_totals_last_days(30, USER_ID)
    hist_df = pd.DataFrame(history, columns=["date","calories","protein","carbs","fat"])
    if not hist_df.empty:
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        hist_df = hist_df.sort_values("date").set_index("date")
        st.line_chart(hist_df[["calories"]])
    else:
        st.info("Aún no hay datos suficientes para la tendencia.")
# --- Gestión de entradas del día ---
    if not df.empty:
        st.subheader("✏️ Editar / 🗑️ Borrar entrada")
    if df.empty:
        st.info("No hay entradas hoy para editar o borrar.")
        st.stop()

# Creamos opciones seguras (dict con id + label)
    options = []
    for _, r in df.iterrows():
        options.append({
            "id": int(r["id"]),
            "label": f"{r['meal']} — {r['name']} — {float(r['grams']):.0f} g"
    })

    if not options:
        st.info("No hay entradas hoy para editar o borrar.")
        st.stop()

    selected_opt = st.selectbox(
        "Selecciona una entrada",
        options,
        format_func=lambda x: x["label"],
        key="entry_select_edit"
)

# Si por cualquier motivo no hay selección aún
    if not selected_opt or "id" not in selected_opt:
        st.info("Selecciona una entrada para continuar.")
        st.stop()

    selected_id = selected_opt["id"]
    row = df[df["id"] == selected_id].iloc[0]

# ---- Editor ----
    colE1, colE2, colE3 = st.columns([2, 1, 1])

    with colE1:
        meals = ["Desayuno", "Almuerzo", "Merienda", "Cena"]
        current_meal = row["meal"] if row["meal"] in meals else meals[0]
        new_meal = st.selectbox(
            "Comida",
            meals,
            index=meals.index(current_meal),
            key=f"meal_edit_{selected_id}"
    )

    with colE2:
        new_grams = st.number_input(
            "Gramos",
            min_value=1.0,
            step=1.0,
            value=float(row["grams"]),
            key=f"grams_edit_{selected_id}"
    )

    with colE3:
        st.write("")
        st.write("")

# Construir food_map una vez (para recalcular macros)
    if "food_map" not in st.session_state:
        cats = list_categories()
        m = {}
        for c in cats:
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
            st.success("Entrada actualizada ✅")
            st.rerun()

        st.warning("⚠️ Borrar elimina la entrada del día (no se puede deshacer).")
        confirm_del = st.checkbox("Confirmo que quiero borrar esta entrada", key=f"confirm_del_{selected_id}")

        if st.button("Borrar entrada", disabled=not confirm_del, key=f"del_entry_{selected_id}"):
            delete_entry_by_id(selected_id)
            st.success("Entrada borrada ✅")
            st.rerun()


# =========================
# TAB 2: OBJETIVOS
# =========================
elif page == "🎯 Objetivos":

    # 1) Defaults desde settings
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

        age = st.number_input(
            "Edad (años)", min_value=1.0, max_value=120.0,
            value=float(saved_age), step=1.0
        )

        weight = st.number_input(
            "Peso (kg)", min_value=1.0, max_value=400.0,
            value=float(saved_weight), step=0.5
        )

        height = st.number_input(
            "Altura (cm)", min_value=50.0, max_value=250.0,
            value=float(saved_height), step=1.0
        )

    with col2:
        activity_options = [
            "Sedentaria (1.2)",
            "Ligera (1.375)",
            "Moderada (1.55)",
            "Alta (1.725)",
            "Muy alta (1.9)",
        ]
        activity_values = [1.2, 1.375, 1.55, 1.725, 1.9]

        # Elegir índice según saved_activity (si no coincide exacto, cae en 1.55)
        try:
            activity_index = activity_values.index(saved_activity)
        except ValueError:
            activity_index = activity_values.index(1.55)

        activity_label = st.selectbox(
            "Actividad física",
            activity_options,
            index=activity_index
        )
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

        # 2) Guardar PERFIL
        set_setting("sex", str(sex))
        set_setting("age", str(age))
        set_setting("weight", str(weight))
        set_setting("height", str(height))
        set_setting("activity", str(activity))
        set_setting("deficit_pct", str(deficit_pct))

        # 3) Guardar OBJETIVOS (usa estas mismas keys en toda la app)
        set_setting("target_maintenance", str(maintenance))
        set_setting("target_deficit_calories", str(deficit_kcal))
        set_setting("target_protein", str(protein_g))
        set_setting("target_carbs", str(carbs_g))
        set_setting("target_fat", str(fat_g))

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


# =========================
# TAB 2: OBJETIVOS
# =========================
elif page == "➕ Añadir alimento":
    # --- TODO: aquí va gestión de alimentos ---
    st.subheader("Gestión de alimentos")

    st.caption("Aquí puedes añadir alimentos nuevos, editar los existentes o borrarlos de la base de datos.")

    mode = st.radio("Modo", ["➕ Añadir", "✏️ Editar", "🗑️ Borrar"], horizontal=True)

    all_foods = list_all_foods()

    # =========================
    # ➕ AÑADIR
    # =========================
    if mode == "➕ Añadir":
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre del alimento")
            category = st.text_input("Categoría", value="Carbohidratos")
        with col2:
            calories = st.number_input("Kcal por 100g", min_value=0.0, value=100.0, step=1.0)
            protein = st.number_input("Proteína por 100g", min_value=0.0, value=0.0, step=0.1)
            carbs = st.number_input("Carbs por 100g", min_value=0.0, value=0.0, step=0.1)
            fat = st.number_input("Grasas por 100g", min_value=0.0, value=0.0, step=0.1)

        if st.button("Guardar alimento", type="primary"):
            clean_name = name.strip()
            clean_cat = category.strip()
            if not clean_name:
                st.error("Falta el nombre del alimento.")
            elif not clean_cat:
                st.error("Falta la categoría.")
            else:
                add_food({
                    "name": clean_name,
                    "category": clean_cat,
                    "calories": float(calories),
                    "protein": float(protein),
                    "carbs": float(carbs),
                    "fat": float(fat),
                })
                st.success("Alimento guardado ✅")
                st.rerun()

    # =========================
    # ✏️ EDITAR
    # =========================
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
                    st.success("Cambios guardados ✅")
                    st.rerun()

    # =========================
    # 🗑️ BORRAR
    # =========================
    else:
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
                st.success("Alimento borrado ✅")
                st.rerun()
    st.subheader("➕ Añadir alimento")

# =========================
# TAB 3: COACH AI
# =========================
elif page == "🧠 Coach IA":
    import json
    from ai_groq import chat_answer, generate_menu_json
    from db_gsheets import list_categories, list_foods_by_category, get_setting, list_entries_by_date
    from core import scale_macros

    def send_coach():
        prompt = st.session_state.get("coach_prompt", "").strip()
        if not prompt:
            return

        st.session_state.chat_history.append({"role": "user", "content": prompt})
        answer = chat_answer(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        # limpiar input (esto es válido porque ocurre dentro del callback)
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
        st.text_input(
            "Escribe tu pregunta de nutrición…",
            key="coach_prompt",
            on_change=send_coach
    )

    with colB:
        st.button("Enviar", type="primary", on_click=send_coach)





    # ✅ TODO lo de menú VA DENTRO de Coach IA
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
        st.session_state["last_menu"] = menu

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







































































