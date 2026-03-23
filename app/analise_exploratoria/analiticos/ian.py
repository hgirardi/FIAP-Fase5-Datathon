from __future__ import annotations

"""Gera e valida o artefato analítico da aba IAN.

Entrada:
- DataFrame anual consolidado da base do projeto, com colunas como RA, ano, IAN e indicadores complementares.

Saída:
- DataFrame enriquecido com colunas derivadas de coorte e transição anual.
- Parquet analítico consumido pela aba IAN no Streamlit.
- JSON simples com o contrato mínimo de colunas esperado pela aba.

Lógica de uso:
- O notebook `01_AED_IAN.ipynb` chama `exportar_base_analitica_ian(df)` ao final da análise.
- Este módulo prepara a base, replica ajustes metodológicos do estudo e gera colunas auxiliares.
- O resultado é salvo em `data/db/02_gold_analytics/ian_analitico.parquet`.
- A aba `analise_exploratoria/abas/ian.py` lê esse arquivo para montar os gráficos sem refazer toda a lógica no app.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_exploratoria.constantes import CAMINHO_ANALYTICS_IAN, CAMINHO_CONTRATO_ANALYTICS_IAN, ORDEM_NIVEIS


COLUNAS_IAN_ANALITICO_OBRIGATORIAS = [
    "RA",
    "ano",
    "IAN",
    "defasagem",
    "nivel_label",
    "nivel_ordem",
    "tipo_escola_macro",
    "status_ian",
    "grupo_ian",
    "em_defasagem",
    "IDA",
    "IEG",
    "IAA",
    "IPS",
    "IPP",
    "IPV",
    "INDE",
    "registro_coorte",
    "coorte_ian",
    "evolucao_ian",
    "transicao_ian",
]


def _normalizar_nivel(valor: object) -> str:
    """Padroniza o rótulo do nível para manter a ordenação do app."""
    if pd.isna(valor):
        return "N/D"
    return str(valor).strip().upper()


def _normalizar_escola(valor: object) -> str:
    """Agrupa nomes de instituição em macrogrupos usados nos gráficos."""
    if pd.isna(valor):
        return "Outro/Não informado"

    texto = str(valor).strip().lower()
    if not texto:
        return "Outro/Não informado"
    if "pública" in texto or "publica" in texto:
        return "Pública"
    if any(
        token in texto
        for token in [
            "privada",
            "bolsa",
            "decisão",
            "decisao",
            "rede",
            "jp ii",
            "apadrinhamento",
            "parceira",
            "universitário",
            "universitario",
            "formado",
            "concluiu",
        ]
    ):
        return "Privada"
    return "Outro/Não informado"


def _classificar_evolucao_ian(ian_inicio: float, ian_fim: float) -> str:
    """Resume a trajetória do aluno dentro da coorte observada."""
    if ian_inicio == 10 and ian_fim == 10:
        return "Manteve adequado"
    if ian_fim == 10 and ian_inicio < 10:
        return "Recuperou"
    if ian_fim > ian_inicio:
        return "Melhorou"
    if ian_fim < ian_inicio:
        return "Piorou"
    return "Estável (defasado)"


def _classificar_transicao_ian(ian_atual: float, ian_proximo: float) -> str:
    """Classifica a mudança entre anos consecutivos para leitura temporal."""
    adequado_atual = ian_atual == 10
    adequado_proximo = ian_proximo == 10
    if adequado_atual and adequado_proximo:
        return "Manteve adequado"
    if adequado_atual and not adequado_proximo:
        return "Piorou"
    if not adequado_atual and adequado_proximo:
        return "Recuperou"
    return "Manteve defasado"


def gerar_base_analitica_ian(df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece a base anual com colunas de coorte e transição do IAN."""
    base = df.copy()

    # Replica a correção já usada na análise: zeros em 2024 podem significar não avaliados.
    nao_avaliados = (base["ano"] == 2024) & base["IAA"].isna()
    for coluna in ["IDA", "IEG"]:
        mascara = nao_avaliados & (base[coluna] == 0)
        base.loc[mascara, coluna] = np.nan

    # Padroniza os campos de leitura para que notebook e app usem os mesmos rótulos.
    base["nivel_label"] = base["nivel"].apply(_normalizar_nivel)
    base["nivel_ordem"] = base["nivel_label"].map(ORDEM_NIVEIS)
    base["tipo_escola_macro"] = base["instituicao"].apply(_normalizar_escola)
    base["status_ian"] = base["IAN"].map({10.0: "Em fase", 5.0: "Defasagem moderada", 2.5: "Defasagem severa"})
    base["grupo_ian"] = base["IAN"].map({10.0: "Adequado (10.0)", 5.0: "Moderada (5.0)", 2.5: "Severa (2.5)"})
    base["em_defasagem"] = base["IAN"] < 10

    linhas: list[dict[str, object]] = []
    colunas_proximo = [
        "IAN",
        "IDA",
        "IEG",
        "IAA",
        "IPS",
        "IPP",
        "IPV",
        "INDE",
        "nivel_label",
        "nivel_ordem",
        "tipo_escola_macro",
        "status_ian",
        "grupo_ian",
        "em_defasagem",
    ]

    for ra, grupo in base.sort_values(["RA", "ano"]).groupby("RA"):
        grupo = grupo.sort_values("ano").reset_index(drop=True)
        primeiro = grupo.iloc[0]
        ultimo = grupo.iloc[-1]
        n_anos = int(grupo["ano"].nunique())
        possui_coorte = n_anos >= 2 and int(primeiro["ano"]) in [2022, 2023]
        coorte_ian = f"Desde {int(primeiro['ano'])}" if possui_coorte else pd.NA
        evolucao_ian = _classificar_evolucao_ian(primeiro["IAN"], ultimo["IAN"]) if possui_coorte else pd.NA

        for indice in range(len(grupo)):
            atual = grupo.iloc[indice]
            linha = atual.to_dict()

            # A leitura de coorte fica só na primeira linha do aluno para evitar duplicidade.
            linha["registro_coorte"] = bool(indice == 0 and possui_coorte)
            linha["coorte_ian"] = coorte_ian if indice == 0 and possui_coorte else pd.NA
            linha["evolucao_ian"] = evolucao_ian if indice == 0 and possui_coorte else pd.NA
            linha["IAN_inicio"] = primeiro["IAN"] if indice == 0 and possui_coorte else pd.NA
            linha["IAN_fim"] = ultimo["IAN"] if indice == 0 and possui_coorte else pd.NA
            linha["ano_inicio_ian"] = int(primeiro["ano"]) if indice == 0 and possui_coorte else pd.NA
            linha["ano_fim_ian"] = int(ultimo["ano"]) if indice == 0 and possui_coorte else pd.NA
            linha["n_anos_ian"] = n_anos if indice == 0 and possui_coorte else pd.NA

            # As colunas *_proximo existem apenas quando a transição anual é consecutiva.
            if indice < len(grupo) - 1 and int(grupo.iloc[indice + 1]["ano"]) == int(atual["ano"]) + 1:
                proximo = grupo.iloc[indice + 1]
                linha["ano_proximo"] = int(proximo["ano"])
                for coluna in colunas_proximo:
                    linha[f"{coluna}_proximo"] = proximo[coluna]
                linha["transicao_ian"] = _classificar_transicao_ian(atual["IAN"], proximo["IAN"])
            else:
                linha["ano_proximo"] = pd.NA
                for coluna in colunas_proximo:
                    linha[f"{coluna}_proximo"] = pd.NA
                linha["transicao_ian"] = pd.NA

            linhas.append(linha)

    resultado = pd.DataFrame(linhas).sort_values(["RA", "ano"]).reset_index(drop=True)
    return resultado


