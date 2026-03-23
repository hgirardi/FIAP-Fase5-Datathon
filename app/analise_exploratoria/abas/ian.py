from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.dados import carregar_analytics_ian
from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, CORES_ESCOLA, NIVEIS, ORDEM_ESCOLAS


def renderizar_ian() -> None:
    """Renderiza a aba de IAN consumindo o parquet analítico do notebook."""
    st.subheader("IAN — Adequação de Nível")
    st.markdown(
        "Registra a defasagem de aprendizagem do aluno por meio da comparação entre sua fase atual na Associação e a fase ideal esperada para sua idade."
    )
    st.caption(
        "Fórmula: D = Fase Efetiva - Fase Ideal. "
        "Dados necessários: fase atual do estudante na Associação e fase ideal conforme a idade."
    )

    df_ian = carregar_analytics_ian()

    # O mapa de calor usa a defasagem média para destacar níveis mais críticos por ano.
    calor = (
        df_ian.dropna(subset=["defasagem", "nivel_ordem"])
        .groupby(["nivel_label", "nivel_ordem", "ano"])["defasagem"]
        .mean()
        .reset_index(name="defasagem_media")
        .sort_values(["nivel_ordem", "ano"])
    )

    # As transições consecutivas permitem comparar os sinais do ano anterior entre grupos.
    anterior = df_ian[df_ian["transicao_ian"].isin(["Piorou", "Manteve adequado"])].copy()
    compara = (
        anterior.groupby("transicao_ian")[["IDA", "IEG", "IAA", "IPS", "IPP", "IPV"]]
        .mean()
        .T.reset_index()
        .rename(columns={"index": "indicador"})
        .melt(id_vars="indicador", var_name="grupo", value_name="media")
    )

    perfil_real = (
        df_ian[df_ian["defasagem_cat"].notna()]
        .groupby(["ano", "defasagem_cat"])
        .size()
        .reset_index(name="quantidade")
    )
    ordem_defasagem = ["Adiantado", "Na fase", "Leve (-1)", "Moderada (-2)", "Severa (< -2)"]
    perfil_real = perfil_real[perfil_real["defasagem_cat"].isin(ordem_defasagem)].copy()
    perfil_real["participacao"] = perfil_real.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    defasagem_escola = (
        df_ian[df_ian["tipo_escola_macro"].isin(ORDEM_ESCOLAS)]
        .groupby(["ano", "tipo_escola_macro"])["em_defasagem"]
        .mean()
        .reset_index(name="taxa")
    )

    piora = anterior[anterior["transicao_ian"] == "Piorou"]
    adequado = anterior[anterior["transicao_ian"] == "Manteve adequado"]
    diff_ipp = piora["IPP"].mean() - adequado["IPP"].mean()
    calor_2024 = calor[calor["ano"] == 2024].sort_values("defasagem_media")
    pior_nivel_2024 = calor_2024.iloc[0]
    melhor_nivel_2024 = calor_2024.iloc[-1]
    ipp_piora = piora["IPP"].mean()
    ipp_adequado = adequado["IPP"].mean()
    perfil_2024 = perfil_real[perfil_real["ano"] == 2024].set_index("defasagem_cat")["participacao"]
    publica_2024 = defasagem_escola[
        (defasagem_escola["ano"] == 2024) & (defasagem_escola["tipo_escola_macro"] == "Pública")
    ]["taxa"].iloc[0]
    privada_2024 = defasagem_escola[
        (defasagem_escola["ano"] == 2024) & (defasagem_escola["tipo_escola_macro"] == "Privada")
    ]["taxa"].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_perfil = (
            alt.Chart(perfil_real)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "defasagem_cat:N",
                    title="Perfil de defasagem",
                    sort=ordem_defasagem,
                    scale=alt.Scale(
                        domain=ordem_defasagem,
                        range=["#2563eb", "#16a34a", "#facc15", "#f97316", "#dc2626"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("defasagem_cat:N", title="Perfil"),
                    alt.Tooltip("quantidade:Q", title="Registros"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Perfil real da defasagem por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Perfil real da defasagem por ano",
            (
                f"Em 2024, {perfil_2024.get('Na fase', 0) + perfil_2024.get('Adiantado', 0):.1%} dos alunos estão na fase ou adiantados, "
                f"{perfil_2024.get('Leve (-1)', 0):.1%} têm defasagem leve, {perfil_2024.get('Moderada (-2)', 0):.1%} moderada "
                f"e {perfil_2024.get('Severa (< -2)', 0):.1%} severa."
            ),
            chart_perfil,
        )

    with col2:
        chart_calor = (
            alt.Chart(calor)
            .mark_rect()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("nivel_label:N", sort=NIVEIS, title="Nível"),
                color=alt.Color("defasagem_media:Q", title="Defasagem média", scale=alt.Scale(scheme="redyellowgreen", domain=[-1, 1])),
                tooltip=[
                    alt.Tooltip("nivel_label:N", title="Nível"),
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("defasagem_media:Q", title="Defasagem média", format=".2f"),
                ],
            )
            .properties(height=320, title="Defasagem média por nível")
        )
        texto = (
            alt.Chart(calor)
            .mark_text(size=11, color="#111827")
            .encode(
                x=alt.X("ano:O", sort=ANOS),
                y=alt.Y("nivel_label:N", sort=NIVEIS),
                text=alt.Text("defasagem_media:Q", format=".2f"),
            )
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Defasagem média por nível",
            (
                f"Valores negativos indicam atraso em relação à fase ideal, zero indica alinhamento e valores positivos indicam alunos acima do esperado. "
                f"Em 2024, o nível mais crítico é `{pior_nivel_2024['nivel_label']}` com média de {pior_nivel_2024['defasagem_media']:.2f}, "
                f"enquanto `{melhor_nivel_2024['nivel_label']}` aparece com {melhor_nivel_2024['defasagem_media']:.2f}."
            ),
            chart_calor + texto,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_escola = (
            alt.Chart(defasagem_escola)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("taxa:Q", title="Taxa em defasagem", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "tipo_escola_macro:N",
                    title="Tipo de escola",
                    sort=ORDEM_ESCOLAS,
                    scale=alt.Scale(domain=ORDEM_ESCOLAS, range=[CORES_ESCOLA[item] for item in ORDEM_ESCOLAS]),
                ),
                xOffset="tipo_escola_macro:N",
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("tipo_escola_macro:N", title="Tipo de escola"),
                    alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                ],
            )
            .properties(height=320, title="Defasagem por tipo de escola")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Defasagem por tipo de escola",
            (
                f"Em 2024, a defasagem atinge {publica_2024:.1%} na escola pública, contra {privada_2024:.1%} na privada, "
                "mostrando que o contexto escolar também ajuda a explicar onde o atraso se concentra."
            ),
            chart_escola,
        )

    with col4:
        chart_compara = (
            alt.Chart(compara)
            .mark_bar()
            .encode(
                x=alt.X("indicador:N", title=None),
                y=alt.Y("media:Q", title="Média no ano anterior"),
                color=alt.Color("grupo:N", title=None, scale=alt.Scale(range=["#dc2626", "#16a34a"])),
                xOffset="grupo:N",
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("grupo:N", title="Grupo"),
                    alt.Tooltip("media:Q", title="Média", format=".2f"),
                ],
            )
            .properties(height=320, title="Quem piora já dava sinais no ano anterior")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Quem piora já dava sinais no ano anterior",
            (
                f"Antes da piora no IAN, esse grupo já tinha IPP médio de {ipp_piora:.2f}, contra {ipp_adequado:.2f} "
                f"entre os que permanecem adequados, uma diferença de {abs(diff_ipp):.2f} ponto(s)."
            ),
            chart_compara,
        )
