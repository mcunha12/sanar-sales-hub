# supabase_client.py

import streamlit as st
from supabase import create_client, Client

@st.singleton
def get_supabase_client() -> Client:
    """
    Cria e retorna o cliente Supabase, usando o cache do Streamlit
    para garantir que a conexão seja criada apenas uma vez.
    """
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Para facilitar, já chamamos a função aqui e exportamos a variável
supabase = get_supabase_client()