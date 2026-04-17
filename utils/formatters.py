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


def format_weight(value: float | int, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    suffix = " kg"
    return f"{format_decimal(float(value), decimals)}{suffix}"


def format_signed_percent(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):+.{decimals}f}%".replace(".", ",")


def variation_arrow(value: float | int | None) -> str:
    if value is None or pd.isna(value) or float(value) == 0:
        return "➖"
    return "🔺" if float(value) > 0 else "🔻"


def classify_variation(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Sem base comparativa"
    numeric_value = float(value)
    if numeric_value > 10:
        return "Forte crescimento"
    if numeric_value < -10:
        return "Queda relevante"
    return "Estavel"


def build_daily_tooltip_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy().sort_values("Data").reset_index(drop=True)
    df["Data_str"] = pd.to_datetime(df["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df["Valor_fmt"] = pd.to_numeric(df["ValorTotal"], errors="coerce").apply(format_currency)
    df["Peso_fmt"] = pd.to_numeric(df.get("PesoTotal", 0), errors="coerce").apply(
        lambda value: format_weight(value, decimals=0)
    )

    if "R$/KG" in df.columns:
        ratio_series = pd.to_numeric(df["R$/KG"], errors="coerce")
    else:
        ratio_series = pd.to_numeric(df["ValorTotal"], errors="coerce") / pd.to_numeric(
            df.get("PesoTotal", 0), errors="coerce"
        ).replace(0, pd.NA)
    df["RKG"] = ratio_series.fillna(0)
    df["RKG_fmt"] = df["RKG"].apply(lambda value: f"R$ {format_ratio(value)}")

    df["Valor_anterior"] = pd.to_numeric(df["ValorTotal"], errors="coerce").shift(1)
    df["Var_%"] = (
        (pd.to_numeric(df["ValorTotal"], errors="coerce") - df["Valor_anterior"])
        / df["Valor_anterior"].replace(0, pd.NA)
    ) * 100
    df["Var_fmt"] = df["Var_%"].apply(format_signed_percent)
    df["Seta"] = df["Var_%"].apply(variation_arrow)
    df["Status"] = df["Var_%"].apply(classify_variation)
    return df


def build_category_tooltip_dataframe(
    dataframe: pd.DataFrame,
    *,
    label_column: str,
    value_column: str,
    value_mode: str = "currency",
    weight_column: str | None = None,
    ratio_column: str | None = None,
) -> pd.DataFrame:
    df = dataframe.copy().reset_index(drop=True)
    value_series = pd.to_numeric(df[value_column], errors="coerce")
    mean_value = value_series.mean()
    total_value = value_series.sum()

    df["Label"] = df[label_column].astype(str)

    if value_mode == "weight":
        df["Valor_fmt"] = value_series.apply(lambda value: format_weight(value, decimals=0))
    elif value_mode == "ratio":
        df["Valor_fmt"] = value_series.apply(lambda value: f"R$ {format_ratio(value)}")
    elif value_mode == "integer":
        df["Valor_fmt"] = value_series.apply(format_integer)
    else:
        df["Valor_fmt"] = value_series.apply(format_currency)

    df["Rank"] = value_series.rank(method="dense", ascending=False).astype(int)
    df["Participacao"] = (value_series / total_value).fillna(0) if total_value else 0
    df["Participacao_fmt"] = pd.Series(df["Participacao"]).apply(format_percent)
    df["Vs_media_%"] = ((value_series / mean_value) - 1) * 100 if mean_value else 0
    df["Vs_media_fmt"] = pd.Series(df["Vs_media_%"]).apply(format_signed_percent)
    df["Seta"] = pd.Series(df["Vs_media_%"]).apply(variation_arrow)

    if weight_column:
        df["Peso_fmt"] = pd.to_numeric(df[weight_column], errors="coerce").apply(
            lambda value: format_weight(value, decimals=0)
        )
    else:
        df["Peso_fmt"] = "-"

    if ratio_column:
        df["RKG_fmt"] = pd.to_numeric(df[ratio_column], errors="coerce").apply(
            lambda value: f"R$ {format_ratio(value)}"
        )
    else:
        df["RKG_fmt"] = "-"

    return df


def build_scatter_tooltip_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy().reset_index(drop=True)
    peso_medio = pd.to_numeric(df["PesoTotal"], errors="coerce").mean()
    valor_medio = pd.to_numeric(df["ValorTotal"], errors="coerce").mean()

    ratio_series = pd.to_numeric(df["ValorTotal"], errors="coerce") / pd.to_numeric(
        df["PesoTotal"], errors="coerce"
    ).replace(0, pd.NA)
    df["Produto_str"] = df["Produto"].astype(str)
    df["Tipo_str"] = df["TIPO"].astype(str)
    df["Valor_fmt"] = pd.to_numeric(df["ValorTotal"], errors="coerce").apply(format_currency)
    df["Peso_fmt"] = pd.to_numeric(df["PesoTotal"], errors="coerce").apply(
        lambda value: format_weight(value, decimals=0)
    )
    df["Qtd_fmt"] = pd.to_numeric(df["QuantidadeTotal"], errors="coerce").apply(format_integer)
    df["RKG_fmt"] = ratio_series.fillna(0).apply(lambda value: f"R$ {format_ratio(value)}")

    quadrants = []
    for _, row in df.iterrows():
        high_weight = float(row["PesoTotal"]) >= float(peso_medio)
        high_value = float(row["ValorTotal"]) >= float(valor_medio)
        if high_weight and high_value:
            quadrants.append("Alto peso e alto valor")
        elif high_weight:
            quadrants.append("Alto peso e baixo valor")
        elif high_value:
            quadrants.append("Baixo peso e alto valor")
        else:
            quadrants.append("Baixo peso e baixo valor")
    df["Quadrante"] = quadrants
    return df


def build_pie_tooltip_dataframe(dataframe: pd.DataFrame, *, label_column: str, value_column: str) -> pd.DataFrame:
    df = dataframe.copy().reset_index(drop=True)
    value_series = pd.to_numeric(df[value_column], errors="coerce")
    total_value = value_series.sum()
    df["Label"] = df[label_column].astype(str)
    df["Valor_fmt"] = value_series.apply(format_currency)
    participacao = (value_series / total_value).fillna(0) if total_value else 0
    df["Participacao_fmt"] = pd.Series(participacao).apply(format_percent)
    df["Rank"] = value_series.rank(method="dense", ascending=False).astype(int)
    return df


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