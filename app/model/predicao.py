import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from bisect import bisect_left

from model.config import MODELO_PATH, PERCENTIS_PATH, FAIXAS_RISCO


@st.cache_resource
def carregar_modelo():
    """Carrega modelo e metadados do joblib (com cache)."""
    dados = joblib.load(MODELO_PATH)
    return dados['modelo'], dados['features']


@st.cache_resource
def carregar_percentis():
    """Carrega percentis de 2024 para normalização (com cache)."""
    with open(PERCENTIS_PATH, 'r') as f:
        return json.load(f)


def calcular_percentil(valor, distribuicao):
    """Calcula o percentil de um valor em relação à distribuição de 2024."""
    if np.isnan(valor):
        return np.nan
    pos = bisect_left(distribuicao, valor)
    return pos / len(distribuicao)


def calcular_ian(fase_atual, fase_ideal):
    """Calcula o IAN baseado na diferença entre fase atual e ideal."""
    d = fase_atual - fase_ideal
    if d >= 0:
        return 10.0
    elif d >= -2:
        return 5.0
    else:
        return 2.5


def classificar_faixa(probabilidade):
    """Classifica a probabilidade em uma faixa de risco."""
    for nome, faixa in FAIXAS_RISCO.items():
        if faixa['min'] <= probabilidade < faixa['max']:
            return nome, faixa
    return 'Muito alto', FAIXAS_RISCO['Muito alto']


def gerar_recomendacoes(dados_aluno):
    """Gera recomendações baseadas nos indicadores do aluno."""
    recs = []

    if dados_aluno.get('IAN', 10) < 10:
        recs.append('📚 Aluno está defasado — acompanhamento acadêmico prioritário para recuperação de nível')

    if dados_aluno.get('nivel_num', 0) <= 2:
        recs.append('⚠️ Aluno nos níveis iniciais (ALFA-2) — período de maior vulnerabilidade para defasagem')

    if dados_aluno.get('IPV_norm', 1) < 0.25:
        recs.append('🎯 Ponto de Virada baixo — incentivar engajamento e participação ativa no programa')

    if dados_aluno.get('IPP_norm', 1) < 0.25:
        recs.append('🧠 Avaliação psicopedagógica baixa — considerar acompanhamento individualizado')

    if dados_aluno.get('IDA_norm', 1) < 0.25:
        recs.append('📖 Desempenho acadêmico no quartil inferior — reforço em disciplinas específicas')

    if dados_aluno.get('resiliencia', 0) < -3:
        recs.append('💪 Gap IPP-IAN muito negativo — suporte emocional e motivacional')

    if dados_aluno.get('tipo_escola', 1) == 0:
        recs.append('🏫 Aluno de escola pública — grupo com maior taxa histórica de defasagem e abandono')

    if not recs:
        recs.append('✅ Indicadores dentro dos padrões esperados — manter acompanhamento regular')

    return recs


def prever_risco(ida, ips, ipp, ipv, ian, nivel_num, tipo_escola):
    """
    Recebe indicadores brutos, normaliza e retorna a predição.
    Retorna: (probabilidade, faixa_nome, faixa_info, recomendações, dados_normalizados)
    """
    modelo, features = carregar_modelo()
    percentis = carregar_percentis()

    # Normalizar indicadores
    ida_norm = calcular_percentil(ida, percentis['IDA'])
    ips_norm = calcular_percentil(ips, percentis['IPS'])
    ipp_norm = calcular_percentil(ipp, percentis['IPP'])
    ipv_norm = calcular_percentil(ipv, percentis['IPV'])

    # Calcular gap IPP-IAN
    resiliencia = ipp - ian

    # Montar features
    dados = {
        'IDA_norm': ida_norm,
        'IPS_norm': ips_norm,
        'IPP_norm': ipp_norm,
        'IPV_norm': ipv_norm,
        'IAN': ian,
        'resiliencia': resiliencia,
        'nivel_num': nivel_num,
        'tipo_escola': tipo_escola,
    }

    df_input = pd.DataFrame([dados])[features]

    # Predição
    probabilidade = modelo.predict_proba(df_input)[0][1]
    faixa_nome, faixa_info = classificar_faixa(probabilidade)
    recomendacoes = gerar_recomendacoes(dados)

    return probabilidade, faixa_nome, faixa_info, recomendacoes, dados
