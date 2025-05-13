import streamlit as st
import streamlit_authenticator as stauth
from pymongo import MongoClient
import urllib.parse
from datetime import datetime
import tempfile
import os
from bson.objectid import ObjectId
from utils.r2_utils import get_r2_client
import uuid

# --- Configurações iniciais ---
API_KEY = st.secrets['OPENAI_API_KEY']
MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gjkin5a.mongodb.net/personalAI?retryWrites=true&w=majority&appName=Cluster0"
BUCKET_PUBLIC_URL = st.secrets['ENDPOINT_URL']
BUCKET_PUBLIC_URL_2 = st.secrets['URL_BUCKET']
R2_KEY = st.secrets['R2_KEY']
R2_SECRET_KEY = st.secrets['R2_SECRET_KEY']

# --- Layout ---
layout = st.query_params.get("layout", "centered")
if layout not in ["wide", "centered"]:
    layout = "centered"

st.set_page_config(page_title="Comparador de Execuções - Personal", layout=layout)

with st.sidebar:
    st.write(f"Layout atual: **{layout.upper()}**")
    if layout == "centered":
        if st.button("🖥️ Versão Desktop"):
            st.markdown(
                '<meta http-equiv="refresh" content="0; URL=/?layout=wide">',
                unsafe_allow_html=True
            )
    else:
        if st.button("📱 Versão Mobile"):
            st.markdown(
                '<meta http-equiv="refresh" content="0; URL=/?layout=centered">',
                unsafe_allow_html=True
            )

# --- Conexão com MongoDB ---
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (MONGO_USER, MONGO_PASS))
db = client.personalAI
coll_users = db.usuarios
coll_jobs = db.jobs_fila


# Configura o client R2
r2 = get_r2_client(R2_KEY, R2_SECRET_KEY, BUCKET_PUBLIC_URL)
BUCKET_NAME = st.secrets["R2_BUCKET"]

# --- Autenticação ---
users = list(coll_users.find({}, {'_id': 0}))
credentials = {
    'usernames': {
        u['username']: {
            'name': u['name'],
            'password': u['password'][0]
        } for u in users
    }
}
authenticator = stauth.Authenticate(credentials, 'cookie', 'key123', cookie_expiry_days=1)
authenticator.login()

# --- App Principal ---
def show_student_dashboard():
    st.title("🏋️ Análise de Exercícios com IA")
    st.image("assets/logo.jpg", width=200)
    st.header(f"Bem-vindo, {st.session_state['name']}")

    if authenticator.logout():
        st.session_state["authentication_status"] = None

    student_name = st.text_input("Nome do aluno")
    with st.expander("📤 Upload dos Vídeos"):
        ref_video = st.file_uploader("Vídeo de Referência", type=["mp4"])
        exec_video = st.file_uploader("Vídeo de Execução", type=["mp4"])

    if ref_video and exec_video and student_name:

        if st.button("🚀 Enviar para Análise"):
            with st.spinner("Enviando arquivos..."):
                ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                ref_temp.write(ref_video.read())
                exec_temp.write(exec_video.read())

                # Upload para o R2
                ref_filename = f"{uuid.uuid4()}_ref.mp4"
                exec_filename = f"{uuid.uuid4()}_exec.mp4"
                
                r2.upload_file(Filename=ref_temp.name, Bucket=BUCKET_NAME, Key=ref_filename)
                r2.upload_file(Filename=exec_temp.name, Bucket=BUCKET_NAME, Key=exec_filename)
                
                ref_url = f"https://{BUCKET_NAME}.r2.cloudflarestorage.com/{ref_filename}"
                exec_url = f"https://{BUCKET_NAME}.r2.cloudflarestorage.com/{exec_filename}"

                job_data = {
                    "user": st.session_state['username'],
                    "student": student_name,
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                    "ref_path": ref_url,
                    "exec_path": exec_url
                }

                # Grava no MongoDB
                result = coll_jobs.insert_one(job_data)
                st.success(f"✅ Enviado para análise. ID do job: {result.inserted_id}")
                #job_id = coll_jobs.insert_one(job_data).inserted_id
                #st.success("✅ Enviado para análise. Verifique abaixo o status.")

    st.divider()
    st.subheader("📊 Minhas Análises")
    jobs = coll_jobs.find({"user": st.session_state['username']}).sort("created_at", -1)
    
    for job in jobs:
        created_at = job.get("created_at")
    
        # Garante que 'created_at' seja um datetime para usar strftime
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                try:
                    created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
                except Exception:
                    created_at = None
    
        date_str = created_at.strftime('%d/%m/%Y %H:%M') if created_at else "Data inválida"
    
        with st.expander(f"📌 {job['student']} - {date_str}"):
            st.write(f"**Status:** {job['status'].capitalize()}")
    
            if job['status'] == "done":
                if 'video_url' in job:
                    st.video(f"{BUCKET_PUBLIC_URL_2}/{job['video_url']}")
                    st.download_button(
                        "📥 Baixar Vídeo",
                        f"{BUCKET_PUBLIC_URL_2}/{job['video_url']}",
                        file_name=f"{job['student']}_comparativo.mp4"
                    )
    
                if 'report_url' in job:
                    st.download_button(
                        "📄 Baixar PDF",
                        f"{BUCKET_PUBLIC_URL_2}/{job['report_url']}",
                        file_name=f"{BUCKET_PUBLIC_URL_2}/{job['report_url']}"
                    )
    
                if 'feedback' in job:
                    st.markdown("📋 Feedback Inteligente")
                    st.write(job['feedback'])
    
            elif job['status'] == "error":
                st.error("Erro na análise. Tente novamente.")

