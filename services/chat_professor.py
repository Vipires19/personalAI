## Importando bibliotecas e criando o client
import streamlit as st
from langchain.tools import tool
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.prebuilt import create_react_agent
from langchain_openai.chat_models import ChatOpenAI
import os
from langchain_community.document_loaders import Docx2txtLoader
import uuid
import logging
import sqlite3
from datetime import datetime
from fpdf import FPDF
from langgraph.checkpoint.mongodb import MongoDBSaver
import logging
import sqlite3
import boto3
from pymongo import MongoClient
import urllib.parse
from io import BytesIO
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch

MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
embedding_model = OpenAIEmbeddings(api_key=st.secrets["OPENAI_API_KEY"], model="text-embedding-3-large")
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (MONGO_USER, MONGO_PASS))
db = client.personalAI
coll = db.memoria_chat
coll2 = db.alunos
coll3 = db.treinos
coll4 = db.avaliação
coll5 = db.vetores
coll6 = db.feedback


#DB_PATH1 = "memoria_chatbot2.db"

def carrega_txt(caminho):
    loader = Docx2txtLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

caminho = "files/Manual de Apoio para Montagem de Treinos.docx"

OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
BUCKET_PUBLIC_URL = st.secrets['ENDPOINT_URL']
BUCKET_PUBLIC_URL_2 = st.secrets['URL_BUCKET']
R2_KEY = st.secrets['R2_KEY']
R2_SECRET_KEY = st.secrets['R2_SECRET_KEY']
BUCKET = 'personalai'

SYSTEM_PROMPT = """
🧠 Backstory:
Você é Atlas, um agente LLM operando dentro de um sistema LangGraph, com acesso a ferramentas para consultar banco de dados e documentos técnicos. Seu papel é atuar como um assistente virtual inteligente para personal trainers, fornecendo suporte analítico, pedagógico e prático com base nas ferramentas disponíveis. Seu papel é apoiar personal trainers no uso da plataforma, ajudando a interpretar relatórios, tirar dúvidas, sugerir boas práticas e mostrar como a IA pode facilitar o acompanhamento dos alunos.

📚 Fonte de informação:
Para responder perguntas técnicas, utilize a função consultar_material_de_apoio, que acessa os documentos enviados pelos personal trainers.


🎯 Diretrizes de comportamento:
- Sempre mantenha um **tom amigável, confiante e acessível**, como um parceiro de trabalho experiente.
- Seu foco principal é **ajudar personal trainers a aproveitarem ao máximo as funcionalidades e benefícios da plataforma CamppoAI**.
- Você pode:
  - Sugerir boas práticas no uso dos relatórios e vídeos.
  - Explicar como interpretar os gráficos e dados das análises.
  - Dar dicas de como comparar vídeos, monitorar progresso e gerar engajamento com alunos.
  - Ensinar como compartilhar vídeos e PDFs com os alunos de forma clara e simples.
  - Falar sobre como a IA pode ajudar a automatizar partes do acompanhamento.
  - Comentar sobre funcionalidades futuras (caso haja interesse do usuário).

🚫 Limites:
- Não deve, em hipótese alguma, fornecer diagnósticos de saúde, prescrição de treino ou nutrição.
- Caso o usuário pergunte sobre temas fora da plataforma (como musculação geral, dieta ou treinos específicos), oriente gentilmente que seu foco é no suporte ao uso da plataforma CamppoAI.

📋 Fluxo para geração de planos de treino:
1. Sempre que o usuário mencionar que deseja um treino, **interrompa o fluxo e pergunte se é para um aluno específico.** Não prossiga até obter essa resposta.
2. Se sim:
   - Solicite o **nome do aluno**.
   - Acesse os dados do aluno no banco de dados usando a função apropriada.
3. Só então prossiga com as perguntas: objetivo, nível, frequência e equipamentos.
4. Personalize as sugestões com base nas informações do aluno.
5. Após finalizar a sugestão de treino, sempre pergunte: "Você quer adicionar algum aquecimento ou alongamento específico antes ou depois do treino?"
6. Quando for montar um treino, **sempre gere a divisão e os exercícios de cada dia juntos**. O plano de treino deve ser enviado completo, sem etapas intermediárias.

📝 Análise de feedbacks:
- Sempre que o usuário perguntar sobre evolução, adaptação ou se um treino precisa de mudança, utilize as funções de análise de feedback.
- Leve em consideração: esforço, recuperação, frequência de treino, duração e objetivo.
- Gere recomendações claras, sempre explicando o *porquê* da sugestão.

💬 Exemplo de saudação:
"E aí, Personal! 👊 Eu sou o Atlas, seu assistente digital da CamppoAI Solutions. Tô aqui pra te ajudar a tirar o máximo da nossa plataforma de análise de exercícios. Me conta, o que você precisa hoje?"
"""

