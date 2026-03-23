from __future__ import annotations

"""Gera e valida o artefato analítico da aba IPV.

Entrada:
- DataFrame anual consolidado da base do projeto, com IPV e indicadores auxiliares.

Saída:
- DataFrame anual enriquecido com colunas de transição para o ano seguinte.
- Parquet analítico consumido pela aba IPV no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `07_AED_IPV.ipynb` chama `exportar_base_analitica_ipv(df)` ao final da análise.
- Este módulo preserva os registros anuais e adiciona os campos necessários para as leituras temporais.
- O resultado é salvo em `data/db/02_gold_analytics/ipv_analitico.parquet`.
- A aba `analise_exploratoria/abas/ipv.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import pandas as pd

from analise_exploratoria.apoio import normalizar_nivel
from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IPV, CAMINHO_CONTRATO_ANALYTICS_IPV


COLUNAS_IPV_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IPV",
    "IDA",
    "IEG",
    "IAA",
    "IPS",
    "IPP",
    "IAN",
    "nivel_label",
    "ano_proximo",
    "transicao",
    "IPV_proximo",
]


def gerar_base_analitica_ipv(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com as transições temporais usadas na aba IPV."""
    base = df.copy().sort_values(["RA", "ano"]).reset_index(drop=True)
    base["nivel_label"] = base["nivel"].apply(normalizar_nivel)

    indicadores = ["IPV", "IDA", "IEG", "IAA", "IPS", "IPP", "IAN"]
    linhas: list[dict[str, object]] = []

    for _, grupo in base.groupby("RA", sort=False):
        grupo = grupo.sort_values("ano").reset_index(drop=True)

        for indice in range(len(grupo)):
            atual = grupo.iloc[indice]
            linha = atual.to_dict()

            # As colunas temporais existem apenas quando a transição anual é consecutiva.
            if indice < len(grupo) - 1 and int(grupo.iloc[indice + 1]["ano"]) == int(atual["ano"]) + 1:
                proximo = grupo.iloc[indice + 1]
                linha["ano_proximo"] = int(proximo["ano"])
                linha["transicao"] = f"{int(atual['ano'])}->{int(proximo['ano'])}"
                for indicador in indicadores:
                    linha[f"{indicador}_proximo"] = proximo[indicador]
            else:
                linha["ano_proximo"] = pd.NA
                linha["transicao"] = pd.NA
                for indicador in indicadores:
                    linha[f"{indicador}_proximo"] = pd.NA

            linhas.append(linha)

    return pd.DataFrame(linhas).sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_ipv(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IPV."""
    faltantes = [coluna for coluna in COLUNAS_IPV_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IPV incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ipv(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IPV
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ipv(df)
    validar_base_analitica_ipv(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IPV para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IPV_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IPV.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IPV.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IPV.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

