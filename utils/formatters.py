from __future__ import annotations

import pandas as pd


def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def abreviar_valor(valor: float | int) -> str:
    valor_float = float(valor)
    sinal = "-" if valor_float < 0 else ""
    valor_abs = abs(valor_float)

    if valor_abs >= 1_000_000:
        return f"{sinal}{valor_abs / 1_000_000:.1f}M"
    if valor_abs >= 1_000:
        return f"{sinal}{valor_abs / 1_000:.1f}K"
    if valor_abs.is_integer():
        return f"{sinal}{int(valor_abs)}"
    return f"{sinal}{valor_abs:.1f}"


def format_integer(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_decimal(value: float, decimals: int = 2) -> str:
    pattern = f"{{value:,.{decimals}f}}"
    return pattern.format(value=value).replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_br(valor, moeda: bool = False, decimals: int = 2) -> str:
    if valor is None or pd.isna(valor):
        return "-"

    numeric_value = float(valor)
    if moeda:
        return format_currency(numeric_value)

    return format_decimal(numeric_value, decimals)


def format_ratio(value: float) -> str:
    return format_decimal(value, 2)


def format_percent(value: float) -> str:
    return f"{value:.1%}".replace(".", ",")


def format_date(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%d/%m/%Y")


def format_dataframe_ptbr(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()

    for column in df.columns:
        lower_column = str(column).lower()

        if lower_column == "data":
            df[column] = pd.to_datetime(df[column], errors="coerce").apply(format_date)
            continue

        if lower_column in {"valortotal", "valor"}:
            numeric_series = pd.to_numeric(df[column], errors="coerce")
            df[column] = numeric_series.apply(lambda value: formatar_br(value, moeda=True))
            continue

        if lower_column in {"pesototal", "pesounitario", "r$/kg", "r$/kg medio", "r_kg"}:
            numeric_series = pd.to_numeric(df[column], errors="coerce")
            df[column] = numeric_series.apply(lambda value: formatar_br(value, decimals=2))
            continue

        if lower_column in {"quantidadetotal", "linhas", "row_count", "codproduto", "cod_prod"}:
            numeric_series = pd.to_numeric(df[column], errors="coerce")
            df[column] = numeric_series.apply(lambda value: "-" if pd.isna(value) else format_integer(value))
            continue

        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = pd.to_datetime(df[column], errors="coerce").apply(format_date)

    return df