@tool("consultar_material_de_apoio")
def consultar_material_de_apoio(pergunta: str) -> str:
    """
    Consulta o material de apoio técnico enviado pelos personal trainers para responder perguntas específicas.
    """
    vectorStore = MongoDBAtlasVectorSearch(coll5, embedding=embedding_model, index_name='default')
    docs = vectorStore.similarity_search(pergunta)
    if not docs:
        return "Nenhum conteúdo relevante encontrado no material de apoio."
    
    return "\n\n".join([doc.page_content[:400] for doc in docs])

@tool('analisar_feedback_node')
def analisar_feedback_node(nome_aluno: str) -> dict:
    """
    Analisa o feedback mais recente do aluno considerando suas características pessoais
    e retorna sugestões ou observações relevantes.
    """

    aluno = coll2.find_one({"student_name": nome_aluno})
    feedback = coll6.find_one({"student": nome_aluno}, sort=[("data", -1)])

    if not aluno or not feedback:
        return {"erro": "Aluno ou feedback não encontrado."}

    objetivo = aluno.get("objective", "Não informado").capitalize()
    experiencia = aluno.get("experience", "Não informado").capitalize()
    estilo = aluno.get("style", "Não informado")
    tempo = aluno.get("duration", 60)
    frequencia = aluno.get("frequency", 3)

    esforco = feedback.get("esforco", "Não informado")
    recuperacao = feedback.get("recover", "Não informado")
    mensagem = feedback.get("message", "")
    tags = feedback.get("tags", [])

    analise = []

    if esforco in ["Muito Alto", "Extremo"]:
        analise.append("Esforço elevado relatado. Verificar se a intensidade está adequada ao condicionamento do aluno.")
    elif esforco in ["Muito Baixo"]:
        analise.append("Esforço muito baixo. O treino pode estar fácil demais, dependendo do objetivo.")

    if recuperacao in ["Ruim", "Péssima"]:
        analise.append("Recuperação insuficiente. Pode ser necessário ajustar o volume, carga ou tempo de descanso.")
    elif recuperacao in ["Excelente", "Boa"] and esforco in ["Moderado", "Alto"]:
        analise.append("Boa recuperação com esforço adequado. Sinal de que o treino está bem ajustado.")

    if experiencia.lower() in ["iniciante", "sedentário"]:
        analise.append("Aluno com pouca experiência. Importante evitar sobrecargas nas primeiras semanas.")

    if frequencia < 3:
        analise.append("Frequência baixa. Foque em treinos mais completos em cada sessão.")
    elif frequencia >= 5 and tempo >= 60:
        analise.append("Boa disponibilidade. Pode-se distribuir melhor o volume ao longo da semana.")

    if "funcional" in estilo.lower():
        analise.append("Estilo funcional indicado. Use movimentos multiarticulares variados.")
    elif "musculação" in estilo.lower():
        analise.append("Estilo musculação. Pode usar divisões tradicionais com progressão de carga.")

    if objetivo.lower() == "emagrecimento":
        analise.append("Foco em emagrecimento. Mantenha intensidade e frequência para maximizar gasto calórico.")
    elif objetivo.lower() == "hipertrofia":
        analise.append("Foco em hipertrofia. Cuidar do volume, técnica e descanso entre sessões.")

    if tags:
        analise.append(f"Tags do feedback: {', '.join(tags)}")
    if mensagem:
        analise.append(f"Comentário do aluno: \"{mensagem}\"")

    return {
        "aluno": nome_aluno,
        "objetivo": objetivo,
        "experiencia": experiencia,
        "esforco": esforco,
        "recuperacao": recuperacao,
        "analise_ia": analise
    }

