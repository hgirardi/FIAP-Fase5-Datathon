from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, CORES_COHERENCIA, NIVEIS
from analise_exploratoria.dados import carregar_analytics_iaa


def renderizar_iaa() -> None:
    """Renderiza a aba de IAA consumindo o parquet analítico do notebook."""
    st.subheader("IAA — Autoavaliação")
    st.markdown(
        "Registra a autoavaliação do aluno sobre si mesmo, seus estudos, suas relações e seu vínculo com a Associação."
    )
    st.caption(
        "Fórmula: IAA = soma das pontuações das respostas do estudante / número total de perguntas. "
        "As perguntas são avaliadas de 0 a 10."
    )

    df_iaa = carregar_analytics_iaa()
    faixas_iaa = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    df_iaa["faixa_iaa"] = pd.cut(
        df_iaa["IAA"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_iaa,
        include_lowest=True,
        right=False,
    )
    iaa_faixa = (
        df_iaa.dropna(subset=["IAA", "faixa_iaa"])
        .groupby(["ano", "faixa_iaa"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    iaa_faixa["participacao"] = iaa_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    iaa_ida = df_iaa.dropna(subset=["IAA", "IDA"]).copy()
    iaa_ida_faixa = (
        iaa_ida.groupby("faixa_iaa", observed=False)["IDA"]
        .mean()
        .reindex(faixas_iaa)
        .reset_index()
    )
    coerencia = iaa_ida.groupby(["ano", "coerencia_iaa"]).size().reset_index(name="quantidade")
    coerencia = coerencia[coerencia["coerencia_iaa"] != "Sem dado"].copy()
    coerencia["participacao"] = coerencia.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    gap_nivel = (
        iaa_ida.dropna(subset=["nivel_ordem"])
        .groupby(["nivel_label", "nivel_ordem"])["gap_iaa_ida"]
        .median()
        .reset_index(name="gap_mediano")
        .sort_values("nivel_ordem")
    )

    trio = df_iaa.dropna(subset=["IAA", "IDA", "IEG", "coerencia_combinada"]).copy()
    trio_count = trio["coerencia_combinada"].value_counts(normalize=True).rename_axis("grupo").reset_index(name="participacao")
    corr_iaa_ida = iaa_ida["IAA"].corr(iaa_ida["IDA"])
    corr_iaa_ieg = trio["IAA"].corr(trio["IEG"])
    superestima = coerencia[coerencia["coerencia_iaa"].isin(["Superestima leve (1-2)", "Superestima (>2)"])]
    superestima_pct = superestima.groupby("ano")["participacao"].sum().mean()
    ambos = trio_count[trio_count["grupo"] == "Superestima ambos"]["participacao"].iloc[0]
    nivel_3_gap = gap_nivel.loc[gap_nivel["nivel_label"] == "3", "gap_mediano"].iloc[0]
    gap_melhor = gap_nivel["gap_mediano"].min()
    iaa_por_ano = df_iaa.groupby("ano")["IAA"].mean().reindex(ANOS)
    faixa_topo_2022 = iaa_faixa[iaa_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2024 = iaa_faixa[iaa_faixa["ano"] == 2024].sort_values("participacao", ascending=False).iloc[0]
    ano_mais_superestima = (
        superestima.groupby("ano")["participacao"].sum().sort_values(ascending=False).index[0]
        if not superestima.empty
        else None
    )
    faixa_maior_ida = iaa_ida_faixa.sort_values("IDA", ascending=False).iloc[0]
    faixa_menor_ida = iaa_ida_faixa.sort_values("IDA", ascending=True).iloc[0]
    superestima_por_ano = (
        superestima.groupby("ano")["participacao"].sum().reindex(ANOS)
        if not superestima.empty
        else pd.Series(index=ANOS, dtype=float)
    )
    superestima_severa = (
        coerencia[coerencia["coerencia_iaa"] == "Superestima (>2)"]
        .groupby("ano")["participacao"]
        .sum()
        .reindex(ANOS, fill_value=0)
    )

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(iaa_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_iaa:N",
                    title="Faixa de IAA",
                    sort=faixas_iaa,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_iaa:N", title="Faixa de IAA"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IAA por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IAA por ano",
            (
                f"O IAA médio vai de {iaa_por_ano.loc[2022]:.2f} em 2022 para {iaa_por_ano.loc[2024]:.2f} em 2024; "
                f"em 2022 a faixa mais comum é `{faixa_topo_2022['faixa_iaa']}` ({faixa_topo_2022['participacao']:.1%}) "
                f"e, em 2024, ela passa a ser `{faixa_topo_2024['faixa_iaa']}` ({faixa_topo_2024['participacao']:.1%}). "
                f"Em média, {superestima_pct:.1%} dos alunos se superestimam, com maior concentração desse comportamento em "
                f"{ano_mais_superestima}."
            ),
            chart_dist,
        )

    with col2:
        chart_relacao = (
            alt.Chart(iaa_ida_faixa)
            .mark_bar(color="#7c3aed")
            .encode(
                x=alt.X("faixa_iaa:N", sort=faixas_iaa, title="Faixa de IAA"),
                y=alt.Y("IDA:Q", title="IDA médio"),
                tooltip=[
                    alt.Tooltip("faixa_iaa:N", title="Faixa de IAA"),
                    alt.Tooltip("IDA:Q", title="IDA médio", format=".2f"),
                ],
            )
            .properties(height=320, title="IAA x IDA")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "IAA x IDA",
            (
                f"Se a autoavaliação explicasse bem o desempenho, esperaríamos uma subida clara das barras conforme o IAA aumenta. "
                f"A leitura real é mais instável: a maior média de IDA aparece na faixa `{faixa_maior_ida['faixa_iaa']}` ({faixa_maior_ida['IDA']:.2f}) "
                f"e a menor na faixa `{faixa_menor_ida['faixa_iaa']}` ({faixa_menor_ida['IDA']:.2f}), com correlação fraca entre IAA e IDA (r={corr_iaa_ida:.3f})."
            ),
            chart_relacao,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_coerencia = (
            alt.Chart(coerencia)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "coerencia_iaa:N",
                    title="Coerência",
                    scale=alt.Scale(
                        domain=list(CORES_COHERENCIA.keys()),
                        range=list(CORES_COHERENCIA.values()),
                    ),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("coerencia_iaa:N", title="Coerência"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Coerência IAA x IDA por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Coerência IAA x IDA por ano",
            (
                "O gráfico separa alunos coerentes, com subestimação e com dois níveis de superestimação: "
                "`Superestima leve (1-2)` indica autoavaliação de 1 a 2 pontos acima do desempenho real, "
                "enquanto `Superestima (>2)` indica uma distância ainda maior. "
                f"Somando as duas faixas, a superestimação vai de {superestima_por_ano.loc[2022]:.1%} em 2022 "
                f"para {superestima_por_ano.loc[2024]:.1%} em 2024; dentro desse total, a parcela mais severa "
                f"fica em {superestima_severa.loc[2024]:.1%} em 2024."
            ),
            chart_coerencia,
        )

    with col4:
        chart_gap = (
            alt.Chart(gap_nivel)
            .mark_bar()
            .encode(
                x=alt.X("nivel_label:N", sort=NIVEIS, title="Nível"),
                y=alt.Y("gap_mediano:Q", title="Gap mediano (IAA - IDA)"),
                color=alt.condition(alt.datum.nivel_label == "3", alt.value("#dc2626"), alt.value("#2563eb")),
                tooltip=[
                    alt.Tooltip("nivel_label:N", title="Nível"),
                    alt.Tooltip("gap_mediano:Q", title="Gap mediano", format=".2f"),
                ],
            )
            .properties(height=320, title="Superestimação por nível")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Superestimação por nível",
            (
                "O gap representa a diferença entre a autoavaliação do aluno (IAA) e seu desempenho acadêmico observado (IDA): "
                "quanto maior o valor, maior a superestimação. "
                f"O nível 3 tem gap mediano de {nivel_3_gap:.2f}, acima do melhor nível observado ({gap_melhor:.2f}), "
                "concentrando a maior distorção entre percepção e resultado."
            ),
            chart_gap,
        )
