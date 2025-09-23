import streamlit as st
from supabase import create_client
from styles import load_css, render_header, icon_home

st.set_page_config(
    page_title="Sales Copilot Hub",
    page_icon="🧠",
    layout="wide"
)

# Carrega o CSS em todas as páginas
load_css()

# Inicializa a conexão e salva no estado da sessão
if 'conn' not in st.session_state:
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        st.session_state.conn = create_client(url, key)
        st.toast("Conexão com Supabase estabelecida!", icon="✅")
    except Exception as e:
        st.error("Falha CRÍTICA ao conectar com Supabase. Verifique as chaves em .streamlit/secrets.toml")
        st.stop()

# --- Conteúdo da Página Principal ---
render_header(
    title="Bem-vindo ao Sales Copilot Hub",
    subtitle="Selecione uma ferramenta no menu à esquerda para começar.",
    icon_svg=icon_home
)

st.markdown("""
    <div class="custom-card">
        <h4>Ferramentas Disponíveis:</h4>
        <ul>
            <li><b>Conversas em Aberto:</b> Analise conversas com clientes em tempo real e gere insights com IA.</li>
            <li><b>RAG - Base de Conhecimento:</b> Faça perguntas em linguagem natural para a base de conhecimento de vendas.</li>
        </ul>
    </div>
""", unsafe_allow_html=True)