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
import urllib
import urllib.parse

API_KEY = st.secrets['OPENAI_API_KEY']
st.set_page_config(page_title="Comparador de Execuções - Personal", layout="wide")

mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]

username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password), ssl = True)
st.cache_resource = client
db = client.personalAI
coll = db.usuarios

# --- Authentication ---
# Load hashed passwords

user = coll.find({})
users = []
for item in user:
    item.pop('_id', None)
    users.append(item)

usuarios = {'usernames' : {}}
for item in users:
    usuarios['usernames'][item['username']] = {'name' : item['name'], 'password' : item['password'][0]}
  
credentials = usuarios

authenticator = stauth.Authenticate(credentials= credentials, cookie_name= 'random_cookie_name', cookie_key='key123', cookie_expiry_days= 1)
authenticator.login()


def app_principal():
    st.title("🏋️ Sistema de Análise de Exercícios com IA")
    st.image("assets/logo.jpg", width=200)
    st.header(f"Bem-vindo, {st.session_state['name']}")
    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None
    st.write("Faça upload dos vídeos para comparar a execução do aluno com o modelo de referência.")

    # Campo para nome do aluno
    student_name = st.text_input("Nome do aluno:", max_chars=50)

    # Uploads
    ref_video = st.file_uploader("Vídeo de Referência", type=["mp4", "mov", "m4v", "avi", "webm", "qt"])
    exec_video = st.file_uploader("Vídeo de Execução", type=["mp4", "mov", "m4v", "avi", "webm","qt"])

    if ref_video and exec_video and student_name:
        if st.button("🚀 Analisar"):
            with st.spinner("Processando vídeos..."):
                ref_temp = None
                exec_temp = None
                comparative_video_bytes = None

                try:
                    # Salva os uploads temporariamente
                    ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    ref_temp.write(ref_video.read())
                    exec_temp.write(exec_video.read())

                    # Extração de poses (para análise)
                    frames_ref, landmarks_ref = extract_landmarks_from_video(ref_temp.name)
                    frames_exec, landmarks_exec = extract_landmarks_from_video(exec_temp.name)
                    
                    # Análise dos movimentos
                    insights, avg_error, avg_errors = analyze_poses(landmarks_ref, landmarks_exec)

                    # Gera vídeo comparativo COM anotações
                    comparative_video_bytes = generate_comparative_video(frames_ref, landmarks_ref, frames_exec, landmarks_exec)

                    # Gera relatório PDF
                    output_video_path_for_report = os.path.join("reports", f"{student_name}_comparativo.mp4")
                    if comparative_video_bytes:
                        os.makedirs("reports", exist_ok=True)
                        with open(output_video_path_for_report, "wb") as f:
                            f.write(comparative_video_bytes)
                        full_feedback = generate_feedback_via_openai(avg_errors, API_KEY)
                        generate_pdf_report(student_name, insights, avg_error, output_video_path_for_report, f"reports/{student_name}_relatorio.pdf", full_feedback=full_feedback)

                    else:
                        st.error("Erro ao gerar o vídeo comparativo com anotações.")

                finally:
                    # Limpeza dos arquivos temporários, garantindo que sejam fechados
                    if ref_temp:
                        ref_temp.close()
                        try:
                            os.unlink(ref_temp.name)
                        except Exception as e:
                            st.warning(f"Não foi possível remover o arquivo temporário de referência: {e}")
                    if exec_temp:
                        exec_temp.close()
                        try:
                            os.unlink(exec_temp.name)
                        except Exception as e:
                            st.warning(f"Não foi possível remover o arquivo temporário de execução: {e}")

            st.success("✅ Análise concluída!")

            # Exibição do vídeo
            if comparative_video_bytes:
                st.header("🎬 Vídeo Comparativo:")
                if os.path.exists(output_video_path_for_report):
                #with open(output_video_path_for_report, "rb") as video_file:
                    st.video(output_video_path_for_report)
                    #st.video(video_file.read())
                else:
                    st.error("⚠️ Vídeo não encontrado no caminho esperado.")
    

                #full_feedback = generate_feedback_via_openai(avg_errors, API_KEY)
                st.subheader("📋 Feedback Inteligente")
                st.write(full_feedback)

                st.download_button("📄 Baixar Relatório PDF", data=open(f"reports/{student_name}_relatorio.pdf", "rb"), file_name=f"{student_name}_relatorio.pdf")

    else:
        st.info("Preencha o nome do aluno e envie os dois vídeos para começar.")

def main():
    if st.session_state["authentication_status"]:
        app_principal()

    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect")

    elif st.session_state["authentication_status"] == None:
        st.warning("Please enter your username and password")

if __name__ == '__main__':
    main()
