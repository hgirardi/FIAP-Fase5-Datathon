from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import (
    categoria_defasagem,
    coerencia_detalhada,
    concordancia_ipp,
    normalizar_escola,
    normalizar_nivel,
    primeiro_valido,
)
from analise_exploratoria.constantes import (
    CAMINHO_ANALYTICS_IAN,
    CAMINHO_ANALYTICS_IDA,
    CAMINHO_ANALYTICS_IEG,
    CAMINHO_ANALYTICS_IAA,
    CAMINHO_ANALYTICS_IPS,
    CAMINHO_ANALYTICS_IPP,
    CAMINHO_ANALYTICS_IPV,
    CAMINHO_DADOS,
    COLUNAS_PEDRA,
    INDICADORES,
    INDICADORES_BASE,
    ORDEM_PEDRAS,
    ORDEM_NIVEIS,
    FAIXAS_IPS,
    PEDRA_PARA_NUMERO,
)
from analise_exploratoria.analiticos.ian import validar_base_analitica_ian
from analise_exploratoria.analiticos.ida import validar_base_analitica_ida
from analise_exploratoria.analiticos.ieg import validar_base_analitica_ieg
from analise_exploratoria.analiticos.iaa import validar_base_analitica_iaa
from analise_exploratoria.analiticos.ips import validar_base_analitica_ips
from analise_exploratoria.analiticos.ipp import validar_base_analitica_ipp
from analise_exploratoria.analiticos.ipv import validar_base_analitica_ipv


@st.cache_data
def carregar_base_dados() -> pd.DataFrame:
    df = pd.read_parquet(CAMINHO_DADOS).copy()

    nao_avaliados = (df["ano"] == 2024) & df["IAA"].isna()
    for coluna in ["IDA", "IEG"]:
        mascara = nao_avaliados & (df[coluna] == 0)
        df.loc[mascara, coluna] = np.nan

    df["nivel_label"] = df["nivel"].apply(normalizar_nivel)
    df["nivel_ordem"] = df["nivel_label"].map(ORDEM_NIVEIS)
    df["tipo_escola_macro"] = df["instituicao"].apply(normalizar_escola)
    df["tipo_escola_macro"] = df["tipo_escola_macro"].replace({"Privada/Bolsa": "Privada"})
    df["status_ian"] = df["IAN"].map(
        {
            10.0: "Em fase",
            5.0: "Defasagem moderada",
            2.5: "Defasagem severa",
        }
    )
    df["grupo_ian"] = df["IAN"].map(
        {
            10.0: "Adequado (10.0)",
            5.0: "Moderada (5.0)",
            2.5: "Severa (2.5)",
        }
    )
    df["em_defasagem"] = df["IAN"] < 10
    df["defasagem_cat"] = df["defasagem"].apply(categoria_defasagem)
    df["primeiro_ano_status"] = np.where(df["ano"] == df["ano_ingresso"], "Primeiro ano", "Veterano")
    df["tempo_programa"] = (df["ano"] - df["ano_ingresso"]).astype("Int64")
    df["gap_iaa_ida"] = df["IAA"] - df["IDA"]
    df["gap_iaa_ieg"] = df["IAA"] - df["IEG"]
    df["coerencia_iaa"] = df["gap_iaa_ida"].apply(coerencia_detalhada)
    df["pedra_resumo"] = df["pedra"].where(df["pedra"].isin(ORDEM_PEDRAS))

    mediana_ipp = df["IPP"].median()
    ipp_validos = df[["IPP", "IAN"]].notna().all(axis=1)
    df.loc[ipp_validos, "concordancia_ipp"] = df.loc[ipp_validos].apply(
        lambda row: concordancia_ipp(row, mediana_ipp), axis=1
    )

    return df


@st.cache_data
def carregar_analytics_ian() -> pd.DataFrame:
    """Lê o artefato analítico do IAN e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IAN).copy()
    if "instituicao" in df.columns:
        df["tipo_escola_macro"] = df["instituicao"].apply(normalizar_escola)
    elif "tipo_escola_macro" in df.columns:
        df["tipo_escola_macro"] = df["tipo_escola_macro"].replace({"Privada/Bolsa": "Privada"})
    validar_base_analitica_ian(df)
    return df


@st.cache_data
def carregar_analytics_ida() -> pd.DataFrame:
    """Lê o artefato analítico do IDA e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IDA).copy()
    validar_base_analitica_ida(df)
    return df


@st.cache_data
def carregar_analytics_ieg() -> pd.DataFrame:
    """Lê o artefato analítico do IEG e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IEG).copy()
    validar_base_analitica_ieg(df)
    return df


@st.cache_data
def carregar_analytics_iaa() -> pd.DataFrame:
    """Lê o artefato analítico do IAA e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IAA).copy()
    validar_base_analitica_iaa(df)
    return df


@st.cache_data
def carregar_analytics_ips() -> pd.DataFrame:
    """Lê o artefato analítico do IPS e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IPS).copy()
    validar_base_analitica_ips(df)
    return df


@st.cache_data
def carregar_analytics_ipp() -> pd.DataFrame:
    """Lê o artefato analítico do IPP e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IPP).copy()
    validar_base_analitica_ipp(df)
    return df


