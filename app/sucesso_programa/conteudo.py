from __future__ import annotations

from pathlib import Path

import yaml


CAMINHO_RESPOSTAS = Path(__file__).resolve().parent / "config" / "respostas.yaml"


def carregar_perguntas_sucesso() -> list[dict]:
    """Lê o conteúdo editorial da página Sucesso do Programa."""
    conteudo = yaml.safe_load(CAMINHO_RESPOSTAS.read_text(encoding="utf-8")) or {}
    return conteudo.get("perguntas", [])
