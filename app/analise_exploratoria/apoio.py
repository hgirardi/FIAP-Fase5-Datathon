from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.constantes import ANOS


def primeiro_valido(serie: pd.Series) -> object:
    validos = serie.dropna()
    return validos.iloc[0] if not validos.empty else np.nan


def normalizar_escola(valor: object) -> str:
    if pd.isna(valor):
        return "Outro/Não informado"

    texto = str(valor).strip().lower()
    if not texto:
        return "Outro/Não informado"
    if "pública" in texto or "publica" in texto:
        return "Pública"
    if any(
        token in texto
        for token in [
            "privada",
            "bolsa",
            "decisão",
            "decisao",
            "rede",
            "jp ii",
            "apadrinhamento",
            "parceira",
            "universitário",
            "universitario",
            "formado",
            "concluiu",
        ]
    ):
        return "Privada"
    return "Outro/Não informado"


def normalizar_nivel(valor: object) -> str:
    if pd.isna(valor):
        return "N/D"
    return str(valor).strip().upper()


def categoria_defasagem(valor: object) -> str:
    if pd.isna(valor):
        return "Sem dado"
    if float(valor) > 0:
        return "Adiantado"
    if float(valor) == 0:
        return "Na fase"
    if float(valor) == -1:
        return "Leve (-1)"
    if float(valor) == -2:
        return "Moderada (-2)"
    return "Severa (< -2)"


def coerencia_detalhada(gap: object) -> str:
    if pd.isna(gap):
        return "Sem dado"
    if gap > 2:
        return "Superestima (>2)"
    if gap > 1:
        return "Superestima leve (1-2)"
    if gap < -2:
        return "Subestima (< -2)"
    if gap < -1:
        return "Subestima leve (-2 a -1)"
    return "Coerente (±1)"


def concordancia_ipp(row: pd.Series, mediana_ipp: float) -> str:
    defasado = row["IAN"] < 10
    ipp_baixo = row["IPP"] < mediana_ipp
    if defasado and ipp_baixo:
        return "Confirma: defasado + IPP baixo"
    if defasado and not ipp_baixo:
        return "Contradiz: defasado + IPP alto"
    if not defasado and not ipp_baixo:
        return "Confirma: adequado + IPP alto"
    return "Contradiz: adequado + IPP baixo"


def classificar_evolucao_ian(row: pd.Series) -> str:
    if row["IAN_inicio"] == 10 and row["IAN_fim"] == 10:
        return "Manteve adequado"
    if row["IAN_fim"] == 10 and row["IAN_inicio"] < 10:
        return "Recuperou"
    if row["IAN_fim"] > row["IAN_inicio"]:
        return "Melhorou"
    if row["IAN_fim"] < row["IAN_inicio"]:
        return "Piorou"
    return "Estável (defasado)"


def classificar_evolucao_pedra(delta: float) -> str:
    if pd.isna(delta):
        return "Sem dado"
    if delta > 0:
        return "Subiu"
    if delta < 0:
        return "Caiu"
    return "Manteve"


def coerencia_combinada(row: pd.Series) -> str:
    superestima_ida = row["gap_iaa_ida"] > 1.5
    superestima_ieg = row["gap_iaa_ieg"] > 1.5
    subestima_ida = row["gap_iaa_ida"] < -1.5
    subestima_ieg = row["gap_iaa_ieg"] < -1.5

    if superestima_ida and superestima_ieg:
        return "Superestima ambos"
    if subestima_ida and subestima_ieg:
        return "Subestima ambos"
    if superestima_ida or superestima_ieg:
        return "Superestima parcial"
    if subestima_ida or subestima_ieg:
        return "Subestima parcial"
    return "Coerente"


def cartao_metrica(rotulo: str, valor: str, ajuda: str | None = None) -> None:
    st.metric(rotulo, valor, help=ajuda)


def caixa_informativa(texto: str) -> None:
    st.markdown(f"*{texto}*")


def renderizar_grafico_com_titulo_subtitulo(titulo: str, subtitulo: str, grafico: alt.TopLevelMixin) -> None:
    st.markdown(f"#### {titulo}")
    if subtitulo:
        st.markdown(f"*{subtitulo}*")
    st.altair_chart(grafico.properties(title=""), use_container_width=True)


def boxplot_por_ano(df: pd.DataFrame, coluna: str) -> alt.Chart:
    dados = df.dropna(subset=[coluna]).copy()
    box = (
        alt.Chart(dados)
        .mark_boxplot(size=35, color="#93c5fd")
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y(f"{coluna}:Q", title=coluna),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip(f"{coluna}:Q", title=coluna, format=".2f"),
            ],
        )
    )
    medias = (
        alt.Chart(dados)
        .mark_point(color="#1d4ed8", filled=True, size=90)
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y(f"mean({coluna}):Q", title=coluna),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip(f"mean({coluna}):Q", title="Média", format=".2f"),
            ],
        )
    )
    texto = medias.mark_text(dy=-10, color="#1d4ed8").encode(text=alt.Text(f"mean({coluna}):Q", format=".2f"))
    return (box + medias + texto).properties(height=320)


def lista_destaques(linhas: list[str]) -> None:
    st.markdown("\n".join(f"- {linha}" for linha in linhas))
