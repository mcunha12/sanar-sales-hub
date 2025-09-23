import streamlit as st
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="Sales Copilot Hub",
    page_icon="🧠",
    layout="wide"
)

# Inicializa a conexão e salva no estado da sessão
if 'conn' not in st.session_state:
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        st.session_state.conn = create_client(url, key)
    except Exception as e:
        st.error("Falha CRÍTICA ao conectar com Supabase. Verifique as chaves em .streamlit/secrets.toml")
        st.stop()

# --- Conteúdo da Página Principal (Padrão Streamlit) ---
st.title("🚀 Bem-vindo ao Sales Copilot Hub")
st.divider()
st.header("Selecione uma ferramenta no menu à esquerda para começar.")
st.markdown(
    """
    - **Conversas em Aberto**: Analise conversas com clientes em tempo real e gere insights com IA.
    - **RAG - Base de Conhecimento**: Faça perguntas em linguagem natural para a base de conhecimento de vendas.
    """
)