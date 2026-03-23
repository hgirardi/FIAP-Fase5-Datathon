from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, GRUPOS_IAN
from analise_exploratoria.dados import carregar_analytics_ida


def renderizar_ida() -> None:
    """Renderiza a aba de IDA consumindo o parquet analítico do notebook."""
    st.subheader("IDA — Desempenho Acadêmico")
    st.markdown(
        "Registra o desempenho acadêmico do aluno nas avaliações padronizadas e internas das disciplinas ofertadas pela Associação."
    )
    st.caption(
        "Fórmula: IDA = (Nota Matemática + Nota Português + Nota Inglês) / 3. "
        "Dados necessários: notas internas da associação."
    )

    df_ida = carregar_analytics_ida()

    # O artefato já traz o tipo do aluno e os rótulos de leitura usados nos gráficos.
    faixas_ida = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    df_ida["faixa_ida"] = pd.cut(
        df_ida["IDA"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_ida,
        include_lowest=True,
        right=False,
    )
    ida_faixa = (
        df_ida.dropna(subset=["IDA", "faixa_ida"])
        .groupby(["ano", "faixa_ida"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    ida_faixa["participacao"] = ida_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    ida_tipo_media = (
        df_ida.dropna(subset=["IDA"])
        .groupby(["ano", "tipo_aluno"])["IDA"]
        .mean()
        .reset_index()
    )

    ida_nivel = (
        df_ida.dropna(subset=["IDA", "nivel_ordem"])
        .groupby(["nivel_label", "nivel_ordem", "ano"])["IDA"]
        .mean()
        .reset_index()
        .sort_values(["nivel_ordem", "ano"])
    )

    ida_ian = (
        df_ida.dropna(subset=["IDA", "grupo_ian"])
        .groupby("grupo_ian")["IDA"]
        .mean()
        .reindex(GRUPOS_IAN)
        .reset_index()
    )

    nivel_3 = ida_nivel[ida_nivel["nivel_label"] == "3"]["IDA"].mean()
    outros = ida_nivel[ida_nivel["nivel_label"] != "3"]["IDA"].mean()
    medias = ida_tipo_media.pivot(index="ano", columns="tipo_aluno", values="IDA")
    diff_veterano = (medias["Veterano"] - medias["Ingressante"]).mean()
    adequado = ida_ian.loc[ida_ian["grupo_ian"] == "Adequado (10.0)", "IDA"].iloc[0]
    moderada = ida_ian.loc[ida_ian["grupo_ian"] == "Moderada (5.0)", "IDA"].iloc[0]
    ida_por_ano = df_ida.groupby("ano")["IDA"].mean().reindex(ANOS)
    faixa_topo_2024 = ida_faixa[ida_faixa["ano"] == 2024].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2022 = ida_faixa[ida_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(ida_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_ida:N",
                    title="Faixa de IDA",
                    sort=faixas_ida,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_ida:N", title="Faixa de IDA"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IDA por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IDA por ano",
            (
                f"O IDA médio fica em {ida_por_ano.loc[2022]:.2f} em 2022, {ida_por_ano.loc[2023]:.2f} em 2023 "
                f"e {ida_por_ano.loc[2024]:.2f} em 2024; em 2022 a faixa mais comum é `{faixa_topo_2022['faixa_ida']}` "
                f"({faixa_topo_2022['participacao']:.1%}) e, em 2024, ela passa a ser `{faixa_topo_2024['faixa_ida']}` "
                f"({faixa_topo_2024['participacao']:.1%})."
            ),
            chart_dist,
        )

    with col2:
        chart_tipo = (
            alt.Chart(ida_tipo_media)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("IDA:Q", title="IDA médio"),
                color=alt.Color("tipo_aluno:N", title=None, scale=alt.Scale(range=["#dc2626", "#2563eb"])),
                xOffset="tipo_aluno:N",
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("tipo_aluno:N", title="Tipo"),
                    alt.Tooltip("IDA:Q", title="IDA médio", format=".2f"),
                ],
            )
            .properties(height=320, title="Ingressantes x veteranos")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Ingressantes x veteranos",
            f"Na média dos anos, veteranos ficam {diff_veterano:+.2f} ponto(s) acima dos ingressantes, sugerindo ganho com permanência no programa.",
            chart_tipo,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_nivel = (
            alt.Chart(ida_nivel)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("IDA:Q", title="IDA médio"),
                color=alt.Color("nivel_label:N", title="Nível"),
                tooltip=[
                    alt.Tooltip("nivel_label:N", title="Nível"),
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("IDA:Q", title="IDA médio", format=".2f"),
                ],
            )
            .properties(height=320, title="IDA por nível ao longo do tempo")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "IDA por nível ao longo do tempo",
            f"O nível 3 registra IDA médio de {nivel_3:.2f}, contra {outros:.2f} nos demais níveis, mantendo uma lacuna de {abs(nivel_3 - outros):.2f} ponto(s).",
            chart_nivel,
        )

    with col4:
        chart_ian = (
            alt.Chart(ida_ian)
            .mark_bar(color="#0f766e")
            .encode(
                x=alt.X("grupo_ian:N", sort=GRUPOS_IAN, title="Grupo de IAN"),
                y=alt.Y("IDA:Q", title="IDA médio"),
                tooltip=[
                    alt.Tooltip("grupo_ian:N", title="Grupo"),
                    alt.Tooltip("IDA:Q", title="IDA médio", format=".2f"),
                ],
            )
            .properties(height=320, title="Defasagem e desempenho não são a mesma coisa")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Defasagem e desempenho não são a mesma coisa",
            f"Alunos adequados no IAN têm IDA médio de {adequado:.2f}, contra {moderada:.2f} nos moderadamente defasados, uma diferença de {adequado - moderada:.2f} ponto(s).",
            chart_ian,
        )
