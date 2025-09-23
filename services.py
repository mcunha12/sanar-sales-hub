import streamlit as st
import openai
import json
import requests # Importa a biblioteca para requisições HTTP

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
# A inicialização do Pinecone com a biblioteca não é mais necessária para esta página.
# Vamos manter apenas a inicialização da OpenAI.
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception as e:
    st.error(f"Erro ao inicializar a API da OpenAI: {e}")

# --- FUNÇÕES DO AGENTE ---

def classify_query(user_query: str, system_prompt: str) -> list:
    """Classifica a query do usuário em especialidades."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result_json = json.loads(response.choices[0].message.content)
        
        # O n8n espera a saída direta, que pode ser a lista em si ou dentro de uma chave
        if isinstance(result_json, list):
            return result_json
        elif isinstance(result_json, dict):
            # Procura por uma chave que contenha uma lista (ex: 'output', 'specialties')
            for key, value in result_json.items():
                if isinstance(value, list):
                    return value
        
        st.warning(f"Formato de JSON inesperado do classificador: {result_json}")
        return []
    except Exception as e:
        st.error(f"Erro ao classificar a query: {e}")
        return []

# MUDANÇA: Função substituída para fazer a chamada POST direta
def query_pinecone_assistant(user_query: str) -> tuple[str, str]:
    """
    Envia uma pergunta para o assistente de chat do Pinecone via requisição POST.
    """
    pinecone_url = "https://prod-1-data.ke.pinecone.io/assistant/chat/ia-assistant"
    api_key = st.secrets.get("PINECONE_API_KEY")

    if not api_key:
        return "Erro: Chave da API do Pinecone não configurada.", "[]"

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key 
    }
    
    body = {
        "messages": [
            {
                "role": "user",
                "content": user_query
            }
        ],
        "stream": False,
        "model": "gpt-4o"
    }

    try:
        response = requests.post(pinecone_url, headers=headers, json=body, timeout=60)
        response.raise_for_status()  # Lança um erro para status HTTP 4xx/5xx
        
        data = response.json()
        
        rag_content = data.get("message", {}).get("content", "Nenhum conteúdo retornado.")
        citations = data.get("citations", [])
        
        return rag_content, json.dumps(citations, indent=2, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão com a API do Pinecone: {e}")
        return "Ocorreu um erro ao se comunicar com a base de conhecimento.", "[]"
    except Exception as e:
        st.error(f"Erro ao processar a resposta do Pinecone: {e}")
        return "Ocorreu um erro ao processar a resposta da base de conhecimento.", "[]"

def get_sales_insight(user_query: str, specialties: list, rag_content: str, citations: str, system_prompt: str) -> str:
    """Gera o insight final para o vendedor."""
    final_prompt = system_prompt.format(
        specialties=", ".join(specialties) if specialties else "Nenhuma",
        user_query=user_query,
        rag_content=rag_content,
        citations=citations
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o", # GPT-5 não está disponível, usando gpt-4o
            messages=[
                {"role": "system", "content": final_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro ao gerar insight de vendas: {e}")
        return "Não foi possível gerar o insight. Tente novamente."