from __future__ import annotations

"""Gera e valida o artefato analítico da aba IAA.

Entrada:
- DataFrame anual consolidado da base do projeto, com IAA, IDA, IEG e colunas auxiliares.

Saída:
- DataFrame enriquecido com campos derivados usados nas leituras do IAA.
- Parquet analítico consumido pela aba IAA no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `04_AED_IAA.ipynb` chama `exportar_base_analitica_iaa(df)` ao final da análise.
- Este módulo replica os ajustes metodológicos usados no app e prepara os gaps de coerência.
- O resultado é salvo em `data/db/02_gold_analytics/iaa_analitico.parquet`.
- A aba `analise_exploratoria/abas/iaa.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_exploratoria.apoio import coerencia_combinada, coerencia_detalhada, normalizar_nivel
from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IAA, CAMINHO_CONTRATO_ANALYTICS_IAA, ORDEM_NIVEIS


COLUNAS_IAA_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IAA",
    "IDA",
    "IEG",
    "nivel_label",
    "nivel_ordem",
    "gap_iaa_ida",
    "gap_iaa_ieg",
    "coerencia_iaa",
    "coerencia_combinada",
]


def gerar_base_analitica_iaa(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com os campos auxiliares usados na aba IAA."""
    base = df.copy()

    # Mantém a correção de não avaliados em 2024 para preservar a leitura do app.
    nao_avaliados = (base["ano"] == 2024) & base["IAA"].isna()
    for coluna in ["IDA", "IEG"]:
        mascara = nao_avaliados & (base[coluna] == 0)
        base.loc[mascara, coluna] = np.nan

    base["nivel_label"] = base["nivel"].apply(normalizar_nivel)
    base["nivel_ordem"] = base["nivel_label"].map(ORDEM_NIVEIS)
    base["gap_iaa_ida"] = base["IAA"] - base["IDA"]
    base["gap_iaa_ieg"] = base["IAA"] - base["IEG"]
    base["coerencia_iaa"] = base["gap_iaa_ida"].apply(coerencia_detalhada)

    validos_trio = base[["IAA", "IDA", "IEG"]].notna().all(axis=1)
    base["coerencia_combinada"] = pd.NA
    base.loc[validos_trio, "coerencia_combinada"] = base.loc[validos_trio].apply(coerencia_combinada, axis=1)

    return base.sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_iaa(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IAA."""
    faltantes = [coluna for coluna in COLUNAS_IAA_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IAA incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_iaa(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IAA
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_iaa(df)
    validar_base_analitica_iaa(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato deixa explícito quais colunas a aba espera consumir.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IAA para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IAA_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IAA.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IAA.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IAA.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

