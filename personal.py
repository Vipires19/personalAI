import streamlit as st
import streamlit_authenticator as stauth
from pymongo import MongoClient
import urllib.parse
from datetime import datetime
import tempfile
from utils.r2_utils import get_r2_client
from utils.fomularios import forms_aluno,editar_aluno,avaliacao,visualizar_aluno,dash_prof,avaliacao_alunos,treinos_alunos,dash_aluno,treino_manual,pag_arquivos,feedback
import uuid
from services.chat_professor import AgentChat
from langchain_core.prompts.chat import AIMessage
import logging

# --- Configurações iniciais ---
API_KEY = st.secrets['OPENAI_API_KEY']
MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gjkin5a.mongodb.net/personalAI?retryWrites=true&w=majority&appName=Cluster0"
BUCKET_PUBLIC_URL = st.secrets['ENDPOINT_URL']
BUCKET_PUBLIC_URL_2 = st.secrets['URL_BUCKET']
R2_KEY = st.secrets['R2_KEY']
R2_SECRET_KEY = st.secrets['R2_SECRET_KEY']
DB_PATH = "database/memoria_chatbot.db"

agent_1 = AgentChat(DB_PATH)
model_1 = agent_1.memory_agent()


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

def analise_exec(student_name):
    student_name = student_name

    with st.expander("📤 Upload do Vídeo"):
        exec_video = st.file_uploader("🎥 Vídeo de Execução", type=["mp4"])
        exercise = st.selectbox(
            "🏋️‍♂️ Qual exercício está sendo analisado?",
            ["agachamento_livre", "stiff", "supino_reto", "remada_curvada", "desenvolvimento"]
        )

    if exec_video and student_name and exercise:
        if st.button("🚀 Enviar para Análise"):
            with st.spinner("Enviando arquivos..."):
                exec_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                exec_temp.write(exec_video.read())

                exec_filename = f"{uuid.uuid4()}_exec.mp4"

                # Upload para R2
                r2.upload_file(
                    Filename=exec_temp.name,
                    Bucket=BUCKET_NAME,
                    Key=exec_filename
                )

                exec_url = f"https://{BUCKET_NAME}.r2.cloudflarestorage.com/{exec_filename}"

                job_data = {
                    "user": st.session_state['username'],
                    "student": student_name,
                    "exercise": exercise,
                    "video_path": exec_url,
                    "status": "pending",
                    "created_at": datetime.utcnow()
                }

                result = coll_jobs.insert_one(job_data)
                st.success(f"✅ Enviado para análise. ID do job: {result.inserted_id}")

    st.divider()
    st.subheader("📊 Minhas Análises")
    jobs = coll_jobs.find({"user": st.session_state['username']}).sort("created_at", -1)

    for job in jobs:
        created_at = job.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                try:
                    created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
                except Exception:
                    created_at = None

        date_str = created_at.strftime('%d/%m/%Y %H:%M') if created_at else "Data inválida"

        with st.expander(f"📌 {job['student']} - {job.get('exercise', 'Exercício não informado')} - {date_str}"):
            st.write(f"**Status:** {job['status'].capitalize()}")

            if job['status'] == "done":
                if 'report_url' in job:
                    st.download_button(
                        "📄 Baixar Relatório PDF",
                        f"{BUCKET_PUBLIC_URL_2}/{job['report_url']}",
                        file_name=f"{job['student']}_{job.get('exercise', '')}_relatorio.pdf"
                    )

                if 'feedback' in job:
                    st.markdown("📋 Feedback Inteligente")
                    st.write(job['feedback'])

                if 'medias' in job:
                    st.markdown("📐 Médias dos Ângulos")
                    st.json(job['medias'])

                if 'status_por_articulacao' in job:
                    st.markdown("📊 Status por Articulação")
                    st.json(job['status_por_articulacao'])

            elif job['status'] == "error":
                st.error("❌ Erro na análise. Tente novamente.")

