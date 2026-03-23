from __future__ import annotations

import altair as alt
import streamlit as st

from components.layout import layout
from sucesso_programa import carregar_perguntas_sucesso, renderizar_grafico_sucesso


layout("Sucesso do Programa")
alt.data_transformers.disable_max_rows()


@alt.theme.register("eixo_x_horizontal_sucesso", enable=True)
def _tema_eixo_x_horizontal_sucesso() -> dict:
    return {"config": {"axisX": {"labelAngle": 0}}}


st.header("🎯 Sucesso do Programa")
st.markdown(
    """
As perguntas abaixo sintetizam os principais pontos que o projeto precisa responder sobre desempenho,
defasagem, engajamento, permanência e impacto do programa. Em cada bloco, os gráficos ajudam a sustentar
as conclusões com evidências da base da Passos Mágicos.
"""
)

for pergunta in carregar_perguntas_sucesso():
    with st.expander(pergunta["titulo"], expanded=False):
        st.markdown(pergunta["resposta"])

        graficos = pergunta.get("graficos", [])
        for inicio in range(0, len(graficos), 2):
            colunas = st.columns(2)
            lote = graficos[inicio:inicio + 2]
            for coluna, grafico_id in zip(colunas, lote):
                with coluna:
                    renderizar_grafico_sucesso(grafico_id)
