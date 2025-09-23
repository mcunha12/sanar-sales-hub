import streamlit as st
from collections import defaultdict
import json
import services
import pandas as pd
from styles import load_css, render_header, icon_dashboard

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
load_css()

if 'conn' not in st.session_state:
    st.error("Conexão com o Supabase não encontrada. Por favor, recarregue a página principal primeiro.")
    st.stop()
conn = st.session_state.conn

@st.cache_data(ttl=300)
def get_conversations(_conn):
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
    st.info("Gerando insights... Este processo pode levar um momento.")
    with st.spinner("Analisando conversa com a IA..."):
        try:
            messages_df = messages_df.sort_values('ordemmensagens')
            conversation_text = "\n".join([
                f"{'Cliente' if str(row['message_id']).startswith('wamid') else 'Vendedor'}: {row['mensagem']}"
                for index, row in messages_df.tail(30).iterrows()
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
        except Exception as e:
            st.error(f"Não foi possível gerar os insights: {e}")
            if 'insights' in st.session_state:
                del st.session_state.insights

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
with kpi1:
    st.metric(label="Conversas Totais 👥", value=total_conversas)
with kpi2:
    st.metric(label="Em Negociação ⚡️", value=conversas_em_negociacao)
with kpi3:
    st.metric(label="Taxa Conversão 🎯", value=f"{taxa_conversao:.0f}%")

st.divider()

search_col, filter_col = st.columns([4, 1])
with search_col:
    search_term = st.text_input("Buscar...", placeholder="🔍 Buscar por cliente, mensagem ou conteúdo...", label_visibility="collapsed")
with filter_col:
    negociacao_status = st.toggle("Apenas em Negociação", value=True)

filtered_conversations = []
for ticket_id, group in conversations:
    if negociacao_status and not group['em_negociacao'].any():
        continue
    if search_term and not (group['user_identity'].iloc[0].lower().strip().startswith(search_term.lower().strip()) or group['mensagem'].str.lower().str.contains(search_term.lower()).any()):
        continue
    filtered_conversations.append((ticket_id, group))

st.write(f"{len(filtered_conversations)} de {total_conversas} conversas")
st.write("")

if 'selected_ticket_id' not in st.session_state:
    st.session_state.selected_ticket_id = None

if st.session_state.selected_ticket_id:
    # VISTA DE DETALHES DA CONVERSA
    pass # A lógica de detalhes pode ser adicionada aqui se necessário
else:
    # VISTA DE LISTA DE CONVERSAS
    for ticket_id, group in filtered_conversations:
        group = group.sort_values('ordemmensagens', ascending=False)
        last_msg = group.iloc[0]
        
        card_html = f"""
            <div class="custom-card">
                <div>
                    <span>{last_msg['user_identity']}</span>
                    {'<span class="badge-negociando">✨ Negociando</span>' if last_msg['em_negociacao'] else ''}
                </div>
                <p style="color: #4A4A4A; margin-top: 0.5rem; margin-bottom: 0;">{last_msg['mensagem']}</p>
            </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)