from __future__ import annotations

"""Gera e valida o artefato analítico da aba IPS.

Entrada:
- DataFrame anual consolidado da base do projeto, com IPS e indicadores temporais auxiliares.

Saída:
- DataFrame anual enriquecido com colunas de transição para o ano seguinte.
- Parquet analítico consumido pela aba IPS no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `05_AED_IPS.ipynb` chama `exportar_base_analitica_ips(df)` ao final da análise.
- Este módulo preserva os registros anuais e adiciona os campos necessários para as leituras temporais.
- O resultado é salvo em `data/db/02_gold_analytics/ips_analitico.parquet`.
- A aba `analise_exploratoria/abas/ips.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IPS, CAMINHO_CONTRATO_ANALYTICS_IPS, FAIXAS_IPS


COLUNAS_IPS_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "turma",
    "IPS",
    "faixa_IPS",
    "ano_proximo",
    "transicao",
    "delta_IDA",
    "delta_IEG",
    "caiu_IDA",
    "caiu_IEG",
]


def gerar_base_analitica_ips(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com as transições temporais usadas na aba IPS."""
    base = df.copy().sort_values(["RA", "ano"]).reset_index(drop=True)

    # A faixa é calculada no registro atual para manter a leitura temporal do notebook.
    base["faixa_IPS"] = pd.cut(
        base["IPS"],
        bins=[0, 4, 6, 8, 10],
        labels=FAIXAS_IPS,
        include_lowest=True,
    )

    linhas: list[dict[str, object]] = []
    colunas_proximo = ["IPS", "IDA", "IEG"]

    for ra, grupo in base.groupby("RA", sort=False):
        grupo = grupo.sort_values("ano").reset_index(drop=True)

        for indice in range(len(grupo)):
            atual = grupo.iloc[indice]
            linha = atual.to_dict()

            # As colunas temporais existem apenas quando a transição anual é consecutiva.
            if indice < len(grupo) - 1 and int(grupo.iloc[indice + 1]["ano"]) == int(atual["ano"]) + 1:
                proximo = grupo.iloc[indice + 1]
                linha["ano_proximo"] = int(proximo["ano"])
                linha["transicao"] = f"{int(atual['ano'])}->{int(proximo['ano'])}"
                for coluna in colunas_proximo:
                    linha[f"{coluna}_proximo"] = proximo[coluna]
                linha["delta_IDA"] = proximo["IDA"] - atual["IDA"] if pd.notna(proximo["IDA"]) and pd.notna(atual["IDA"]) else pd.NA
                linha["delta_IEG"] = proximo["IEG"] - atual["IEG"] if pd.notna(proximo["IEG"]) and pd.notna(atual["IEG"]) else pd.NA
                linha["caiu_IDA"] = bool(linha["delta_IDA"] < -1) if pd.notna(linha["delta_IDA"]) else pd.NA
                linha["caiu_IEG"] = bool(linha["delta_IEG"] < -1) if pd.notna(linha["delta_IEG"]) else pd.NA
            else:
                linha["ano_proximo"] = pd.NA
                linha["transicao"] = pd.NA
                for coluna in colunas_proximo:
                    linha[f"{coluna}_proximo"] = pd.NA
                linha["delta_IDA"] = pd.NA
                linha["delta_IEG"] = pd.NA
                linha["caiu_IDA"] = pd.NA
                linha["caiu_IEG"] = pd.NA

            linhas.append(linha)

    return pd.DataFrame(linhas).sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_ips(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IPS."""
    faltantes = [coluna for coluna in COLUNAS_IPS_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IPS incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ips(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IPS
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ips(df)
    validar_base_analitica_ips(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato deixa explícito quais colunas a aba espera consumir.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IPS para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IPS_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IPS.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IPS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IPS.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

