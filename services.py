# services.py
import streamlit as st
import openai
from pinecone import Pinecone
import json

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    
    # Nova inicialização do Pinecone
    pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
    
    INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]
    
    # Checa se o índice existe e o seleciona
    if INDEX_NAME in pc.list_indexes().names():
        pinecone_index = pc.Index(INDEX_NAME)
    else:
        st.error(f"Índice '{INDEX_NAME}' não encontrado no Pinecone.")
        pinecone_index = None

except Exception as e:
    st.error(f"Erro ao inicializar os serviços de API: {e}")
    pinecone_index = None

# --- FUNÇÕES DO AGENTE ---

def classify_query(user_query: str, system_prompt: str) -> list:
    """
    Usa o GPT-4.1 (substituído pelo gpt-4o) para classificar a query do usuário em especialidades.
    """
    try:
        response = openai.chat.completions.create(
            # O modelo "gpt-4.1" não existe, usaremos o gpt-4o que é o mais recente.
            # GPT-5 ainda não foi lançado publicamente.
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        # O output do modelo deve ser um JSON string, ex: '{"output": ["Cardiologia"]}'
        # Ajuste a extração baseado na estrutura exata que o modelo retorna.
        # Vamos assumir que ele retorna um JSON com uma chave "output".
        result_json = json.loads(response.choices[0].message.content)
        
        # Flexibilidade para extrair a lista, pode ser result_json['output'] ou só result_json
        if isinstance(result_json, list):
            return result_json
        elif isinstance(result_json, dict) and 'output' in result_json:
             return result_json['output']
        else:
            print(f"Formato de JSON inesperado: {result_json}")
            return []

    except Exception as e:
        print(f"Erro ao classificar a query: {e}")
        return []

def query_pinecone(user_query: str, specialties: list, top_k=5) -> tuple[str, str]:
    """
    Busca no Pinecone por conteúdo relevante, filtrando pelas especialidades.
    """
    if not pinecone_index or not specialties:
        return "Não foi possível realizar a busca. Nenhuma especialidade identificada.", "[]"

    try:
        # 1. Criar o embedding da pergunta do usuário
        embedding_response = openai.embeddings.create(
            input=[user_query],
            model="text-embedding-3-small" # Modelo de embedding recomendado
        )
        query_vector = embedding_response.data[0].embedding

        # 2. Fazer a busca no Pinecone com filtro
        # O filtro assume que você tem um metadado chamado "specialty" nos seus vetores
        results = pinecone_index.query(
            vector=query_vector,
            top_k=top_k,
            filter={
                "specialty": {"$in": [s.lower() for s in specialties]}
            },
            include_metadata=True
        )

        # 3. Formatar o conteúdo e as citações
        rag_content = ""
        citations = []
        for match in results['matches']:
            # Assumindo que seus metadados têm as chaves 'text', 'source_url', 'course_name'
            rag_content += f"Fonte: {match['metadata'].get('course_name', 'N/A')}\nConteúdo: {match['metadata'].get('text', '')}\n\n"
            citations.append({
                "course_name": match['metadata'].get('course_name', 'N/A'),
                "source_url": match['metadata'].get('source_url', '#'),
                "score": match['score']
            })
        
        return rag_content, json.dumps(citations, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Erro ao buscar no Pinecone: {e}")
        return "Ocorreu um erro ao buscar na base de conhecimento.", "[]"


def get_sales_insight(user_query: str, specialties: list, rag_content: str, citations: str, system_prompt: str) -> str:
    """
    Gera o insight final para o vendedor usando o modelo 'Estrategista de Vendas'.
    """
    # Substitui os placeholders no prompt do sistema
    final_prompt = system_prompt.format(
        specialties=", ".join(specialties),
        user_query=user_query,
        rag_content=rag_content,
        citations=citations
    )

    try:
        response = openai.chat.completions.create(
            # Usando gpt-4o como substituto do "gpt5"
            model="gpt-4o",
            messages=[
                {"role": "system", "content": final_prompt}
                # Não precisamos de uma mensagem de 'user' pois todo o contexto já está no prompt do sistema.
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao gerar insight de vendas: {e}")
        return "Não foi possível gerar o insight. Tente novamente."