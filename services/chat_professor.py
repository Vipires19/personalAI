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

MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (MONGO_USER, MONGO_PASS))
db = client.personalAI
coll = db.memoria_chat
coll2 = db.alunos
coll3 = db.treinos
coll4 = db.avaliação

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

documento = carrega_txt(caminho)

SYSTEM_PROMPT = """
🧠 Backstory:
Você é Atlas, o assistente digital oficial da plataforma de análise de exercícios da **CamppoAI Solutions**. Seu papel é apoiar personal trainers no uso da plataforma, ajudando a interpretar relatórios, tirar dúvidas, sugerir boas práticas e mostrar como a IA pode facilitar o acompanhamento dos alunos.

📚 Fonte de informação:
Você tem acesso ao seguinte documento como referência principal para suas respostas:

####
{}
####

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
1. Sempre pergunte antes: **"Esse plano é para um aluno específico?"**
2. Se sim:
   - Solicite o **nome do aluno**.
   - Acesse os dados do aluno no banco de dados usando a função apropriada.
3. Só então prossiga com as perguntas: objetivo, nível, frequência e equipamentos.
4. Personalize as sugestões com base nas informações do aluno.

💬 Exemplo de saudação:
"E aí, Personal! 👊 Eu sou o Atlas, seu assistente digital da CamppoAI Solutions. Tô aqui pra te ajudar a tirar o máximo da nossa plataforma de análise de exercícios. Me conta, o que você precisa hoje?"
"""


@tool('get_user')
def get_user_by_name(name: str) -> dict:
    """
    Busca os dados do aluno pelo nome.
    """
    user_data = coll2.find_one({'student_name': name}, {'_id': 0})
    return user_data or {"erro": "Aluno não encontrado"}

@tool("salvar_treino")
def salvar_treino(user: str, student: str, treino: str) -> str:
    """
    Salva o plano de treino no banco de dados.
    """
    doc = {
        "user": user,
        "student": student,
        "treino": treino,
        "date": datetime.now()
    }
    coll3.insert_one(doc)
    return "Treino salvo com sucesso."

@tool("gerar_treino_personalizado")
def gerar_treino_personalizado(objective: str, experience: str, frequency: int, equipments: str) -> dict:
    """
    Gera uma sugestão de treino com base no objetivo, nível, dias disponíveis e equipamentos.
    Retorna um dicionário com os campos editáveis.
    """
    sugestao = f"""
Plano de treino para {objective.upper()} ({experience.capitalize()}) - {frequency}x/semana
Equipamentos disponíveis: {equipments}

Exemplo de divisão semanal:
- Dia 1: Peito + Tríceps
- Dia 2: Costas + Bíceps
- Dia 3: Pernas + Abdômen
- Dia 4: Ombro + Core
- Dia 5: HIIT + Mobilidade

*Obs: Exercícios e séries serão adaptados conforme equipamentos disponíveis.*
"""
    return {
        "objetivo": objective,
        "nivel": experience,
        "dias": frequency,
        "equipamentos": equipments,
        "treino_sugerido": sugestao.strip()
    }

def generate_and_upload_pdf_treino(nome_aluno: str, treino: str, s3_client, bucket_name: str) -> str:
    """
    Gera um PDF com o plano de treino e envia para Cloudflare R2. Retorna a URL pública.
    """
    # Nome seguro e único do arquivo
    safe_name = nome_aluno.strip().replace(" ", "_").lower()
    unique_id = uuid.uuid4().hex[:6]
    filename = f"{safe_name}_treino_{datetime.utcnow().date()}_{unique_id}.pdf"
    r2_key = f"treinos/{filename}"

    # Gerar o PDF em memória
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"Plano de Treino - {nome_aluno}", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, treino)

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    # Upload para Cloudflare R2
    s3_client.put_object(
        Bucket=bucket_name,
        Key=r2_key,
        Body=pdf_buffer,
        ContentType='application/pdf',
        ACL='public-read'  # se necessário
    )

    # Gerar a URL pública
    return f"https://{bucket_name}.r2.cloudflarestorage.com/{r2_key}"

@tool("gerar_pdf_treino")
def gerar_pdf_treino(nome_aluno: str, treino: str) -> str:
    """
    Gera um PDF com o plano de treino e envia para o armazenamento R2, retornando o link.
    """
    s3_client = boto3.client(
        's3',
        endpoint_url=BUCKET_PUBLIC_URL_2,
        aws_access_key_id=R2_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )
    bucket_name = BUCKET

    url_pdf = generate_and_upload_pdf_treino(nome_aluno, treino, s3_client, bucket_name)
    return f"\U0001F4C4 PDF gerado com sucesso: {url_pdf}"

@tool('get_evolution_feedback')
def get_evolution_feedback(student_name: str, user: str) -> str:
    """
    Retorna um feedback sobre a evolução física de um aluno com base nas duas últimas avaliações.
    Parâmetros:
    - student_name: nome do aluno
    - user: nome do professor responsável
    """
    resultados = list(coll4.find(
        {"student_name": student_name, "user": user}
    ).sort("last", -1).limit(2))

    if len(resultados) < 2:
        return "Ainda não há avaliações suficientes para gerar feedback de evolução. Pelo menos duas avaliações são necessárias."

    atual, anterior = resultados[0], resultados[1]

    def delta(key):
        return atual.get(key, 0) - anterior.get(key, 0)

    feedback = []

    # Comparação das principais métricas
    if delta("body_fat") < 0:
        feedback.append("✅ Houve redução na porcentagem de gordura corporal.")
    elif delta("body_fat") > 0:
        feedback.append("⚠️ A gordura corporal aumentou desde a última avaliação.")

    if delta("peso") < 0:
        feedback.append("📉 O peso corporal total diminuiu.")
    elif delta("peso") > 0:
        feedback.append("📈 O peso corporal aumentou.")

    medidas = ["chest", "shoulder", "waist", "hip", "thigh"]
    for medida in medidas:
        diff = delta(medida)
        if abs(diff) > 0.5:
            direcao = "aumentou" if diff > 0 else "diminuiu"
            feedback.append(f"🔍 A medida de {medida} {direcao} em {abs(diff):.1f} cm.")

    data_anterior = anterior.get("last", datetime.min).strftime("%d/%m/%Y")
    data_atual = atual.get("last", datetime.min).strftime("%d/%m/%Y")
    
    header = f"📅 Comparação entre avaliações de {data_anterior} e {data_atual} para {student_name}:\n"
    return header + "\n".join(feedback)


tools = [gerar_treino_personalizado, gerar_pdf_treino,salvar_treino,get_user_by_name,get_evolution_feedback]
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