def validar_base_analitica_ian(df: pd.DataFrame) -> None:
    """Confere o contrato mínimo esperado pela aba do IAN."""
    faltantes = [coluna for coluna in COLUNAS_IAN_ANALITICO_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(f"Base analitica do IAN incompleta. Colunas ausentes: {faltantes}")


def exportar_base_analitica_ian(df: pd.DataFrame, caminho_saida: Path | None = None) -> Path:
    """Gera o parquet analítico e salva o contrato de colunas da aba."""
    caminho = caminho_saida or CAMINHO_ANALYTICS_IAN
    caminho.parent.mkdir(parents=True, exist_ok=True)

    base_analitica = gerar_base_analitica_ian(df)
    validar_base_analitica_ian(base_analitica)
    base_analitica.to_parquet(caminho, index=False)

    # O contrato facilita a manutenção quando a aba for evoluída ou replicada.
    contrato = {
        "arquivo": caminho.name,
        "descricao": "Base analitica enriquecida da aba IAN para o Streamlit.",
        "colunas_obrigatorias": COLUNAS_IAN_ANALITICO_OBRIGATORIAS,
        "observacao": "As colunas de coorte valem apenas na primeira linha de cada aluno elegivel; as colunas *_proximo valem apenas quando existe transicao anual consecutiva.",
    }
    CAMINHO_CONTRATO_ANALYTICS_IAN.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_CONTRATO_ANALYTICS_IAN.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    return caminho
