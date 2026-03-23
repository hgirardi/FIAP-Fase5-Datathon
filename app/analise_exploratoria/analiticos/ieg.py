from __future__ import annotations

"""Gera e valida o artefato analítico da aba IEG.

Entrada:
- DataFrame anual consolidado da base do projeto, com IEG, IDA, IPV e colunas auxiliares.

Saída:
- DataFrame enriquecido com campos derivados usados nas leituras do IEG.
- Parquet analítico consumido pela aba IEG no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `03_AED_IEG.ipynb` chama `exportar_base_analitica_ieg(df)` ao final da análise.
- Este módulo replica os ajustes metodológicos usados no app e prepara os perfis combinados.
- O resultado é salvo em `data/db/02_gold_analytics/ieg_analitico.parquet`.
- A aba `analise_exploratoria/abas/ieg.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IEG, CAMINHO_CONTRATO_ANALYTICS_IEG


COLUNAS_IEG_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IEG",
    "IDA",
    "IPV",
    "nivel_label",
    "quadrante_ieg_ida",
]


def _classificar_quadrante(serie_ieg: pd.Series, serie_ida: pd.Series) -> pd.Series:
    """Classifica o quadrante de engajamento e desempenho usando as medianas válidas."""
    mediana_ieg = serie_ieg.median()
    mediana_ida = serie_ida.median()

    return np.select(
        [
            (serie_ieg >= mediana_ieg) & (serie_ida >= mediana_ida),
            (serie_ieg >= mediana_ieg) & (serie_ida < mediana_ida),
            (serie_ieg < mediana_ieg) & (serie_ida >= mediana_ida),
        ],
        [
            "Engajado + Bom desempenho",
            "Engajado + Baixo desempenho",
            "Desengajado + Bom desempenho",
        ],
        default="Desengajado + Baixo desempenho",
    )


def gerar_base_analitica_ieg(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com os campos auxiliares usados na aba IEG."""
    base = df.copy()

    # Mantém a correção de não avaliados em 2024 para preservar a leitura do notebook.
    nao_avaliados = (base["ano"] == 2024) & base["IAA"].isna()
    for coluna in ["IDA", "IEG"]:
        mascara = nao_avaliados & (base[coluna] == 0)
        base.loc[mascara, coluna] = np.nan

    base["nivel_label"] = base["nivel"].fillna("N/D").astype(str).str.strip().str.upper()

    # O quadrante resume os quatro perfis usados na leitura executiva da aba.
    validos_quadrante = base[["IEG", "IDA"]].notna().all(axis=1)
    base["quadrante_ieg_ida"] = pd.NA
    base.loc[validos_quadrante, "quadrante_ieg_ida"] = _classificar_quadrante(
        base.loc[validos_quadrante, "IEG"],
        base.loc[validos_quadrante, "IDA"],
    )

    return base.sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_ieg(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IEG."""
    faltantes = [coluna for coluna in COLUNAS_IEG_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IEG incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ieg(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IEG
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ieg(df)
    validar_base_analitica_ieg(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato deixa explícito quais colunas a aba espera consumir.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IEG para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IEG_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IEG.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IEG.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IEG.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

