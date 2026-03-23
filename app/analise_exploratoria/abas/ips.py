from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, FAIXAS_IPS
from analise_exploratoria.dados import carregar_analytics_ips


def renderizar_ips(df: pd.DataFrame | None = None, pares: pd.DataFrame | None = None) -> None:
    """Renderiza a aba de IPS consumindo o parquet analítico do notebook."""
    st.subheader("IPS — Indicador Psicossocial")
    st.markdown(
        "Avalia aspectos comportamentais, emocionais e sociais do aluno a partir da observação da equipe de psicologia."
    )
    st.caption(
        "Fórmula: IPS = soma das pontuações dos avaliadores / número de avaliadores. "
        "As avaliações são feitas por psicólogos e consideram aspectos comportamentais, emocionais e sociais."
    )

    df_ips = carregar_analytics_ips()
    cores_anos = {
        2022: "#dc2626",
        2023: "#f59e0b",
        2024: "#2563eb",
    }
    cores_anos_suaves = {
        2022: "#fee2e2",
        2023: "#fef3c7",
        2024: "#dbeafe",
    }
    nomes_indicadores_delta = {
        "delta_IDA": "Delta de IDA",
        "delta_IEG": "Delta de IEG",
    }
    nomes_indicadores_queda = {
        "caiu_IDA": "Queda forte em IDA",
        "caiu_IEG": "Queda forte em IEG",
    }
    faixas_ips_distribuicao = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    df_ips["faixa_ips_distribuicao"] = pd.cut(
        df_ips["IPS"],
        bins=[0, 2, 4, 6, 8, 10.0001],
        labels=faixas_ips_distribuicao,
        include_lowest=True,
        right=False,
    )
    ips_faixa = (
        df_ips.dropna(subset=["IPS", "faixa_ips_distribuicao"])
        .groupby(["ano", "faixa_ips_distribuicao"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    ips_faixa["participacao"] = ips_faixa.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    turma_por_ano = (
        df_ips[df_ips["IPS"].notna()]
        .groupby(["ano", "turma"])["IPS"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "ips_medio", "std": "desvio", "count": "n"})
    )
    turma_por_ano["desvio"] = turma_por_ano["desvio"].fillna(0)
    turma_por_ano["avaliacao_uniforme"] = np.where(turma_por_ano["desvio"] == 0, "Desvio zero", "Com variação")
    turmas_desvio_zero = (
        turma_por_ano[turma_por_ano["desvio"] == 0]
        .sort_values(["ano", "turma"])
        .copy()
    )
    tabela_desvio_zero = turmas_desvio_zero[["ano", "turma", "ips_medio", "n"]].rename(
        columns={
            "ano": "Ano",
            "turma": "Turma",
            "ips_medio": "IPS médio",
            "n": "Alunos",
        }
    )

    def destacar_linha_por_ano(linha: pd.Series) -> list[str]:
        ano = linha["Ano"]
        cor_fundo = cores_anos_suaves.get(ano, "#ffffff")
        return [f"background-color: {cor_fundo}"] * len(linha)

    tabela_desvio_zero_estilizada = (
        tabela_desvio_zero.style
        .apply(destacar_linha_por_ano, axis=1)
        .format({"IPS médio": "{:.2f}"})
    )

    turma_2023 = turma_por_ano[turma_por_ano["ano"] == 2023].sort_values("ips_medio").copy()

    turma_evolucao = (
        df_ips[df_ips["ano"].isin([2023, 2024]) & df_ips["IPS"].notna()]
        .pivot_table(index="turma", columns="ano", values="IPS", aggfunc="mean")
        .dropna()
        .reset_index()
    )
    turma_evolucao["delta"] = turma_evolucao[2024] - turma_evolucao[2023]
    turma_evolucao_longa = turma_evolucao.melt(id_vars=["turma", "delta"], value_vars=[2023, 2024], var_name="ano", value_name="ips_medio")

    pares_ips = df_ips.dropna(subset=["transicao", "faixa_IPS"]).copy()
    leituras_temporais = {}
    for transicao in ["2022->2023", "2023->2024"]:
        ips_trans = pares_ips[pares_ips["transicao"] == transicao].copy()
        base_faixa = (
            ips_trans.groupby("faixa_IPS")
            .size()
            .reindex(FAIXAS_IPS)
            .reset_index(name="alunos_faixa")
        )
        delta_df = (
            ips_trans.groupby("faixa_IPS")[["delta_IDA", "delta_IEG"]]
            .mean()
            .reindex(FAIXAS_IPS)
            .reset_index()
            .melt(id_vars="faixa_IPS", var_name="indicador", value_name="delta")
        )
        delta_df = delta_df.merge(base_faixa, on="faixa_IPS", how="left")
        delta_df["indicador_label"] = delta_df["indicador"].map(nomes_indicadores_delta).fillna(delta_df["indicador"])
        queda_df = (
            ips_trans.groupby("faixa_IPS")[["caiu_IDA", "caiu_IEG"]]
            .mean()
            .reindex(FAIXAS_IPS)
            .reset_index()
            .melt(id_vars="faixa_IPS", var_name="indicador", value_name="taxa")
        )
        queda_df = queda_df.merge(base_faixa, on="faixa_IPS", how="left")
        queda_df["indicador_label"] = queda_df["indicador"].map(nomes_indicadores_queda).fillna(queda_df["indicador"])
        leituras_temporais[transicao] = {
            "ips_trans": ips_trans,
            "delta_df": delta_df,
            "queda_df": queda_df,
            "corr_delta_ida": ips_trans["IPS"].corr(ips_trans["delta_IDA"]),
            "corr_delta_ieg": ips_trans["IPS"].corr(ips_trans["delta_IEG"]),
            "maior_queda_ida": delta_df.iloc[:0],
        }
        leituras_temporais[transicao]["maior_queda_ida"] = (
            queda_df[queda_df["indicador"] == "caiu_IDA"].sort_values("taxa", ascending=False).iloc[0]
        )
        leituras_temporais[transicao]["maior_queda_ieg"] = (
            queda_df[queda_df["indicador"] == "caiu_IEG"].sort_values("taxa", ascending=False).iloc[0]
        )

    zero_std = (turma_2023["desvio"] == 0).sum()
    zero_por_ano = turma_por_ano.assign(desvio_zero=turma_por_ano["desvio"] == 0).groupby("ano")["desvio_zero"].sum().reindex(ANOS, fill_value=0)
    subiram = (turma_evolucao["delta"] > 0).mean()
    ips_por_ano = df_ips.groupby("ano")["IPS"].mean().reindex(ANOS)
    faixa_topo_2022 = ips_faixa[ips_faixa["ano"] == 2022].sort_values("participacao", ascending=False).iloc[0]
    faixa_topo_2024 = ips_faixa[ips_faixa["ano"] == 2024].sort_values("participacao", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        chart_dist = (
            alt.Chart(ips_faixa)
            .mark_bar()
            .encode(
                x=alt.X("ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
                color=alt.Color(
                    "faixa_ips_distribuicao:N",
                    title="Faixa de IPS",
                    sort=faixas_ips_distribuicao,
                    scale=alt.Scale(range=["#dc2626", "#f97316", "#facc15", "#65a30d", "#15803d"]),
                ),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("faixa_ips_distribuicao:N", title="Faixa de IPS"),
                    alt.Tooltip("quantidade:Q", title="Alunos"),
                    alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                ],
            )
            .properties(height=320, title="Distribuição do IPS por ano")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Distribuição do IPS por ano",
            (
                f"O IPS médio sai de {ips_por_ano.loc[2022]:.2f} em 2022 para {ips_por_ano.loc[2023]:.2f} em 2023 "
                f"e {ips_por_ano.loc[2024]:.2f} em 2024; a faixa mais comum sai de `{faixa_topo_2022['faixa_ips_distribuicao']}` "
                f"em 2022 ({faixa_topo_2022['participacao']:.1%}) para `{faixa_topo_2024['faixa_ips_distribuicao']}` "
                f"em 2024 ({faixa_topo_2024['participacao']:.1%}), e em 2023 {zero_std} turmas tiveram desvio zero."
            ),
            chart_dist,
        )

    with col2:
        chart_evolucao = (
            alt.Chart(turma_evolucao_longa)
            .mark_line(point=True, opacity=0.45)
            .encode(
                x=alt.X("ano:O", sort=[2023, 2024], title="Ano"),
                y=alt.Y("ips_medio:Q", title="IPS médio"),
                detail="turma:N",
                color=alt.condition(alt.datum.delta > 0, alt.value("#16a34a"), alt.value("#dc2626")),
                tooltip=[
                    alt.Tooltip("turma:N", title="Turma"),
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("ips_medio:Q", title="IPS médio", format=".2f"),
                ],
            )
            .properties(height=320, title="Evolução do IPS por turma (2023->2024)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Evolução do IPS por turma (2023->2024)",
            (
                "Cada linha representa uma turma presente nos dois anos, mostrando como o IPS médio mudou de 2023 para 2024. "
                f"No conjunto, {subiram:.1%} das turmas sobem no período; quando muitas linhas avançam ao mesmo tempo, "
                "isso sugere uma mudança geral no padrão de avaliação, e não necessariamente uma melhora real e homogênea de todas as turmas."
            ),
            chart_evolucao,
        )

    col3, col4 = st.columns(2)
    with col3:
        chart_turma = (
            alt.Chart(zero_por_ano.reset_index().rename(columns={"ano": "Ano", "desvio_zero": "turmas_com_desvio_zero"}))
            .mark_bar()
            .encode(
                x=alt.X("Ano:O", sort=ANOS, title="Ano"),
                y=alt.Y("turmas_com_desvio_zero:Q", title="Turmas com desvio zero"),
                color=alt.Color(
                    "Ano:O",
                    title=None,
                    legend=None,
                    scale=alt.Scale(
                        domain=ANOS,
                        range=[cores_anos[2022], cores_anos[2023], cores_anos[2024]],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("Ano:O", title="Ano"),
                    alt.Tooltip("turmas_com_desvio_zero:Q", title="Turmas"),
                ],
            )
            .properties(height=320, title="Turmas com desvio padrão zero no IPS")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Turmas com desvio padrão zero no IPS",
            (
                "O gráfico mostra quantas turmas, em cada ano, tiveram todos os alunos avaliados com exatamente o mesmo IPS. "
                f"Esse padrão aparece em {zero_por_ano.loc[2022]} turma(s) em 2022, {zero_por_ano.loc[2023]} em 2023 "
                f"e {zero_por_ano.loc[2024]} em 2024. Isso deve ser tratado como um alerta: é muito improvável que todos "
                "os alunos de uma mesma turma tenham exatamente o mesmo resultado, e esse comportamento pode indicar "
                "problemas de preenchimento ou padronização indevida, comprometendo a credibilidade da avaliação."
            ),
            chart_turma,
        )

    with col4:
        st.markdown("#### Detalhamento das Turmas com Desvio Zero")
        st.markdown(
            "*A tabela abaixo mostra em quais anos e turmas esse padrão ocorreu, além do IPS médio registrado e do número de alunos avaliados.*"
        )
        st.dataframe(tabela_desvio_zero_estilizada, use_container_width=True, hide_index=True, height=320)

    col5, col6 = st.columns(2)
    with col5:
        leitura_2022_2023 = leituras_temporais["2022->2023"]
        chart_delta = (
            alt.Chart(leitura_2022_2023["delta_df"])
            .mark_bar()
            .encode(
                x=alt.X("faixa_IPS:N", sort=FAIXAS_IPS, title="Faixa de IPS em 2022"),
                y=alt.Y("delta:Q", title="Delta no ano seguinte"),
                color=alt.Color("indicador_label:N", title=None, scale=alt.Scale(range=["#dc2626", "#f59e0b"])),
                xOffset="indicador_label:N",
                tooltip=[
                    alt.Tooltip("faixa_IPS:N", title="Faixa"),
                    alt.Tooltip("indicador_label:N", title="Indicador"),
                    alt.Tooltip("delta:Q", title="Delta", format=".2f"),
                    alt.Tooltip("alunos_faixa:Q", title="Alunos na faixa"),
                ],
            )
            .properties(height=320, title="IPS atual x delta futuro (2022->2023)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "IPS atual x delta futuro (2022->2023)",
            (
                f"Na transição 2022->2023, o IPS absoluto tem poder muito fraco para antecipar queda futura: "
                f"r={leitura_2022_2023['corr_delta_ida']:.3f} com delta de IDA e "
                f"r={leitura_2022_2023['corr_delta_ieg']:.3f} com delta de IEG. "
                "Use o tooltip para verificar quantos alunos existem em cada faixa."
            ),
            chart_delta,
        )

    with col6:
        leitura_2023_2024 = leituras_temporais["2023->2024"]
        chart_delta_2 = (
            alt.Chart(leitura_2023_2024["delta_df"])
            .mark_bar()
            .encode(
                x=alt.X("faixa_IPS:N", sort=FAIXAS_IPS, title="Faixa de IPS em 2023"),
                y=alt.Y("delta:Q", title="Delta no ano seguinte"),
                color=alt.Color("indicador_label:N", title=None, scale=alt.Scale(range=["#dc2626", "#f59e0b"])),
                xOffset="indicador_label:N",
                tooltip=[
                    alt.Tooltip("faixa_IPS:N", title="Faixa"),
                    alt.Tooltip("indicador_label:N", title="Indicador"),
                    alt.Tooltip("delta:Q", title="Delta", format=".2f"),
                    alt.Tooltip("alunos_faixa:Q", title="Alunos na faixa"),
                ],
            )
            .properties(height=320, title="IPS atual x delta futuro (2023->2024)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "IPS atual x delta futuro (2023->2024)",
            (
                f"Na transição 2023->2024, o IPS absoluto continua com baixo poder de antecipação: "
                f"r={leitura_2023_2024['corr_delta_ida']:.3f} com delta de IDA e "
                f"r={leitura_2023_2024['corr_delta_ieg']:.3f} com delta de IEG. "
                "Use o tooltip para verificar quantos alunos existem em cada faixa."
            ),
            chart_delta_2,
        )

    col7, col8 = st.columns(2)
    with col7:
        chart_queda_1 = (
            alt.Chart(leitura_2022_2023["queda_df"])
            .mark_bar()
            .encode(
                x=alt.X("faixa_IPS:N", sort=FAIXAS_IPS, title="Faixa de IPS em 2022"),
                y=alt.Y("taxa:Q", title="% com queda > 1 ponto", axis=alt.Axis(format="%")),
                color=alt.Color("indicador_label:N", title=None, scale=alt.Scale(range=["#dc2626", "#f59e0b"])),
                xOffset="indicador_label:N",
                tooltip=[
                    alt.Tooltip("faixa_IPS:N", title="Faixa"),
                    alt.Tooltip("indicador_label:N", title="Indicador"),
                    alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                    alt.Tooltip("alunos_faixa:Q", title="Alunos na faixa"),
                ],
            )
            .properties(height=320, title="Quedas fortes no ano seguinte (2022->2023)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Quedas fortes no ano seguinte (2022->2023)",
            (
                "Aqui, `queda forte` significa recuo superior a 1 ponto no indicador de um ano para o outro. "
                f"Em 2022->2023, a maior taxa de queda forte em IDA aparece na faixa "
                f"`{leitura_2022_2023['maior_queda_ida']['faixa_IPS']}` ({leitura_2022_2023['maior_queda_ida']['taxa']:.1%}), "
                f"enquanto em IEG o pico está em `{leitura_2022_2023['maior_queda_ieg']['faixa_IPS']}` "
                f"({leitura_2022_2023['maior_queda_ieg']['taxa']:.1%}). "
                "Use o tooltip para verificar quantos alunos compõem cada faixa."
            ),
            chart_queda_1,
        )

    with col8:
        chart_queda_2 = (
            alt.Chart(leitura_2023_2024["queda_df"])
            .mark_bar()
            .encode(
                x=alt.X("faixa_IPS:N", sort=FAIXAS_IPS, title="Faixa de IPS em 2023"),
                y=alt.Y("taxa:Q", title="% com queda > 1 ponto", axis=alt.Axis(format="%")),
                color=alt.Color("indicador_label:N", title=None, scale=alt.Scale(range=["#dc2626", "#f59e0b"])),
                xOffset="indicador_label:N",
                tooltip=[
                    alt.Tooltip("faixa_IPS:N", title="Faixa"),
                    alt.Tooltip("indicador_label:N", title="Indicador"),
                    alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                    alt.Tooltip("alunos_faixa:Q", title="Alunos na faixa"),
                ],
            )
            .properties(height=320, title="Quedas fortes no ano seguinte (2023->2024)")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Quedas fortes no ano seguinte (2023->2024)",
            (
                "Aqui, `queda forte` significa recuo superior a 1 ponto no indicador de um ano para o outro. "
                f"Em 2023->2024, a maior taxa de queda forte em IDA aparece na faixa "
                f"`{leitura_2023_2024['maior_queda_ida']['faixa_IPS']}` ({leitura_2023_2024['maior_queda_ida']['taxa']:.1%}), "
                f"enquanto em IEG o pico está em `{leitura_2023_2024['maior_queda_ieg']['faixa_IPS']}` "
                f"({leitura_2023_2024['maior_queda_ieg']['taxa']:.1%}). "
                "Use o tooltip para verificar quantos alunos compõem cada faixa."
            ),
            chart_queda_2,
        )
