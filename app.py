# app.py
# app.py
import streamlit as st
st.set_page_config(page_title="Calculadora de calorías y macros", layout="wide")

st.markdown("""
<style>

/* Fondo principal */
.main {
    background-color: #0F172A;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0B1221;
}

/* Tarjetas métricas */
div[data-testid="stMetric"] {
    background-color: #1E293B;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #2D3748;
}

/* Inputs y selectores */
div.stTextInput input,
div.stNumberInput input,
div.stSelectbox div[data-baseweb="select"] {
    background-color: #1E293B !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid #2D3748 !important;
}

/* Botones principales */
div.stButton > button {
    background-color: #16A34A;
    color: white;
    border-radius: 12px;
    border: none;
    padding: 10px 18px;
    font-weight: bold;
    transition: all 0.3s ease;
}

div.stButton > button:hover {
    background-color: #22C55E;
}

/* Expander */
div[data-testid="stExpander"] {
    background-color: #1E293B;
    border-radius: 12px;
    border: 1px solid #2D3748;
}

/* Tablas */
div[data-testid="stDataFrame"] {
    background-color: #1E293B;
    border-radius: 12px;
    padding: 10px;
}

/* Barras de progreso */
div[data-testid="stProgress"] > div > div {
    background-color: #16A34A;
}

/* Títulos */
h1, h2, h3, h4 {
    color: #F1F5F9;
}

/* Texto normal */
p, label {
    color: #CBD5E1;
}

</style>
""", unsafe_allow_html=True)


import pandas as pd
from datetime import date

from db import (
    init_db, seed_foods_if_empty,
    list_categories, list_foods_by_category, add_food,
    add_entry, list_entries_by_date, daily_totals_last_days,
    set_setting, get_setting,
    list_all_foods, update_food, delete_food_by_id
)
from core import scale_macros, calculate_goals
from your_foods import FOODS  # tu lista gigante original para cargar la BD la primera vez
from db import update_entry, delete_entry_by_id


st.set_page_config(page_title="Calculadora de calorías y macros", layout="wide")

init_db()
seed_foods_if_empty(FOODS)

st.title("Calculadora de calorías y macros")

selected_date = st.sidebar.date_input("📅 Día", value=date.today())
selected_date_str = selected_date.isoformat()

page = st.sidebar.radio(
    "",
    ["📊 Dashboard", "🍽 Registro", "🎯 Objetivos", "➕ Añadir alimento", "🧠 Coach IA"],
    label_visibility="collapsed"
)

def page_dashboard(selected_date_str):
    st.title("📊 Dashboard")
    st.caption(f"Día: {selected_date_str}")
    # TODO: pega aquí tu código del Dashboard

def page_registro(selected_date_str):
    st.subheader("🍽 Registro")
    # TODO: pega aquí tu código del Registro

def page_objetivos(selected_date_str):
    st.subheader("🎯 Objetivos")
    # TODO: pega aquí tu código de Objetivos

def page_add_food(selected_date_str):
    st.subheader("➕ Añadir alimento")
    # TODO: pega aquí tu código de Añadir alimento

def page_coach(selected_date_str):
    st.subheader("🧠 Coach IA")
    # TODO: pega aquí tu código del Coach IA
PAGES = {
    "📊 Dashboard": page_dashboard,
    "🍽 Registro": page_registro,
    "🎯 Objetivos": page_objetivos,
    "➕ Añadir alimento": page_add_food,
    "🧠 Coach IA": page_coach,
}

PAGES[page](selected_date_str)

# ======================
# TAB 0: DASHBOARD
# ======================
if page == "📊 Dashboard":
   st.title("📊 Dashboard")
   st.caption(f"Día: {selected_date_str}")
   st.divider()

rows = list_entries_by_date(selected_date_str)

total_kcal = sum(r["calories"] for r in rows) if rows else 0
total_protein = sum(r["protein"] for r in rows) if rows else 0
total_carbs = sum(r["carbs"] for r in rows) if rows else 0
total_fat = sum(r["fat"] for r in rows) if rows else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🔥 Calorías", f"{total_kcal:.0f} kcal")
with col2:
    st.metric("🥩 Proteína", f"{total_protein:.1f} g")
