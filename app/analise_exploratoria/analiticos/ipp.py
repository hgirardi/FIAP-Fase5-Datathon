from __future__ import annotations

"""Gera e valida o artefato analítico da aba IPP.

Entrada:
- DataFrame anual consolidado da base do projeto, com IPP, IAN e progressão anual.

Saída:
- DataFrame anual enriquecido com concordância e transições consecutivas.
- Parquet analítico consumido pela aba IPP no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `06_AED_IPP.ipynb` chama `exportar_base_analitica_ipp(df)` ao final da análise.
- Este módulo preserva os registros anuais e adiciona os campos necessários para as leituras de concordância e evolução.
- O resultado é salvo em `data/db/02_gold_analytics/ipp_analitico.parquet`.
- A aba `analise_exploratoria/abas/ipp.py` lê esse arquivo para montar os gráficos sem recalcular a análise no Streamlit.
"""

import json
from pathlib import Path

import pandas as pd

from analise_exploratoria.apoio import concordancia_ipp, normalizar_nivel
from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IPP, CAMINHO_CONTRATO_ANALYTICS_IPP, ORDEM_NIVEIS


COLUNAS_IPP_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IPP",
    "IAN",
    "grupo_ian",
    "concordancia_ipp",
    "nivel_label",
    "nivel_ordem",
    "ano_proximo",
    "transicao",
    "IPP_proximo",
    "IAN_proximo",
    "delta_IPP",
    "avancou_fase",
]


def gerar_base_analitica_ipp(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com concordância e transições do IPP."""
    base = df.copy().sort_values(["RA", "ano"]).reset_index(drop=True)

    base["nivel_label"] = base["nivel"].apply(normalizar_nivel)
    base["nivel_ordem"] = base["nivel_label"].map(ORDEM_NIVEIS)
    base["grupo_ian"] = base["IAN"].map(
        {
            10.0: "Adequado (10.0)",
            5.0: "Moderada (5.0)",
            2.5: "Severa (2.5)",
        }
    )

    mediana_ipp = base["IPP"].median()
    validos = base[["IPP", "IAN"]].notna().all(axis=1)
    base.loc[validos, "concordancia_ipp"] = base.loc[validos].apply(
        lambda row: concordancia_ipp(row, mediana_ipp), axis=1
    )

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
                linha["IPP_proximo"] = proximo["IPP"]
                linha["IAN_proximo"] = proximo["IAN"]
                linha["nivel_ordem_proximo"] = proximo["nivel_ordem"]
                linha["delta_IPP"] = proximo["IPP"] - atual["IPP"] if pd.notna(proximo["IPP"]) and pd.notna(atual["IPP"]) else pd.NA
                if pd.notna(proximo["nivel_ordem"]) and pd.notna(atual["nivel_ordem"]):
                    linha["avancou_fase"] = bool(proximo["nivel_ordem"] > atual["nivel_ordem"])
                else:
                    linha["avancou_fase"] = pd.NA
            else:
                linha["ano_proximo"] = pd.NA
                linha["transicao"] = pd.NA
                linha["IPP_proximo"] = pd.NA
                linha["IAN_proximo"] = pd.NA
                linha["nivel_ordem_proximo"] = pd.NA
                linha["delta_IPP"] = pd.NA
                linha["avancou_fase"] = pd.NA

            linhas.append(linha)

    return pd.DataFrame(linhas).sort_values(["RA", "ano"]).reset_index(drop=True)


def validar_base_analitica_ipp(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IPP."""
    faltantes = [coluna for coluna in COLUNAS_IPP_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IPP incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ipp(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IPP
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ipp(df)
    validar_base_analitica_ipp(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato deixa explícito quais colunas a aba espera consumir.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IPP para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IPP_ANALITICO_OBRIGATORIAS,
        "observacao": "A base preserva os registros anuais originais e adiciona somente os campos auxiliares usados nos graficos do IPP.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IPP.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IPP.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho

