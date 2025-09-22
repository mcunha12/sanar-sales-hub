import streamlit as st
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Sales Copilot Hub",
    page_icon="🧠",
    layout="wide"
)

# --- INICIALIZAÇÃO DA CONEXÃO DIRETA COM SUPABASE-PY ---
# Verificamos se o cliente já não existe no estado da sessão
if 'conn' not in st.session_state:
    try:
        # Lemos as chaves diretamente do secrets.toml
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_key"]
        
        # Criamos o cliente Supabase diretamente e o armazenamos na sessão
        st.session_state.conn = create_client(url, key)
        
        st.toast("Conexão com Supabase estabelecida!", icon="✅")
    except Exception as e:
        st.error("Falha CRÍTICA ao conectar com Supabase. Verifique as chaves em .streamlit/secrets.toml")
        st.error(f"Detalhe do erro: {e}")
        st.stop() # Interrompe o app se a conexão falhar

# --- Conteúdo da Página Principal ---
st.title("Bem-vindo ao Sales Copilot Hub 🚀")
st.write("---")
st.header("Selecione uma ferramenta no menu à esquerda para começar.")