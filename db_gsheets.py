# db_gsheets.py
from __future__ import annotations

import datetime as dt
import time
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


SHEET_ID = st.secrets["SPREADSHEET_ID"]
TAB_FOODS = "foods"
TAB_ENTRIES = "entries"
TAB_SETTINGS = "settings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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
    return _client().open_by_key(SHEET_ID)

@st.cache_resource
def _ws(tab_name: str):
    return _sh().worksheet(tab_name)


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        s = str(x).strip()

        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            if s.count(".") >= 1 and s.replace(".", "").isdigit():
                s = s.replace(".", "")

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

    # ✅ ID sin leer la hoja (evita 429). Milisegundos UTC -> int grande único.
    new_id = int(dt.datetime.utcnow().timestamp() * 1000)

    ws.append_row([
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
    ], value_input_option="USER_ENTERED")

    _cache_bump(TAB_ENTRIES)
    st.cache_data.clear()

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


def get_setting(key: str, default: Any = None) -> Any:
    rows = _get_all_records(TAB_SETTINGS)
    for r in rows:
        if str(r.get("key", "")).strip() == key:
            v = r.get("value", "")
            return v if v != "" else default
    return default


def set_setting(key: str, value: str) -> None:
    ws = _ws(TAB_SETTINGS)
    rows = ws.get_all_records()

    for i, r in enumerate(rows, start=2):
        if str(r.get("key", "")).strip() == key:
            ws.update(f"A{i}:B{i}", [[key, value]], value_input_option="USER_ENTERED")
            _cache_bump(TAB_SETTINGS)
            return

    ws.append_row([key, value], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")
    _cache_bump(TAB_SETTINGS)

