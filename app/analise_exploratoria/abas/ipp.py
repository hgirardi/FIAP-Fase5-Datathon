from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, GRUPOS_IAN
from analise_exploratoria.dados import carregar_analytics_ipp


def renderizar_ipp(df: pd.DataFrame | None = None, pares: pd.DataFrame | None = None) -> None:
    """Renderiza a aba de IPP consumindo o parquet analítico do notebook."""
    st.subheader("IPP — Aspectos Psicopedagógicos")
    st.markdown(
        "Avalia aspectos cognitivos, emocionais, comportamentais e de aprendizagem do aluno a partir da equipe pedagógica e psicopedagógica."
    )
    st.caption(
        "Fórmula: IPP = soma das avaliações sobre aspectos pedagógicos / número de avaliações."
    )

    df_ipp = carregar_analytics_ipp()
    nomes_concordancia = {
        "Confirma: defasado + IPP baixo": "Confirma / defasado",
        "Contradiz: defasado + IPP alto": "Contradiz / defasado",
        "Confirma: adequado + IPP alto": "Confirma / adequado",
        "Contradiz: adequado + IPP baixo": "Contradiz / adequado",
    }
    faixas_ipp = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    df_ipp["faixa_ipp"] = pd.cut(
        df_ipp["IPP"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_ipp,
        include_lowest=True,
        right=False,
    )
    ipp_faixa = (
        df_ipp.dropna(subset=["IPP", "faixa_ipp"])
        .groupby(["ano", "faixa_ipp"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    ipp_faixa["participacao"] = ipp_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    mesmos_alunos = df_ipp[df_ipp["ano"].isin([2022, 2023])].groupby("RA").filter(lambda grupo: grupo["ano"].nunique() == 2)
    ipp_delta = mesmos_alunos.pivot_table(index="RA", columns="ano", values="IPP", aggfunc="first").dropna()
    ipp_delta["delta"] = ipp_delta[2023] - ipp_delta[2022]
    delta_resumo = pd.DataFrame(
        {
            "grupo": ["Subiu > 1 ponto", "Entre -1 e +1", "Caiu > 1 ponto"],
            "participacao": [
                (ipp_delta["delta"] > 1).mean(),
                ((ipp_delta["delta"] >= -1) & (ipp_delta["delta"] <= 1)).mean(),
                (ipp_delta["delta"] < -1).mean(),
            ],
        }
    )

    por_ian = (
        df_ipp.dropna(subset=["IPP", "grupo_ian"])
        .groupby(["ano", "grupo_ian"])["IPP"]
        .mean()
        .reset_index()
    )
    por_ian["grupo_ian"] = pd.Categorical(por_ian["grupo_ian"], categories=GRUPOS_IAN, ordered=True)

    concordancia = (
        df_ipp.dropna(subset=["concordancia_ipp"])
        .groupby(["ano", "concordancia_ipp"])
        .size()
        .reset_index(name="quantidade")
    )
    concordancia["concordancia_curta"] = concordancia["concordancia_ipp"].map(nomes_concordancia).fillna(concordancia["concordancia_ipp"])
    concordancia["participacao"] = concordancia.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    defasados = df_ipp[(df_ipp["IAN"] < 10) & (df_ipp["IAN_proximo"] < 10)].dropna(subset=["avancou_fase"]).copy()
    mascara_avancou = defasados["avancou_fase"].astype("boolean")
    defasados["avancou_fase"] = mascara_avancou
    defasados["grupo_fase"] = defasados["avancou_fase"].map({True: "Avançou de fase", False: "Não avançou"})
    defasados_compare = (
        defasados.groupby("grupo_fase")[["IPP_proximo", "delta_IPP"]]
        .mean()
        .reset_index()
        .melt(id_vars="grupo_fase", var_name="medida", value_name="valor")
    )

    corr_ipp_ian = df_ipp.dropna(subset=["IPP", "IAN"])["IPP"].corr(df_ipp.dropna(subset=["IPP", "IAN"])["IAN"])
    contradiz_pct = df_ipp.dropna(subset=["concordancia_ipp"])["concordancia_ipp"].str.contains("Contradiz").mean()
    avancou_delta = defasados[mascara_avancou.fillna(False)]["delta_IPP"].mean()
    nao_avancou_delta = defasados[~mascara_avancou.fillna(False)]["delta_IPP"].mean()
    subiu_forte = delta_resumo.loc[delta_resumo["grupo"] == "Subiu > 1 ponto", "participacao"].iloc[0]
    caiu_forte = delta_resumo.loc[delta_resumo["grupo"] == "Caiu > 1 ponto", "participacao"].iloc[0]
    ipp_adequado = por_ian[por_ian["grupo_ian"] == "Adequado (10.0)"]["IPP"].mean()
    ipp_severo = por_ian[por_ian["grupo_ian"] == "Severa (2.5)"]["IPP"].mean()
    ipp_por_ano = df_ipp.groupby("ano")["IPP"].mean().reindex(ANOS)
    faixa_topo_2022 = ipp_faixa[ipp_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2023 = ipp_faixa[ipp_faixa["ano"] == 2023].sort_values("participacao", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(ipp_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_ipp:N",
                    title="Faixa de IPP",
                    sort=faixas_ipp,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_ipp:N", title="Faixa de IPP"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IPP por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IPP por ano",
            (
                f"O IPP médio sai de {ipp_por_ano.loc[2022]:.2f} em 2022 para {ipp_por_ano.loc[2023]:.2f} em 2023; "
                f"a faixa mais comum muda de `{faixa_topo_2022['faixa_ipp']}` ({faixa_topo_2022['participacao']:.1%}) "
                f"para `{faixa_topo_2023['faixa_ipp']}` ({faixa_topo_2023['participacao']:.1%}), "
                f"com avanço médio de {ipp_delta['delta'].mean():+.2f} ponto(s) nos mesmos alunos."
            ),
            chart_dist,
        )

    with col2:
        chart_delta = (
            alt.Chart(delta_resumo)
            .mark_bar()
            .encode(
                x=alt.X("grupo:N", title=None, sort=None),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color("grupo:N", title=None, scale=alt.Scale(range=["#16a34a", "#f59e0b", "#dc2626"])),
                tooltip=[
                    alt.Tooltip("grupo:N", title="Grupo"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Variação do IPP nos mesmos alunos (2022->2023)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Variação do IPP nos mesmos alunos (2022->2023)",
            f"{subiu_forte:.1%} dos alunos sobem mais de 1 ponto no período, enquanto {caiu_forte:.1%} recuam mais de 1 ponto.",
            chart_delta,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_ian = (
            alt.Chart(por_ian)
            .mark_bar()
            .encode(
                x=alt.X("grupo_ian:N", sort=GRUPOS_IAN, title="Grupo de IAN"),
                y=alt.Y("IPP:Q", title="IPP médio"),
                color=alt.Color(
                    "ano:O",
                    title="Ano",
                    scale=alt.Scale(
                        domain=[2022, 2023, 2024],
                        range=["#dc2626", "#f59e0b", "#2563eb"],
                    ),
                ),
                xOffset="ano:O",
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("grupo_ian:N", title="Grupo"),
                    alt.Tooltip("IPP:Q", title="IPP médio", format=".2f"),
                ],
            )
            .properties(height=320, title="IPP por grupo de IAN")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "IPP por grupo de IAN",
            (
                f"Os grupos mais adequados no IAN tendem a aparecer com IPP mais alto. "
                f"No gráfico, o IPP médio sai de {ipp_severo:.2f} na defasagem severa para {ipp_adequado:.2f} no grupo adequado, "
                "mas a diferença entre as faixas é moderada, mostrando que os dois indicadores não contam exatamente a mesma história."
            ),
            chart_ian,
        )

    with col4:
        chart_concordancia = (
            alt.Chart(concordancia)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color("concordancia_curta:N", title="Leitura"),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("concordancia_curta:N", title="Leitura"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="O IPP confirma ou contradiz o IAN?")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "O IPP confirma ou contradiz o IAN?",
            (
                "As barras se dividem entre situações em que o IPP reforça a leitura do IAN e situações em que aponta para a direção oposta. "
                f"No total, {contradiz_pct:.1%} dos registros entram em zona de contradição, mostrando que os dois indicadores capturam dimensões diferentes da trajetória do aluno."
            ),
            chart_concordancia,
        )

    chart_defasados = (
        alt.Chart(defasados_compare)
        .mark_bar()
        .encode(
            x=alt.X("grupo_fase:N", title=None),
            y=alt.Y("valor:Q", title="Valor médio"),
            color=alt.Color("medida:N", title=None, scale=alt.Scale(range=["#2563eb", "#16a34a"])),
            xOffset="medida:N",
            tooltip=[
                alt.Tooltip("grupo_fase:N", title="Grupo"),
                alt.Tooltip("medida:N", title="Medida"),
                alt.Tooltip("valor:Q", title="Valor", format=".2f"),
            ],
        )
        .properties(height=320, title="Defasados consecutivos: quem avança de fase melhora mais no IPP?")
    )
    renderizar_grafico_com_titulo_subtitulo(
        "Defasados consecutivos: quem avança de fase melhora mais no IPP?",
        f"Mesmo entre alunos ainda defasados, quem avança de fase melhora {avancou_delta:.2f} ponto(s) no IPP, contra {nao_avancou_delta:.2f} entre os que não avançam.",
        chart_defasados,
    )