@tool('get_user')
def get_user_by_name(name: str) -> dict:
    """
    Busca os dados do aluno pelo nome.
    """
    user_data = coll2.find_one({'student_name': name}, {'_id': 0})
    return user_data or {"erro": "Aluno não encontrado"}

@tool("resumir_feedbacks_recentes")
def resumir_feedbacks_recentes(nome_aluno: str) -> dict:
    """
    Resume os últimos feedbacks do aluno, identificando padrões de esforço, recuperação e principais reclamações.

    Parâmetros:
    - feedbacks: lista dos últimos feedbacks do aluno (idealmente os 3-5 mais recentes)

    Retorna:
    - Frequência mais comum de esforço e recuperação
    - Tags mais recorrentes
    - Tendência geral (fadiga, recuperação boa, etc.)
    """
    feedbacks = list(coll6.find({"student": nome_aluno}).sort("data", -1).limit(5))
    if not feedbacks:
        return {"erro": "Nenhum feedback encontrado."}

    esforco_vals = []
    recuperacao_vals = []
    tags_total = []

    for fb in feedbacks:
        esforco_vals.append(fb.get("esforco", ""))
        recuperacao_vals.append(fb.get("recover", ""))
        tags_total.extend(fb.get("tags", []))

    esforco_freq = {e: esforco_vals.count(e) for e in set(esforco_vals)}
    recuperacao_freq = {r: recuperacao_vals.count(r) for r in set(recuperacao_vals)}
    tag_freq = {t: tags_total.count(t) for t in set(tags_total)}

    tendencia = "Aluno em boa recuperação." if "Boa" in recuperacao_freq or "Excelente" in recuperacao_freq else "Possível sinal de fadiga."

    return {
        "esforco_frequente": max(esforco_freq, key=esforco_freq.get),
        "recuperacao_frequente": max(recuperacao_freq, key=recuperacao_freq.get),
        "tags_mais_frequentes": sorted(tag_freq.items(), key=lambda x: -x[1]),
        "tendencia": tendencia
    }

@tool("gerar_relatorio_evolucao")
def gerar_relatorio_evolucao(nome_aluno: str) -> dict:
    """
    Gera um relatório comparativo entre as duas últimas avaliações físicas do aluno.

    Parâmetros:
    - avaliacoes: lista com ao menos dois documentos de avaliação corporal ordenados por data.

    Retorna:
    - Um dicionário com as diferenças de gordura, massa magra e peso total entre as duas datas.
    """

    avaliacoes = list(coll4.find({"student_name": nome_aluno}).sort("last", 1))
    if len(avaliacoes) < 2:
        return {"erro": "É necessário pelo menos duas avaliações para gerar comparativo."}

    av1, av2 = avaliacoes[-2], avaliacoes[-1]
    comparativo = []

    delta_fat = av2["body_fat"] - av1["body_fat"]
    delta_muscle = av2["body_muscle"] - av1["body_muscle"]
    delta_peso = av2["peso"] - av1["peso"]

    if delta_fat < 0:
        comparativo.append(f"Perdeu {abs(round(delta_fat, 2))} kg de gordura corporal.")
    elif delta_fat > 0:
        comparativo.append(f"Ganhou {round(delta_fat, 2)} kg de gordura corporal.")

    if delta_muscle > 0:
        comparativo.append(f"Ganhou {round(delta_muscle, 2)} kg de massa magra.")
    elif delta_muscle < 0:
        comparativo.append(f"Perdeu {abs(round(delta_muscle, 2))} kg de massa magra.")

    if delta_peso > 0:
        comparativo.append(f"Ganhou {round(delta_peso, 2)} kg de peso total.")
    elif delta_peso < 0:
        comparativo.append(f"Perdeu {abs(round(delta_peso, 2))} kg de peso total.")

    return {
        "data_inicial": av1["last"],
        "data_final": av2["last"],
        "comparativo": comparativo
    }

