from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.dados import carregar_analytics_ieg


def renderizar_ieg() -> None:
    """Renderiza a aba de IEG consumindo o parquet analítico do notebook."""
    st.subheader("IEG — Engajamento das Atividades")
    st.markdown(
        "Mede o engajamento do aluno nas tarefas curriculares e nas demais atividades promovidas pela Associação."
    )
    st.caption(
        "Fórmula: IEG = soma das pontuações das tarefas realizadas e registradas / número de tarefas. "
        "Exemplos: participação em tarefas de casa, atividades acadêmicas e voluntariado."
    )

    df_ieg = carregar_analytics_ieg()
    faixas_ieg = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    nomes_quadrante = {
        "Engajado + Bom desempenho": "Engaj. / bom",
        "Engajado + Baixo desempenho": "Engaj. / baixo",
        "Desengajado + Bom desempenho": "Deseng. / bom",
        "Desengajado + Baixo desempenho": "Deseng. / baixo",
    }
    df_ieg["faixa_ieg"] = pd.cut(
        df_ieg["IEG"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_ieg,
        include_lowest=True,
        right=False,
    )
    ieg_faixa = (
        df_ieg.dropna(subset=["IEG", "faixa_ieg"])
        .groupby(["ano", "faixa_ieg"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    ieg_faixa["participacao"] = ieg_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    ieg_ida = df_ieg.dropna(subset=["IEG", "IDA"]).copy()
    quadrantes = (
        ieg_ida["quadrante_ieg_ida"]
        .value_counts(normalize=True)
        .rename_axis("quadrante")
        .reset_index(name="participacao")
    )
    quadrantes["quadrante_curto"] = quadrantes["quadrante"].map(nomes_quadrante).fillna(quadrantes["quadrante"])
    ieg_ipv = df_ieg.dropna(subset=["IEG", "IPV"]).copy()

    zeros_2024 = ((df_ieg["ano"] == 2024) & (df_ieg["IEG"] == 0)).sum()
    corr_ieg_ida = ieg_ida["IEG"].corr(ieg_ida["IDA"])
    corr_ieg_ipv = ieg_ipv["IEG"].corr(ieg_ipv["IPV"])
    principal = quadrantes.sort_values("participacao", ascending=False).iloc[0]
    ieg_por_ano = df_ieg.groupby("ano")["IEG"].mean().sort_index()
    mediana_ieg = ieg_ipv["IEG"].median()
    mediana_ipv = ieg_ipv["IPV"].median()
    faixa_topo_2024 = ieg_faixa[ieg_faixa["ano"] == 2024].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2022 = ieg_faixa[ieg_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(ieg_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_ieg:N",
                    title="Faixa de IEG",
                    sort=faixas_ieg,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_ieg:N", title="Faixa de IEG"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IEG por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IEG por ano",
            (
                f"O IEG médio vai de {ieg_por_ano.loc[2022]:.2f} em 2022 para {ieg_por_ano.loc[2024]:.2f} em 2024, "
                f"mantendo estabilidade; a faixa mais comum sai de `{faixa_topo_2022['faixa_ieg']}` em 2022 "
                f"({faixa_topo_2022['participacao']:.1%}) para `{faixa_topo_2024['faixa_ieg']}` em 2024 "
                f"({faixa_topo_2024['participacao']:.1%}), com apenas {zeros_2024} caso(s) de IEG igual a zero em 2024."
            ),
            chart_dist,
        )

    with col2:
        dispersao = (
            alt.Chart(ieg_ida)
            .mark_circle(size=60, opacity=0.35, color="#2563eb")
            .encode(
                x=alt.X("IEG:Q", title="IEG"),
                y=alt.Y("IDA:Q", title="IDA"),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("nivel_label:N", title="Nível"),
                    alt.Tooltip("IEG:Q", title="IEG", format=".2f"),
                    alt.Tooltip("IDA:Q", title="IDA", format=".2f"),
                ],
            )
        )
        regressao = dispersao.transform_regression("IEG", "IDA").mark_line(color="#dc2626", strokeDash=[6, 4])
        renderizar_grafico_com_titulo_subtitulo(
            "IEG x IDA",
            f"A correlação com IDA é moderada (r={corr_ieg_ida:.3f}) e parecida com a correlação com IPV (r={corr_ieg_ipv:.3f}).",
            dispersao + regressao,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_quad = (
            alt.Chart(quadrantes)
            .mark_bar()
            .encode(
                x=alt.X("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                y=alt.Y("quadrante_curto:N", title=None, sort="-x", axis=alt.Axis(labelLimit=220)),
                color=alt.Color("quadrante_curto:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("quadrante_curto:N", title="Perfil"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Perfis combinados de engajamento e desempenho")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Perfis combinados de engajamento e desempenho",
            (
                "Cada barra combina engajamento no IEG e desempenho no IDA: `Engaj.` indica maior participação nas atividades, "
                "`Deseng.` indica menor participação, e `bom` ou `baixo` se referem ao desempenho acadêmico (IDA) relativo da base. "
                f"O perfil mais frequente é `{nomes_quadrante.get(principal['quadrante'], principal['quadrante'])}`, reunindo {principal['participacao']:.1%} da base observada."
            ),
            chart_quad,
        )

    with col4:
        mapa = (
            alt.Chart(ieg_ipv)
            .mark_rect()
            .encode(
                x=alt.X("IEG:Q", bin=alt.Bin(maxbins=20), title="IEG"),
                y=alt.Y("IPV:Q", bin=alt.Bin(maxbins=20), title="IPV"),
                color=alt.Color("count():Q", title="Alunos", scale=alt.Scale(scheme="yelloworangered")),
                tooltip=[alt.Tooltip("count():Q", title="Alunos")],
            )
            .properties(height=320, title="Densidade IEG x IPV")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Densidade IEG x IPV",
            (
                f"A maior concentração de alunos aparece perto de IEG {mediana_ieg:.2f} e IPV {mediana_ipv:.2f}, "
                "ajudando a identificar onde estão os perfis mais recorrentes da base."
            ),
            mapa,
        )
