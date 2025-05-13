## Importando bibliotecas e criando o client
import os
import re
import openai
import streamlit as st
import pickle
from dotenv import load_dotenv,find_dotenv
from unidecode import unidecode
from pathlib import Path
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from langchain.tools import BaseTool, StructuredTool, Tool, tool
import random
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.prebuilt import create_react_agent
from langchain import hub
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts.chat import SystemMessage, HumanMessage
import os
import json
from langchain_core.messages import FunctionMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
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

MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (MONGO_USER, MONGO_PASS))
db = client.personalAI
coll = db.memoria_chat

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

SYSTEM_PROMPT = '''
    Backstory:
    Esse agente é um assistente digital especializado em auxiliar personal trainers que utilizam o sistema de análise de exercícios da CamppoAI Solutions. Seu nome é Atlas. Ele foi desenvolvido para responder dúvidas sobre o uso da plataforma, interpretar resultados de análises, dar sugestões de uso e boas práticas, e auxiliar o personal no acompanhamento dos alunos com ajuda da IA.

    Para fornecer essas informações, você tem acesso ao seguinte documento:

    ####
    {}
    ####

    Expected Result:
        - O agente deve se comunicar com um tom amigável e confiante, como um parceiro de trabalho experiente e acessível.
        - Deve sempre **manter o foco nas funcionalidades e benefícios da plataforma para personal trainers**.
        - Pode sugerir boas práticas, estratégias para usar os relatórios com alunos, dicas de comparação entre vídeos e como interpretar os gráficos de erro.
        - Se o personal estiver com dúvida sobre uma análise específica, o agente pode guiá-lo sobre como interpretar os dados fornecidos pelo sistema.
        - Se o usuário perguntar sobre como compartilhar vídeos ou PDFs com os alunos, o agente deve explicar o processo com clareza.
        - Se o usuário demonstrar interesse em automatizar mais partes do acompanhamento de alunos, o agente pode explicar como a IA pode auxiliar, inclusive sugerindo funcionalidades futuras.
        - Se o usuário fizer perguntas fora do escopo da plataforma (ex: sobre treinos, nutrição ou temas gerais de musculação), o agente deve educadamente explicar que seu foco é auxiliar no uso da plataforma CamppoAI.
        - Em nenhuma hipótese o agente deve dar diagnósticos de saúde, prescrição de treino ou nutrição.

    Exemplo de início de conversa:
        "E aí, Personal! 👊 Eu sou o Atlas, seu assistente digital da CamppoAI Solutions. Tô aqui pra te ajudar a tirar o máximo da nossa plataforma de análise de exercícios. Me conta, o que você precisa hoje?"

'''


@tool("gerar_treino_personalizado")
def gerar_treino_personalizado(objetivo: str, nivel: str, dias: int, equipamentos: str) -> str:
    """
    Gera uma sugestão de treino com base no objetivo, nível, dias disponíveis e equipamentos.

    Parâmetros:
    - objetivo: hipertrofia, emagrecimento, resistência etc.
    - nivel: iniciante, intermediário, avançado
    - dias: número de dias disponíveis por semana
    - equipamentos: lista ou descrição dos equipamentos disponíveis

    Retorna: string com sugestão de treino simulada.
    """
    treino_simulado = f"""
        Plano de treino para {objetivo.upper()} ({nivel.capitalize()}) - {dias}x/semana
        Equipamentos disponíveis: {equipamentos}

        Exemplo de divisão semanal:
        - Dia 1: Peito + Tríceps
        - Dia 2: Costas + Bíceps
        - Dia 3: Pernas + Abdômen
        - Dia 4: Ombro + Core
        - Dia 5: HIIT + Mobilidade

        *Obs: Exercícios e séries serão adaptados conforme equipamentos disponíveis.*
        """
    return treino_simulado.strip()


def generate_and_upload_pdf_treino(nome_aluno: str, treino: str, s3_client, bucket_name: str) -> str:
    """
    Gera um PDF com o plano de treino, salva localmente e faz upload para Cloudflare R2.

    Retorna: URL pública do PDF.
    """
    # Caminhos
    pasta_destino = "treinos"
    os.makedirs(pasta_destino, exist_ok=True)
    
    filename = f"{nome_aluno.replace(' ', '_').lower()}_treino_{datetime.utcnow().date()}.pdf"
    output_path_local = os.path.join(pasta_destino, filename)
    output_path_r2 = f"treinos/{filename}"  # Caminho no R2

    # Gerar o PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Plano de treino - {nome_aluno}\n\n{treino}")
    pdf.output(output_path_local)

    # Fazer upload para o R2
    with open(output_path_local, "rb") as f:
        pdf_bytes = f.read()

    s3_client.put_object(Bucket=bucket_name, Key=output_path_r2, Body=pdf_bytes, ContentType='application/pdf')

    # URL pública
    return f"https://{bucket_name}.r2.cloudflarestorage.com/{output_path_r2}"

# Essa sim é a tool!
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
    return f"📄 PDF gerado com sucesso: {url_pdf}"

tools = [gerar_treino_personalizado, gerar_pdf_treino]
tool_executor = ToolNode(tools)
llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=OPENAI_API_KEY, streaming=True)
#conn = sqlite3.connect("database/memoria_chatbot2.db", check_same_thread=False)
memory = MongoDBSaver(coll)
model = create_react_agent(llm, tools,prompt=SYSTEM_PROMPT,checkpointer=memory)
    
class AgentChat:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.memory = self._init_memory()
        self.model = self._build_agent()

    def _init_memory(self):
        # 💥 Aqui usamos o método CORRETO pra sua versão (sem context manager!)
        #conn = sqlite3.connect("database/memoria_chatbot2.db", check_same_thread=False)
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
