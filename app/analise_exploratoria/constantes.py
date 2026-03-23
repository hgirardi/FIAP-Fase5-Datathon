from __future__ import annotations

from utils.caminhos import (
    CAMINHO_DF_BASE_2,
    CAMINHO_IAN_ANALITICO,
    CAMINHO_IAN_CONTRATO,
    CAMINHO_IDA_ANALITICO,
    CAMINHO_IDA_CONTRATO,
    CAMINHO_IEG_ANALITICO,
    CAMINHO_IEG_CONTRATO,
    CAMINHO_IAA_ANALITICO,
    CAMINHO_IAA_CONTRATO,
    CAMINHO_IPS_ANALITICO,
    CAMINHO_IPS_CONTRATO,
    CAMINHO_IPP_ANALITICO,
    CAMINHO_IPP_CONTRATO,
    CAMINHO_IPV_ANALITICO,
    CAMINHO_IPV_CONTRATO,
)

# Caminhos dos artefatos analíticos consumidos pelas abas do Streamlit.
CAMINHO_DADOS = CAMINHO_DF_BASE_2
CAMINHO_ANALYTICS_IAN = CAMINHO_IAN_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IAN = CAMINHO_IAN_CONTRATO
CAMINHO_ANALYTICS_IDA = CAMINHO_IDA_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IDA = CAMINHO_IDA_CONTRATO
CAMINHO_ANALYTICS_IEG = CAMINHO_IEG_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IEG = CAMINHO_IEG_CONTRATO
CAMINHO_ANALYTICS_IAA = CAMINHO_IAA_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IAA = CAMINHO_IAA_CONTRATO
CAMINHO_ANALYTICS_IPS = CAMINHO_IPS_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IPS = CAMINHO_IPS_CONTRATO
CAMINHO_ANALYTICS_IPP = CAMINHO_IPP_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IPP = CAMINHO_IPP_CONTRATO
CAMINHO_ANALYTICS_IPV = CAMINHO_IPV_ANALITICO
CAMINHO_CONTRATO_ANALYTICS_IPV = CAMINHO_IPV_CONTRATO

ANOS = [2022, 2023, 2024]
ORDEM_NIVEIS = {
    "ALFA": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
}
NIVEIS = list(ORDEM_NIVEIS.keys())
ORDEM_PEDRAS = ["Quartzo", "Ágata", "Ametista", "Topázio"]
ORDEM_ESCOLAS = ["Pública", "Privada"]
GRUPOS_IAN = ["Severa (2.5)", "Moderada (5.0)", "Adequado (10.0)"]
FAIXAS_IPS = ["Baixo (<=4)", "Médio-baixo (4-6)", "Médio-alto (6-8)", "Alto (>8)"]
INDICADORES = ["IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV"]
INDICADORES_BASE = ["IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "INDE"]
PEDRA_PARA_NUMERO = {"Quartzo": 1, "Ágata": 2, "Ametista": 3, "Topázio": 4}
COLUNAS_PEDRA = {
    2020: "pedra_20",
    2021: "pedra_21",
    2022: "pedra_22",
    2023: "pedra_23",
    2024: "pedra_24",
}

CORES_STATUS = {
    "Em fase": "#15803d",
    "Defasagem moderada": "#f59e0b",
    "Defasagem severa": "#dc2626",
}
CORES_COHERENCIA = {
    "Subestima (< -2)": "#2563eb",
    "Subestima leve (-2 a -1)": "#7dd3fc",
    "Coerente (±1)": "#16a34a",
    "Superestima leve (1-2)": "#f59e0b",
    "Superestima (>2)": "#ea580c",
}
CORES_PEDRA = {
    "Quartzo": "#7c6f64",
    "Ágata": "#4f83c2",
    "Ametista": "#8b5fbf",
    "Topázio": "#d4a017",
}
CORES_ESCOLA = {
    "Pública": "#dc2626",
    "Privada": "#2563eb",
    "Outro/Não informado": "#94a3b8",
}
CORES_TRANSICAO = {
    "Caiu": "#dc2626",
    "Manteve": "#f59e0b",
    "Subiu": "#16a34a",
}
CORES_RISCO = {
    0: "#16a34a",
    1: "#86efac",
    2: "#fde68a",
    3: "#fb923c",
    4: "#ef4444",
    5: "#7f1d1d",
}
