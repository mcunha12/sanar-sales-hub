import streamlit as st
import pandas as pd
import json
from collections import defaultdict
import services
from styles import load_css, render_header, icon_dashboard
from datetime import datetime

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
load_css()

# Garante que a conexão com o Supabase existe
if 'conn' not in st.session_state:
    st.error("Conexão com o Supabase não encontrada. Por favor, vá para a página principal primeiro.")
    st.stop()
conn = st.session_state.conn

@st.cache_data(ttl=300)
def get_conversations(_conn):
    """Busca e processa todas as mensagens do Supabase."""
    try:
        response = _conn.rpc('get_messages_data').execute()
        if not response.data or not isinstance(response.data, list):
            return pd.DataFrame()
        df = pd.DataFrame(response.data)
        df['curso'] = df['tags'].apply(lambda x: x.split(',')[0].strip() if x and isinstance(x, str) else 'Não especificado')
        df['ordemmensagens'] = pd.to_numeric(df['ordemmensagens'], errors='coerce')
        df.dropna(subset=['ordemmensagens'], inplace=True)
        df['ordemmensagens'] = df['ordemmensagens'].astype(int)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao executar a função do Supabase: {e}")
        return pd.DataFrame()

def generate_insights_from_conversation(messages_df: pd.DataFrame):
    """Gera insights de IA a partir de uma conversa."""
    with st.spinner("Analisando conversa com a IA..."):
        try:
            messages_df = messages_df.sort_values('ordemmensagens')
            conversation_text = "\n".join([
                f"{'Cliente' if str(row['message_id']).startswith('wamid') else 'Vendedor'}: {row['mensagem']}"
                for _, row in messages_df.tail(30).iterrows()
            ])
            prompt = f"""
            Você é um especialista em análise de conversas de vendas B2C. Analise a conversa abaixo e retorne APENAS um JSON válido com os seguintes campos:
            === CONVERSA ===
            {conversation_text}
            === INSTRUÇÕES ===
            Responda APENAS com um objeto JSON contendo as seguintes chaves:
            - "resumo": "Um resumo conciso do que já foi conversado."
            - "objecao": "Se houver uma objeção clara (preço, tempo, etc.), descreva-a. Se não, retorne 'Nenhuma objeção clara identificada'."
            - "ponto_fraco": "Identifique um ponto de dor ou necessidade do cliente que pode ser explorado para facilitar a venda. Se não houver, retorne 'Nenhum ponto fraco evidente'."
            - "follow_up": {{
                "estrategia": "Descreva em uma frase a estratégia para a próxima mensagem de follow up.",
                "copy": "Escreva a mensagem exata (a 'copy') para ser enviada ao cliente, baseada na estratégia."
              }}
            """
            response = services.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a sales analysis AI. Always return valid, complete JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            insights = json.loads(response.choices[0].message.content)
            st.session_state.insights = insights
            st.toast("Insights gerados com sucesso!", icon="✨")
        except Exception as e:
            st.error(f"Não foi possível gerar os insights: {e}")
            if 'insights' in st.session_state:
                del st.session_state.insights

def format_timestamp(ts_str):
    """Formata a data/hora para exibição de forma segura."""
    if not ts_str or not isinstance(ts_str, str):
        return "--"
    try:
        # Tenta converter de um formato ISO com 'Z' ou timezone
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m %H:%M')
    except ValueError:
        return "--"

# --- RENDERIZAÇÃO DA PÁGINA ---
render_header(
    title="Dashboard de Vendas IA",
    subtitle="Insights acionáveis e métricas de conversão em tempo real",
    icon_svg=icon_dashboard
)

all_messages_df = get_conversations(conn)

if all_messages_df.empty:
    st.warning("Não há dados de conversas para exibir.")
    st.stop()
    
conversations = all_messages_df.groupby('ticket_id')

total_conversas = len(conversations)
conversas_em_negociacao = sum(1 for _, group in conversations if group['em_negociacao'].any())
taxa_conversao = (conversas_em_negociacao / total_conversas * 100) if total_conversas > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Conversas Totais 👥", value=total_conversas)
kpi2.metric(label="Em Negociação ⚡️", value=conversas_em_negociacao)
kpi3.metric(label="Taxa Conversão 🎯", value=f"{taxa_conversao:.0f}%")

st.divider()

