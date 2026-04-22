from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import streamlit as st
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from utils.db import get_engine, get_database_schema, log_database_event, qualify_table_name, test_database_connection
from utils.theme import apply_brand_theme, render_sidebar_brand

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SOURCE_PATH = DATA_DIR / "base.xlsx"
SOURCE_SHEET = "ANUAL"
SALES_TABLE = "sales"
METADATA_TABLE = "metadata"
SHEET_REGISTRY_TABLE = "sheet_registry"
LAST_UPDATED_AT_KEY = "last_updated_at"
SOURCE_PATTERNS = ("*.xlsx", "*.xlsm", "*.xls")
REQUIRED_COLUMNS = [
    "Data",
    "CodProduto",
    "Produto",
    "QuantidadeTotal",
    "ValorTotal",
    "PesoUnitario",
    "PesoTotal",
    "TIPO",
]


def ensure_data_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_metadata_tables(connection: Connection) -> None:
    connection.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {qualify_table_name(METADATA_TABLE)} (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {qualify_table_name(SHEET_REGISTRY_TABLE)} (
                sheet_name TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                row_count INTEGER NOT NULL
            )
            """
        )
    )


def bootstrap_source_file() -> Path:
    ensure_data_directory()
    if SOURCE_PATH.exists():
        return SOURCE_PATH

    candidates: list[Path] = []
    for pattern in SOURCE_PATTERNS:
        candidates.extend(sorted(DATA_DIR.glob(pattern)))
        candidates.extend(sorted(ROOT_DIR.glob(pattern)))

    for candidate in candidates:
        if candidate == SOURCE_PATH:
            continue
        materialize_workbook_copy(candidate)
        return SOURCE_PATH

    raise FileNotFoundError("Nenhuma planilha foi encontrada em data/ ou na raiz do projeto.")


def materialize_workbook_copy(source) -> Path:
    ensure_data_directory()
    workbook = pd.ExcelFile(source)
    with pd.ExcelWriter(SOURCE_PATH, engine="openpyxl") as writer:
        for sheet_name in workbook.sheet_names:
            workbook.parse(sheet_name=sheet_name).to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )
    return SOURCE_PATH


def parse_numeric_series(series: pd.Series, currency: bool = False) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    text = series.astype(str).str.strip()
    if currency:
        text = text.str.replace("R$", "", regex=False)
    text = text.str.replace(" ", "", regex=False)
    text = text.str.replace(".", "", regex=False)
    text = text.str.replace(",", ".", regex=False)
    converted = pd.to_numeric(text, errors="coerce")
    return numeric.fillna(converted).fillna(0.0)


def normalize_sales_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()
    df.columns = [str(column).strip() for column in df.columns]

    if "TIPO" not in df.columns and "Unnamed: 7" in df.columns:
        df = df.rename(columns={"Unnamed: 7": "TIPO"})

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "A planilha nao contem as colunas esperadas: " + ", ".join(missing_columns)
        )

    df = df[REQUIRED_COLUMNS].copy()
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Data"])
    df["QuantidadeTotal"] = parse_numeric_series(df["QuantidadeTotal"])
    df["ValorTotal"] = parse_numeric_series(df["ValorTotal"], currency=True)
    df["PesoUnitario"] = parse_numeric_series(df["PesoUnitario"])
    df["PesoTotal"] = parse_numeric_series(df["PesoTotal"])
    df["CodProduto"] = pd.to_numeric(df["CodProduto"], errors="coerce").fillna(0).astype(int)
    df["Produto"] = df["Produto"].astype(str).str.strip()
    df["TIPO"] = df["TIPO"].fillna("NAO INFORMADO").astype(str).str.strip()
    return df


def normalize_generic_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()
    df.columns = [str(column).strip() for column in df.columns]
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def sanitize_table_name(sheet_name: str, used_names: set[str]) -> str:
    base_name = re.sub(r"[^a-z0-9]+", "_", sheet_name.lower()).strip("_") or "sheet"
    table_name = f"sheet_{base_name}"
    suffix = 1
    while table_name in used_names:
        suffix += 1
        table_name = f"sheet_{base_name}_{suffix}"
    used_names.add(table_name)
    return table_name


def replace_database_contents(source_file: Path, source_name: str, source_token: str) -> None:
    log_database_event(f"replace_database_contents started for {source_name}")
    workbook = pd.ExcelFile(source_file)
    if SOURCE_SHEET not in workbook.sheet_names:
        raise ValueError(f"A planilha enviada precisa conter a aba {SOURCE_SHEET}.")

    updated_at = datetime.now().isoformat(timespec="seconds")

    engine = get_engine()
    schema = get_database_schema()

    with engine.begin() as connection:
        log_database_event("ensuring metadata tables")
        create_metadata_tables(connection)
        existing_tables = inspect(connection).get_table_names(schema=schema)
        preserved_tables = {METADATA_TABLE, SHEET_REGISTRY_TABLE}
        for table_name in existing_tables:
            if table_name not in preserved_tables:
                connection.execute(text(f"DROP TABLE IF EXISTS {qualify_table_name(table_name, schema)}"))

        connection.execute(text(f"DELETE FROM {qualify_table_name(SHEET_REGISTRY_TABLE, schema)}"))

        used_names = {METADATA_TABLE, SHEET_REGISTRY_TABLE, SALES_TABLE}
        for sheet_name in workbook.sheet_names:
            log_database_event(f"loading sheet {sheet_name}")
            sheet_df = workbook.parse(sheet_name=sheet_name)
            if sheet_name == SOURCE_SHEET:
                normalized_df = normalize_sales_dataframe(sheet_df)
                normalized_df.to_sql(
                    SALES_TABLE,
                    connection,
                    schema=schema,
                    if_exists="replace",
                    index=False,
                    method="multi",
                    chunksize=1000,
                )
                connection.execute(
                    text(
                        f"""
                        INSERT INTO {qualify_table_name(SHEET_REGISTRY_TABLE, schema)}(sheet_name, table_name, row_count)
                        VALUES(:sheet_name, :table_name, :row_count)
                        ON CONFLICT (sheet_name) DO UPDATE
                        SET table_name = EXCLUDED.table_name,
                            row_count = EXCLUDED.row_count
                        """
                    ),
                    {"sheet_name": sheet_name, "table_name": SALES_TABLE, "row_count": len(normalized_df)},
                )
                continue

            normalized_df = normalize_generic_dataframe(sheet_df)
            table_name = sanitize_table_name(sheet_name, used_names)
            normalized_df.to_sql(
                table_name,
                connection,
                schema=schema,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=1000,
            )
            connection.execute(
                text(
                    f"""
                    INSERT INTO {qualify_table_name(SHEET_REGISTRY_TABLE, schema)}(sheet_name, table_name, row_count)
                    VALUES(:sheet_name, :table_name, :row_count)
                    ON CONFLICT (sheet_name) DO UPDATE
                    SET table_name = EXCLUDED.table_name,
                        row_count = EXCLUDED.row_count
                    """
                ),
                {"sheet_name": sheet_name, "table_name": table_name, "row_count": len(normalized_df)},
            )

        connection.execute(
            text(
                f"""
                INSERT INTO {qualify_table_name(METADATA_TABLE, schema)}(key, value)
                VALUES(:key, :value)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """
            ),
            {"key": "source_token", "value": source_token},
        )
        connection.execute(
            text(
                f"""
                INSERT INTO {qualify_table_name(METADATA_TABLE, schema)}(key, value)
                VALUES(:key, :value)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """
            ),
            {"key": "source_name", "value": source_name},
        )
        connection.execute(
            text(
                f"""
                INSERT INTO {qualify_table_name(METADATA_TABLE, schema)}(key, value)
                VALUES(:key, :value)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """
            ),
            {"key": LAST_UPDATED_AT_KEY, "value": updated_at},
        )
    log_database_event("replace_database_contents finished")


def save_uploaded_source(uploaded_file) -> Path:
    file_bytes = BytesIO(uploaded_file.getvalue())
    materialize_workbook_copy(file_bytes)
    return SOURCE_PATH


def clear_data_caches() -> None:
    load_sales_data.clear()
    load_sheet_registry.clear()
    load_sheet_preview.clear()
    st.session_state.pop(DB_INIT_STATE_KEY, None)
    st.session_state.pop(DB_INIT_SOURCE_NAME_KEY, None)
    st.session_state.pop(DB_INIT_ERROR_KEY, None)
    st.session_state.pop(DB_INIT_LOGS_KEY, None)


def ensure_last_updated_metadata(connection: Connection, fallback_updated_at: str | None = None) -> None:
    schema = get_database_schema()
    stored_updated_at = connection.execute(
        text(
            f"SELECT value FROM {qualify_table_name(METADATA_TABLE, schema)} WHERE key = :key"
        ),
        {"key": LAST_UPDATED_AT_KEY},
    ).fetchone()
    if stored_updated_at is not None:
        return

    effective_updated_at = fallback_updated_at or datetime.now().isoformat(timespec="seconds")
    connection.execute(
        text(
            f"""
            INSERT INTO {qualify_table_name(METADATA_TABLE, schema)}(key, value)
            VALUES(:key, :value)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """
        ),
        {"key": LAST_UPDATED_AT_KEY, "value": effective_updated_at},
    )


def hide_default_sidebar_navigation() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_navigation() -> None:
    st.sidebar.title("Navegacao")
    st.sidebar.page_link("app.py", label="Inicio", icon="🏠")
    st.sidebar.page_link("pages/1_Geral.py", label="Geral", icon="📊")
    st.sidebar.page_link("pages/2_Logistica.py", label="Logistica", icon="🚚")
    st.sidebar.page_link("pages/3_Produtos.py", label="Produtos", icon="📦")
    st.sidebar.page_link("pages/4_Inteligencia.py", label="Inteligencia", icon="🧠")
    st.sidebar.page_link("pages/5_Comparativo.py", label="Comparativo", icon="📈")
    st.sidebar.divider()


def handle_workbook_upload() -> None:
    st.sidebar.subheader("Atualizar planilha")
    uploaded_file = st.sidebar.file_uploader(
        "Envie a planilha completa",
        type=["xlsx", "xlsm", "xls"],
        key="global_workbook_upload",
        help="Ao confirmar o upload, todo o conteudo do banco sera substituido.",
    )

    if st.sidebar.button(
        "Substituir conteudo do banco",
        key="global_replace_button",
        use_container_width=True,
    ):
        if uploaded_file is None:
            st.sidebar.error("Selecione uma planilha antes de atualizar.")
            return

        try:
            saved_file = save_uploaded_source(uploaded_file)
            replace_database_contents(
                saved_file,
                uploaded_file.name,
                str(saved_file.stat().st_mtime_ns),
            )
            clear_data_caches()
            st.session_state["upload_status"] = f"Base substituida com {uploaded_file.name}."
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Falha ao importar a planilha: {exc}")

    status_message = st.session_state.pop("upload_status", None)
    if status_message:
        st.sidebar.success(status_message)


def initialize_database() -> str:
    init_state = st.session_state.get(DB_INIT_STATE_KEY)
    if init_state == "ready":
        return st.session_state.get(DB_INIT_SOURCE_NAME_KEY, "Banco remoto")
    if init_state == "running":
        raise RuntimeError("Inicializacao do banco ja esta em andamento. Aguarde alguns segundos.")

    source_file = None

    try:
        st.session_state[DB_INIT_STATE_KEY] = "running"
        st.session_state.pop(DB_INIT_ERROR_KEY, None)
        emit_init_log("initialize_database started")
        engine = get_engine()
        schema = get_database_schema()
        test_database_connection(engine=engine, attempts=2, delay_seconds=1.0)

        with engine.begin() as connection:
            emit_init_log("creating metadata tables")
            create_metadata_tables(connection)

        with engine.connect() as connection:
            emit_init_log("checking sales table existence")
            sales_table_exists = inspect(connection).has_table(SALES_TABLE, schema=schema)

        if not sales_table_exists:
            emit_init_log("sales table missing, bootstrapping workbook import")
            source_file = bootstrap_source_file()
            source_token = str(source_file.stat().st_mtime_ns)
            replace_database_contents(source_file, source_file.name, source_token)
            fallback_updated_at = datetime.fromtimestamp(source_file.stat().st_mtime).isoformat(
                timespec="seconds"
            )
        else:
            emit_init_log("sales table already exists")
            fallback_updated_at = None

        with engine.begin() as connection:
            emit_init_log("ensuring last updated metadata")
            ensure_last_updated_metadata(connection, fallback_updated_at)
            stored_name = connection.execute(
                text(f"SELECT value FROM {qualify_table_name(METADATA_TABLE, schema)} WHERE key = :key"),
                {"key": "source_name"},
            ).fetchone()

        emit_init_log("initialize_database finished")
        source_name = "Banco remoto"
        if stored_name:
            source_name = stored_name[0]
        elif source_file is not None:
            source_name = source_file.name

        st.session_state[DB_INIT_STATE_KEY] = "ready"
        st.session_state[DB_INIT_SOURCE_NAME_KEY] = source_name
        return source_name
    except Exception as exc:
        emit_init_log(f"initialize_database failed: {exc}")
        st.session_state[DB_INIT_STATE_KEY] = "failed"
        st.session_state[DB_INIT_ERROR_KEY] = str(exc)
        raise RuntimeError(f"Falha ao inicializar o banco de dados: {exc}") from exc


@st.cache_data
def load_sales_data() -> pd.DataFrame:
    initialize_database()
    engine = get_engine()
    schema = get_database_schema()
    with engine.connect() as connection:
        df = pd.read_sql_query(text(f"SELECT * FROM {qualify_table_name(SALES_TABLE, schema)}"), connection)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.normalize()
    return df


@st.cache_data
def load_sheet_registry() -> pd.DataFrame:
    initialize_database()
    engine = get_engine()
    schema = get_database_schema()
    with engine.connect() as connection:
        return pd.read_sql_query(
            text(
                f"SELECT sheet_name, table_name, row_count FROM {qualify_table_name(SHEET_REGISTRY_TABLE, schema)} ORDER BY sheet_name"
            ),
            connection,
        )


@st.cache_data
def load_sheet_preview(sheet_name: str, limit: int = 200) -> pd.DataFrame:
    registry = load_sheet_registry()
    selected_sheet = registry.loc[registry["sheet_name"] == sheet_name]
    if selected_sheet.empty:
        return pd.DataFrame()

    table_name = selected_sheet.iloc[0]["table_name"]
    engine = get_engine()
    schema = get_database_schema()
    with engine.connect() as connection:
        return pd.read_sql_query(
            text(f"SELECT * FROM {qualify_table_name(table_name, schema)} LIMIT :limit"),
            connection,
            params={"limit": int(limit)},
        )


def get_last_updated_at() -> str | None:
    initialize_database()
    engine = get_engine()
    schema = get_database_schema()
    with engine.connect() as connection:
        row = connection.execute(
            text(f"SELECT value FROM {qualify_table_name(METADATA_TABLE, schema)} WHERE key = :key"),
            {"key": LAST_UPDATED_AT_KEY},
        ).fetchone()
    return row[0] if row else None


FILTERS_STATE_KEY = "filtros"
PERIOD_INPUT_KEY = "filtros.periodo.input"
TYPE_WIDGET_KEY = "filtros.tipos"
PRODUCT_WIDGET_KEY = "filtros.produtos"
DB_INIT_STATE_KEY = "database.initialization.state"
DB_INIT_SOURCE_NAME_KEY = "database.initialization.source_name"
DB_INIT_ERROR_KEY = "database.initialization.error"
DB_INIT_LOGS_KEY = "database.initialization.logs"


def emit_init_log(message: str) -> None:
    log_database_event(message)
    logs = st.session_state.setdefault(DB_INIT_LOGS_KEY, [])
    logs.append(message)
    if len(logs) > 50:
        del logs[:-50]


def get_initialization_logs() -> list[str]:
    return list(st.session_state.get(DB_INIT_LOGS_KEY, []))


def init_session_state() -> None:
    if FILTERS_STATE_KEY not in st.session_state:
        st.session_state[FILTERS_STATE_KEY] = {
            "periodo": None,
            "tipos": [],
            "produtos": [],
        }


def get_default_period(df: pd.DataFrame) -> tuple[date, date] | None:
    if df.empty or "Data" not in df.columns:
        return None
    return (df["Data"].min().date(), df["Data"].max().date())


def normalize_period_selection(value, default_period: tuple[date, date] | None) -> tuple[date, date] | None:
    if default_period is None:
        return None

    if not value:
        return default_period

    if isinstance(value, (tuple, list)):
        if len(value) >= 2:
            start_date, end_date = value[0], value[1]
        elif len(value) == 1:
            start_date = end_date = value[0]
        else:
            return default_period
    else:
        start_date = end_date = value

    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return (start_date, end_date)


def build_period_bounds(value, default_period: tuple[date, date] | None) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    selected_period = normalize_period_selection(value, default_period)
    if selected_period is None:
        return None

    start_date, end_date = selected_period
    data_inicio = pd.to_datetime(start_date)
    data_fim = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return data_inicio, data_fim


def init_filtros(df: pd.DataFrame) -> None:
    init_session_state()
    default_period = get_default_period(df)

    filtros = st.session_state[FILTERS_STATE_KEY]
    filtros.setdefault("periodo", default_period)
    filtros.setdefault("tipos", [])
    filtros.setdefault("produtos", [])

    available_types = sorted(df["TIPO"].dropna().unique()) if "TIPO" in df.columns else []
    available_products = sorted(df["Produto"].dropna().unique()) if "Produto" in df.columns else []

    filtros["tipos"] = [item for item in filtros["tipos"] if item in available_types]
    filtros["produtos"] = [item for item in filtros["produtos"] if item in available_products]

    if default_period is not None:
        selected_period = normalize_period_selection(filtros.get("periodo"), default_period)
        if selected_period is None:
            selected_period = default_period

        start_date = max(selected_period[0], default_period[0])
        end_date = min(selected_period[1], default_period[1])
        if start_date > end_date:
            start_date, end_date = default_period
        filtros["periodo"] = (start_date, end_date)
    else:
        filtros["periodo"] = None

    st.session_state[TYPE_WIDGET_KEY] = list(filtros["tipos"])
    st.session_state[PRODUCT_WIDGET_KEY] = list(filtros["produtos"])
    if filtros["periodo"] is None and PERIOD_INPUT_KEY in st.session_state:
        del st.session_state[PERIOD_INPUT_KEY]


def sync_period_filter() -> None:
    init_session_state()
    filtros = st.session_state[FILTERS_STATE_KEY]
    filtros["periodo"] = normalize_period_selection(
        st.session_state.get(PERIOD_INPUT_KEY),
        filtros.get("periodo"),
    )


def sync_type_filter() -> None:
    init_session_state()
    st.session_state[FILTERS_STATE_KEY]["tipos"] = list(st.session_state.get(TYPE_WIDGET_KEY, []))


def sync_product_filter() -> None:
    init_session_state()
    st.session_state[FILTERS_STATE_KEY]["produtos"] = list(
        st.session_state.get(PRODUCT_WIDGET_KEY, [])
    )


def clear_global_filters(df: pd.DataFrame) -> None:
    init_session_state()
    default_period = get_default_period(df)

    st.session_state[FILTERS_STATE_KEY] = {
        "periodo": default_period,
        "tipos": [],
        "produtos": [],
    }

    st.session_state[TYPE_WIDGET_KEY] = []
    st.session_state[PRODUCT_WIDGET_KEY] = []
    if PERIOD_INPUT_KEY in st.session_state:
        del st.session_state[PERIOD_INPUT_KEY]


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    init_session_state()
    filtered_df = df.copy()
    if "Data" in filtered_df.columns:
        filtered_df["Data"] = pd.to_datetime(filtered_df["Data"], errors="coerce")

    filtros = st.session_state.get(
        FILTERS_STATE_KEY,
        {"periodo": None, "tipos": [], "produtos": []},
    )
    selected_types = filtros.get("tipos", [])
    selected_products = filtros.get("produtos", [])
    selected_period = filtros.get("periodo")

    if selected_types:
        filtered_df = filtered_df[filtered_df["TIPO"].isin(selected_types)]

    if selected_products:
        filtered_df = filtered_df[filtered_df["Produto"].isin(selected_products)]

    if selected_period:
        period_bounds = build_period_bounds(selected_period, get_default_period(df))
        if period_bounds is not None:
            data_inicio, data_fim = period_bounds
            filtered_df = filtered_df[
                (filtered_df["Data"] >= data_inicio) & (filtered_df["Data"] <= data_fim)
            ]

    return filtered_df


def render_global_sidebar(df: pd.DataFrame, source_name: str, sheet_count: int) -> None:
    init_session_state()
    apply_brand_theme()
    hide_default_sidebar_navigation()
    render_sidebar_brand()
    render_sidebar_navigation()
    handle_workbook_upload()

    st.sidebar.title("Filtros")
    st.sidebar.caption(f"Fonte de dados: {source_name}")
    st.sidebar.caption(f"Abas importadas: {sheet_count}")

    init_filtros(df)
    filtros = st.session_state[FILTERS_STATE_KEY]
    default_period = get_default_period(df)

    st.sidebar.multiselect(
        "Tipo",
        sorted(df["TIPO"].dropna().unique()),
        key=TYPE_WIDGET_KEY,
        on_change=sync_type_filter,
    )
    st.sidebar.multiselect(
        "Produto",
        sorted(df["Produto"].dropna().unique()),
        key=PRODUCT_WIDGET_KEY,
        on_change=sync_product_filter,
    )

    if default_period is not None:
        st.sidebar.date_input(
            "Periodo",
            value=normalize_period_selection(filtros.get("periodo"), default_period),
            min_value=default_period[0],
            max_value=default_period[1],
            key=PERIOD_INPUT_KEY,
            on_change=sync_period_filter,
        )

        period_bounds = build_period_bounds(filtros.get("periodo"), default_period)
        if period_bounds is not None:
            data_inicio, data_fim = period_bounds
            st.sidebar.info(
                f"Periodo: {data_inicio.strftime('%d/%m/%Y')} ate {data_fim.strftime('%d/%m/%Y')}"
            )

    st.sidebar.button(
        "Limpar filtros",
        key="clear_filters",
        use_container_width=True,
        on_click=clear_global_filters,
        args=(df,),
    )


def get_dashboard_context() -> tuple[pd.DataFrame, str, pd.DataFrame]:
    init_session_state()
    source_name = initialize_database()
    df = load_sales_data()
    sheet_registry = load_sheet_registry()
    render_global_sidebar(df, source_name, len(sheet_registry))
    from utils.theme import render_global_update_notice

    render_global_update_notice(source_name, get_last_updated_at())
    filtered_df = apply_filters(df)
    return filtered_df, source_name, sheet_registry