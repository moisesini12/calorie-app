# db_gsheets.py
from __future__ import annotations

import datetime as dt
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

SHEET_ID = st.secrets["SPREADSHEET_ID"]
TAB_FOODS = "foods"
TAB_ENTRIES = "entries"
TAB_SETTINGS = "settings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _retry_gs(fn, *args, **kwargs):
    """
    Reintentos para fallos temporales de Google Sheets:
    429 rate limit, 500/503 server errors, etc.
    """
    max_tries = 6
    for attempt in range(max_tries):
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            status = None
            try:
                status = getattr(getattr(e, "response", None), "status_code", None)
            except Exception:
                status = None

            # Reintentar solo en errores típicamente temporales
            if status in (429, 500, 503) or status is None:
                sleep = min(8.0, 0.6 * (2 ** attempt)) + random.random() * 0.25
                time.sleep(sleep)
                continue
            raise


# ---- Cache versioning helpers (evita 429 y refresca al escribir) ----
def _cache_bump(tab_name: str) -> None:
    k = f"_v_{tab_name}"
    st.session_state[k] = st.session_state.get(k, 0) + 1

def _cache_ver(tab_name: str) -> int:
    return st.session_state.get(f"_v_{tab_name}", 0)


# ---------- Helpers ----------
@st.cache_resource
def _client() -> gspread.Client:
    sa_info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_resource
def _sh():
    try:
        return _retry_gs(_client().open_by_key, SHEET_ID)
    except Exception as e:
        import streamlit as st
        import gspread

        msg = str(e)

        st.error("❌ No puedo abrir Google Sheet (gspread).")
        st.caption("Causas típicas: SHEET_ID mal / hoja no compartida con el service account / APIs o cuota.")

        # Intento sacar info útil (a veces viene dentro del texto)
        st.code(msg)

        st.info(
            "Checklist rápida:\n"
            "1) SHEET_ID correcto (entre /d/ y /edit en la URL)\n"
            "2) Hoja compartida con el service account (client_email) como Editor\n"
            "3) En Google Cloud: Sheets API y Drive API habilitadas\n"
            "4) Si es cuota/rate limit: espera 1-2 min y recarga"
        )

        st.stop()


def _ws(tab_name: str):
    # NO cachear worksheet: evita estados raros tras errores de API/cuota
    return _retry_gs(_sh().worksheet, tab_name)


