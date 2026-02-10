import streamlit as st
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"  # buen equilibrio calidad/velocidad (si no, usa 3.1-8b-instant)

def get_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY en Streamlit Secrets.")
    return Groq(api_key=api_key)

def chat_answer(messages, model: str = DEFAULT_MODEL, temperature: float = 0.4) -> str:
    """
    messages: lista [{"role":"system|user|assistant","content":"..."}]
    """
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content

def generate_menu_json(context_text: str, allowed_food_names: list[str], model: str = DEFAULT_MODEL) -> str:
    """
    Devuelve JSON como texto (lo parseamos luego).
    """
    system = (
        "Eres un coach nutricional. Responde SIEMPRE en JSON válido, sin texto extra. "
        "Solo puedes usar alimentos que estén en la lista allowed_foods."
    )

    user = f"""
Contexto:
{context_text}

allowed_foods = {allowed_food_names}

Devuelve un JSON con este esquema exacto:
{{
  "meals": [
    {{"meal":"Desayuno","items":[{{"name":"...","grams":123}}, ...]}},
    {{"meal":"Almuerzo","items":[...]}},
    {{"meal":"Merienda","items":[...]}},
    {{"meal":"Cena","items":[...]}}
  ]
}}

Reglas:
- Usa solo nombres EXACTOS de allowed_foods.
- grams debe ser número (sin unidades).
- No inventes macros. Solo elige alimentos y cantidades.
"""
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},  # JSON mode (Groq lo soporta en varios modelos)
    )
    return resp.choices[0].message.content