def show_personal_dashboard():
    st.title("🏋️ Análise de Exercícios com IA")
    st.image("assets/logo.jpg", width=200)
    st.header(f"Bem-vindo, {st.session_state['name']}")

    if authenticator.logout():
        st.session_state["authentication_status"] = None

    student_name = st.text_input("Nome do aluno")
    with st.expander("📤 Upload dos Vídeos"):
        ref_video = st.file_uploader("Vídeo de Referência", type=["mp4"])
        exec_video = st.file_uploader("Vídeo de Execução", type=["mp4"])

    if ref_video and exec_video and student_name:

        if st.button("🚀 Enviar para Análise"):
            with st.spinner("Enviando arquivos..."):
                ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                ref_temp.write(ref_video.read())
                exec_temp.write(exec_video.read())

                # Upload para o R2
                ref_filename = f"{uuid.uuid4()}_ref.mp4"
                exec_filename = f"{uuid.uuid4()}_exec.mp4"
                
                r2.upload_file(Filename=ref_temp.name, Bucket=BUCKET_NAME, Key=ref_filename)
                r2.upload_file(Filename=exec_temp.name, Bucket=BUCKET_NAME, Key=exec_filename)
                
                ref_url = f"https://{BUCKET_NAME}.r2.cloudflarestorage.com/{ref_filename}"
                exec_url = f"https://{BUCKET_NAME}.r2.cloudflarestorage.com/{exec_filename}"

                job_data = {
                    "user": st.session_state['username'],
                    "student": student_name,
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                    "ref_path": ref_url,
                    "exec_path": exec_url
                }

                # Grava no MongoDB
                result = coll_jobs.insert_one(job_data)
                st.success(f"✅ Enviado para análise. ID do job: {result.inserted_id}")
                #job_id = coll_jobs.insert_one(job_data).inserted_id
                #st.success("✅ Enviado para análise. Verifique abaixo o status.")

    st.divider()
    st.subheader("📊 Minhas Análises")
    jobs = coll_jobs.find({"user": st.session_state['username']}).sort("created_at", -1)
    
    for job in jobs:
        created_at = job.get("created_at")
    
        # Garante que 'created_at' seja um datetime para usar strftime
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                try:
                    created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
                except Exception:
                    created_at = None
    
        date_str = created_at.strftime('%d/%m/%Y %H:%M') if created_at else "Data inválida"
    
        with st.expander(f"📌 {job['student']} - {date_str}"):
            st.write(f"**Status:** {job['status'].capitalize()}")
    
            if job['status'] == "done":
                if 'video_url' in job:
                    st.video(f"{BUCKET_PUBLIC_URL_2}/{job['video_url']}")
                    st.download_button(
                        "📥 Baixar Vídeo",
                        f"{BUCKET_PUBLIC_URL_2}/{job['video_url']}",
                        file_name=f"{job['student']}_comparativo.mp4"
                    )
    
                if 'report_url' in job:
                    st.download_button(
                        "📄 Baixar PDF",
                        f"{BUCKET_PUBLIC_URL_2}/{job['report_url']}",
                        file_name=f"{BUCKET_PUBLIC_URL_2}/{job['report_url']}"
                    )
    
                if 'feedback' in job:
                    st.markdown("📋 Feedback Inteligente")
                    st.write(job['feedback'])
    
            elif job['status'] == "error":
                st.error("Erro na análise. Tente novamente.")
                
# --- Execução ---
if st.session_state["authentication_status"]:
    user_doc = coll_users.find_one({"username": st.session_state["username"]})
    if user_doc and "role" in user_doc:
        st.session_state["role"] = user_doc["role"]
    
    role = st.session_state["role"]

    if role == "personal":
        show_personal_dashboard()
    elif role == "aluno":
        show_student_dashboard()
        

elif st.session_state["authentication_status"] == False:
    st.error("Usuário/senha incorretos")
elif st.session_state["authentication_status"] is None:
    st.warning("Informe usuário e senha")
