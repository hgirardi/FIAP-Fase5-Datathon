from __future__ import annotations

import altair as alt
import streamlit as st

from components.layout import layout
from analise_exploratoria.abas import (
    renderizar_ian,
    renderizar_iaa,
    renderizar_ida,
    renderizar_ieg,
    renderizar_inde,
    renderizar_ipp,
    renderizar_ips,
    renderizar_ipv,
    renderizar_panorama,
)
from analise_exploratoria.dados import carregar_base_dados, montar_base_pedras, montar_pares, montar_score_risco


layout("Análise Exploratória")
alt.data_transformers.disable_max_rows()


@alt.theme.register("eixo_x_horizontal", enable=True)
def _tema_eixo_x_horizontal() -> dict:
    return {"config": {"axisX": {"labelAngle": 0}}}

st.header("🔍 Análise Exploratória")
st.markdown(
    """
Consolidação dos principais achados da análise exploratória em uma leitura visual, objetiva e orientada à decisão.
Cada aba demonstra evidências sobre desempenho, defasagem, engajamento e permanência, facilitando a compreensão dos fatores que mais impactam a trajetória dos alunos acompanhados pela Passos Mágicos.
"""
)


base = carregar_base_dados()
pares = montar_pares(base)
base_pedras = montar_base_pedras(base)
risco = montar_score_risco(base)

abas = st.tabs(
    [
        "Visão Estratégica",
        "IAN",
        "IDA",
        "IEG",
        "IAA",
        "IPS",
        "IPP",
        "IPV",
        "INDE",
    ]
)

with abas[0]:
    renderizar_panorama(base, risco, base_pedras)

with abas[1]:
    renderizar_ian()

with abas[2]:
    renderizar_ida()

with abas[3]:
    renderizar_ieg()

with abas[4]:
    renderizar_iaa()

with abas[5]:
    renderizar_ips()

with abas[6]:
    renderizar_ipp()

with abas[7]:
    renderizar_ipv()

with abas[8]:
    renderizar_inde(base)
