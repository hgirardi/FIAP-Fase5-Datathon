from __future__ import annotations

"""Gera e valida o artefato analítico da aba IDA.

Entrada:
- DataFrame anual consolidado da base do projeto, com RA, ano, IDA e colunas de apoio.

Saída:
- DataFrame enriquecido com campos auxiliares para as leituras da aba IDA.
- Parquet analítico consumido pela aba IDA no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `02_AED_IDA.ipynb` chama `exportar_base_analitica_ida(df)` ao final da análise.
- Este módulo replica os ajustes metodológicos usados no app e adiciona rótulos derivados.
- O resultado é salvo em `data/db/02_gold_analytics/ida_analitico.parquet`.
- A aba `analise_exploratoria/abas/ida.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IDA, CAMINHO_CONTRATO_ANALYTICS_IDA, ORDEM_NIVEIS


COLUNAS_IDA_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IDA",
    "IAN",
    "nivel_label",
    "nivel_ordem",
    "grupo_ian",
    "primeiro_ano",
    "tipo_aluno",
]


def _normalizar_nivel(valor: object) -> str:
    """Padroniza o rótulo do nível para manter a ordenação da aba."""
    if pd.isna(valor):
        return "N/D"
    return str(valor).strip().upper()


def gerar_base_analitica_ida(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com os campos auxiliares usados na aba IDA."""
    base = df.copy()

    # Replica a correção metodológica já aplicada no app para registros não avaliados em 2024.
    nao_avaliados = (base["ano"] == 2024) & base["IAA"].isna()
    mascara_ida = nao_avaliados & (base["IDA"] == 0)
    base.loc[mascara_ida, "IDA"] = np.nan

    base["nivel_label"] = base["nivel"].apply(_normalizar_nivel)
    base["nivel_ordem"] = base["nivel_label"].map(ORDEM_NIVEIS)
    base["grupo_ian"] = base["IAN"].map(
        {
            10.0: "Adequado (10.0)",
            5.0: "Moderada (5.0)",
            2.5: "Severa (2.5)",
        }
    )

    # O tipo do aluno é definido a partir do primeiro ano observado na base consolidada.
    primeiro_ano = base.groupby("RA")["ano"].transform("min")
    base["primeiro_ano"] = primeiro_ano
    base["tipo_aluno"] = np.where(base["ano"] == primeiro_ano, "Ingressante", "Veterano")

    return base.sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_ida(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IDA."""
    faltantes = [coluna for coluna in COLUNAS_IDA_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IDA incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ida(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IDA
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ida(df)
    validar_base_analitica_ida(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato deixa explícito quais colunas a aba espera consumir.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IDA para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IDA_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IDA.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IDA.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IDA.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