def _norm_col(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("í", "i").replace("ó", "o").replace("á", "a").replace("é", "e").replace("ú", "u")
    s = s.replace(" ", "_")
    return s

def _row_to_dict(header: list, row: list) -> dict:
    h = [_norm_col(x) for x in header]
    out = {}
    for i, k in enumerate(h):
        if not k:
            continue
        out[k] = row[i] if i < len(row) else ""
    return out

def _dict_to_row(header: list, data: dict) -> list:
    h = [_norm_col(x) for x in header]
    return [data.get(k, "") for k in h]


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "":
            return default

        # Formatos típicos:
        #  - "1.234,56" -> 1234.56
        #  - "1234,56"  -> 1234.56
        #  - "1234.56"  -> 1234.56
        if "," in s and "." in s:
            # asumimos miles con '.' y decimales con ','
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            # decimales con coma
            s = s.replace(",", ".")

        return float(s)
    except Exception:
        return default


def _to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or x == "":
            return default
        return int(float(str(x).replace(",", ".")))
    except Exception:
        return default

def _norm_date(d: Any) -> str:
    if d is None:
        return ""
    s = str(d).strip()
    if not s:
        return ""

    try:
        return dt.date.fromisoformat(s).isoformat()
    except Exception:
        pass

    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass

    return s


@st.cache_data(ttl=300)
def _get_all_records_cached(tab_name: str, version: int):
    ws = _ws(tab_name)
    values = ws.get_all_values()

    if not values:
        return []

    raw_headers = values[0]
    headers = []
    seen = set()

    for i, h in enumerate(raw_headers):
        h = str(h).strip()
        if not h:
            headers.append(f"_col_{i}")
        elif h in seen:
            headers.append(f"{h}_{i}")
        else:
            headers.append(h)
            seen.add(h)

    records = []
    for row in values[1:]:
        while len(row) < len(headers):
            row.append("")
        record = {headers[i]: row[i] for i in range(len(headers))}
        records.append(record)

    return records


def _get_all_records(tab_name: str):
    return _get_all_records_cached(tab_name, _cache_ver(tab_name))


def _find_row_index_by_id(tab_name: str, id_value: int) -> Optional[int]:
    ws = _ws(tab_name)
    col = ws.col_values(1)  # columna A
    target = str(id_value)
    for i, v in enumerate(col[1:], start=2):
        if str(v).strip() == target:
            return i
    return None


# ---------- Public API ----------
def init_db() -> None:
    try:
        sh = _sh()
        existing = [ws.title for ws in sh.worksheets()]
        required = [TAB_FOODS, TAB_ENTRIES, TAB_SETTINGS]
        missing = [t for t in required if t not in existing]
        if missing:
            raise RuntimeError(f"Faltan pestañas en el Sheet: {missing}. Tengo: {existing}")
    except Exception as e:
        raise RuntimeError(
            f"No puedo abrir el Google Sheet (id={SHEET_ID}) o no encuentro pestañas "
            f"foods/entries/settings. Error real: {repr(e)}"
        ) from e


def seed_foods_if_empty(foods):
    ws = _ws(TAB_FOODS)

    if ws.acell("A2").value or ws.acell("B2").value:
        return

    rows_to_add = []
    next_id = 1
    for f in foods:
        rows_to_add.append([
            next_id,
            f["name"],
            f["category"],
            _to_float(f.get("calories", 0)),
            _to_float(f.get("protein", 0)),
            _to_float(f.get("carbs", 0)),
            _to_float(f.get("fat", 0)),
        ])
        next_id += 1

    ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
    _cache_bump(TAB_FOODS)


def list_categories() -> List[str]:
    foods = _get_all_records(TAB_FOODS)
    cats = sorted({str(f.get("category", "")).strip() for f in foods if f.get("category")})
    return cats


def list_foods_by_category(category: str) -> List[Dict[str, Any]]:
    foods = _get_all_records(TAB_FOODS)

    out = []
    for f in foods:
        if str(f.get("category", "")).strip() == category:
            out.append({
                "id": _to_int(f.get("id")),
                "name": str(f.get("name", "")).strip(),
                "category": str(f.get("category", "")).strip(),
                "calories": _to_float(f.get("calories")),
                "protein": _to_float(f.get("protein")),
                "carbs": _to_float(f.get("carbs")),
                "fat": _to_float(f.get("fat")),
            })
    return out


def list_all_foods() -> List[Dict[str, Any]]:
    foods = _get_all_records(TAB_FOODS)
    out = []
    for f in foods:
        out.append({
            "id": _to_int(f.get("id")),
            "name": str(f.get("name", "")).strip(),
            "category": str(f.get("category", "")).strip(),
            "calories": _to_float(f.get("calories")),
            "protein": _to_float(f.get("protein")),
            "carbs": _to_float(f.get("carbs")),
            "fat": _to_float(f.get("fat")),
        })
    out.sort(key=lambda x: (x["category"], x["name"]))
    return out


def add_food(food: Dict[str, Any]) -> int:
    ws = _ws(TAB_FOODS)

    # id sin lecturas: time_ns
    new_id = int(time.time_ns() // 1_000_000)

    ws.append_row([
        new_id,
        food["name"],
        food["category"],
        _to_float(food.get("calories", 0)),
        _to_float(food.get("protein", 0)),
        _to_float(food.get("carbs", 0)),
        _to_float(food.get("fat", 0)),
    ], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")

    _cache_bump(TAB_FOODS)
    return new_id


def update_food(food_id: int, updates: Dict[str, Any]) -> None:
    row_idx = _find_row_index_by_id(TAB_FOODS, food_id)
    if row_idx is None:
        raise ValueError(f"No existe food id={food_id}")

    ws = _ws(TAB_FOODS)
    current = ws.row_values(row_idx)
    while len(current) < 7:
        current.append("")

    merged = [
        str(food_id),
        str(updates.get("name")) if updates.get("name") is not None else current[1],
        str(updates.get("category")) if updates.get("category") is not None else current[2],
        str(updates.get("calories")) if updates.get("calories") is not None else current[3],
        str(updates.get("protein")) if updates.get("protein") is not None else current[4],
        str(updates.get("carbs")) if updates.get("carbs") is not None else current[5],
        str(updates.get("fat")) if updates.get("fat") is not None else current[6],
    ]

    ws.update(f"A{row_idx}:G{row_idx}", [merged], value_input_option="USER_ENTERED")
    _cache_bump(TAB_FOODS)


def delete_food_by_id(food_id: int) -> None:
    row_idx = _find_row_index_by_id(TAB_FOODS, food_id)
    if row_idx is None:
        return
    _ws(TAB_FOODS).delete_rows(row_idx)
    _cache_bump(TAB_FOODS)


def add_entry(entry: Dict[str, Any]) -> int:
    ws = _ws(TAB_ENTRIES)

    # ID único basado en timestamp (estable y sin lecturas previas)
    new_id = int(dt.datetime.utcnow().timestamp() * 1000)

    row_values = [
        new_id,
        entry.get("user_id", ""),
        entry["entry_date"],
        entry["meal"],
        entry["name"],
        _to_float(entry.get("grams", 0)),
        _to_float(entry.get("calories", 0)),
        _to_float(entry.get("protein", 0)),
        _to_float(entry.get("carbs", 0)),
        _to_float(entry.get("fat", 0)),
    ]

    # Escribir fila
    ws.append_row(
        row_values,
        value_input_option="USER_ENTERED",
        insert_data_option="INSERT_ROWS"
    )

    # Invalidar caches
    _cache_bump(TAB_ENTRIES)
    st.cache_data.clear()

    # ✅ Verificación robusta: buscar el ID en columna A
    try:
        cell = ws.find(str(new_id), in_column=1)
        if cell is None:
            raise RuntimeError(
                f"No encuentro el id={new_id} tras escribir. "
                "Probable: sheet equivocado o permisos."
            )
    except Exception as e:
        raise RuntimeError(
            f"No puedo verificar escritura en '{TAB_ENTRIES}'. Error: {repr(e)}"
        ) from e

    return new_id






def list_entries_by_date(entry_date: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = _get_all_records(TAB_ENTRIES)
    target = _norm_date(entry_date)

    out = []
    for r in rows:
        d = _norm_date(r.get("entry_date", ""))
        if d != target:
            continue

        if user_id is not None:
            if str(r.get("user_id", "")).strip() != str(user_id).strip():
                continue

        out.append({
            "id": _to_int(r.get("id")),
            "user_id": str(r.get("user_id", "")).strip(),
            "entry_date": d,
            "meal": str(r.get("meal", "")).strip(),
            "name": str(r.get("name", "")).strip(),
            "grams": _to_float(r.get("grams")),
            "calories": _to_float(r.get("calories")),
            "protein": _to_float(r.get("protein")),
            "carbs": _to_float(r.get("carbs")),
            "fat": _to_float(r.get("fat")),
        })
    return out


def update_entry(entry_id: int, **updates) -> None:
    row_idx = _find_row_index_by_id(TAB_ENTRIES, entry_id)
    if row_idx is None:
        raise ValueError(f"No existe entry id={entry_id}")

    ws = _ws(TAB_ENTRIES)
    current = ws.row_values(row_idx)
    while len(current) < 10:
        current.append("")

    def pick(col0: int, key: str):
        v = updates.get(key, None)
        return str(v) if v is not None else current[col0]

    merged = [
        str(entry_id),
        pick(1, "user_id"),
        pick(2, "entry_date"),
        pick(3, "meal"),
        pick(4, "name"),
        pick(5, "grams"),
        pick(6, "calories"),
        pick(7, "protein"),
        pick(8, "carbs"),
        pick(9, "fat"),
    ]

    ws.update(f"A{row_idx}:J{row_idx}", [merged], value_input_option="USER_ENTERED")
    _cache_bump(TAB_ENTRIES)


def delete_entry_by_id(entry_id: int) -> None:
    row_idx = _find_row_index_by_id(TAB_ENTRIES, entry_id)
    if row_idx is None:
        return
    _ws(TAB_ENTRIES).delete_rows(row_idx)
    _cache_bump(TAB_ENTRIES)


def daily_totals_last_days(days: int = 30, user_id: Optional[str] = None) -> List[Tuple[str, float, float, float, float]]:
    rows = _get_all_records(TAB_ENTRIES)
    today = dt.date.today()
    start = today - dt.timedelta(days=days - 1)

    agg: Dict[str, Dict[str, float]] = {}

    for r in rows:
        if user_id is not None:
            if str(r.get("user_id", "")).strip() != str(user_id).strip():
                continue

        d = _norm_date(r.get("entry_date", ""))
        if not d:
            continue

        try:
            dd = dt.date.fromisoformat(d)
        except Exception:
            continue

        if dd < start or dd > today:
            continue

        if d not in agg:
            agg[d] = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

        agg[d]["calories"] += _to_float(r.get("calories"))
        agg[d]["protein"] += _to_float(r.get("protein"))
        agg[d]["carbs"] += _to_float(r.get("carbs"))
        agg[d]["fat"] += _to_float(r.get("fat"))

    out = []
    for d in sorted(agg.keys()):
        a = agg[d]
        out.append((d, a["calories"], a["protein"], a["carbs"], a["fat"]))
    return out


def _scoped_setting_key(key: str, user_id: Optional[str]) -> str:
    """
    Si user_id está presente, guardamos settings por usuario:
      "user::key"
    Si no, usamos key tal cual (modo global).
    """
    uid = (str(user_id).strip() if user_id is not None else "")
    k = str(key).strip()
    return f"{uid}::{k}" if uid else k


def get_setting(
    key: str,
    default: Any = None,
    user_id: Optional[str] = None,
    fallback_global: bool = True,
) -> Any:
    """
    Lee setting por usuario si user_id != None.
    Si no existe y fallback_global=True, prueba también la key global (sin user).
    """
    rows = _get_all_records(TAB_SETTINGS)

    scoped = _scoped_setting_key(key, user_id)
    for r in rows:
        if str(r.get("key", "")).strip() == scoped:
            v = r.get("value", "")
            return v if v != "" else default

    if fallback_global and user_id is not None:
        # fallback a key global (por compatibilidad con lo ya guardado)
        for r in rows:
            if str(r.get("key", "")).strip() == str(key).strip():
                v = r.get("value", "")
                return v if v != "" else default

    return default


def set_setting(key: str, value: str, user_id: Optional[str] = None) -> None:
    """
    Escribe setting por usuario si user_id != None.
    No toca el valor global.
    """
    ws = _ws(TAB_SETTINGS)
    scoped = _scoped_setting_key(key, user_id)

    rows = ws.get_all_records()

    for i, r in enumerate(rows, start=2):
        if str(r.get("key", "")).strip() == scoped:
            ws.update(f"A{i}:B{i}", [[scoped, value]], value_input_option="USER_ENTERED")
            _cache_bump(TAB_SETTINGS)
            return

    ws.append_row([scoped, value], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")
    _cache_bump(TAB_SETTINGS)











