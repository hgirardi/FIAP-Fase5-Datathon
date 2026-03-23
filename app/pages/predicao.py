from __future__ import annotations

import streamlit as st
from components.layout import layout
from model.config import NIVEIS, TIPOS_ESCOLA
from model.predicao import prever_risco, calcular_ian

layout("Predição de Risco")

st.header('🤖 Predição de Risco de Defasagem')
st.markdown(
    'Preencha os indicadores do aluno para estimar a probabilidade '
    'de defasagem no próximo ano.'
)

# Formulário
with st.form('form_predicao'):
    st.subheader('Dados do Aluno')

    col1, col2, col3 = st.columns(3)

    with col1:
        nivel = st.selectbox(
            'Fase Atual',
            options=list(NIVEIS.keys()),
            index=3,
            help='Fase atual do aluno na Passos Mágicos'
        )

        fase_ideal = st.selectbox(
            'Fase Ideal',
            options=list(NIVEIS.keys()),
            index=3,
            help='Fase ideal conforme a idade do aluno'
        )

        tipo_escola = st.selectbox(
            'Tipo de Escola',
            options=list(TIPOS_ESCOLA.keys()),
            help='Instituição de ensino do aluno'
        )

    with col2:
        ida = st.slider('IDA (Desempenho Acadêmico)', 0.0, 10.0, 6.5, 0.1,
                        help='Média das notas de Matemática, Português e Inglês')
        ips = st.slider('IPS (Psicossocial)', 0.0, 10.0, 6.5, 0.1,
                        help='Avaliação psicossocial do aluno')
        ipp = st.slider('IPP (Psicopedagógico)', 0.0, 10.0, 7.0, 0.1,
                        help='Avaliação psicopedagógica do aluno')

    with col3:
        ipv = st.slider('IPV (Ponto de Virada)', 0.0, 10.0, 7.0, 0.1,
                        help='Avaliação do ponto de virada do aluno')

    submitted = st.form_submit_button('Calcular Risco', type='primary', use_container_width=True)

# Resultado
if submitted:
    nivel_num = float(NIVEIS[nivel])
    fase_ideal_num = float(NIVEIS[fase_ideal])
    ian = calcular_ian(nivel_num, fase_ideal_num)
    escola_num = float(TIPOS_ESCOLA[tipo_escola])

    defasagem_label = {10.0: 'Em fase', 5.0: 'Moderada', 2.5: 'Severa'}

    prob, faixa_nome, faixa_info, recomendacoes, dados_norm = prever_risco(
        ida=ida, ips=ips, ipp=ipp, ipv=ipv,
        ian=ian, nivel_num=nivel_num, tipo_escola=escola_num
    )

    # Header com resultado
    st.divider()
    st.markdown(f"""
        <div style='
            background-color: {faixa_info['cor']}; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 5px solid {faixa_info['cor']};
            margin-bottom: 20px;
        '>
            <h2 style='margin:0;color: #333;'>
                {faixa_info['emoji']} Risco: {faixa_nome}
            </h2>
            <p style='margin:10px 0 0 0; font-size: 25px; color: #333;'>
                Probabilidade de defasagem no próximo ano: <strong>{prob * 100:.1f}%</strong>
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     st.metric("Probabilidade", f"{prob * 100:.1f}%")
    # with col2:
    #     st.metric("Faixa de Risco", faixa_nome)
    # with col3:
    #     d = nivel_num - fase_ideal_num
    #     st.metric("Defasagem", f"{d:+.0f} ({defasagem_label[ian]})")

    # Barra de risco
    st.markdown('**Escala de risco:**')
    st.progress(prob)

    # Contexto
    contexto = {
        'Muito baixo': 'Historicamente, apenas ~5% dos alunos nessa faixa ficaram defasados.',
        'Baixo': 'Historicamente, ~27% dos alunos nessa faixa ficaram defasados.',
        'Moderado': 'Historicamente, ~49% dos alunos nessa faixa ficaram defasados.',
        'Alto': 'Historicamente, ~74% dos alunos nessa faixa ficaram defasados.',
        'Muito alto': 'Historicamente, ~94% dos alunos nessa faixa ficaram defasados.',
    }
    st.info(f"💡 {contexto.get(faixa_nome, '')}")

    # Recomendações
    st.divider()
    st.subheader('📋 Recomendações')
    for rec in recomendacoes:
        st.markdown(f'- {rec}')

    # Detalhes técnicos
    with st.expander('ℹ️ Detalhes técnicos'):
        d = nivel_num - fase_ideal_num
        st.markdown(f'**Defasagem calculada:** {nivel_num:.0f} - {fase_ideal_num:.0f} = {d:.0f} → IAN = {ian} ({defasagem_label[ian]})')
        st.markdown('**Features normalizadas enviadas ao modelo:**')

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'- IDA (percentil): `{dados_norm["IDA_norm"]:.3f}`')
            st.markdown(f'- IPS (percentil): `{dados_norm["IPS_norm"]:.3f}`')
            st.markdown(f'- IPP (percentil): `{dados_norm["IPP_norm"]:.3f}`')
            st.markdown(f'- IPV (percentil): `{dados_norm["IPV_norm"]:.3f}`')
        with col2:
            st.markdown(f'- IAN: `{ian}`')
            st.markdown(f'- Gap IPP-IAN: `{dados_norm["resiliencia"]:.2f}`')
            st.markdown(f'- Nível: `{nivel_num:.0f}`')
            st.markdown(f'- Tipo escola: `{escola_num:.0f}` (0=Pública, 1=Privada)')