with col3:
    st.metric("🍚 Carbs", f"{total_carbs:.1f} g")
with col4:
    st.metric("🥑 Grasas", f"{total_fat:.1f} g")

st.divider()
st.subheader("🎯 Progreso de objetivos")

target_kcal = float(get_setting("target_deficit_calories", 1800))
target_p = float(get_setting("target_protein", 120))
target_c = float(get_setting("target_carbs", 250))
target_f = float(get_setting("target_fat", 60))

def ratio(v, t):
    return 0.0 if t <= 0 else min(v / t, 1.0)

# Calorías
st.markdown(f"**🔥 Calorías:** {total_kcal:.0f} / {target_kcal:.0f}")
st.progress(ratio(total_kcal, target_kcal))
st.caption(f"{ratio(total_kcal, target_kcal)*100:.1f}% del objetivo")
st.write("")

# Proteína
st.markdown(f"**🥩 Proteína:** {total_protein:.1f} / {target_p:.1f} g")
st.progress(ratio(total_protein, target_p))
st.caption(f"{ratio(total_protein, target_p)*100:.1f}% del objetivo")
st.write("")

# Carbs
st.markdown(f"**🍚 Carbs:** {total_carbs:.1f} / {target_c:.1f} g")
st.progress(ratio(total_carbs, target_c))
st.caption(f"{ratio(total_carbs, target_c)*100:.1f}% del objetivo")
st.write("")

# Grasas
st.markdown(f"**🥑 Grasas:** {total_fat:.1f} / {target_f:.1f} g")
st.progress(ratio(total_fat, target_f))
st.caption(f"{ratio(total_fat, target_f)*100:.1f}% del objetivo")


# =========================
# TAB 1: REGISTRO
# =========================
elif page == "Registro":
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
	    meal = st.selectbox("Comida", ["Desayuno", "Almuerzo", "Merienda", "Cena"], key="meal_add")
    with col3:
        st.write("")
        st.write("")
        add_btn = st.button("Añadir al registro")

    if add_btn:
        macros = scale_macros(food, grams)
        entry = {
            "entry_date": selected_date_str,
            "meal": meal,
            "name": food["name"],
            "grams": grams,
            **macros
        }
        add_entry(entry)
        st.success("Añadido ✅")

    st.subheader("Registro")
    rows = list_entries_by_date(selected_date_str)
    df = pd.DataFrame(rows, columns=["id","meal","name","grams","calories","protein","carbs","fat"])
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)

target_def = get_setting("target_deficit_calories")
target_p = get_setting("target_protein")
target_c = get_setting("target_carbs")
target_f = get_setting("target_fat")

targets_ok = all([target_def, target_p, target_c, target_f])


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
    history = daily_totals_last_days(30)
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

    # Creamos una lista de opciones legibles
    options = []
    for _, row in df.iterrows():
        options.append({
            "id": int(row["id"]),
            "label": f"{row['meal']} — {row['name']} — {row['grams']:.0f} g"
        })

    selected_opt = st.selectbox(
        "Selecciona una entrada",
        options,
        format_func=lambda x: x["label"]
    )

    selected_id = selected_opt["id"]
    row = df[df["id"] == selected_id].iloc[0]

    colE1, colE2, colE3 = st.columns([2, 1, 1])
    with colE1:
        new_meal = st.selectbox(
    "Comida",
    ["Desayuno", "Almuerzo", "Merienda", "Cena"],
    index=["Desayuno","Almuerzo","Merienda","Cena"].index(row["meal"]),
    key=f"meal_edit_{selected_id}"
)

    with colE2:
        new_grams = st.number_input("Gramos", min_value=1.0, step=1.0, value=float(row["grams"]))
    with colE3:
        st.write("")

    # Necesitamos recalcular macros con los nuevos gramos
    # OJO: buscamos el alimento en BD (foods_in_cat solo tiene la categoría actual)
    # Solución: guardamos un diccionario rápido de alimentos por nombre:
    # (pon esto una vez cerca del inicio de tab1, después de cargar categorías)
    # food_map = {f["name"]: f for cat in categories for f in list_foods_by_category(cat)}

    if "food_map" not in st.session_state:
        # build una vez por sesión
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
        if st.button("Guardar cambios", type="primary"):
            macros = scale_macros(base_food, new_grams)
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
        confirm_del = st.checkbox("Confirmo que quiero borrar esta entrada")
        if st.button("Borrar entrada", disabled=not confirm_del):
            delete_entry_by_id(selected_id)
            st.success("Entrada borrada ✅")
            st.rerun()