@tool("sugerir_ajustes_treino")
def sugerir_ajustes_treino(nome_aluno: str) -> dict:
    """
    Sugere alterações no treino com base no feedback do aluno e em suas características pessoais.

    Parâmetros:
    - aluno: dict contendo os dados do aluno (objetivo, experiência, frequência, estilo, etc.)
    - feedback: dict com o último feedback do aluno (esforço, recuperação, mensagem)

    Retorna:
    - Um dicionário com data e sugestões de ajustes específicos no treino atual.
    """
    aluno = coll2.find_one({"student_name": nome_aluno})
    feedback = coll6.find_one({"student": nome_aluno}, sort=[("data", -1)])
     
    ajustes = []

    esforco = feedback.get("esforco", "").lower()
    recuperacao = feedback.get("recover", "").lower()
    objetivo = aluno.get("objective", "").lower()
    estilo = aluno.get("style", "").lower()
    frequencia = aluno.get("frequency", 3)
    tempo = aluno.get("duration", 60)
    experiencia = aluno.get("experience", "").lower()

    if esforco in ["muito alto", "extremo"]:
        ajustes.append("Reduzir o volume ou intensidade dos treinos para evitar sobrecarga.")
    elif esforco in ["muito baixo"]:
        ajustes.append("Aumentar a intensidade ou carga para gerar estímulo efetivo.")

    if recuperacao in ["ruim", "péssima"]:
        ajustes.append("Adicionar mais tempo de descanso ou ajustar a divisão do treino.")
    elif recuperacao in ["excelente", "boa"] and esforco in ["alto", "moderado"]:
        ajustes.append("Recuperação boa. Pode considerar aumento gradual da intensidade.")

    if objetivo == "emagrecimento":
        ajustes.append("Focar em treinos com maior gasto calórico e menor tempo de descanso.")

    if experiencia in ["iniciante", "sedentário"]:
        ajustes.append("Evitar sobrecarga. Progredir aos poucos com foco em técnica.")

    if frequencia < 3:
        ajustes.append("Treinos devem ser mais completos e intensos para compensar baixa frequência.")
    elif frequencia >= 5 and tempo >= 60:
        ajustes.append("Boa disponibilidade. Permite treinos com maior variação e progressão.")

    return {
        "aluno": aluno["student_name"],
        "data_feedback": feedback["data"].strftime("%Y-%m-%d %H:%M"),
        "ajustes": ajustes
    }

@tool("detectar_alerta_fadiga")
def detectar_alerta_fadiga(nome_aluno: str) -> dict:
    """
    Detecta sinais de fadiga ou sobrecarga com base nos últimos feedbacks do aluno.

    Parâmetros:
    - nome_aluno: Nome do aluno.

    Retorna:
    - Um alerta indicando se há risco de sobrecarga, com base em esforço e recuperação recentes.
    """
    feedbacks = list(coll6.find({"student": nome_aluno}).sort("data", -1).limit(3))

    if not feedbacks:
        return {"erro": "Sem feedbacks suficientes para análise de fadiga."}

    alerta = False
    contador_alerta = 0
    detalhes = []

    for fb in feedbacks:
        esforco = fb.get("esforco", "").lower()
        recuperacao = fb.get("recover", "").lower()

        if esforco in ["muito alto", "extremo"] and recuperacao in ["ruim", "péssima"]:
            contador_alerta += 1
            detalhes.append(f"Feedback de {fb['data'].strftime('%d/%m')}: esforço alto e má recuperação.")

    if contador_alerta >= 2:
        alerta = True

    return {
        "aluno": nome_aluno,
        "alerta_fadiga": alerta,
        "detalhes": detalhes if alerta else ["Nenhum padrão preocupante detectado."]
    }

