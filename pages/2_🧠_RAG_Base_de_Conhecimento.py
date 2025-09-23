import streamlit as st
import services
import config
from styles import load_css, render_header, icon_rag # Importa as novas funções

st.set_page_config(page_title="Busca RAG", layout="wide")
load_css() # Aplica o CSS

render_header(
    title="Assistente de Vendas com RAG",
    subtitle="Faça perguntas sobre nossos cursos e a IA irá buscar a informação em nossa base.",
    icon_svg=icon_rag
)

if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []

for message in st.session_state.rag_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Qual a sua dúvida?"):
    st.session_state.rag_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando e buscando informações..."):
            st.write("1️⃣ **Classificando a intenção...**")
            specialties = services.classify_query(prompt, config.CLASSIFIER_SYSTEM_PROMPT)
            
            if not specialties:
                st.warning("Nenhuma especialidade específica identificada. A busca pode ser menos precisa.")
            else:
                st.write(f"✅ **Especialidades identificadas:** `{'`, `'.join(specialties)}`")
            
            st.write("2️⃣ **Buscando na base de conhecimento...**")
            rag_content, citations = services.query_pinecone_assistant(prompt)
            
            if "Erro" in rag_content or "Não foi possível" in rag_content:
                st.error(rag_content)
            else:
                st.write("✅ **Informações relevantes encontradas!**")
                
                st.write("3️⃣ **Gerando insight com o Estrategista de Vendas AI...**")
                final_response = services.get_sales_insight(
                    user_query=prompt,
                    specialties=specialties,
                    rag_content=rag_content,
                    citations=citations,
                    system_prompt=config.SALES_COACH_SYSTEM_PROMPT
                )
                
                st.markdown(final_response)
                st.session_state.rag_messages.append({"role": "assistant", "content": final_response})