from __future__ import annotations

import streamlit as st
from components.layout import layout

layout("Home")


def renderizar_bloco_funcionalidade(titulo: str, descricao: str, itens: list[str], destaque: str, borda: str) -> None:
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid {borda};
            min-height: 470px;
            height: auto;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 1rem;
            overflow-wrap: break-word;
            word-break: break-word;
        ">
            <div>
                <h3>{titulo}</h3>
                <p>{descricao}</p>
                <ul>
                    {''.join(f'<li>{item}</li>' for item in itens)}
                </ul>
            </div>
            <p><strong>{destaque}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Header
st.markdown("""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
    <h1>🔮 Sistema Preditivo de Defasagem Escolar</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">
        Utilizando Machine Learning para identificar alunos em risco de defasagem
    </p>
</div>
""", unsafe_allow_html=True)

# Introdução
st.markdown("### 👋 Bem-vindo!")
st.write("""
Este sistema foi desenvolvido como parte do **Datathon 2025** da FIAP, 
em parceria com a **Associação Passos Mágicos**, com o objetivo de criar uma 
ferramenta inteligente para identificar alunos em risco de defasagem escolar.
""")

st.divider()

# Funcionalidades
st.markdown("### Funcionalidades")

col1, col2, col3, col4 = st.columns(4)

with col1:
    renderizar_bloco_funcionalidade(
        "🤖 Predição de Risco",
        "Formulário para avaliação individual de risco de defasagem baseado em:",
        [
            "Indicadores PEDE (IDA, IPS, IPP, IPV)",
            "Situação de defasagem atual (IAN)",
            "Nível e tipo de escola",
        ],
        "→ Resultado com probabilidade, faixa de risco e recomendações",
        "#3498db",
    )

    if st.button("🤖 Acessar Predição de Risco", use_container_width=True):
        st.switch_page("pages/predicao.py")

with col2:
    renderizar_bloco_funcionalidade(
        "🔍 Análise Exploratória",
        "Painel de análise dos indicadores educacionais e psicossociais para apoiar a leitura dos dados dos alunos:",
        [
            "Evolução de desempenho, defasagem, engajamento e permanência",
            "Gráficos interativos com recortes por ano, nível e perfil",
            "Leituras que ajudam a identificar prioridades de acompanhamento",
        ],
        "→ Apoio à compreensão dos dados e à tomada de decisão da ONG",
        "#9b59b6",
    )

    if st.button("🔍 Acessar Análise Exploratória", use_container_width=True):
        st.switch_page("pages/analise_exploratoria.py")

with col3:
    renderizar_bloco_funcionalidade(
        "🎯 Sucesso do Programa",
        "Respostas executivas para as principais perguntas do projeto, organizadas em blocos objetivos:",
        [
            "Conclusões diretas para cada pergunta obrigatória",
            "Gráficos que sustentam cada resposta",
            "Leitura orientada ao impacto do programa",
        ],
        "→ Síntese dos resultados para apresentação e tomada de decisão",
        "#f39c12",
    )

    if st.button("🎯 Acessar Sucesso do Programa", use_container_width=True):
        st.switch_page("pages/sucesso_programa.py")

with col4:
    renderizar_bloco_funcionalidade(
        "📋 Sobre o Modelo",
        "Informações técnicas sobre o modelo preditivo:",
        [
            "Features utilizadas e importância",
            "Métricas de performance (AUC, Acurácia)",
            "Faixas de risco e validação",
            "Limitações e fonte dos dados",
        ],
        "→ Transparência sobre como o modelo funciona",
        "#2ecc71",
    )

    if st.button("📋 Sobre o Modelo", use_container_width=True):
        st.switch_page("pages/sobre.py")

st.divider()

# Métricas do modelo
st.markdown("### 📈 Sobre o Modelo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">
        <h2>1,369</h2>
        <p>Pares de<br>Treino</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">
        <h2>8</h2>
        <p>Features<br>Selecionadas</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">
        <h2>87%</h2>
        <p>AUC-ROC<br>do Modelo</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">
        <h2>~81%</h2>
        <p>Acurácia<br>do Modelo</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Sobre o projeto
st.markdown("### 👨‍💻 Sobre o Projeto")

st.markdown("""
<div style="background-color: #e7f3ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #2196F3;">
    <h4>📚 FIAP — Datathon 2024</h4>
    <p><strong>Aluno:</strong> Henrique Girardi dos Santos</p>
    <p><strong>RM:</strong> 362082</p>
    <p><strong>Curso:</strong> Pós-graduação em Data Analytics</p>
    <p><strong>Objetivo:</strong> Desenvolver um sistema de predição de defasagem escolar utilizando 
    técnicas de Machine Learning para auxiliar a ONG Passos Mágicos na identificação 
    precoce de alunos em risco.</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>FIAP | Datathon 2024 | Henrique Girardi</p>
    <p style="font-size: 0.9rem;">
        Este sistema é uma ferramenta de apoio à decisão e não substitui a avaliação profissional.
    </p>
</div>
""", unsafe_allow_html=True)
