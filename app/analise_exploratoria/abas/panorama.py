from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import cartao_metrica, classificar_evolucao_pedra, renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, COLUNAS_PEDRA, CORES_ESCOLA, CORES_PEDRA, CORES_TRANSICAO, ORDEM_ESCOLAS, ORDEM_NIVEIS, ORDEM_PEDRAS, PEDRA_PARA_NUMERO


def renderizar_panorama(df: pd.DataFrame, risco_df: pd.DataFrame, base_pedras: pd.DataFrame) -> None:
    st.subheader("Visão Estratégica")

    ano_atual = df[df["ano"] == 2024].copy()
    pedra_2024 = base_pedras["pedra_24"].dropna()
    topazio_pct = (pedra_2024 == "Topázio").mean() if not pedra_2024.empty else np.nan
    risco_alto = (risco_df[risco_df["ano"] == 2024]["score_risco"] >= 4).mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cartao_metrica("Registros", f"{len(df):,}".replace(",", "."))
    with col2:
        cartao_metrica("Alunos únicos", f"{df['RA'].nunique():,}".replace(",", "."))
    with col3:
        cartao_metrica("Defasagem 2024", f"{ano_atual['em_defasagem'].mean():.1%}")
    with col4:
        cartao_metrica("Risco alto 2024", f"{risco_alto:.1%}")

    resumo = (
        df.groupby("ano")
        .agg(
            alunos=("RA", "nunique"),
            defasagem=("em_defasagem", "mean"),
        )
        .reset_index()
    )

    chart_alunos = (
        alt.Chart(resumo)
        .mark_line(point=True, strokeWidth=3, color="#0f766e")
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y("alunos:Q", title="Alunos únicos"),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("alunos:Q", title="Alunos"),
            ],
        )
        .properties(height=320)
    )
    chart_defasagem = (
        alt.Chart(resumo)
        .mark_line(point=True, strokeWidth=3, color="#b45309")
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y("defasagem:Q", title="Taxa de defasagem", axis=alt.Axis(format="%")),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("defasagem:Q", title="Taxa", format=".1%"),
            ],
        )
        .properties(height=320)
    )

    comentario_base = (
        f"A base acompanhada cresce de {int(resumo.loc[resumo['ano'] == 2022, 'alunos'].iloc[0])} para "
        f"{int(resumo.loc[resumo['ano'] == 2024, 'alunos'].iloc[0])} alunos entre 2022 e 2024."
    )
    if pd.notna(topazio_pct):
        comentario_base += f" A participação de Topázio em 2024 chega a {topazio_pct:.1%}, reforçando a melhora recente da composição da base."

    comentario_defasagem = (
        f"A taxa de defasagem cai de {resumo.loc[resumo['ano'] == 2022, 'defasagem'].iloc[0]:.1%} "
        f"para {resumo.loc[resumo['ano'] == 2024, 'defasagem'].iloc[0]:.1%} no mesmo período."
    )

    col5, col6 = st.columns(2)
    with col5:
        renderizar_grafico_com_titulo_subtitulo("Crescimento da base", comentario_base, chart_alunos)
    with col6:
        renderizar_grafico_com_titulo_subtitulo("Queda da defasagem", comentario_defasagem, chart_defasagem)

    base_longa = (
        base_pedras.reset_index()[["RA", "pedra_20", "pedra_21", "pedra_22", "pedra_23", "pedra_24"]]
        .melt(id_vars="RA", var_name="coluna_pedra", value_name="pedra")
        .dropna()
    )
    base_longa["ano"] = base_longa["coluna_pedra"].map(
        {
            "pedra_20": 2020,
            "pedra_21": 2021,
            "pedra_22": 2022,
            "pedra_23": 2023,
            "pedra_24": 2024,
        }
    )
    pedras_ano = base_longa.groupby(["ano", "pedra"]).size().reset_index(name="quantidade")
    pedras_ano["participacao"] = pedras_ano.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    linhas_mobilidade = []
    for inicio, fim in [(2020, 2022), (2022, 2024)]:
        coluna_inicio = COLUNAS_PEDRA[inicio]
        coluna_fim = COLUNAS_PEDRA[fim]
        pares = base_pedras[[coluna_inicio, coluna_fim, "ano_ingresso"]].dropna().copy()
        pares = pares[pares["ano_ingresso"] <= inicio].copy()
        pares["delta"] = pares[coluna_fim].map(PEDRA_PARA_NUMERO) - pares[coluna_inicio].map(PEDRA_PARA_NUMERO)
        pares["evolucao"] = pares["delta"].apply(classificar_evolucao_pedra)
        distribuicao = pares["evolucao"].value_counts(normalize=True)
        for status in ["Caiu", "Manteve", "Subiu"]:
            linhas_mobilidade.append(
                {
                    "transicao": f"{inicio}->{fim}",
                    "evolucao": status,
                    "participacao": distribuicao.get(status, 0.0),
                }
            )
    mobilidade_df = pd.DataFrame(linhas_mobilidade)

    chart_pedras = (
        alt.Chart(pedras_ano)
        .mark_bar()
        .encode(
            x=alt.X("ano:O", title="Ano"),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color(
                "pedra:N",
                title="Pedra",
                scale=alt.Scale(domain=ORDEM_PEDRAS, range=[CORES_PEDRA[item] for item in ORDEM_PEDRAS]),
            ),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("pedra:N", title="Pedra"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    comentario_pedras = "A participação das pedras acompanha a evolução da base e ajuda a visualizar a mudança de perfil dos alunos ao longo do período."

    chart_mobilidade = (
        alt.Chart(mobilidade_df)
        .mark_bar()
        .encode(
            x=alt.X("transicao:N", title="Janela"),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color(
                "evolucao:N",
                title="Mobilidade",
                scale=alt.Scale(
                    domain=["Caiu", "Manteve", "Subiu"],
                    range=[CORES_TRANSICAO[item] for item in ["Caiu", "Manteve", "Subiu"]],
                ),
            ),
            tooltip=[
                alt.Tooltip("transicao:N", title="Janela"),
                alt.Tooltip("evolucao:N", title="Mobilidade"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    comentario_mobilidade = "A mobilidade positiva das pedras mostra recuperação recente e reforça o efeito de acompanhamento ao longo do tempo."

    col7, col8 = st.columns(2)
    with col7:
        renderizar_grafico_com_titulo_subtitulo("Distribuição histórica de pedras (2020-2024)", comentario_pedras, chart_pedras)
    with col8:
        renderizar_grafico_com_titulo_subtitulo("Mobilidade de pedras", comentario_mobilidade, chart_mobilidade)

    score_dist = risco_df.groupby(["ano", "score_risco"]).size().reset_index(name="quantidade")
    score_dist["participacao"] = score_dist.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())
    chart_score = (
        alt.Chart(score_dist)
        .mark_bar(size=22)
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            xOffset=alt.XOffset("score_risco:O", sort=sorted(risco_df["score_risco"].dropna().unique())),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color(
                "score_risco:O",
                title="Score de Fragilidade Acadêmica",
                scale=alt.Scale(
                    domain=sorted(risco_df["score_risco"].dropna().unique()),
                    range=["#16a34a", "#86efac", "#fde68a", "#fb923c", "#ef4444", "#7f1d1d"],
                ),
            ),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("score_risco:O", title="Score de Fragilidade Acadêmica"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
                alt.Tooltip("quantidade:Q", title="Casos"),
            ],
        )
        .properties(height=320)
    )

    comentario_score = (
        "Score composto por 5 fatores binários: defasado (IAN < 10), desempenho acadêmico "
        "abaixo do 25º percentil do ano (IDA), autoavaliação mais de 2 pontos acima do "
        "desempenho real (IAA - IDA > 2), engajamento abaixo do 25º percentil do ano (IEG) "
        "e primeiro ano no programa. Cada fator presente soma 1 ponto. Quanto maior o score, "
        "maior a fragilidade: score ≥ 4 requer atenção urgente, score 3 requer monitoramento preventivo."
    )

    inde_score = risco_df.groupby(["ano", "score_risco"])["INDE"].mean().reset_index(name="inde_medio")

    nivel3 = df.copy()
    nivel3["grupo"] = np.where(nivel3["nivel_label"] == "3", "Nível 3", "Outros níveis")
    nivel3_compare = (
        nivel3.groupby("grupo")[["IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "INDE"]]
        .mean()
        .reset_index()
        .melt(id_vars="grupo", var_name="indicador", value_name="media")
    )

    chart_inde = (
        alt.Chart(inde_score)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("score_risco:O", title="Score de Fragilidade Acadêmica"),
            y=alt.Y("inde_medio:Q", title="INDE médio"),
            color=alt.Color(
                "ano:O",
                title="Ano",
                scale=alt.Scale(
                    domain=ANOS,
                    range=["#0f766e", "#f97316", "#7c3aed"],
                ),
            ),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("score_risco:O", title="Score de Fragilidade Acadêmica"),
                alt.Tooltip("inde_medio:Q", title="INDE médio", format=".2f"),
            ],
        )
        .properties(height=320)
    )
    chart_nivel3 = (
        alt.Chart(nivel3_compare)
        .mark_bar()
        .encode(
            x=alt.X("indicador:N", title=None),
            y=alt.Y("media:Q", title="Média"),
            color=alt.Color("grupo:N", title=None, scale=alt.Scale(range=["#dc2626", "#2563eb"])),
            xOffset="grupo:N",
            tooltip=[
                alt.Tooltip("indicador:N", title="Indicador"),
                alt.Tooltip("grupo:N", title="Grupo"),
                alt.Tooltip("media:Q", title="Média", format=".2f"),
            ],
        )
        .properties(height=320)
    )

    comentario_inde = "Quanto maior o score de fragilidade acadêmica, menor o INDE médio. O score resume sinais já capturados pelas dimensões acadêmicas e psicossociais."
    nivel_3_media = nivel3_compare[nivel3_compare["grupo"] == "Nível 3"]["media"].mean()
    outros_media = nivel3_compare[nivel3_compare["grupo"] == "Outros níveis"]["media"].mean()
    comentario_nivel3 = (
        f"O nível 3 concentra as piores médias entre os indicadores (salvo IPP e IPS), com desempenho médio {abs(nivel_3_media - outros_media):.2f} ponto(s) abaixo dos demais níveis."
    )

    col7, col8 = st.columns(2)
    with col7:
        renderizar_grafico_com_titulo_subtitulo("Score de Fragilidade Acadêmica ao longo dos anos", comentario_score, chart_score)
    with col8:
        renderizar_grafico_com_titulo_subtitulo("INDE x Score de Fragilidade Acadêmica", comentario_inde, chart_inde)

    abandono_nivel = (
        df[df["ano"].isin([2022, 2023])].copy()
    )
    ra_2023 = set(df[df["ano"] == 2023]["RA"])
    ra_2024 = set(df[df["ano"] == 2024]["RA"])
    abandono_nivel["saiu"] = 0
    abandono_nivel.loc[(abandono_nivel["ano"] == 2022) & (~abandono_nivel["RA"].isin(ra_2023)), "saiu"] = 1
    abandono_nivel.loc[(abandono_nivel["ano"] == 2023) & (~abandono_nivel["RA"].isin(ra_2024)), "saiu"] = 1
    abandono_nivel = abandono_nivel[~abandono_nivel["nivel_label"].isin(["7", "8"])].copy()
    abandono_nivel = (
        abandono_nivel.groupby("nivel_label")["saiu"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "taxa", "count": "n"})
    )
    abandono_nivel["nivel_ordem"] = abandono_nivel["nivel_label"].map(ORDEM_NIVEIS)
    abandono_nivel = abandono_nivel.sort_values("nivel_ordem")

    chart_abandono_nivel = (
        alt.Chart(abandono_nivel)
        .mark_bar(color="#dc2626")
        .encode(
            x=alt.X("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            y=alt.Y("nivel_label:N", sort=list(ORDEM_NIVEIS.keys()), title="Nível"),
            tooltip=[
                alt.Tooltip("nivel_label:N", title="Nível"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                alt.Tooltip("n:Q", title="Casos"),
            ],
        )
        .properties(height=320)
    )

    nivel_3_abandono = abandono_nivel.loc[abandono_nivel["nivel_label"] == "3", "taxa"].iloc[0]
    maior_abandono_nivel = abandono_nivel.sort_values("taxa", ascending=False).iloc[0]
    comentario_abandono_nivel = (
        f"O nível {maior_abandono_nivel['nivel_label']} concentra a maior taxa de abandono ({maior_abandono_nivel['taxa']:.1%}). "
        f"O nível 3 segue como ponto crítico, com {nivel_3_abandono:.1%}."
    )

    col7, col8 = st.columns(2)
    with col7:
        renderizar_grafico_com_titulo_subtitulo("O efeito nível 3", comentario_nivel3, chart_nivel3)
    with col8:
        renderizar_grafico_com_titulo_subtitulo("Abandono por nível", comentario_abandono_nivel, chart_abandono_nivel)

    abandono_pedra = (
        df[df["ano"].isin([2022, 2023])].copy()
    )
    abandono_pedra["saiu"] = 0
    abandono_pedra.loc[(abandono_pedra["ano"] == 2022) & (~abandono_pedra["RA"].isin(ra_2023)), "saiu"] = 1
    abandono_pedra.loc[(abandono_pedra["ano"] == 2023) & (~abandono_pedra["RA"].isin(ra_2024)), "saiu"] = 1
    abandono_pedra = abandono_pedra[~abandono_pedra["nivel_label"].isin(["7", "8"])].copy()
    abandono_pedra["tipo_escola_macro"] = abandono_pedra["tipo_escola_macro"].replace({"Privada/Bolsa": "Privada"})

    abandono_escola = (
        abandono_pedra.groupby("tipo_escola_macro")["saiu"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "taxa", "count": "n"})
    )
    abandono_escola = abandono_escola[abandono_escola["tipo_escola_macro"].isin(ORDEM_ESCOLAS)].copy()
    abandono_pedra = (
        abandono_pedra.groupby("pedra_resumo")["saiu"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "taxa", "count": "n"})
    )
    abandono_pedra = abandono_pedra[abandono_pedra["pedra_resumo"].isin(ORDEM_PEDRAS)].copy()

    chart_abandono_escola = (
        alt.Chart(abandono_escola)
        .mark_bar()
        .encode(
            x=alt.X("tipo_escola_macro:N", sort=ORDEM_ESCOLAS, title=None),
            y=alt.Y("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            color=alt.Color(
                "tipo_escola_macro:N",
                title=None,
                scale=alt.Scale(
                    domain=ORDEM_ESCOLAS,
                    range=[CORES_ESCOLA[item] for item in ORDEM_ESCOLAS],
                ),
            ),
            tooltip=[
                alt.Tooltip("tipo_escola_macro:N", title="Tipo"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                alt.Tooltip("n:Q", title="Casos"),
            ],
        )
        .properties(height=320)
    )
    chart_abandono_pedra = (
        alt.Chart(abandono_pedra)
        .mark_bar()
        .encode(
            x=alt.X("pedra_resumo:N", sort=ORDEM_PEDRAS, title="Pedra"),
            y=alt.Y("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            color=alt.Color(
                "pedra_resumo:N",
                title=None,
                scale=alt.Scale(domain=ORDEM_PEDRAS, range=[CORES_PEDRA[item] for item in ORDEM_PEDRAS]),
            ),
            tooltip=[
                alt.Tooltip("pedra_resumo:N", title="Pedra"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
                alt.Tooltip("n:Q", title="Casos"),
            ],
        )
        .properties(height=320)
    )

    quartzo_abandono = abandono_pedra.loc[abandono_pedra["pedra_resumo"] == "Quartzo", "taxa"].iloc[0]
    comentario_abandono_pedra = f"Quartzo concentra a maior taxa de abandono da base, chegando a {quartzo_abandono:.1%}."

    col9, col10 = st.columns(2)
    with col9:
        renderizar_grafico_com_titulo_subtitulo(
            "Abandono por tipo de escola",
            "A escola pública abandona mais do que a privada, sugerindo fatores externos além do acadêmico.",
            chart_abandono_escola,
        )
    with col10:
        renderizar_grafico_com_titulo_subtitulo("Abandono por pedra", comentario_abandono_pedra, chart_abandono_pedra)