@tool("consultar_avaliacoes")
def consultar_avaliacoes(nome_aluno: str) -> dict:
    """
    Consulta o histórico de avaliações físicas do aluno, mostrando data, gordura, massa magra e peso.

    Parâmetros:
    - nome_aluno: Nome do aluno cujas avaliações devem ser consultadas.

    Retorna:
    - Lista de avaliações ordenadas da mais antiga à mais recente.
    """
    avaliacoes = list(coll4.find({"student_name": nome_aluno}).sort("last", 1))

    if not avaliacoes:
        return {"erro": "Nenhuma avaliação encontrada para este aluno."}

    historico = [
        {
            "data": av["last"].strftime("%Y-%m-%d"),
            "gordura_kg": round(av.get("body_fat", 0), 2),
            "massa_magra_kg": round(av.get("body_muscle", 0), 2),
            "peso_kg": round(av.get("peso", 0), 2),
            "gordura_percent": round(av.get("fat_percent", 0), 2)
        }
        for av in avaliacoes
    ]

    return {
        "aluno": nome_aluno,
        "avaliacoes": historico
    }

@tool("listar_feedbacks_aluno")
def listar_feedbacks_aluno(nome_aluno: str) -> dict:
    """
    Lista os feedbacks mais recentes do aluno, com data, esforço e recuperação.

    Parâmetros:
    - nome_aluno: Nome do aluno para quem se deseja consultar os feedbacks.

    Retorna:
    - Um dicionário com até 5 feedbacks, contendo data, esforço e recuperação de cada um.
    """
    feedbacks = list(coll6.find({"student": nome_aluno}).sort("data", -1).limit(5))

    if not feedbacks:
        return {"erro": "Nenhum feedback encontrado para o aluno informado."}

    historico = [
        {
            "data": fb["data"].strftime("%Y-%m-%d %H:%M"),
            "esforco": fb.get("esforco", "Não informado"),
            "recuperacao": fb.get("recover", "Não informado")
        }
        for fb in feedbacks
    ]

    return {
        "aluno": nome_aluno,
        "feedbacks_recentes": historico
    }

tools = [listar_feedbacks_aluno,consultar_avaliacoes,detectar_alerta_fadiga,resumir_feedbacks_recentes, gerar_relatorio_evolucao,sugerir_ajustes_treino,get_user_by_name,analisar_feedback_node,consultar_material_de_apoio]
tool_executor = ToolNode(tools)
llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=OPENAI_API_KEY, streaming=True)
memory = MongoDBSaver(coll)
model = create_react_agent(llm, tools,prompt=SYSTEM_PROMPT,checkpointer=memory)
    
class AgentChat:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.memory = self._init_memory()
        self.model = self._build_agent()

    def _init_memory(self):
        # 💥 Aqui usamos o método CORRETO pra sua versão (sem context manager!)
        memory = MongoDBSaver(coll)
        return memory
    
    def _build_agent(self):
        llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
        return create_react_agent(
            model=llm,
            tools=tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.memory
        )
    
    def _create_db_schema(self):
        # Cria o banco de dados e a estrutura necessária
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Aqui você deve criar a estrutura do banco de dados necessária
            # Caso o banco de dados seja novo, crie as tabelas e colunas esperadas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER,
                data TEXT
            )
            ''')

            conn.commit()
            conn.close()
            print("Banco de dados criado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao criar o banco de dados: {str(e)}")
            raise e

    def memory_agent(self):
        return self.model    

