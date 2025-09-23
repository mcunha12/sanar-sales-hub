import streamlit as st
from collections import defaultdict
import json
import services
import pandas as pd

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")

# Pega a conexão do estado da sessão, que foi criada no app.py
if 'conn' not in st.session_state:
    st.error("Conexão com o Supabase não encontrada. Por favor, recarregue a página principal primeiro.")
    st.stop()
conn = st.session_state.conn

# --- CSS CUSTOMIZADO PARA REPLICAR O DESIGN ---
def load_css():
    st.markdown("""
        <style>
            /* Remove o padding padrão do Streamlit */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }
            /* Estilo para os cards de métricas (KPIs) */
            div[data-testid="metric-container"] {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 0.75rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            }
            /* Título da métrica */
            div[data-testid="metric-container"] label {
                font-size: 1rem;
                color: #4A4A4A;
                font-weight: 500;
            }
            /* Valor da métrica */
            div[data-testid="metric-container"] div:nth-of-type(2) {
                font-size: 2.5rem;
                font-weight: 700;
                color: #1E1E1E;
            }
            /* Estilo para o card de cada conversa */
            .conversation-card {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
                transition: all 0.2s ease-in-out;
            }
            .conversation-card:hover {
                box-shadow: 0 4px 12px -1px rgba(0, 0, 0, 0.1), 0 2px 8px -2px rgba(0, 0, 0, 0.1);
                border-color: #0072C6; /* Cor primária azul para destacar */
            }
            /* Badge "Negociando" */
            .badge-negociando {
                display: inline-block;
                background-color: #E0F7FA;
                color: #00796B;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: 600;
                margin-left: 0.5rem;
                vertical-align: middle;
            }
            /* Footer do card da conversa */
            .card-footer {
                color: #888888;
                font-size: 0.875rem;
                display: flex;
                gap: 1.5rem;
                margin-top: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_conversations(_conn):
    """Busca e processa todas as mensagens do Supabase."""
    try:
        response = _conn.rpc('get_messages_data').execute()
        if not response.data or not isinstance(response.data, list):
            return pd.DataFrame()
        df = pd.DataFrame(response.data)
        df['curso'] = df['tags'].apply(lambda x: x.split(',')[0].strip() if x and ',' in x else 'Não especificado')
        df['ordemmensagens'] = pd.to_numeric(df['ordemmensagens'], errors='coerce')
        df.dropna(subset=['ordemmensagens'], inplace=True)
        df['ordemmensagens'] = df['ordemmensagens'].astype(int)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao executar a função do Supabase: {e}")
        return pd.DataFrame()

def render_page():
    load_css()
    
    # --- CABEÇALHO ---
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2rem;">
            <div style="background-color: #0072C6; border-radius: 10px; padding: 10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bar-chart-3"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>
            </div>
            <div>
                <h1 style="margin-bottom: 0; color: #1E1E1E;">Dashboard de Vendas IA</h1>
                <p style="margin-top: 0; color: #888888;">Insights acionáveis e métricas de conversão em tempo real</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    all_messages_df = get_conversations(conn)

    if all_messages_df.empty:
        st.warning("Não há dados de conversas para exibir.")
        st.stop()
        
    conversations = all_messages_df.groupby('ticket_id')
    
    # --- CÁLCULO DAS MÉTRICAS (KPIs) ---
    total_conversas = len(conversations)
    conversas_em_negociacao = sum(1 for _, group in conversations if group['em_negociacao'].any())
    taxa_conversao = (conversas_em_negociacao / total_conversas * 100) if total_conversas > 0 else 0

    # --- EXIBIÇÃO DAS MÉTRICAS (KPIs) ---
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric(label="Conversas Totais 👥", value=total_conversas)
    with kpi2:
        st.metric(label="Em Negociação ⚡️", value=conversas_em_negociacao)
    with kpi3:
        st.metric(label="Taxa Conversão 🎯", value=f"{taxa_conversao:.0f}%")

    st.divider()

    # --- BARRA DE FERRAMENTAS: BUSCA E FILTRO ---
    search_col, filter_col = st.columns([4, 1])
    with search_col:
        search_term = st.text_input("Buscar por cliente, mensagem ou conteúdo...", placeholder="🔍 Buscar por cliente, mensagem ou conteúdo...", label_visibility="collapsed")
    with filter_col:
        negociacao_status = st.toggle("Em Negociação", value=True)

    # --- APLICAÇÃO DOS FILTROS ---
    filtered_conversations = []
    for ticket_id, group in conversations:
        # Filtro de status
        if negociacao_status and not group['em_negociacao'].any():
            continue
            
        # Filtro de busca
        if search_term:
            search_lower = search_term.lower()
            if not (
                group['user_identity'].iloc[0].lower().strip().startswith(search_lower.strip()) or 
                group['mensagem'].str.lower().str.contains(search_lower).any()
            ):
                continue
                
        filtered_conversations.append((ticket_id, group))

    st.write(f"{len(filtered_conversations)} de {total_conversas} conversas")
    st.write("") # Espaçamento

    # --- LISTA DE CONVERSAS ---
    for ticket_id, group in filtered_conversations:
        group = group.sort_values('ordemmensagens', ascending=False)
        last_msg = group.iloc[0]
        
        # Usamos st.markdown para criar a estrutura do card com as classes CSS
        card_html = f"""
            <div class="conversation-card">
                <div>
                    <span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0072C6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M17 18a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2"/><rect width="18" height="18" x="3" y="4" rx="2"/><circle cx="12" cy="10" r="2"/><line x1="8" x2="8" y1="2" y2="4"/><line x1="16" x2="16" y1="2" y2="4"/></svg>{last_msg['user_identity']}</span>
                    {'<span class="badge-negociando">✨ Negociando</span>' if last_msg['em_negociacao'] else ''}
                </div>
                <p style="color: #4A4A4A; margin-top: 0.5rem; margin-bottom: 0;">{last_msg['mensagem']}</p>
                <div class="card-footer">
                    <span>💬 {len(group)} msgs</span>
                    <span>🕒 --</span>
                </div>
            </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        # O botão fica fora do HTML para manter a funcionalidade do Streamlit
        if st.button("Ver Conversa Completa", key=ticket_id, use_container_width=True):
             # Adicione a lógica para ver a conversa aqui, se necessário
             st.info(f"Botão para o ticket {ticket_id} foi clicado.")


# O ideal é que a lógica de detalhes da conversa (que foi removida para simplificar)
# seja adicionada aqui, controlada por st.session_state como antes.
render_page()