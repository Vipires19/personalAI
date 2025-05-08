import streamlit as st
import streamlit_authenticator as stauth
from pymongo import MongoClient
import urllib.parse
import datetime
import tempfile
import os
from bson.objectid import ObjectId

# --- Configurações iniciais ---
API_KEY = st.secrets['OPENAI_API_KEY']
MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
BUCKET_PUBLIC_URL = st.secrets['R2_PUBLIC_URL']

# --- Conexão com MongoDB ---
client = MongoClient(MONGO_URI, ssl=True)
db = client.personalAI
coll_users = db.usuarios
coll_jobs = db.jobs

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

# --- Layout ---
layout = st.query_params.get("layout", "centered")
if layout not in ["wide", "centered"]:
    layout = "centered"
st.set_page_config(page_title="Comparador de Execuções - Personal", layout=layout)

with st.sidebar:
    if layout == "centered":
        if st.button("Versão Desktop"):
            st.markdown('<meta http-equiv="refresh" content="0; URL=/?layout=wide">', unsafe_allow_html=True)
    else:
        if st.button("Versão Mobile"):
            st.markdown('<meta http-equiv="refresh" content="0; URL=/?layout=centered">', unsafe_allow_html=True)

# --- App Principal ---
def app():
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

                job_data = {
                    "user": st.session_state['username'],
                    "student": student_name,
                    "status": "pending",
                    "created_at": datetime.datetime.utcnow(),
                    "ref_path": ref_temp.name,
                    "exec_path": exec_temp.name
                }
                job_id = coll_jobs.insert_one(job_data).inserted_id

                st.success("✅ Enviado para análise. Verifique abaixo o status.")

    st.divider()
    st.subheader("📊 Minhas Análises")
    jobs = coll_jobs.find({"user": st.session_state['username']}).sort("created_at", -1)
    for job in jobs:
        with st.expander(f"📌 {job['student']} - {job['created_at'].strftime('%d/%m/%Y %H:%M')}"):
            st.write(f"**Status:** {job['status'].capitalize()}")
            if job['status'] == "done":
                if 'video_url' in job:
                    st.video(f"{BUCKET_PUBLIC_URL}/{job['video_url']}")
                    st.download_button("📥 Baixar Vídeo", f"{BUCKET_PUBLIC_URL}/{job['video_url']}", file_name=f"{job['student']}_comparativo.mp4")
                if 'report_url' in job:
                    st.download_button("📄 Baixar PDF", f"{BUCKET_PUBLIC_URL}/{job['report_url']}", file_name=f"{job['student']}_relatorio.pdf")
                if 'feedback' in job:
                    with st.expander("📋 Feedback Inteligente"):
                        st.write(job['feedback'])
            elif job['status'] == "error":
                st.error("Erro na análise. Tente novamente.")

# --- Execução ---
if st.session_state["authentication_status"]:
    app()
elif st.session_state["authentication_status"] == False:
    st.error("Usuário/senha incorretos")
elif st.session_state["authentication_status"] is None:
    st.warning("Informe usuário e senha")
