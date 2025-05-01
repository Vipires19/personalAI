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
import streamlit.components.v1 as components

# ----------------- Função de detecção de dispositivo -----------------
def detectar_dispositivo():
    if "dispositivo_detectado" not in st.session_state:
        components.html(
            """
            <script>
            const isMobile = /android|iphone|ipad|mobile/i.test(navigator.userAgent);
            window.parent.postMessage({isMobile: isMobile}, "*");
            </script>
            """,
            height=0
        )

# Valor default
if "is_mobile" not in st.session_state:
    st.session_state["is_mobile"] = False

# ----------------- Configura Mongo e Autenticação -----------------
API_KEY = st.secrets['OPENAI_API_KEY']
st.set_page_config(page_title="Comparador de Execuções - Personal", layout="wide")

mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]
username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)
client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client.personalAI
coll = db.usuarios

# Autenticação
user = coll.find({})
usuarios = {'usernames': {}}
for item in user:
    item.pop('_id', None)
    usuarios['usernames'][item['username']] = {'name': item['name'], 'password': item['password'][0]}

authenticator = stauth.Authenticate(credentials=usuarios, cookie_name='random_cookie_name', cookie_key='key123', cookie_expiry_days=1)
authenticator.login()

# ----------------- App Principal -----------------
def app_principal():
    st.title("🏋️ Sistema de Análise de Exercícios com IA")
    st.image("assets/logo.jpg", width=200)
    st.header(f"Bem-vindo, {st.session_state['name']}")
    if authenticator.logout():
        st.session_state["authentication_status"] = None

    st.write("Envie os vídeos para comparar a execução do aluno com o modelo de referência.")
    student_name = st.text_input("Nome do aluno:", max_chars=50)
    ref_video = st.file_uploader("Vídeo de Referência", type=["mp4", "mov", "m4v", "avi", "webm", "qt"])
    exec_video = st.file_uploader("Vídeo de Execução", type=["mp4", "mov", "m4v", "avi", "webm", "qt"])

    detectar_dispositivo()

    if ref_video and exec_video and student_name:
        if st.button("🚀 Analisar"):
            with st.spinner("Processando os vídeos..."):
                ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                ref_temp.write(ref_video.read())
                exec_temp.write(exec_video.read())

                try:
                    frames_ref, landmarks_ref = extract_landmarks_from_video(ref_temp.name)
                    frames_exec, landmarks_exec = extract_landmarks_from_video(exec_temp.name)
                    insights, avg_error, avg_errors = analyze_poses(landmarks_ref, landmarks_exec)

                    comparative_video_bytes = generate_comparative_video(frames_ref, landmarks_ref, frames_exec, landmarks_exec)
                    if not comparative_video_bytes:
                        st.error("Erro ao gerar o vídeo comparativo.")
                        return

                    full_feedback = generate_feedback_via_openai(avg_errors, API_KEY)

                    st.success("✅ Análise concluída!")
                    st.header("🎬 Resultado da Comparacão")

                    if st.session_state["is_mobile"]:
                        st.warning("Modo celular detectado. Baixe o vídeo abaixo para evitar travamentos.")
                        st.download_button("📥 Baixar vídeo", data=comparative_video_bytes, file_name="comparativo.mp4")
                    else:
                        st.video(comparative_video_bytes)

                    st.subheader("📋 Feedback Inteligente")
                    st.write(full_feedback)

                    os.makedirs("reports", exist_ok=True)
                    video_path = f"reports/{student_name}_comparativo.mp4"
                    with open(video_path, "wb") as f:
                        f.write(comparative_video_bytes)
                    report_path = f"reports/{student_name}_relatorio.pdf"
                    generate_pdf_report(student_name, insights, avg_error, video_path, report_path, full_feedback=full_feedback)

                    if os.path.exists(report_path):
                        with open(report_path, "rb") as pdf_file:
                            st.download_button("📄 Baixar Relatório PDF", data=pdf_file.read(), file_name=f"{student_name}_relatorio.pdf")

                finally:
                    ref_temp.close()
                    exec_temp.close()
                    try:
                        os.unlink(ref_temp.name)
                        os.unlink(exec_temp.name)
                    except:
                        pass
    else:
        st.info("Preencha o nome do aluno e envie os dois vídeos para começar.")

# ----------------- Main -----------------
def main():
    if st.session_state["authentication_status"]:
        app_principal()
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password incorretos")
    elif st.session_state["authentication_status"] is None:
        st.warning("Digite seu usuário e senha para acessar")

if __name__ == '__main__':
    main()
