from __future__ import annotations

import pandas as pd


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    receita = float(df["ValorTotal"].sum()) if not df.empty else 0.0
    peso = float(df["PesoTotal"].sum()) if not df.empty else 0.0
    quantidade = float(df["QuantidadeTotal"].sum()) if not df.empty else 0.0
    r_kg = receita / peso if peso > 0 else 0.0
    ticket_medio = receita / quantidade if quantidade > 0 else 0.0
    return {
        "receita": receita,
        "peso": peso,
        "quantidade": quantidade,
        "r_kg": r_kg,
        "ticket_medio": ticket_medio,
    }


def build_daily_analysis(df: pd.DataFrame) -> pd.DataFrame:
    normalized_df = df.copy()
    normalized_df["Data"] = pd.to_datetime(normalized_df["Data"], errors="coerce").dt.normalize()
    daily = (
        normalized_df.groupby("Data", as_index=False)
        .agg(
            {
                "ValorTotal": "sum",
                "PesoTotal": "sum",
                "QuantidadeTotal": "sum",
            }
        )
        .sort_values("Data")
    )
    daily["R$/KG"] = daily["ValorTotal"] / daily["PesoTotal"].replace(0, pd.NA)
    daily["R$/KG"] = daily["R$/KG"].fillna(0)
    return daily


def get_daily_highlights(daily_df: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    if daily_df.empty:
        return None, None
    best_day = daily_df.loc[daily_df["ValorTotal"].idxmax()]
    worst_day = daily_df.loc[daily_df["ValorTotal"].idxmin()]
    return best_day, worst_day


def build_type_analysis(df: pd.DataFrame) -> pd.DataFrame:
    type_df = (
        df.groupby("TIPO", as_index=False)
        .agg(
            {
                "ValorTotal": "sum",
                "PesoTotal": "sum",
                "QuantidadeTotal": "sum",
            }
        )
        .sort_values("ValorTotal", ascending=False)
    )
    type_df["R$/KG"] = type_df["ValorTotal"] / type_df["PesoTotal"].replace(0, pd.NA)
    type_df["R$/KG"] = type_df["R$/KG"].fillna(0)
    total_receita = type_df["ValorTotal"].sum()
    type_df["Participacao"] = type_df["ValorTotal"] / total_receita if total_receita > 0 else 0
    return type_df


def build_product_analysis(df: pd.DataFrame) -> pd.DataFrame:
    product_df = (
        df.groupby("Produto", as_index=False)
        .agg(
            {
                "ValorTotal": "sum",
                "QuantidadeTotal": "sum",
                "PesoTotal": "sum",
            }
        )
        .sort_values("ValorTotal", ascending=False)
    )
    product_df["R$/KG"] = product_df["ValorTotal"] / product_df["PesoTotal"].replace(0, pd.NA)
    product_df["R$/KG"] = product_df["R$/KG"].fillna(0)
    return product_df