# --- BARRA DE FERRAMENTAS ---
search_col, filter_col = st.columns([4, 1])
search_term = search_col.text_input("Buscar...", placeholder="🔍 Buscar por cliente ou conteúdo...", label_visibility="collapsed")
negociacao_status = filter_col.toggle("Apenas em Negociação", value=True)

# --- LÓGICA DE FILTRAGEM ---
filtered_conversations = []
for ticket_id, group in conversations:
    if negociacao_status and not group['em_negociacao'].any():
        continue
    if search_term and not (group['user_identity'].iloc[0].lower().strip().startswith(search_term.lower().strip()) or group['mensagem'].str.lower().str.contains(search_term.lower(), na=False).any()):
        continue
    filtered_conversations.append((ticket_id, group))

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'selected_ticket_id' not in st.session_state:
    st.session_state.selected_ticket_id = None

# --- RENDERIZAÇÃO CONDICIONAL: LISTA OU DETALHES ---
if st.session_state.selected_ticket_id:
    # --- VISTA DE DETALHES DA CONVERSA ---
    ticket_id = st.session_state.selected_ticket_id
    messages_df = conversations.get_group(ticket_id)
    first_row = messages_df.iloc[0]

    if st.button("⬅️ Voltar para a lista"):
        st.session_state.selected_ticket_id = None
        st.session_state.insights = None
        st.rerun()

    st.header(f"Conversa: {ticket_id}")
    st.caption(f"Cliente: {first_row['user_identity']} | Curso de Interesse: {first_row['curso']}")
    
    if st.button("✨ Gerar Insights com IA"):
        st.session_state.insights = None
        generate_insights_from_conversation(messages_df)

    if 'insights' in st.session_state and st.session_state.insights:
        insights = st.session_state.insights
        st.subheader("🧠 Insights Gerados pela IA")
        st.markdown(f"**Resumo:** {insights.get('resumo', 'N/A')}")
        st.markdown(f"**Objeção Identificada:** {insights.get('objecao', 'N/A')}")
        st.markdown(f"**Ponto a Explorar:** {insights.get('ponto_fraco', 'N/A')}")
        
        follow_up = insights.get('follow_up', {})
        with st.container(border=True):
            st.markdown(f"**Estratégia de Follow-up:** {follow_up.get('estrategia', 'N/A')}")
            st.markdown("**Próxima Mensagem (Copy):**")
            st.code(follow_up.get('copy', 'N/A'), language=None)

    st.divider()
    
    with st.container(height=500):
        for _, msg in messages_df.sort_values('ordemmensagens').iterrows():
            is_client = str(msg['message_id']).startswith('wamid')
            sender_name = msg['user_identity'] if is_client else msg['from_message']
            
            with st.chat_message("user" if is_client else "assistant"):
                st.write(msg.get('mensagem', '*Mensagem vazia*'))
                st.caption(f"{sender_name} - {format_timestamp(msg.get('data_hora'))}")
else:
    # --- VISTA DE LISTA DE CONVERSAS ---
    st.write(f"{len(filtered_conversations)} de {total_conversas} conversas")
    st.write("") 

    for ticket_id, group in filtered_conversations:
        group = group.sort_values('ordemmensagens', ascending=False)
        last_msg = group.iloc[0]
        
        card_html = f"""
            <div class="custom-card">
                <div>
                    <span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0072C6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M17 18a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2"/><rect width="18" height="18" x="3" y="4" rx="2"/><circle cx="12" cy="10" r="2"/><line x1="8" x2="8" y1="2" y2="4"/><line x1="16" x2="16" y1="2" y2="4"/></svg>{last_msg['user_identity']}</span>
                    {'<span class="badge-negociando">✨ Negociando</span>' if last_msg['em_negociacao'] else ''}
                </div>
                <p style="color: #4A4A4A; margin-top: 0.5rem; margin-bottom: 0;">{last_msg['mensagem']}</p>
                <div class="card-footer">
                    <span>💬 {len(group)} msgs</span>
                    <span>🕒 {format_timestamp(last_msg['data_hora'])}</span>
                </div>
            </div>
        """
        # CORREÇÃO: Adicionando unsafe_allow_html=True para renderizar o HTML
        st.markdown(card_html, unsafe_allow_html=True)
        
        if st.button("Ver Conversa Completa", key=ticket_id, use_container_width=True):
            st.session_state.selected_ticket_id = ticket_id
            st.rerun()