@st.cache_data
def carregar_analytics_ipv() -> pd.DataFrame:
    """Lê o artefato analítico do IPV e valida o contrato esperado pela aba."""
    df = pd.read_parquet(CAMINHO_ANALYTICS_IPV).copy()
    validar_base_analitica_ipv(df)
    return df


@st.cache_data
def montar_pares(df: pd.DataFrame) -> pd.DataFrame:
    linhas: list[dict[str, object]] = []

    for ra, grupo in df.sort_values(["RA", "ano"]).groupby("RA"):
        registros = grupo.to_dict("records")
        for atual, proximo in zip(registros, registros[1:]):
            if int(proximo["ano"]) != int(atual["ano"]) + 1:
                continue

            linha: dict[str, object] = {
                "RA": ra,
                "ano_atual": int(atual["ano"]),
                "ano_proximo": int(proximo["ano"]),
                "transicao": f"{int(atual['ano'])}->{int(proximo['ano'])}",
            }
            for coluna in [
                "IAN",
                "IDA",
                "IEG",
                "IAA",
                "IPS",
                "IPP",
                "IPV",
                "INDE",
                "pedra_resumo",
                "nivel_label",
                "nivel_ordem",
                "tipo_escola_macro",
                "primeiro_ano_status",
                "gap_iaa_ida",
                "gap_iaa_ieg",
                "coerencia_iaa",
            ]:
                linha[f"{coluna}_atual"] = atual.get(coluna)
                linha[f"{coluna}_proximo"] = proximo.get(coluna)
            linhas.append(linha)

    pares = pd.DataFrame(linhas)
    if pares.empty:
        return pares

    pares["delta_IDA"] = pares["IDA_proximo"] - pares["IDA_atual"]
    pares["delta_IEG"] = pares["IEG_proximo"] - pares["IEG_atual"]
    pares["delta_IPP"] = pares["IPP_proximo"] - pares["IPP_atual"]
    pares["adequado_atual"] = pares["IAN_atual"] == 10
    pares["adequado_proximo"] = pares["IAN_proximo"] == 10
    pares["transicao_ian"] = np.select(
        [
            pares["adequado_atual"] & pares["adequado_proximo"],
            pares["adequado_atual"] & ~pares["adequado_proximo"],
            ~pares["adequado_atual"] & pares["adequado_proximo"],
        ],
        ["Manteve adequado", "Piorou", "Recuperou"],
        default="Manteve defasado",
    )
    pares["faixa_IPS"] = pd.cut(
        pares["IPS_atual"],
        bins=[0, 4, 6, 8, 10],
        labels=FAIXAS_IPS,
        include_lowest=True,
    )
    pares["caiu_IDA"] = pares["delta_IDA"] < -1
    pares["caiu_IEG"] = pares["delta_IEG"] < -1
    pares["avancou_fase"] = pares["nivel_ordem_proximo"] > pares["nivel_ordem_atual"]
    return pares


@st.cache_data
def montar_base_pedras(df: pd.DataFrame) -> pd.DataFrame:
    base = (
        df.sort_values(["RA", "ano"])
        .groupby("RA")
        .agg(
            ano_ingresso=("ano_ingresso", primeiro_valido),
            pedra_20=("pedra_20", primeiro_valido),
            pedra_21=("pedra_21", primeiro_valido),
            pedra_22=("pedra_22", primeiro_valido),
            pedra_23=("pedra_23", primeiro_valido),
        )
    )

    pedra_24 = (
        df[df["ano"] == 2024]
        .groupby("RA")["pedra"]
        .agg(primeiro_valido)
        .rename("pedra_24")
    )

    base = base.join(pedra_24)
    for coluna in COLUNAS_PEDRA.values():
        base[coluna] = base[coluna].where(base[coluna].isin(ORDEM_PEDRAS))
    return base


@st.cache_data
def montar_score_risco(df: pd.DataFrame) -> pd.DataFrame:
    risco = df.copy()
    risco["risco_defasagem"] = (risco["IAN"] < 10).astype(int)
    risco["risco_primeiro_ano"] = (risco["ano_ingresso"] == risco["ano"]).astype(int)
    risco["risco_ida_baixo"] = (
        risco.groupby("ano")["IDA"].transform(lambda serie: (serie < serie.quantile(0.25)).astype(int))
    )
    risco["risco_ieg_baixo"] = (
        risco.groupby("ano")["IEG"].transform(lambda serie: (serie < serie.quantile(0.25)).astype(int))
    )
    risco["risco_superestima"] = (risco["gap_iaa_ida"] > 2).astype(int)
    risco["score_risco"] = risco[
        [
            "risco_defasagem",
            "risco_primeiro_ano",
            "risco_ida_baixo",
            "risco_ieg_baixo",
            "risco_superestima",
        ]
    ].sum(axis=1)
    return risco
