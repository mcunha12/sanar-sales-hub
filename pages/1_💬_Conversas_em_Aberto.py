import streamlit as st
from collections import defaultdict
import json
import services
import pandas as pd

st.set_page_config(page_title="Conversas", layout="wide")

# Pega a conexão do estado da sessão, que foi criada no app.py
if 'conn' not in st.session_state:
    st.error("Conexão com o Supabase não encontrada. Por favor, recarregue a página principal primeiro.")
    st.stop()
conn = st.session_state.conn

@st.cache_data(ttl=300)
def get_conversations(_conn):
    """Busca e processa todas as mensagens do Supabase."""
    try:
        response = _conn.rpc('get_messages_data').execute()
        if not response.data or not isinstance(response.data, list):
            st.warning("Nenhuma mensagem retornada pelo banco de dados.")
            return pd.DataFrame() # Retorna um DataFrame vazio
        
        # Converte para DataFrame para facilitar a manipulação
        df = pd.DataFrame(response.data)
        
        # MUDANÇA: Limpeza e extração de informações importantes
        df['curso'] = df['tags'].apply(lambda x: x.split(',')[0].strip() if x and ',' in x else 'Não especificado')
        df['ordemmensagens'] = pd.to_numeric(df['ordemmensagens'], errors='coerce')
        df.dropna(subset=['ordemmensagens'], inplace=True)
        df['ordemmensagens'] = df['ordemmensagens'].astype(int)
        
        return df

    except Exception as e:
        st.error(f"Ocorreu um erro ao executar a função do Supabase: {e}")
        return pd.DataFrame()

def generate_insights_from_conversation(messages_df: pd.DataFrame):
    """Prepara o prompt e chama a IA para gerar insights."""
    st.info("Gerando insights... Este processo pode levar um momento.")
    
    with st.spinner("Analisando conversa com a IA..."):
        try:
            # Ordena as mensagens para garantir a ordem cronológica
            messages_df = messages_df.sort_values('ordemmensagens')
            
            # MUDANÇA: Identifica o remetente baseado na regra do message_id
            conversation_text = "\n".join([
                f"{'Cliente' if str(row['message_id']).startswith('wamid') else 'Vendedor'}: {row['mensagem']}"
                for index, row in messages_df.tail(30).iterrows() # Pega as últimas 30 mensagens
            ])

            # MUDANÇA: Novo prompt de IA conforme solicitado
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

def render_page():
    st.title("📬 Conversas em Aberto")
    
    # Busca todos os dados
    all_messages_df = get_conversations(conn)

    if all_messages_df.empty:
        st.warning("Não há dados de conversas para exibir.")
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    # Filtro de Cursos
    cursos_disponiveis = sorted(all_messages_df['curso'].unique())
    cursos_selecionados = st.sidebar.multiselect("Filtrar por Curso", cursos_disponiveis, default=cursos_disponiveis)
    
    # Filtro de Status de Negociação
    negociacao_status = st.sidebar.toggle("Apenas em negociação", value=True)

    # Aplica os filtros
    filtered_df = all_messages_df[all_messages_df['curso'].isin(cursos_selecionados)]
    if negociacao_status:
        filtered_df = filtered_df[filtered_df['em_negociacao'] == True]
    
    # MUDANÇA: Agrupa por ticket_id para formar as conversas
    conversations = filtered_df.groupby('ticket_id')

    if 'selected_ticket_id' not in st.session_state:
        st.session_state.selected_ticket_id = None
        
    if st.session_state.selected_ticket_id:
        # --- VISTA DE DETALHES DA CONVERSA ---
        ticket_id = st.session_state.selected_ticket_id
        messages_df = conversations.get_group(ticket_id)
        
        # Pega a primeira linha para obter informações gerais
        first_row = messages_df.iloc[0]
        user_identity = first_row['user_identity']

        if st.button("⬅️ Voltar para a lista"):
            st.session_state.selected_ticket_id = None
            st.session_state.insights = None
            st.rerun()

        st.header(f"Conversa: {ticket_id}")
        st.caption(f"Cliente: {user_identity} | Curso de Interesse: {first_row['curso']}")
        
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

        st.write("---")
        
        # MUDANÇA: Plotagem do chat com a nova lógica
        with st.container(height=500):
            for _, msg in messages_df.sort_values('ordemmensagens').iterrows():
                is_client = str(msg['message_id']).startswith('wamid')
                sender_name = msg['user_identity'] if is_client else msg['from_message']
                
                with st.chat_message("user" if is_client else "assistant"):
                    st.write(msg.get('mensagem', '*Mensagem vazia*'))
                    st.caption(f"{sender_name} - {msg.get('data_hora')}")

    else:
        # --- VISTA DE LISTA DE CONVERSAS ---
        st.write(f"Exibindo **{len(conversations)}** conversas.")
        for ticket_id, group in conversations:
            group = group.sort_values('ordemmensagens', ascending=False)
            last_msg = group.iloc[0]

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"Ticket: {last_msg['ticket_id']}")
                    st.caption(f"Cliente: {last_msg['user_identity']} | Curso: {last_msg['curso']}")
                    st.write(f"_{last_msg['mensagem']}_")
                with col2:
                    st.metric("Mensagens", len(group))
                    if last_msg['em_negociacao']:
                        st.success("Em Negociação")
                    if st.button("Analisar Conversa", key=ticket_id):
                        st.session_state.selected_ticket_id = ticket_id
                        st.rerun()

render_page()