from __future__ import annotations

from dataclasses import dataclass

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import classificar_evolucao_pedra, renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import (
    ANOS,
    CORES_COHERENCIA,
    CORES_PEDRA,
    CORES_STATUS,
    CORES_TRANSICAO,
    FAIXAS_IPS,
    GRUPOS_IAN,
    NIVEIS,
    ORDEM_NIVEIS,
    ORDEM_ESCOLAS,
    ORDEM_PEDRAS,
    PEDRA_PARA_NUMERO,
)
from analise_exploratoria.dados import (
    carregar_analytics_iaa,
    carregar_analytics_ian,
    carregar_analytics_ida,
    carregar_analytics_ieg,
    carregar_analytics_ipp,
    carregar_analytics_ips,
    carregar_analytics_ipv,
    carregar_base_dados,
    montar_base_pedras,
    montar_score_risco,
)


@dataclass
class BlocoGrafico:
    titulo: str
    subtitulo: str
    grafico: alt.TopLevelMixin


def _bloco_ian_defasagem() -> BlocoGrafico:
    df = carregar_analytics_ian()
    calor = (
        df.dropna(subset=["defasagem", "nivel_ordem"])
        .groupby(["nivel_label", "nivel_ordem", "ano"])["defasagem"]
        .mean()
        .reset_index(name="defasagem_media")
        .sort_values(["nivel_ordem", "ano"])
    )
    chart = (
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
        .properties(height=320)
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
    return BlocoGrafico(
        "IAN > Defasagem média por nível",
        "Valores negativos indicam atraso em relação à fase ideal; quanto mais negativo, maior a defasagem do grupo naquele nível.",
        chart + texto,
    )


def _bloco_ian_perfil_real() -> BlocoGrafico:
    df = carregar_analytics_ian()
    ordem_defasagem = ["Adiantado", "Na fase", "Leve (-1)", "Moderada (-2)", "Severa (< -2)"]
    perfil_real = (
        df[df["defasagem_cat"].notna()]
        .groupby(["ano", "defasagem_cat"])
        .size()
        .reset_index(name="quantidade")
    )
    perfil_real = perfil_real[perfil_real["defasagem_cat"].isin(ordem_defasagem)].copy()
    perfil_real["participacao"] = perfil_real.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())

    perfil_2024 = perfil_real[perfil_real["ano"] == 2024].set_index("defasagem_cat")["participacao"]
    chart = (
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAN > Perfil real da defasagem por ano",
        (
            f"Em 2024, {perfil_2024.get('Na fase', 0) + perfil_2024.get('Adiantado', 0):.1%} dos alunos estão na fase ou adiantados, "
            f"{perfil_2024.get('Leve (-1)', 0):.1%} têm defasagem leve, {perfil_2024.get('Moderada (-2)', 0):.1%} moderada "
            f"e {perfil_2024.get('Severa (< -2)', 0):.1%} severa."
        ),
        chart,
    )


def _bloco_ian_escola() -> BlocoGrafico:
    df = carregar_analytics_ian()
    base = (
        df[df["tipo_escola_macro"].isin(ORDEM_ESCOLAS)]
        .groupby(["ano", "tipo_escola_macro"])["em_defasagem"]
        .mean()
        .reset_index(name="taxa")
    )
    publica_2024 = base[(base["ano"] == 2024) & (base["tipo_escola_macro"] == "Pública")]["taxa"].iloc[0]
    privada_2024 = base[(base["ano"] == 2024) & (base["tipo_escola_macro"] == "Privada")]["taxa"].iloc[0]
    chart = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y("taxa:Q", title="Taxa em defasagem", axis=alt.Axis(format="%")),
            color=alt.Color("tipo_escola_macro:N", title="Tipo de escola"),
            xOffset="tipo_escola_macro:N",
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("tipo_escola_macro:N", title="Tipo de escola"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAN > Defasagem por tipo de escola",
        f"Em 2024, a defasagem atinge {publica_2024:.1%} na escola pública, contra {privada_2024:.1%} na privada, mostrando maior vulnerabilidade nesse contexto escolar.",
        chart,
    )


