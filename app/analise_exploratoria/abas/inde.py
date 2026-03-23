from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analise_exploratoria.apoio import renderizar_grafico_com_titulo_subtitulo
from analise_exploratoria.constantes import ANOS, INDICADORES, INDICADORES_BASE


def renderizar_inde(df: pd.DataFrame) -> None:
    st.subheader("INDE — Multidimensionalidade")
    st.markdown(
        "O INDE é o Índice de Desenvolvimento Educacional da Passos Mágicos. Ele reúne, em uma única medida, "
        "indicadores das dimensões acadêmica, psicossocial e psicopedagógica para acompanhar o desenvolvimento global do aluno."
    )
    st.markdown(
        "<small style='color: rgba(49, 51, 63, 0.6);'>"
        "Fase 0 a 7: INDE = IAN x 0,1 + IDA x 0,2 + IEG x 0,2 + IAA x 0,1 + IPS x 0,1 + IPP x 0,1 + IPV x 0,2.<br>"
        "Fase 8: INDE = IAN x 0,1 + IDA x 0,4 + IEG x 0,2 + IAA x 0,1 + IPS x 0,2."
        "</small>",
        unsafe_allow_html=True,
    )

    inde_valido = df[~df["nivel_label"].isin(["8", "9"])].copy()
    inde_valido = inde_valido.dropna(subset=INDICADORES + ["INDE"]).copy()
    inde_valido["INDE_calc"] = (
        inde_valido["IAN"] * 0.1
        + inde_valido["IDA"] * 0.2
        + inde_valido["IEG"] * 0.2
        + inde_valido["IAA"] * 0.1
        + inde_valido["IPS"] * 0.1
        + inde_valido["IPP"] * 0.1
        + inde_valido["IPV"] * 0.2
    )
    inde_valido["diff"] = (inde_valido["INDE"] - inde_valido["INDE_calc"]).abs()

    corr_rows = []
    for indicador in INDICADORES:
        validos = df[["INDE", indicador]].dropna()
        corr_rows.append({"indicador": indicador, "correlacao": validos["INDE"].corr(validos[indicador])})
    corr_df = pd.DataFrame(corr_rows).sort_values("correlacao", ascending=False)

    matriz_df = df[INDICADORES + ["INDE"]].dropna().corr().stack().reset_index()
    matriz_df.columns = ["eixo_x", "eixo_y", "correlacao"]

    combo = df.dropna(subset=["INDE", "IDA", "IEG", "IPS", "IPP"]).copy()
    for indicador in ["IDA", "IEG", "IPS", "IPP"]:
        mediana = combo[indicador].median()
        combo[f"{indicador}_nivel"] = np.where(combo[indicador] >= mediana, "Alto", "Baixo")
    combo["perfil"] = (
        "IDA:" + combo["IDA_nivel"]
        + " | IEG:" + combo["IEG_nivel"]
        + " | IPS:" + combo["IPS_nivel"]
        + " | IPP:" + combo["IPP_nivel"]
    )
    combo["perfil_exibicao"] = (
        "IDA:" + combo["IDA_nivel"]
        + " | IEG:" + combo["IEG_nivel"]
        + " |\nIPS:" + combo["IPS_nivel"]
        + " | IPP:" + combo["IPP_nivel"]
    )
    combo_rank = (
        combo.groupby(["perfil", "perfil_exibicao"])["INDE"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "inde_medio", "count": "n"})
    )
    combo_rank = combo_rank.sort_values("inde_medio", ascending=False)
    combo_plot = pd.concat([combo_rank.head(5), combo_rank.tail(5)]).reset_index(drop=True)
    combo_plot["grupo"] = ["5 melhores"] * 5 + ["5 piores"] * 5
    diff_media = inde_valido["diff"].mean()
    principal_indicador = corr_df.iloc[0]
    segundo_indicador = corr_df.iloc[1]

    col1, col2 = st.columns(2)
    with col1:
        dispersao = (
            alt.Chart(inde_valido)
            .mark_circle(size=60, opacity=0.35, color="#2563eb")
            .encode(
                x=alt.X("INDE_calc:Q", title="INDE calculado"),
                y=alt.Y("INDE:Q", title="INDE real"),
                tooltip=[
                    alt.Tooltip("ano:O", title="Ano"),
                    alt.Tooltip("INDE_calc:Q", title="Calculado", format=".3f"),
                    alt.Tooltip("INDE:Q", title="Real", format=".3f"),
                    alt.Tooltip("diff:Q", title="Diferença", format=".4f"),
                ],
            )
        )
        diagonal = alt.Chart(pd.DataFrame({"x": [3, 10], "y": [3, 10]})).mark_line(color="#dc2626", strokeDash=[6, 4]).encode(
            x="x:Q", y="y:Q"
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Validação da fórmula do INDE",
            (
                f"O gráfico compara o INDE calculado pela fórmula com o INDE registrado na base. "
                f"Como os pontos ficam praticamente sobre a linha de referência e a diferença média é de apenas {diff_media:.4f}, "
                "a composição do índice aparece consistente com a regra oficial."
            ),
            dispersao + diagonal,
        )

    with col2:
        chart_corr = (
            alt.Chart(corr_df)
            .mark_bar()
            .encode(
                x=alt.X("correlacao:Q", title="Correlação com INDE"),
                y=alt.Y("indicador:N", sort="-x", title=None),
                color=alt.condition(alt.datum.correlacao > 0, alt.value("#16a34a"), alt.value("#dc2626")),
                tooltip=[
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("correlacao:Q", title="Correlação", format=".3f"),
                ],
        )
        .properties(height=320, title="Peso real dos indicadores no INDE")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "Peso real dos indicadores no INDE",
            (
                f"Este gráfico mostra quais indicadores mais caminham junto com o INDE. "
                f"No topo aparecem `{principal_indicador['indicador']}` e `{segundo_indicador['indicador']}`, "
                "sugerindo que eles têm papel mais forte para puxar o índice geral para cima ou para baixo."
            ),
            chart_corr,
        )

    col3, col4 = st.columns(2)
    with col3:
        mapa_calor = (
            alt.Chart(matriz_df)
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
        .properties(height=360, title="Matriz de correlação")
        )
        texto = mapa_calor.mark_text(size=10).encode(text=alt.Text("correlacao:Q", format=".2f"))
        renderizar_grafico_com_titulo_subtitulo(
            "Matriz de correlação",
            (
                f"A matriz ajuda a enxergar quais indicadores costumam variar juntos. "
                f"Os pares `IDA x IEG`, `IDA x IPV` e `IEG x IPV` aparecem entre os mais próximos, "
                "indicando que desempenho, engajamento e ponto de virada tendem a se reforçar mutuamente dentro do índice."
            ),
            mapa_calor + texto,
        )

    with col4:
        chart_combo = (
            alt.Chart(combo_plot)
            .mark_bar()
            .encode(
                x=alt.X("inde_medio:Q", title="INDE médio"),
                y=alt.Y(
                    "perfil_exibicao:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=280),
                ),
                color=alt.Color("grupo:N", title=None, scale=alt.Scale(range=["#16a34a", "#dc2626"])),
                tooltip=[
                    alt.Tooltip("perfil:N", title="Perfil"),
                    alt.Tooltip("inde_medio:Q", title="INDE médio", format=".2f"),
                    alt.Tooltip("n:Q", title="Registros"),
                ],
        )
        .properties(height=360, width=220, title="5 melhores e 5 piores combinações")
        )
        renderizar_grafico_com_titulo_subtitulo(
            "5 melhores e 5 piores combinações",
            (
                f"O gráfico compara as combinações de perfil com melhores e piores resultados de INDE. "
                f"No topo, a melhor combinação chega a {combo_rank.iloc[0]['inde_medio']:.2f}; na base, a pior fica em {combo_rank.iloc[-1]['inde_medio']:.2f}, "
                "mostrando como a combinação entre indicadores altos e baixos muda bastante o resultado final do índice."
            ),
            chart_combo,
        )
