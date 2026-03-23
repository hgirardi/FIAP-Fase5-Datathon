from __future__ import annotations

from pathlib import Path


"""Centraliza os caminhos usados pelo app Streamlit.

Os notebooks seguem independentes. Este módulo existe apenas para evitar
repetição de caminhos no código da aplicação.
"""

# A raiz é derivada a partir do próprio app para manter o import estável.
RAIZ_PROJETO = Path(__file__).resolve().parents[2]

PASTA_DB = RAIZ_PROJETO / "data" / "db"
PASTA_MODELOS = RAIZ_PROJETO / "data" / "models"

CAMINHO_DF_BASE_2 = PASTA_DB / "01_silver_processed" / "df_base_2.parquet"
CAMINHO_IAN_ANALITICO = PASTA_DB / "02_gold_analytics" / "ian_analitico.parquet"
CAMINHO_IAN_CONTRATO = PASTA_DB / "02_gold_analytics" / "ian_analitico_contrato.json"
CAMINHO_IDA_ANALITICO = PASTA_DB / "02_gold_analytics" / "ida_analitico.parquet"
CAMINHO_IDA_CONTRATO = PASTA_DB / "02_gold_analytics" / "ida_analitico_contrato.json"
CAMINHO_IEG_ANALITICO = PASTA_DB / "02_gold_analytics" / "ieg_analitico.parquet"
CAMINHO_IEG_CONTRATO = PASTA_DB / "02_gold_analytics" / "ieg_analitico_contrato.json"
CAMINHO_IAA_ANALITICO = PASTA_DB / "02_gold_analytics" / "iaa_analitico.parquet"
CAMINHO_IAA_CONTRATO = PASTA_DB / "02_gold_analytics" / "iaa_analitico_contrato.json"
CAMINHO_IPS_ANALITICO = PASTA_DB / "02_gold_analytics" / "ips_analitico.parquet"
CAMINHO_IPS_CONTRATO = PASTA_DB / "02_gold_analytics" / "ips_analitico_contrato.json"
CAMINHO_IPP_ANALITICO = PASTA_DB / "02_gold_analytics" / "ipp_analitico.parquet"
CAMINHO_IPP_CONTRATO = PASTA_DB / "02_gold_analytics" / "ipp_analitico_contrato.json"
CAMINHO_IPV_ANALITICO = PASTA_DB / "02_gold_analytics" / "ipv_analitico.parquet"
CAMINHO_IPV_CONTRATO = PASTA_DB / "02_gold_analytics" / "ipv_analitico_contrato.json"
CAMINHO_MODELO_RISCO = PASTA_MODELOS / "modelo_risco_defasagem.joblib"
CAMINHO_PERCENTIS_2024 = PASTA_MODELOS / "percentis_2024.json"