def agent_memory(agent_model, input: str, thread_id: str, date : str = None):
    try:
        if not thread_id:
            raise ValueError("thread_id é obrigatório no config.")

        inputs = {"messages": [{"role": "user", "content": input}]}
        print(f"Entradas para o modelo: {inputs}")

        # Apenas passa o thread_id no config, pois a memória já está no modelo
        config = {"configurable": {"thread_id": thread_id, "data": date}}
        
        # Executa o agente
        messages = agent_model.invoke(inputs, config)
        print(f"Mensagens geradas: {messages}")

        # Filtra a resposta
        for msg in reversed(messages["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content

        return "Erro: Nenhuma resposta encontrada."

    except Exception as e:
        logging.error(f"Erro ao invocar o agente: {str(e)}")
        raise

def run_agent_interface():
    if 'mensagens' not in st.session_state:
        st.session_state["mensagens"] = []
    if 'conversa_atual' not in st.session_state:
        st.session_state["conversa_atual"] = ''   
    
    mensagens = st.session_state["mensagens"]

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])

    prompt = st.chat_input("Fale com o ATLAS 🌎")
    if prompt:
        nova_mensagem = {'role': 'user', 'content': prompt}
        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])
        mensagens.append(nova_mensagem)
        st.session_state['mensagens'] = mensagens

        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown('⎸')

        respostas = agent_memory(
            agent_model=model_1,
            input=prompt,
            thread_id=st.session_state['name'],
            date=datetime.utcnow()
        )

        placeholder.markdown(respostas)

        nova_mensagem = {'role': 'assistant', 'content': respostas}
        mensagens.append(nova_mensagem)
        st.session_state['mensagens'] = mensagens

# --- App Principal ---
def show_student_dashboard():
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "home"

    with st.sidebar:
        if authenticator.logout():
            st.session_state["authentication_status"] = None

        st.divider()

        #if st.button("💪 Seus treinos"):
        #    st.session_state["pagina_atual"] = "treinos"

        if st.button("📈 Suas avaliações"):
            st.session_state["pagina_atual"] = "avaliacao"

        if st.button("🔁 FEEDBACKS"):
            st.session_state["pagina_atual"] = "feedback"

        if st.button("🏠 Voltar ao início"):
            st.session_state["pagina_atual"] = "home"

    # Conteúdo principal com base na seleção
    if st.session_state["pagina_atual"] == "home":
        st.title("🏋️ Hub AtlaAI 🌎")
        st.image("assets/logo.png", width=200)
        st.header(f"Bem-vindo, {st.session_state['name']}")
        dash_aluno(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "avaliacao":
        st.title("📈 Suas Avaliações Físicas")
        avaliacao_alunos(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "feedback":
        st.title("🔁 FEEDBACKS")
        st.header(f'Olá, {st.session_state["name"]}!')
        st.markdown('Deixe seu feedback em relação ao treino realizado')
        feedback(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "home":
        st.info("Selecione uma opção no menu lateral para começar.")

def show_personal_dashboard():
    # Inicializa o estado da página se não estiver presente
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "home"

    # Sidebar de navegação
    with st.sidebar:
        if authenticator.logout():
            st.session_state["authentication_status"] = None

        st.divider()

        if st.button("📖 Cadastro de alunos"):
            st.session_state["pagina_atual"] = "cadastro"

        if st.button("👁️ Visualizar alunos"):
            st.session_state["pagina_atual"] = "visualiza"

        if st.button("✏️ Editar dados de aluno"):
            st.session_state["pagina_atual"] = "editar"

        if st.button("📈 Fazer Avaliação do aluno"):
            st.session_state["pagina_atual"] = "avaliacao"

        if st.button("🤖🏃‍♂️‍➡️ Agent treinador"):
            st.session_state["pagina_atual"] = "agent"

        if st.button("🗃️ Ajude o Atlas à aprender"):
            st.session_state["pagina_atual"] = "uploader"

        if st.button("🏠 Voltar ao início"):
            st.session_state["pagina_atual"] = "home"

    # Conteúdo principal com base na seleção
    if st.session_state["pagina_atual"] == "home":
        st.title("🏋️ HUB Personal Trainer CAMPPO AI")
        st.image("assets/logo.png", width=200)
        st.header(f"Bem-vindo, {st.session_state['name']}")
    
    if st.session_state["pagina_atual"] == "cadastro":
        st.title("📖 Cadastro de alunos")
        forms_aluno(st.session_state['name'])

    if st.session_state['pagina_atual'] == "visualiza":
        st.title("👁️ Visualizar alunos")
        visualizar_aluno(st.session_state['name'])

    if st.session_state["pagina_atual"] == "editar":
        st.title("✏️ Editar dados de aluno")
        editar_aluno(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "avaliacao":
        st.title("📈 Fazer Avaliação do aluno")
        avaliacao(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "agent":
        st.title("🤖 Agente IA Treinador")
        run_agent_interface()

    elif st.session_state["pagina_atual"] == "uploader":
        st.title("🗃️ Ajude o Atlas à aprender")
        st.warning('Vídeos do youtube ainda não estão funcionando.')
        pag_arquivos(st.session_state['name'])

    elif st.session_state["pagina_atual"] == "home":
        dash_prof(st.session_state['name'])
        st.info("Selecione uma opção no menu lateral para começar.")
                    
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