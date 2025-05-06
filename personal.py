import streamlit as st
import streamlit_authenticator as stauth
from services.pose_extractor import extract_landmarks_from_video
from services.pose_analyzer import analyze_poses
from services.video_generator import generate_comparative_video
from utils.helpers import generate_pdf_report
from utils.openai_feedback import generate_feedback_via_openai
import tempfile
import os
from pymongo import MongoClient
import urllib.parse

# --- Configuração Inicial ---
API_KEY = st.secrets['OPENAI_API_KEY']

# Lê diretamente da URL (novo API estável)
layout = st.query_params.get("layout", "centered")
if layout not in ["wide", "centered"]:
    layout = "centered"

# Aplica layout antes de qualquer coisa
st.set_page_config(page_title="Comparador de Execuções - Personal", layout=layout)

# Sidebar para alternar layout
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
mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]
username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)

client = MongoClient(
    f"mongodb+srv://{username}:{password}@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    ssl=True
)
db = client.personalAI
coll = db.usuarios

# --- Autenticação ---
user = coll.find({})
users = [dict(item) for item in user]
for item in users:
    item.pop('_id', None)

credentials = {
    'usernames': {
        item['username']: {
            'name': item['name'],
            'password': item['password'][0]
        }
        for item in users
    }
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name='random_cookie_name',
    cookie_key='key123',
    cookie_expiry_days=1
)
authenticator.login()

def app_principal():
    st.title("🏋️ Sistema de Análise de Exercícios com IA")
    st.image("assets/logo.jpg", width=200)
    st.header(f"Bem-vindo, {st.session_state['name']}")
    if authenticator.logout():
        st.session_state["authentication_status"] = None

    st.write("Faça upload dos vídeos para comparar a execução do aluno com o modelo de referência.")
    student_name = st.text_input("Nome do aluno:", max_chars=50)
    with st.expander("📤 Upload dos Vídeos"):
        ref_video = st.file_uploader("Vídeo de Referência", type=["mp4", "mov", "m4v", "avi", "webm", "qt"])
        exec_video = st.file_uploader("Vídeo de Execução", type=["mp4", "mov", "m4v", "avi", "webm", "qt"])

    if ref_video and exec_video and student_name:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Analisar"):
                with st.spinner("Processando vídeos..."):
                    ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    ref_temp.write(ref_video.read())
                    exec_temp.write(exec_video.read())

                    try:
                        frames_ref, landmarks_ref = extract_landmarks_from_video(ref_temp.name)
                        frames_exec, landmarks_exec = extract_landmarks_from_video(exec_temp.name)
                        insights, avg_error, avg_errors = analyze_poses(landmarks_ref, landmarks_exec)
                        comparative_video_bytes = generate_comparative_video(frames_ref, landmarks_ref, frames_exec, landmarks_exec)

                        output_video_path_for_report = os.path.join("reports", f"{student_name}_comparativo.mp4")
                        if comparative_video_bytes:
                            os.makedirs("reports", exist_ok=True)
                            with open(output_video_path_for_report, "wb") as f:
                                f.write(comparative_video_bytes)
                            full_feedback = generate_feedback_via_openai(avg_errors, API_KEY)
                            report_path = f"reports/{student_name}_relatorio.pdf"
                            generate_pdf_report(student_name, insights, avg_error, output_video_path_for_report, report_path, full_feedback=full_feedback)
                    finally:
                        ref_temp.close()
                        exec_temp.close()
                        try:
                            os.unlink(ref_temp.name)
                            os.unlink(exec_temp.name)
                        except:
                            pass

                st.success("✅ Análise concluída!")

                if comparative_video_bytes:
                    st.header("🎬 Vídeo Comparativo:")
                    st.video(comparative_video_bytes)
                    st.download_button("📥 Baixar Vídeo Comparativo", data=comparative_video_bytes, file_name=f"{student_name}_comparativo.mp4")

                    st.subheader("📋 Feedback Inteligente")
                    with st.expander("📋 Ver Feedback Inteligente"):
                        st.write(full_feedback)

                    if os.path.exists(report_path):
                        with open(report_path, "rb") as pdf_file:
                            st.download_button("📄 Baixar Relatório PDF", data=pdf_file.read(), file_name=f"{student_name}_relatorio.pdf")
                    else:
                        st.error("❌ O relatório não foi encontrado após a geração.")
                else:
                    st.error("❌ O vídeo comparativo não foi gerado corretamente.")

def main():
    if st.session_state["authentication_status"]:
        app_principal()
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")

if __name__ == '__main__':
    main()
