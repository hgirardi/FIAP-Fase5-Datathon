from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS
from analise_exploratoria.dados import carregar_analytics_ipv


def renderizar_ipv(df: pd.DataFrame | None = None, pares: pd.DataFrame | None = None) -> None:
    """Renderiza a aba de IPV consumindo o parquet analítico do notebook."""
    st.subheader("IPV — Ponto de Virada")
    st.markdown(
        "Avalia a evolução do aluno em dimensões ligadas à sua transformação pessoal, integração à Associação, desenvolvimento emocional e potencial acadêmico."
    )
    st.caption(
        "Fórmula: IPV = análises longitudinais de progresso acadêmico, engajamento e desenvolvimento emocional."
    )

    ipv_df = carregar_analytics_ipv()
    faixas_ipv = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    ipv_df["faixa_ipv"] = pd.cut(
        ipv_df["IPV"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_ipv,
        include_lowest=True,
        right=False,
    )
    ipv_faixa = (
        ipv_df.dropna(subset=["IPV", "faixa_ipv"])
        .groupby(["ano", "faixa_ipv"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    ipv_faixa["participacao"] = ipv_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())
    correlacoes_gerais = []
    correlacoes_ano = []
    correlacoes_temporais = []
    indicadores = ["IDA", "IEG", "IAA", "IPS", "IPP", "IAN"]

    for indicador in indicadores:
        validos = ipv_df[["IPV", indicador]].dropna()
        if not validos.empty:
            correlacoes_gerais.append({"indicador": indicador, "correlacao": validos["IPV"].corr(validos[indicador])})
        for ano in ANOS:
            validos_ano = ipv_df[ipv_df["ano"] == ano][["IPV", indicador]].dropna()
            if len(validos_ano) > 10:
                correlacoes_ano.append(
                    {
                        "ano": ano,
                        "indicador": indicador,
                        "correlacao": validos_ano["IPV"].corr(validos_ano[indicador]),
                    }
                )
        validos_futuro = ipv_df[[indicador, "IPV_proximo", "transicao"]].dropna()
        if len(validos_futuro) > 10:
            correlacoes_temporais.append(
                {
                    "indicador": indicador,
                    "tipo": "Ano seguinte",
                    "correlacao": validos_futuro[indicador].corr(validos_futuro["IPV_proximo"]),
                }
            )
        validos_mesmo = ipv_df[["IPV", indicador]].dropna()
        if len(validos_mesmo) > 10:
            correlacoes_temporais.append(
                {
                    "indicador": indicador,
                    "tipo": "Mesmo ano",
                    "correlacao": validos_mesmo["IPV"].corr(validos_mesmo[indicador]),
                }
            )

    geral_df = pd.DataFrame(correlacoes_gerais).sort_values("correlacao", ascending=False)
    ano_df = pd.DataFrame(correlacoes_ano)
    temporal_df = pd.DataFrame(correlacoes_temporais)

    transicoes_df: dict[str, pd.DataFrame] = {}
    for transicao in ["2022->2023", "2023->2024"]:
        linhas_transicao = []
        pares_transicao = ipv_df[ipv_df["transicao"] == transicao].copy()
        for indicador in indicadores:
            mesmo = pares_transicao[[indicador, "IPV"]].dropna()
            futuro = pares_transicao[[indicador, "IPV_proximo"]].dropna()
            if len(mesmo) > 10:
                linhas_transicao.append(
                    {
                        "indicador": indicador,
                        "tipo": "Mesmo ano",
                        "correlacao": mesmo[indicador].corr(mesmo["IPV"]),
                    }
                )
            if len(futuro) > 10:
                linhas_transicao.append(
                    {
                        "indicador": indicador,
                        "tipo": "Ano seguinte",
                        "correlacao": futuro[indicador].corr(futuro["IPV_proximo"]),
                    }
                )
        transicoes_df[transicao] = pd.DataFrame(linhas_transicao)
    top_indicador = geral_df.iloc[0]
    top_temporal = temporal_df[temporal_df["tipo"] == "Ano seguinte"].sort_values("correlacao", ascending=False).iloc[0]
    medias_ipv = ipv_df.groupby("ano")["IPV"].mean().reindex(ANOS)
    lideres_por_ano = (
        ano_df.sort_values(["ano", "correlacao"], ascending=[True, False])
        .groupby("ano")
        .first()
        .reset_index()
    )
    media_abs_temporal = (
        temporal_df.assign(correlacao_abs=temporal_df["correlacao"].abs())
        .groupby("tipo")["correlacao_abs"]
        .mean()
    )
    top_2022_2023 = transicoes_df["2022->2023"][transicoes_df["2022->2023"]["tipo"] == "Ano seguinte"].sort_values("correlacao", ascending=False).head(2)
    top_2023_2024 = transicoes_df["2023->2024"][transicoes_df["2023->2024"]["tipo"] == "Ano seguinte"].sort_values("correlacao", ascending=False).head(2)
    faixa_topo_2022 = ipv_faixa[ipv_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2024 = ipv_faixa[ipv_faixa["ano"] == 2024].sort_values("participacao", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(ipv_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_ipv:N",
                    title="Faixa de IPV",
                    sort=faixas_ipv,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_ipv:N", title="Faixa de IPV"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IPV por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IPV por ano",
            (
                f"O IPV médio sai de {medias_ipv.loc[2022]:.2f} em 2022 para {medias_ipv.loc[2023]:.2f} em 2023 "
                f"e retorna para {medias_ipv.loc[2024]:.2f} em 2024; a faixa mais comum sai de `{faixa_topo_2022['faixa_ipv']}` "
                f"em 2022 ({faixa_topo_2022['participacao']:.1%}) para `{faixa_topo_2024['faixa_ipv']}` em 2024 "
                f"({faixa_topo_2024['participacao']:.1%}), mostrando pico em 2023 e recuo no ano seguinte."
            ),
            chart_dist,
        )

    with col2:
        chart_corr = (
            alt.Chart(geral_df)
            .mark_bar()
            .encode(
                x=alt.X("correlacao:Q", title="Correlação com IPV"),
                y=alt.Y("indicador:N", sort="-x", title=None),
                color=alt.condition(alt.datum.correlacao > 0, alt.value("#16a34a"), alt.value("#dc2626")),
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
            )
            .properties(height=320, title="Quem mais caminha com o IPV?")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Quem mais caminha com o IPV?",
            (
                f"Este gráfico resume a relação entre o IPV e os demais indicadores considerando toda a base ao longo dos anos. "
                f"Nessa leitura agregada, `{top_indicador['indicador']}` é o indicador que mais acompanha as variações do IPV, "
                "ou seja, quando um sobe ou desce, o outro tende a se mover na mesma direção com mais frequência do que os demais."
            ),
            chart_corr,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_ano = (
            alt.Chart(ano_df)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("correlacao:Q", title="Correlação"),
                color=alt.Color("indicador:N", title="Indicador"),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
            )
            .properties(height=320, title="Evolução das correlações com IPV")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Evolução das correlações com IPV",
            (
                "Aqui, a relação com o IPV é aberta ano a ano. Em 2022, os maiores destaques são `IDA` e `IEG`; "
                "em 2023, esses dois seguem fortes e `IPP` ganha mais espaço; em 2024, `IPP` vira o principal destaque, "
                "enquanto `IDA` perde força, embora os três continuem entre os sinais mais próximos do IPV."
            ),
            chart_ano,
        )

    with col4:
        chart_temporal = (
            alt.Chart(temporal_df)
            .mark_bar()
            .encode(
                x=alt.X("indicador:N", title=None),
                y=alt.Y("correlacao:Q", title="Correlação"),
                color=alt.Color("tipo:N", title=None, scale=alt.Scale(range=["#2563eb", "#f59e0b"])),
                xOffset="tipo:N",
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("tipo:N", title="Leitura"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
            )
            .properties(height=320, title="Mesmo ano x ano seguinte")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Mesmo ano x ano seguinte",
            (
                "Este gráfico compara duas leituras: a relação dos indicadores com o IPV no mesmo ano e a capacidade desses mesmos sinais de antecipar o IPV do ano seguinte. "
                "Em geral, as barras do mesmo ano aparecem mais altas, mostrando que é mais fácil explicar o presente do que prever o comportamento futuro do indicador."
            ),
            chart_temporal,
        )

    col5, col6 = st.columns(2)
    with col5:
        chart_transicao_1 = (
            alt.Chart(transicoes_df["2022->2023"])
            .mark_bar()
            .encode(
                x=alt.X("indicador:N", title=None),
                y=alt.Y("correlacao:Q", title="Correlação"),
                color=alt.Color("tipo:N", title=None, scale=alt.Scale(range=["#2563eb", "#f59e0b"])),
                xOffset="tipo:N",
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("tipo:N", title="Leitura"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
            )
            .properties(height=320, title="Leitura temporal por transição (2022->2023)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Leitura temporal por transição (2022->2023)",
            (
                f"Na passagem de 2022 para 2023, os sinais que mais ajudam a acompanhar o IPV do ano seguinte são "
                f"`{top_2022_2023.iloc[0]['indicador']}` e `{top_2022_2023.iloc[1]['indicador']}`. "
                "O gráfico também mostra que alguns indicadores perdem bastante força quando saem da leitura do mesmo ano para a tentativa de antecipar o período seguinte."
            ),
            chart_transicao_1,
        )

    with col6:
        chart_transicao_2 = (
            alt.Chart(transicoes_df["2023->2024"])
            .mark_bar()
            .encode(
                x=alt.X("indicador:N", title=None),
                y=alt.Y("correlacao:Q", title="Correlação"),
                color=alt.Color("tipo:N", title=None, scale=alt.Scale(range=["#2563eb", "#f59e0b"])),
                xOffset="tipo:N",
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("tipo:N", title="Leitura"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
            )
            .properties(height=320, title="Leitura temporal por transição (2023->2024)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Leitura temporal por transição (2023->2024)",
            (
                f"Na passagem de 2023 para 2024, os principais sinais para acompanhar o IPV do ano seguinte passam a ser "
                f"`{top_2023_2024.iloc[0]['indicador']}` e `{top_2023_2024.iloc[1]['indicador']}`. "
                "Comparando com a transição anterior, a hierarquia muda, reforçando que os fatores mais próximos do IPV podem variar de um ciclo para outro."
            ),
            chart_transicao_2,
        )
