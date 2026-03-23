from __future__ import annotations

import streamlit as st
from components.layout import layout

layout("Sobre o Modelo")

st.header('📋 Sobre o Modelo')

st.markdown('''
### Objetivo
Prever a probabilidade de um aluno da Associação Passos Mágicos entrar em 
**defasagem escolar** (IAN < 10) no ano seguinte, permitindo intervenção preventiva.

### Modelo
- **Algoritmo:** HistGradientBoostingClassifier (scikit-learn)
- **AUC (ROC):** 0.87 — o modelo distingue corretamente quem vai ficar defasado em 87% dos casos
- **Acurácia:** ~81% — 4 em cada 5 predições estão corretas

### Features utilizadas (8)

| Feature | Descrição | Tipo |
|---------|-----------|------|
| IDA_norm | Desempenho Acadêmico (percentil do ano) | Numérica |
| IPS_norm | Indicador Psicossocial (percentil do ano) | Numérica |
| IPP_norm | Indicador Psicopedagógico (percentil do ano) | Numérica |
| IPV_norm | Ponto de Virada (percentil do ano) | Numérica |
| IAN | Adequação de Nível (2.5, 5.0 ou 10.0) | Numérica |
| Gap IPP-IAN | IPP - IAN (progresso vs defasagem) | Derivada |
| nivel_num | Fase do aluno (0=ALFA a 8) | Numérica |
| tipo_escola | Pública (0) ou Privada (1) | Numérica |

### Importância das Features

Os fatores que mais influenciam a predição (por ordem):
1. **Nível** — alunos nos níveis iniciais (ALFA, 1, 2) têm maior risco
2. **IAN** — quem já está defasado tende a continuar
3. **IPV** — ponto de virada baixo antecede defasagem
4. **Gap IPP-IAN** — discrepância entre avaliação psicopedagógica e defasagem
5. **IPS** — indicador psicossocial
6. **IDA** — desempenho acadêmico
7. **IPP** — indicador psicopedagógico
8. **Tipo de escola** — escola pública tem mais risco

### Faixas de Risco

| Faixa | Probabilidade | % real de defasagem (validação) |
|-------|--------------|-------------------------------|
| 🟢 Muito baixo | < 20% | ~5% |
| 🟢 Baixo | 20-40% | ~27% |
| 🟡 Moderado | 40-60% | ~49% |
| 🟠 Alto | 60-80% | ~74% |
| 🔴 Muito alto | > 80% | ~94% |

### Limitações
- As features normalizadas usam os percentis de **2024** como referência
- O modelo foi treinado com dados de 2022-2024 (1369 pares aluno-ano)
- Mudanças metodológicas na coleta de indicadores podem afetar a precisão futura
- O modelo identifica **risco**, não **certeza** — deve ser usado como ferramenta de triagem

### Fonte dos Dados
Base de dados PEDE 2024 (Pesquisa Extensiva do Desenvolvimento Educacional) — 
Associação Passos Mágicos, Embu-Guaçu, SP.
''')