def _bloco_ian_coorte() -> BlocoGrafico:
    df = carregar_analytics_ian()
    evol = df[df["registro_coorte"]].copy()
    evol_count = evol.groupby(["coorte_ian", "evolucao_ian"]).size().reset_index(name="quantidade")
    evol_count["participacao"] = evol_count.groupby("coorte_ian")["quantidade"].transform(lambda serie: serie / serie.sum())

    anterior = df[df["transicao_ian"].isin(["Piorou", "Manteve adequado"])].copy()
    piora = anterior[anterior["transicao_ian"] == "Piorou"]
    alfa_um = piora["nivel_label"].isin(["ALFA", "1"]).mean()

    chart = (
        alt.Chart(evol_count)
        .mark_bar()
        .encode(
            x=alt.X("coorte_ian:N", title=None),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color("evolucao_ian:N", title="Evolução"),
            tooltip=[
                alt.Tooltip("coorte_ian:N", title="Coorte"),
                alt.Tooltip("evolucao_ian:N", title="Evolução"),
                alt.Tooltip("quantidade:Q", title="Alunos"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAN > Evolução do IAN por coorte",
        f"Entre os alunos que pioram, {alfa_um:.1%} estão concentrados em ALFA e nível 1, mostrando que a vulnerabilidade cresce sobretudo nas etapas iniciais.",
        chart,
    )


def _bloco_ida_distribuicao() -> BlocoGrafico:
    df = carregar_analytics_ida()
    faixas = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    df["faixa_ida"] = pd.cut(df["IDA"], bins=[0, 2, 4, 6, 8, 10.0001], labels=faixas, include_lowest=True, right=False)
    base = (
        df.dropna(subset=["IDA", "faixa_ida"])
        .groupby(["ano", "faixa_ida"], observed=False)
        .size()
        .reset_index(name="quantidade")
    )
    base["participacao"] = base.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())
    medias = df.groupby("ano")["IDA"].mean().reindex(ANOS)
    chart = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color("faixa_ida:N", title="Faixa de IDA", sort=faixas),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("faixa_ida:N", title="Faixa de IDA"),
                alt.Tooltip("quantidade:Q", title="Alunos"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IDA > Distribuição do IDA por ano",
        f"O IDA médio sobe de {medias.loc[2022]:.2f} para {medias.loc[2023]:.2f} e recua para {medias.loc[2024]:.2f} em 2024.",
        chart,
    )


def _bloco_ida_nivel() -> BlocoGrafico:
    df = carregar_analytics_ida()
    base = (
        df.dropna(subset=["IDA", "nivel_ordem"])
        .groupby(["nivel_label", "nivel_ordem", "ano"])["IDA"]
        .mean()
        .reset_index()
        .sort_values(["nivel_ordem", "ano"])
    )
    nivel_3 = base[base["nivel_label"] == "3"]["IDA"].mean()
    outros = base[base["nivel_label"] != "3"]["IDA"].mean()
    chart = (
        alt.Chart(base)
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IDA > IDA por nível ao longo do tempo",
        f"O nível 3 permanece como principal gargalo, com média {abs(nivel_3 - outros):.2f} ponto(s) abaixo dos demais níveis.",
        chart,
    )


def _bloco_ieg_ida() -> BlocoGrafico:
    df = carregar_analytics_ieg()
    base = df.dropna(subset=["IEG", "IDA"]).copy()
    corr = base["IEG"].corr(base["IDA"])
    dispersao = (
        alt.Chart(base)
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
    return BlocoGrafico(
        "IEG > IEG x IDA",
        f"Quanto maior o engajamento, maior tende a ser o desempenho acadêmico, com associação consistente observada na base ({corr:.3f}).",
        dispersao + regressao,
    )


def _bloco_ieg_ipv() -> BlocoGrafico:
    df = carregar_analytics_ieg()
    base = df.dropna(subset=["IEG", "IPV"]).copy()
    med_ieg = base["IEG"].median()
    med_ipv = base["IPV"].median()
    chart = (
        alt.Chart(base)
        .mark_rect()
        .encode(
            x=alt.X("IEG:Q", bin=alt.Bin(maxbins=20), title="IEG"),
            y=alt.Y("IPV:Q", bin=alt.Bin(maxbins=20), title="IPV"),
            color=alt.Color("count():Q", title="Alunos", scale=alt.Scale(scheme="yelloworangered")),
            tooltip=[alt.Tooltip("count():Q", title="Alunos")],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IEG > Densidade IEG x IPV",
        f"A maior concentração de alunos aparece perto de IEG {med_ieg:.2f} e IPV {med_ipv:.2f}, reforçando a proximidade entre engajamento e ponto de virada.",
        chart,
    )


def _bloco_iaa_relacao() -> BlocoGrafico:
    df = carregar_analytics_iaa()
    faixas = ["0 a 2", "2 a 4", "4 a 6", "6 a 8", "8 a 10"]
    base = df.dropna(subset=["IAA", "IDA"]).copy()
    base["faixa_iaa"] = pd.cut(base["IAA"], bins=[0, 2, 4, 6, 8, 10.0001], labels=faixas, include_lowest=True, right=False)
    faixas_df = base.groupby("faixa_iaa", observed=False)["IDA"].mean().reindex(faixas).reset_index()
    corr = base["IAA"].corr(base["IDA"])
    maior = faixas_df.sort_values("IDA", ascending=False).iloc[0]
    chart = (
        alt.Chart(faixas_df)
        .mark_bar(color="#7c3aed")
        .encode(
            x=alt.X("faixa_iaa:N", sort=faixas, title="Faixa de IAA"),
            y=alt.Y("IDA:Q", title="IDA médio"),
            tooltip=[
                alt.Tooltip("faixa_iaa:N", title="Faixa de IAA"),
                alt.Tooltip("IDA:Q", title="IDA médio", format=".2f"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAA > IAA x IDA",
        f"Se a autoavaliação fosse muito aderente ao desempenho real, as barras subiriam de forma mais clara; o comportamento é instável e a faixa `{maior['faixa_iaa']}` concentra a maior média de IDA.",
        chart,
    )


def _bloco_iaa_coerencia() -> BlocoGrafico:
    df = carregar_analytics_iaa()
    base = df.dropna(subset=["IAA", "IDA"]).copy()
    coerencia = base.groupby(["ano", "coerencia_iaa"]).size().reset_index(name="quantidade")
    coerencia = coerencia[coerencia["coerencia_iaa"] != "Sem dado"].copy()
    coerencia["participacao"] = coerencia.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())
    superestima = coerencia[coerencia["coerencia_iaa"].isin(["Superestima leve (1-2)", "Superestima (>2)"])]
    total_super = superestima.groupby("ano")["participacao"].sum().mean()
    chart = (
        alt.Chart(coerencia)
        .mark_bar()
        .encode(
            x=alt.X("ano:O", sort=ANOS, title="Ano"),
            y=alt.Y("participacao:Q", title="Participação", axis=alt.Axis(format="%")),
            color=alt.Color(
                "coerencia_iaa:N",
                title="Coerência",
                scale=alt.Scale(domain=list(CORES_COHERENCIA.keys()), range=list(CORES_COHERENCIA.values())),
            ),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("coerencia_iaa:N", title="Coerência"),
                alt.Tooltip("participacao:Q", title="Participação", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAA > Coerência IAA x IDA por ano",
        f"Somando as faixas de superestimação leve e severa, cerca de {total_super:.1%} da base tende a se avaliar acima do desempenho observado.",
        chart,
    )


def _bloco_iaa_nivel() -> BlocoGrafico:
    df = carregar_analytics_iaa()
    base = df.dropna(subset=["IAA", "IDA", "nivel_ordem"]).copy()
    gap_nivel = (
        base.groupby(["nivel_label", "nivel_ordem"])["gap_iaa_ida"]
        .median()
        .reset_index(name="gap_mediano")
        .sort_values("nivel_ordem")
    )
    nivel_3_gap = gap_nivel.loc[gap_nivel["nivel_label"] == "3", "gap_mediano"].iloc[0]
    gap_melhor = gap_nivel["gap_mediano"].min()
    chart = (
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IAA > Superestimação por nível",
        f"O nível 3 concentra a maior distância entre autoavaliação e desempenho real, com gap mediano de {nivel_3_gap:.2f}, acima do melhor nível observado ({gap_melhor:.2f}).",
        chart,
    )


def _obter_leitura_ips(transicao: str) -> tuple[pd.DataFrame, float, float]:
    df = carregar_analytics_ips()
    base = df.dropna(subset=["transicao", "faixa_IPS"]).copy()
    sub = base[base["transicao"] == transicao].copy()
    delta_df = (
        sub.groupby("faixa_IPS")[["delta_IDA", "delta_IEG"]]
        .mean()
        .reindex(FAIXAS_IPS)
        .reset_index()
        .melt(id_vars="faixa_IPS", var_name="indicador", value_name="delta")
    )
    delta_df["indicador_label"] = delta_df["indicador"].map({"delta_IDA": "Delta de IDA", "delta_IEG": "Delta de IEG"})
    return delta_df, sub["IPS"].corr(sub["delta_IDA"]), sub["IPS"].corr(sub["delta_IEG"])


def _bloco_ips_delta_20222023() -> BlocoGrafico:
    delta_df, corr_ida, corr_ieg = _obter_leitura_ips("2022->2023")
    chart = (
        alt.Chart(delta_df)
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
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPS > IPS atual x delta futuro (2022->2023)",
        f"Na transição 2022→2023, as diferenças entre faixas existem, mas a capacidade do IPS de antecipar quedas futuras ainda aparece fraca (IDA {corr_ida:.3f}; IEG {corr_ieg:.3f}).",
        chart,
    )


def _bloco_ips_delta_20232024() -> BlocoGrafico:
    delta_df, corr_ida, corr_ieg = _obter_leitura_ips("2023->2024")
    chart = (
        alt.Chart(delta_df)
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
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPS > IPS atual x delta futuro (2023->2024)",
        f"Na transição 2023→2024, o padrão se repete: as faixas ajudam pouco a antecipar o que acontecerá com desempenho e engajamento no ano seguinte (IDA {corr_ida:.3f}; IEG {corr_ieg:.3f}).",
        chart,
    )


def _bloco_ipp_grupo_ian() -> BlocoGrafico:
    df = carregar_analytics_ipp()
    base = (
        df.dropna(subset=["IPP", "grupo_ian"])
        .groupby(["ano", "grupo_ian"])["IPP"]
        .mean()
        .reset_index()
    )
    base["grupo_ian"] = pd.Categorical(base["grupo_ian"], categories=GRUPOS_IAN, ordered=True)
    ipp_adequado = base[base["grupo_ian"] == "Adequado (10.0)"]["IPP"].mean()
    ipp_severo = base[base["grupo_ian"] == "Severa (2.5)"]["IPP"].mean()
    chart = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            x=alt.X("grupo_ian:N", sort=GRUPOS_IAN, title="Grupo de IAN"),
            y=alt.Y("IPP:Q", title="IPP médio"),
            color=alt.Color("ano:O", title="Ano", scale=alt.Scale(domain=[2022, 2023, 2024], range=["#dc2626", "#f59e0b", "#2563eb"])),
            xOffset="ano:O",
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("grupo_ian:N", title="Grupo"),
                alt.Tooltip("IPP:Q", title="IPP médio", format=".2f"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPP > IPP por grupo de IAN",
        f"O IPP cresce da defasagem severa ({ipp_severo:.2f}) para o grupo adequado ({ipp_adequado:.2f}), mas as diferenças são moderadas.",
        chart,
    )


def _bloco_ipp_concordancia() -> BlocoGrafico:
    df = carregar_analytics_ipp()
    nomes = {
        "Confirma: defasado + IPP baixo": "Confirma / defasado",
        "Contradiz: defasado + IPP alto": "Contradiz / defasado",
        "Confirma: adequado + IPP alto": "Confirma / adequado",
        "Contradiz: adequado + IPP baixo": "Contradiz / adequado",
    }
    base = (
        df.dropna(subset=["concordancia_ipp"])
        .groupby(["ano", "concordancia_ipp"])
        .size()
        .reset_index(name="quantidade")
    )
    base["concordancia_curta"] = base["concordancia_ipp"].map(nomes).fillna(base["concordancia_ipp"])
    base["participacao"] = base.groupby("ano")["quantidade"].transform(lambda serie: serie / serie.sum())
    contradiz = df.dropna(subset=["concordancia_ipp"])["concordancia_ipp"].str.contains("Contradiz").mean()
    chart = (
        alt.Chart(base)
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPP > O IPP confirma ou contradiz o IAN?",
        f"Cerca de {contradiz:.1%} dos registros entram em zona de contradição, mostrando que IPP e IAN não contam exatamente a mesma história.",
        chart,
    )


def _obter_correlacoes_ipv() -> tuple[pd.DataFrame, pd.DataFrame]:
    ipv_df = carregar_analytics_ipv()
    indicadores = ["IDA", "IEG", "IAA", "IPS", "IPP", "IAN"]
    gerais = []
    anuais = []
    for indicador in indicadores:
        validos = ipv_df[["IPV", indicador]].dropna()
        gerais.append({"indicador": indicador, "correlacao": validos["IPV"].corr(validos[indicador])})
        for ano in ANOS:
            validos_ano = ipv_df[ipv_df["ano"] == ano][["IPV", indicador]].dropna()
            if len(validos_ano) > 10:
                anuais.append({"ano": ano, "indicador": indicador, "correlacao": validos_ano["IPV"].corr(validos_ano[indicador])})
    return pd.DataFrame(gerais).sort_values("correlacao", ascending=False), pd.DataFrame(anuais)


def _bloco_ipv_geral() -> BlocoGrafico:
    gerais, _ = _obter_correlacoes_ipv()
    topo = gerais.iloc[0]["indicador"]
    chart = (
        alt.Chart(gerais)
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPV > Quem mais caminha com o IPV?",
        f"Considerando toda a base, `{topo}` é o indicador que mais acompanha as variações do IPV.",
        chart,
    )


def _bloco_ipv_evolucao() -> BlocoGrafico:
    _, anuais = _obter_correlacoes_ipv()
    chart = (
        alt.Chart(anuais)
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
        .properties(height=320)
    )
    return BlocoGrafico(
        "IPV > Evolução das correlações com IPV",
        "Em 2022, IDA e IEG se destacam; em 2023, IPP ganha força; e em 2024 o IPP assume protagonismo sem tirar IDA e IEG do grupo principal.",
        chart,
    )


def _bloco_inde_matriz() -> BlocoGrafico:
    df = carregar_base_dados()
    matriz = df[["IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "INDE"]].dropna().corr().stack().reset_index()
    matriz.columns = ["eixo_x", "eixo_y", "correlacao"]
    mapa = (
        alt.Chart(matriz)
        .mark_rect()
        .encode(
            x=alt.X("eixo_x:N", title=None),
            y=alt.Y("eixo_y:N", title=None),
            color=alt.Color("correlacao:Q", title="Correlação", scale=alt.Scale(scheme="tealblues")),
            tooltip=[
                alt.Tooltip("eixo_x:N", title="Indicador X"),
                alt.Tooltip("eixo_y:N", title="Indicador Y"),
                alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
            ],
        )
        .properties(height=360)
    )
    texto = mapa.mark_text(size=10).encode(text=alt.Text("correlacao:Q", format=".2f"))
    return BlocoGrafico(
        "INDE > Matriz de correlação",
        "Desempenho acadêmico, engajamento e ponto de virada aparecem fortemente conectados e ajudam a impulsionar o índice global.",
        mapa + texto,
    )


def _bloco_inde_combinacoes() -> BlocoGrafico:
    df = carregar_base_dados()
    combo = df.dropna(subset=["INDE", "IDA", "IEG", "IPS", "IPP"]).copy()
    for indicador in ["IDA", "IEG", "IPS", "IPP"]:
        mediana = combo[indicador].median()
        combo[f"{indicador}_nivel"] = np.where(combo[indicador] >= mediana, "Alto", "Baixo")
    combo["perfil"] = "IDA:" + combo["IDA_nivel"] + " | IEG:" + combo["IEG_nivel"] + " | IPS:" + combo["IPS_nivel"] + " | IPP:" + combo["IPP_nivel"]
    combo["perfil_exibicao"] = (
        "IDA:" + combo["IDA_nivel"]
        + " | IEG:" + combo["IEG_nivel"]
        + " |\nIPS:" + combo["IPS_nivel"]
        + " | IPP:" + combo["IPP_nivel"]
    )
    rank = (
        combo.groupby(["perfil", "perfil_exibicao"])["INDE"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "inde_medio", "count": "n"})
        .sort_values("inde_medio", ascending=False)
    )
    plot = pd.concat([rank.head(5), rank.tail(5)]).reset_index(drop=True)
    plot["grupo"] = ["5 melhores"] * 5 + ["5 piores"] * 5
    chart = (
        alt.Chart(plot)
        .mark_bar()
        .encode(
            x=alt.X("inde_medio:Q", title="INDE médio"),
            y=alt.Y("perfil_exibicao:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280)),
            color=alt.Color("grupo:N", title=None, scale=alt.Scale(range=["#16a34a", "#dc2626"])),
            tooltip=[
                alt.Tooltip("perfil:N", title="Perfil"),
                alt.Tooltip("inde_medio:Q", title="INDE médio", format=".2f"),
                alt.Tooltip("n:Q", title="Registros"),
            ],
        )
        .properties(height=360, width=220)
    )
    return BlocoGrafico(
        "INDE > 5 melhores e 5 piores combinações",
        f"A melhor combinação chega a {rank.iloc[0]['inde_medio']:.2f}, enquanto a pior fica em {rank.iloc[-1]['inde_medio']:.2f}.",
        chart,
    )


def _bloco_efetividade_defasagem() -> BlocoGrafico:
    df = carregar_base_dados()
    resumo = df.groupby("ano").agg(defasagem=("em_defasagem", "mean")).reset_index()
    chart = (
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
    return BlocoGrafico(
        "Visão Estratégica > Queda da defasagem",
        f"A taxa de defasagem cai de {resumo.loc[resumo['ano'] == 2022, 'defasagem'].iloc[0]:.1%} para {resumo.loc[resumo['ano'] == 2024, 'defasagem'].iloc[0]:.1%} entre 2022 e 2024.",
        chart,
    )


def _bloco_efetividade_pedras() -> BlocoGrafico:
    df = carregar_base_dados()
    base_pedras = montar_base_pedras(df)
    base_longa = (
        base_pedras.reset_index()[["RA", "pedra_20", "pedra_21", "pedra_22", "pedra_23", "pedra_24"]]
        .melt(id_vars="RA", var_name="coluna_pedra", value_name="pedra")
        .dropna(subset=["pedra"])
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

    chart = (
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
    return BlocoGrafico(
        "Visão Estratégica > Distribuição histórica de pedras (2020-2024)",
        "A evolução das pedras mostra a mudança de perfil da base ao longo do tempo e ajuda a observar se os alunos avançam do Quartzo para faixas mais altas do programa.",
        chart,
    )


def _bloco_efetividade_mobilidade() -> BlocoGrafico:
    df = carregar_base_dados()
    base_pedras = montar_base_pedras(df)
    linhas = []
    for inicio, fim in [(2020, 2022), (2022, 2024)]:
        coluna_inicio = f"pedra_{str(inicio)[-2:]}"
        coluna_fim = f"pedra_{str(fim)[-2:]}"
        pares = base_pedras[[coluna_inicio, coluna_fim, "ano_ingresso"]].dropna().copy()
        pares = pares[pares["ano_ingresso"] <= inicio].copy()
        pares["delta"] = pares[coluna_fim].map(PEDRA_PARA_NUMERO) - pares[coluna_inicio].map(PEDRA_PARA_NUMERO)
        pares["evolucao"] = pares["delta"].apply(classificar_evolucao_pedra)
        distribuicao = pares["evolucao"].value_counts(normalize=True)
        for status in ["Caiu", "Manteve", "Subiu"]:
            linhas.append({"transicao": f"{inicio}->{fim}", "evolucao": status, "participacao": distribuicao.get(status, 0.0)})
    mobilidade = pd.DataFrame(linhas)
    chart = (
        alt.Chart(mobilidade)
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
    return BlocoGrafico(
        "Visão Estratégica > Mobilidade de pedras",
        "A mobilidade positiva entre pedras reforça sinais de recuperação recente e mostra que parte importante dos alunos avança ao longo do ciclo.",
        chart,
    )


def _bloco_vulnerabilidade_abandono_nivel() -> BlocoGrafico:
    df = carregar_base_dados()
    ra_2023 = set(df.loc[df["ano"] == 2023, "RA"])
    ra_2024 = set(df.loc[df["ano"] == 2024, "RA"])

    abandono = df[df["ano"].isin([2022, 2023])].copy()
    abandono["saiu"] = 0
    abandono.loc[(abandono["ano"] == 2022) & (~abandono["RA"].isin(ra_2023)), "saiu"] = 1
    abandono.loc[(abandono["ano"] == 2023) & (~abandono["RA"].isin(ra_2024)), "saiu"] = 1
    abandono = abandono[~abandono["nivel_label"].isin(["7", "8"])].copy()
    abandono = (
        abandono.groupby("nivel_label")["saiu"]
        .mean()
        .reset_index(name="taxa")
    )
    abandono["nivel_ordem"] = abandono["nivel_label"].map(ORDEM_NIVEIS)
    abandono = abandono.sort_values("nivel_ordem")
    mais_critico = abandono.sort_values("taxa", ascending=False).iloc[0]

    chart = (
        alt.Chart(abandono)
        .mark_bar(color="#dc2626")
        .encode(
            x=alt.X("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            y=alt.Y("nivel_label:N", sort=list(ORDEM_NIVEIS.keys()), title="Nível"),
            tooltip=[
                alt.Tooltip("nivel_label:N", title="Nível"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "Visão Estratégica > Abandono por nível",
        f"O nível {mais_critico['nivel_label']} concentra a maior taxa de abandono ({mais_critico['taxa']:.1%}), reforçando que a vulnerabilidade não está distribuída de forma uniforme na base.",
        chart,
    )


def _bloco_vulnerabilidade_abandono_pedra() -> BlocoGrafico:
    df = carregar_base_dados()
    ra_2023 = set(df.loc[df["ano"] == 2023, "RA"])
    ra_2024 = set(df.loc[df["ano"] == 2024, "RA"])

    abandono = df[df["ano"].isin([2022, 2023])].copy()
    abandono["saiu"] = 0
    abandono.loc[(abandono["ano"] == 2022) & (~abandono["RA"].isin(ra_2023)), "saiu"] = 1
    abandono.loc[(abandono["ano"] == 2023) & (~abandono["RA"].isin(ra_2024)), "saiu"] = 1
    abandono = abandono[~abandono["nivel_label"].isin(["7", "8"])].copy()
    abandono = (
        abandono.groupby("pedra_resumo")["saiu"]
        .mean()
        .reset_index(name="taxa")
    )
    abandono = abandono[abandono["pedra_resumo"].isin(ORDEM_PEDRAS)].copy()
    abandono["pedra_resumo"] = pd.Categorical(abandono["pedra_resumo"], categories=ORDEM_PEDRAS, ordered=True)
    abandono = abandono.sort_values("pedra_resumo")
    mais_critica = abandono.sort_values("taxa", ascending=False).iloc[0]

    chart = (
        alt.Chart(abandono)
        .mark_bar()
        .encode(
            x=alt.X("pedra_resumo:N", sort=ORDEM_PEDRAS, title="Pedra"),
            y=alt.Y("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            color=alt.Color(
                "pedra_resumo:N",
                title=None,
                scale=alt.Scale(domain=ORDEM_PEDRAS, range=[CORES_PEDRA[pedra] for pedra in ORDEM_PEDRAS]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("pedra_resumo:N", title="Pedra"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "Visão Estratégica > Abandono por pedra",
        f"A pedra {mais_critica['pedra_resumo']} concentra a maior taxa de abandono ({mais_critica['taxa']:.1%}), reforçando que os grupos mais frágeis também tendem a estar nas pedras mais baixas.",
        chart,
    )


def _bloco_vulnerabilidade_abandono_escola() -> BlocoGrafico:
    df = carregar_base_dados()
    ra_2023 = set(df.loc[df["ano"] == 2023, "RA"])
    ra_2024 = set(df.loc[df["ano"] == 2024, "RA"])

    abandono = df[df["ano"].isin([2022, 2023])].copy()
    abandono["saiu"] = 0
    abandono.loc[(abandono["ano"] == 2022) & (~abandono["RA"].isin(ra_2023)), "saiu"] = 1
    abandono.loc[(abandono["ano"] == 2023) & (~abandono["RA"].isin(ra_2024)), "saiu"] = 1
    abandono = abandono[~abandono["nivel_label"].isin(["7", "8"])].copy()
    abandono["tipo_escola_macro"] = abandono["tipo_escola_macro"].replace({"Privada/Bolsa": "Privada"})
    abandono = (
        abandono.groupby("tipo_escola_macro")["saiu"]
        .mean()
        .reset_index(name="taxa")
    )
    abandono = abandono[abandono["tipo_escola_macro"].isin(ORDEM_ESCOLAS)].copy()
    abandono = abandono.sort_values("taxa", ascending=False)
    mais_critica = abandono.iloc[0]

    chart = (
        alt.Chart(abandono)
        .mark_bar()
        .encode(
            x=alt.X("tipo_escola_macro:N", title="Tipo de escola"),
            y=alt.Y("taxa:Q", title="Taxa de abandono", axis=alt.Axis(format="%")),
            color=alt.Color(
                "tipo_escola_macro:N",
                title=None,
                scale=alt.Scale(range=["#dc2626", "#2563eb"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("tipo_escola_macro:N", title="Tipo de escola"),
                alt.Tooltip("taxa:Q", title="Taxa", format=".1%"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "Visão Estratégica > Abandono por tipo de escola",
        f"Alunos de {mais_critica['tipo_escola_macro'].lower()} concentram a maior taxa de abandono ({mais_critica['taxa']:.1%}), reforçando o peso do contexto escolar no perfil de maior vulnerabilidade.",
        chart,
    )


def _bloco_insight_score_fragilidade() -> BlocoGrafico:
    df = carregar_base_dados()
    risco = montar_score_risco(df)
    inde_score = risco.groupby(["ano", "score_risco"])["INDE"].mean().reset_index(name="inde_medio")
    chart = (
        alt.Chart(inde_score)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("score_risco:O", title="Score de Fragilidade Acadêmica"),
            y=alt.Y("inde_medio:Q", title="INDE médio"),
            color=alt.Color("ano:O", title="Ano", scale=alt.Scale(domain=ANOS, range=["#0f766e", "#f97316", "#7c3aed"])),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("score_risco:O", title="Score"),
                alt.Tooltip("inde_medio:Q", title="INDE médio", format=".2f"),
            ],
        )
        .properties(height=320)
    )
    return BlocoGrafico(
        "Visão Estratégica > INDE x Score de Fragilidade Acadêmica",
        "Quanto maior o score de fragilidade, menor o INDE médio. O score ajuda a priorizar alunos com maior necessidade de acompanhamento.",
        chart,
    )


def _bloco_insight_nivel3() -> BlocoGrafico:
    df = carregar_base_dados()
    nivel3 = df.copy()
    nivel3["grupo"] = np.where(nivel3["nivel_label"] == "3", "Nível 3", "Outros níveis")
    base = (
        nivel3.groupby("grupo")[["IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "INDE"]]
        .mean()
        .reset_index()
        .melt(id_vars="grupo", var_name="indicador", value_name="media")
    )
    chart = (
        alt.Chart(base)
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
    return BlocoGrafico(
        "Visão Estratégica > O efeito nível 3",
        "O nível 3 concentra as piores médias da base em vários indicadores e aparece como um ponto crítico da trajetória dos alunos.",
        chart,
    )


REGISTRO_GRAFICOS = {
    "ian_defasagem": _bloco_ian_defasagem,
    "ian_perfil_real": _bloco_ian_perfil_real,
    "ian_escola": _bloco_ian_escola,
    "ian_coorte": _bloco_ian_coorte,
    "ida_distribuicao": _bloco_ida_distribuicao,
    "ida_nivel": _bloco_ida_nivel,
    "ieg_ida": _bloco_ieg_ida,
    "ieg_ipv": _bloco_ieg_ipv,
    "iaa_relacao": _bloco_iaa_relacao,
    "iaa_coerencia": _bloco_iaa_coerencia,
    "iaa_nivel": _bloco_iaa_nivel,
    "ips_delta_20222023": _bloco_ips_delta_20222023,
    "ips_delta_20232024": _bloco_ips_delta_20232024,
    "ipp_grupo_ian": _bloco_ipp_grupo_ian,
    "ipp_concordancia": _bloco_ipp_concordancia,
    "ipv_geral": _bloco_ipv_geral,
    "ipv_evolucao": _bloco_ipv_evolucao,
    "inde_matriz": _bloco_inde_matriz,
    "inde_combinacoes": _bloco_inde_combinacoes,
    "efetividade_defasagem": _bloco_efetividade_defasagem,
    "efetividade_pedras": _bloco_efetividade_pedras,
    "efetividade_mobilidade": _bloco_efetividade_mobilidade,
    "vulnerabilidade_abandono_escola": _bloco_vulnerabilidade_abandono_escola,
    "vulnerabilidade_abandono_nivel": _bloco_vulnerabilidade_abandono_nivel,
    "vulnerabilidade_abandono_pedra": _bloco_vulnerabilidade_abandono_pedra,
    "insight_score_fragilidade": _bloco_insight_score_fragilidade,
    "insight_nivel3": _bloco_insight_nivel3,
}


def renderizar_grafico_sucesso(grafico_id: str) -> None:
    """Renderiza um gráfico registrado da seção Sucesso do Programa."""
    bloco = REGISTRO_GRAFICOS[grafico_id]()
    renderizar_grafico_com_titulo_subtitulo(bloco.titulo, bloco.subtitulo, bloco.grafico)
