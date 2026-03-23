# Datathon FIAP - Fase 5

Projeto desenvolvido para a Passos Mágicos com foco em análise de indicadores educacionais e predição de risco de defasagem escolar.

## O que tem neste repositório

- `app/`: aplicação em Streamlit
- `notebooks/`: análises exploratórias, preparação da base e modelagem
- `data/`: bases, artefatos analíticos e modelos salvos

## Principais entregas

- análise exploratória dos indicadores do PEDE
- modelo preditivo para classificação de risco de defasagem
- aplicação em Streamlit para visualização e uso do modelo

## Como rodar a aplicação

Na raiz do projeto:

```bash
streamlit run app/app.py
```

## Estrutura da aplicação

A aplicação está organizada em quatro frentes principais:

- `Predição de Risco`: formulário para estimativa da faixa de risco do aluno
- `Análise Exploratória`: leitura visual dos principais indicadores e achados
- `Sucesso do Programa`: respostas diretas às perguntas centrais do projeto
- `Sobre o Modelo`: visão geral das variáveis e desempenho do modelo

## Observação

Os notebooks foram mantidos como base analítica do projeto, e parte das saídas geradas neles é reutilizada pela aplicação por meio de arquivos em `parquet`.
