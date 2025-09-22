# app.py
import streamlit as st
import services
import config

# --- Configuração da Página ---
st.set_page_config(
    page_title="Sales Copilot RAG",
    page_icon="🧠",
    layout="wide"
)

st.title("🤖 Assistente de Vendas com RAG")
st.write("Faça uma pergunta sobre nossos cursos e a IA irá buscar a informação em nossa base e fornecer insights para sua venda.")

# --- Inicialização do Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Lógica do Chat ---
if prompt := st.chat_input("Qual a sua dúvida? Ex: 'Temos algum curso sobre dor crônica para clínicos?'"):
    # Adiciona e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Inicia o fluxo de agentes
    with st.chat_message("assistant"):
        with st.spinner("Analisando e buscando informações..."):
            # Passo 1: Classificar a query
            st.write("1️⃣ **Classificando a intenção...**")
            specialties = services.classify_query(prompt, config.CLASSIFIER_SYSTEM_PROMPT)
            
            if not specialties:
                st.error("Não foi possível identificar uma especialidade médica na sua pergunta. Por favor, tente ser mais específico.")
            else:
                st.write(f"✅ **Especialidades identificadas:** `{'`, `'.join(specialties)}`")
                
                # Passo 2: Buscar no Pinecone (RAG)
                st.write("2️⃣ **Buscando na base de conhecimento...**")
                rag_content, citations = services.query_pinecone(prompt, specialties)
                
                if "Não foi possível" in rag_content:
                    st.error("Não foi encontrado conteúdo relevante na base de conhecimento para esta combinação de pergunta e especialidades.")
                else:
                    st.write("✅ **Informações relevantes encontradas!**")
                    
                    # Passo 3: Gerar o insight de vendas
                    st.write("3️⃣ **Gerando insight com o Estrategista de Vendas AI...**")
                    final_response = services.get_sales_insight(
                        user_query=prompt,
                        specialties=specialties,
                        rag_content=rag_content,
                        citations=citations,
                        system_prompt=config.SALES_COACH_SYSTEM_PROMPT
                    )
                    
                    st.markdown(final_response)
                    st.session_state.messages.append({"role": "assistant", "content": final_response})