# =========================
# TAB 2: OBJETIVOS
# =========================
elif page == "🎯 Objetivos":
    st.subheader("Calculadora de objetivos")

    # Cargar últimos objetivos guardados (si existen)
    saved_deficit = float(get_setting("deficit_pct", "15"))
    saved_activity = float(get_setting("activity", "1.55"))

    col1, col2 = st.columns(2)
    with col1:
        sex = st.selectbox("Sexo", ["M", "F"])
        age = st.number_input("Edad (años)", min_value=1.0, max_value=120.0, value=25.0, step=1.0)
        weight = st.number_input("Peso (kg)", min_value=1.0, max_value=400.0, value=70.0, step=0.5)
        height = st.number_input("Altura (cm)", min_value=50.0, max_value=250.0, value=175.0, step=1.0)
    with col2:
        activity_label = st.selectbox(
            "Actividad física",
            ["Sedentaria (1.2)", "Ligera (1.375)", "Moderada (1.55)", "Alta (1.725)", "Muy alta (1.9)"],
            index=2
        )
        activity = float(activity_label.split("(")[-1].strip(")"))
        deficit_pct = st.slider("% Déficit (0-30)", 0, 30, int(saved_deficit))

    if st.button("Calcular y guardar objetivos"):
        maintenance, deficit_kcal, protein_g, carbs_g, fat_g = calculate_goals(
            sex=sex, age=age, weight=weight, height=height, activity=activity, deficit_pct=deficit_pct
        )

        # Guardar en settings
        set_setting("target_calories", str(maintenance))
        set_setting("target_deficit_calories", str(deficit_kcal))
        set_setting("target_protein", str(protein_g))
        set_setting("target_carbs", str(carbs_g))
        set_setting("target_fat", str(fat_g))
        set_setting("deficit_pct", str(deficit_pct))
        set_setting("activity", str(activity))

        st.success("Objetivos guardados ✅")

    # Mostrar objetivos guardados
    target_cal = get_setting("target_calories")
    target_def = get_setting("target_deficit_calories")
    target_p = get_setting("target_protein")
    target_c = get_setting("target_carbs")
    target_f = get_setting("target_fat")

    if all([target_cal, target_def, target_p, target_c, target_f]):
        st.subheader("Tus objetivos guardados")
        a, b, c, d, e = st.columns(5)
        a.metric("⚡ Mantenimiento", f"{float(target_cal):.0f} kcal")
        b.metric("🎯 Déficit", f"{float(target_def):.0f} kcal")
        c.metric("🥩 Proteína", f"{float(target_p):.0f} g")
        d.metric("🍚 Carbs", f"{float(target_c):.0f} g")
        e.metric("🥑 Grasas", f"{float(target_f):.0f} g")
    else:
        st.info("Aún no has calculado objetivos. Rellena los datos y guarda.")

# =========================
# TAB 3: AÑADIR ALIMENTO
# =========================
elif page == "➕ Añadir alimento":
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

# =========================
# TAB 3: COACH AI
# =========================
elif page == "🧠 Coach IA":
	
    import json
    import streamlit as st
    from ai_groq import chat_answer, generate_menu_json
    from db import list_categories, list_foods_by_category, get_setting, list_entries_by_date
    from core import scale_macros

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

    prompt = st.chat_input("Pregúntame sobre nutrición…")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        answer = chat_answer(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()


st.divider()
st.subheader("🍽️ Generador de menú (según tus alimentos)")

# Construir lista de alimentos permitidos desde tu BD
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

    # Calcular macros reales con TU base
    totals = {"calories":0.0,"protein":0.0,"carbs":0.0,"fat":0.0}
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
