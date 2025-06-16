import streamlit as st
from pymongo import MongoClient
import streamlit as st
import urllib.parse
#from utils.createUsers import hash_passwords
import streamlit_authenticator as stauth
from datetime import datetime
from utils.file_uploader import carrega_csv,carrega_pdf,carrega_site,carrega_txt,carrega_xlsx,carrega_youtube
from utils.comp_corp import pollock_7_dobras,pollock_3_dobras,percentual_gordura_durnin_womersley,faulkner
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings,ChatOpenAI
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage


MONGO_USER = urllib.parse.quote_plus(st.secrets['MONGO_USER'])
MONGO_PASS = urllib.parse.quote_plus(st.secrets['MONGO_PASS'])
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gjkin5a.mongodb.net/personalAI?retryWrites=true&w=majority&appName=Cluster0"



client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (MONGO_USER, MONGO_PASS))
db = client.personalAI
coll = db.usuarios
coll1 = db.alunos
coll2 = db.avaliação
coll3 = db.treinos
coll4 = db.jobs_fila
coll5 = db.vetores
coll6 = db.feedback

def forms_aluno(professor):
    st.header("🧍‍♂️ Informações Pessoais Básicas")
    st.divider()
    student_name = st.text_input('Nome do aluno')
    idade = st.number_input('Idade do aluno', min_value=0)
    sex = st.selectbox('Sexo do aluno', ['Masculino', 'Feminino'])
    peso = st.number_input('Peso do aluno (KG)')
    altura = st.number_input('Altura do aluno (cm)', min_value=0)
    objective = st.text_input('Objetivo do aluno')
    experience = st.selectbox('Nível de experiência do aluno', ['Iniciante','Intermediário','Avançado'])
    profession = st.text_input('Profissão do aluno')
    routine = st.text_input('Breve relato da rotina diária do aluno')
    st.divider()
    st.header("🩺 Informações de Saúde")
    lesoes = st.text_input("Lesões prévias ou atuais")
    doencas = st.text_input("Doenças ou limitações médicas")
    medical_aprove = st.selectbox("Aprovação médica para prática de atividade física?",['Aprovado','Reprovado','Não avaliado'])
    medicines = st.text_input("Medicamentos de uso contínuo?")
    postura = st.text_input("Problemas de postura identificados?")
    st.divider()
    st.header("🏋️ Histórico e Preferências de Treino")
    frequency = st.number_input("Frequência semanal desejada", min_value=0)
    duration = st.number_input("Duração média por sessão (minutos)")
    equipments = st.text_input("Equipamentos Disponíveis", placeholder = "Academia completa / Halteres / Elásticos / Peso corporal / Outro")
    preferences = st.text_input("Preferência de local", placeholder = "Academia / Casa / Ar livre")
    like = st.text_input("Exercícios que gosta / não gosta")
    exp =  st.text_input("Experiências anteriores com treinos", placeholder = "funciona bem com treino dividido? fullbody? etc.")
    st.divider()
    st.header("📈 Acompanhamento e Avaliação Física")
    body_fat = st.number_input("Porcentagem de gordura corporal")
    st.markdown("Medidas corporais básicas:")
    chest = st.number_input("Toráx (cm)",min_value=0, placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    shoulder1 = st.number_input("Braço direito(cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    shoulder2 = st.number_input("Braço esquerdo(cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    abdomen = st.number_input("Abdomen (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    waist = st.number_input("Cintura (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    hip = st.number_input("Quadril (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    thigh1 = st.number_input("Coxa direita (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    thigh2 = st.number_input("Coxa esquerda (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    calf1 = st.number_input("Panturrilha direita (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    calf2 = st.number_input("Panturrilha esquerda (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    last = st.date_input("Data da avaliação física")
    last_datetime = datetime.datetime.combine(last, datetime.time())
    style = st.text_input("Preferência de estilo de treino", placeholder= "Funcional, musculação, HIIT, mobilidade, etc.")
    time = st.text_input('Tempo disponível por dia')
    st.divider()
    st.header("🔓 Liberar acesso ao aluno")
    user = st.text_input('Nome de usuário')
    password =st.text_input('Senha')

    form_full = {'user' : professor,
                 'student_name' : student_name,
                 'idade' : idade, 
                 'sex' : sex, 
                 'peso' : peso, 
                 'altura' : altura, 
                 'objective' : objective, 
                 'experience' : experience, 
                 'profession' : profession, 
                 'routine' : routine, 
                 'lesoes' : lesoes, 
                 'doencas' : doencas, 
                 'medical_aprove' : medical_aprove, 
                 'medicines' : medicines, 
                 'postura' : postura,
                 'frequency' : frequency, 
                 'duration' : duration, 
                 'equipments' : equipments, 
                 'preferences' : preferences, 
                 'like' : like, 
                 'exp' : exp, 
                 'style' : style, 
                 'time' : time}
    
    form_avaliação = {'user' : professor,
                       'student_name' : student_name,
                       'body_fat' : body_fat,
                       'chest' : chest,
                       'shoulder1' : shoulder1,
                       'shoulder2' : shoulder2,
                       'waist' : waist,
                       'hip' : hip,
                       'thigh1' : thigh1,
                       'thigh2' : thigh2,
                       'calf1' : calf1,
                       'calf2' : calf2,
                       'abdomen' : abdomen, 
                       'idade' : idade, 
                       'sex' : sex, 
                       'peso' : peso, 
                       'altura' : altura,
                       'date' : last_datetime}
    

    hashed_passwords = stauth.Hasher([password]).generate()

    new_user = {
    "name": student_name,
    "username": user,
    "password":hashed_passwords,
    "role": "aluno"}

    if st.button('Confirmar informações'):
        coll1.insert_one(form_full)
        coll2.insert_one(form_avaliação)
        coll.insert_one(new_user)

        print("Documentos inseridos com sucesso")
        st.success(f"✅ Usuário cadastrado com sucesso")
    
    return form_full , form_avaliação

def editar_aluno(professor):
    alunos = coll1.find({"user": professor})
    nomes_alunos = [aluno["student_name"] for aluno in alunos]

    if not nomes_alunos:
        st.info("Você ainda não cadastrou nenhum aluno.")
        return

    nome_selecionado = st.selectbox("Selecione um aluno para editar", nomes_alunos)
    aluno = coll1.find_one({"student_name": nome_selecionado, "user": professor})

    if not aluno:
        st.warning("Erro ao carregar os dados do aluno.")
        return

    # Seção 1: Dados Pessoais
    st.subheader("🧍‍♂️ Informações Pessoais")
    aluno['idade'] = st.number_input("Idade", value=aluno.get("idade", 0))
    aluno['sex'] = st.selectbox("Sexo", ["Masculino", "Feminino"], index=["Masculino", "Feminino"].index(aluno.get("sex", "Masculino")))
    aluno['peso'] = st.number_input("Peso (kg)", value=aluno.get("peso", 0.0))
    aluno['altura'] = st.number_input("Altura (cm)", value=aluno.get("altura", 0))
    aluno['objective'] = st.text_input("Objetivo", value=aluno.get("objective", ""))
    aluno['experience'] = st.selectbox("Experiência", ["Iniciante", "Intermediário", "Avançado"], index=["Iniciante", "Intermediário", "Avançado"].index(aluno.get("experience", "Iniciante")))
    aluno['profession'] = st.text_input("Profissão", value=aluno.get("profession", ""))
    aluno['routine'] = st.text_input("Rotina", value=aluno.get("routine", ""))

    # Seção 2: Saúde
    st.subheader("🩺 Saúde")
    aluno['lesoes'] = st.text_input("Lesões", value=aluno.get("lesoes", ""))
    aluno['doencas'] = st.text_input("Doenças", value=aluno.get("doencas", ""))
    aluno['medical_aprove'] = st.selectbox("Aprovação médica", ["Aprovado", "Reprovado", "Não avaliado"], index=["Aprovado", "Reprovado", "Não avaliado"].index(aluno.get("medical_aprove", "Não avaliado")))
    aluno['medicines'] = st.text_input("Medicamentos", value=aluno.get("medicines", ""))
    aluno['postura'] = st.text_input("Postura", value=aluno.get("postura", ""))

    # Seção 3: Treino
    st.subheader("🏋️ Histórico de Treino")
    aluno['frequency'] = st.number_input("Frequência semanal", value=aluno.get("frequency", 0))
    aluno['duration'] = st.number_input("Duração por sessão", value=aluno.get("duration", 0))
    aluno['equipments'] = st.text_input("Equipamentos", value=aluno.get("equipments", ""))
    aluno['preferences'] = st.text_input("Preferência de local", value=aluno.get("preferences", ""))
    aluno['like'] = st.text_input("Gosta / não gosta", value=aluno.get("like", ""))
    aluno['exp'] = st.text_input("Experiência prévia", value=aluno.get("exp", ""))
    aluno['style'] = st.text_input("Estilo de treino", value=aluno.get("style", ""))
    aluno['time'] = st.text_input("Tempo disponível por dia", value=aluno.get("time", ""))


    if st.button("Salvar alterações"):
        coll1.update_one({"_id": aluno["_id"]}, {"$set": aluno})
        st.success("✅ Informações do aluno atualizadas com sucesso!")

def avaliacao(professor):
    alunos = coll1.find({"user": professor})
    nomes_alunos = [aluno["student_name"] for aluno in alunos]

    if not nomes_alunos:
        st.info("Você ainda não cadastrou nenhum aluno.")
        return


    nome_selecionado = st.selectbox("Selecione um aluno para editar", nomes_alunos)
    aluno = coll1.find_one({"student_name": nome_selecionado, "user": professor})
    avaliacao = coll2.find_one({"student_name": nome_selecionado, "user": professor})

    if not avaliacao:
        st.warning(f"Você ainda não fez a avaliação do aluno {nome_selecionado}.")
        return
    
    
    aluno['peso'] = st.number_input('Peso do aluno (KG)',value=aluno.get("peso", 0))
    aluno['idade'] = st.number_input("Idade", value=aluno.get("idade", 0))
    sex = aluno.get("sex")
    altura = st.number_input('Altura do aluno (cm)', value=aluno.get("altura", 0))
    #body_muscle = st.number_input("Porcentagem de massa magra")
    st.divider()
    st.header("Perimetria")
    chest = st.number_input("Torax (cm)",min_value=0)
    abdomen = st.number_input("Abdomen (cm)",min_value=0)
    waist = st.number_input("Cintura (cm)",min_value=0)
    hip = st.number_input("Quadril (cm)",min_value=0)
    shoulder1_relax = st.number_input("Braço direito relaxado(cm)",min_value=0)
    shoulder1_contract = st.number_input("Braço direito contraído(cm)",min_value=0)
    shoulder1_braquio = st.number_input("Antebraço direito(cm)",min_value=0)
    shoulder2_relax = st.number_input("Braço esquerdo relaxado(cm)",min_value=0)
    shoulder2_contract = st.number_input("Braço esquerdo contraído(cm)",min_value=0)
    shoulder2_braquio = st.number_input("Antebraço esquerdo(cm)",min_value=0)
    thigh1 = st.number_input("Coxa direita (cm)",min_value=0)
    thigh2 = st.number_input("Coxa esquerda (cm)",min_value=0)
    calf1 = st.number_input("Panturrilha direita (cm)",min_value=0)
    calf2 = st.number_input("Panturrilha esquerda (cm)",min_value=0)
    last = datetime.utcnow()
    st.divider()
    st.header('Avaliação de composição corporal')

    protocols = ["Pollock 7 dobras", "Pollock 3 dobras", "Faulkner", "Durnin & Womersley"]
    protocol = st.selectbox("Selecione um protocolo", protocols)

    if protocol == "Pollock 7 dobras":
        triciptal = st.number_input("Tricipital (mm)",min_value=0)
        peitoral = st.number_input("Peitoral (mm)",min_value=0)
        subescapular = st.number_input("Subescapular (mm)",min_value=0)
        axilar_media = st.number_input("Axilar média (mm)",min_value=0)
        suprailiaca = st.number_input("Suprailiaca (mm)",min_value=0)
        abdominal = st.number_input("Abdominal (mm)",min_value=0)
        coxa_media = st.number_input("Coxa média (mm)",min_value=0)
    
        dobras = {
            "triciptal": triciptal,
            "peitoral": peitoral,
            "subescapular": subescapular,
            "axilar_media": axilar_media,
            "suprailiaca": suprailiaca,
            "abdominal": abdominal,
            "coxa_media": coxa_media
        }

        fat_percent = pollock_7_dobras(dobras, aluno['idade'], sex)
        muscle_percent = 100 - fat_percent
        body_muscle = aluno['peso'] * (1 - (fat_percent / 100))
        body_fat = aluno['peso'] - body_muscle

        form_avaliação = {'user' : professor,
                        'student_name' : nome_selecionado,
                        'body_fat' : body_fat,
                        'body_muscle' : body_muscle,
                        'fat_percent' : fat_percent,
                        'muscle_percent' : muscle_percent,
                        'chest' : chest,
                        'shoulder1_relax' : shoulder1_relax,
                        'shoulder1_contract' : shoulder1_contract,
                        'shoulder1_braquio' : shoulder1_braquio,
                        'shoulder2_relax' : shoulder2_relax,
                        'shoulder2_contract' : shoulder2_contract,
                        'shoulder2_braquio' : shoulder2_braquio,
                        'waist' : waist,
                        'hip' : hip,
                        'thigh1' : thigh1,
                        'thigh2' : thigh2,
                        'calf1' : calf1,
                        'calf2' : calf2,
                        'abdomen' : abdomen,
                        'protocolo' : protocol,
                        'triciptal' : triciptal,
                        'peitoral' : peitoral,
                        'subescapular' : subescapular,
                        'axilar_media' : axilar_media,
                        'suprailiaca' : suprailiaca,
                        'abdominal' : abdominal,
                        'coxa_media' : coxa_media, 
                        'idade' : aluno['idade'], 
                        'sex' : sex, 
                        'peso' : aluno['peso'], 
                        'altura' : altura,
                        'last' : last}

    if protocol == "Pollock 3 dobras":
        if sex == "Masculino":
            peitoral = st.number_input("Peitoral (mm)",min_value=0)
            abdominal = st.number_input("Abdominal (mm)",min_value=0)
            coxa_anterior = st.number_input("Coxa anterior (mm)",min_value=0)

            dobras = {
            "peitoral": peitoral,
            "abdominal": abdominal,
            "coxa_anterior": coxa_anterior}

            fat_percent = pollock_3_dobras(dobras,aluno['idade'],sex)
            muscle_percent = 100 - fat_percent
            body_muscle = aluno['peso'] * (1 - (fat_percent / 100))
            body_fat = aluno['peso'] - body_muscle

            form_avaliação = {'user' : professor,
                            'student_name' : nome_selecionado,
                            'body_fat' : body_fat,
                            'body_muscle' : body_muscle,
                            'muscle_percent' : muscle_percent,
                            'fat_percent' : fat_percent,
                            'chest' : chest,
                            'shoulder1_relax' : shoulder1_relax,
                            'shoulder1_contract' : shoulder1_contract,
                            'shoulder1_braquio' : shoulder1_braquio,
                            'shoulder2_relax' : shoulder2_relax,
                            'shoulder2_contract' : shoulder2_contract,
                            'shoulder2_braquio' : shoulder2_braquio,
                            'waist' : waist,
                            'hip' : hip,
                            'thigh1' : thigh1,
                            'thigh2' : thigh2,
                            'calf1' : calf1,
                            'calf2' : calf2,
                            'abdomen' : abdomen,
                            'protocolo' : protocol,
                            'peitoral' : peitoral,
                            'abdominal' : abdominal,
                            'coxa_anterior' : coxa_anterior,  
                            'idade' : aluno['idade'], 
                            'sex' : sex, 
                            'peso' : aluno['peso'], 
                            'altura' : altura,
                            'last' : last}
        
        if sex == "Feminino":
            triciptal = st.number_input("Tricipital (mm)",min_value=0)
            suprailiaca = st.number_input("Supra-ilíaca (mm)",min_value=0)
            coxa_anterior = st.number_input("Coxa anterior (mm)",min_value=0)
    
            dobras = {
            "triciptal": triciptal,
            "suprailiaca": suprailiaca,
            "coxa_anterior": coxa_anterior}

            fat_percent = pollock_3_dobras(dobras,aluno['idade'],sex)
            muscle_percent = 100 - fat_percent
            body_muscle = aluno['peso'] * (1 - (fat_percent / 100))
            body_fat = aluno['peso'] - body_muscle


            form_avaliação = {'user' : professor,
                            'student_name' : nome_selecionado,
                            'body_fat' : body_fat,
                            'body_muscle' : body_muscle,
                            'fat_percent' : fat_percent,
                            'muscle_percent' : muscle_percent,
                            'chest' : chest,
                            'shoulder1_relax' : shoulder1_relax,
                            'shoulder1_contract' : shoulder1_contract,
                            'shoulder1_braquio' : shoulder1_braquio,
                            'shoulder2_relax' : shoulder2_relax,
                            'shoulder2_contract' : shoulder2_contract,
                            'shoulder2_braquio' : shoulder2_braquio,
                            'waist' : waist,
                            'hip' : hip,
                            'thigh1' : thigh1,
                            'thigh2' : thigh2,
                            'calf1' : calf1,
                            'calf2' : calf2,
                            'abdomen' : abdomen,
                            'protocolo' : protocol,
                            'peitoral' : peitoral,
                            'suprailiaca' : suprailiaca,
                            'coxa_anterior' : coxa_anterior,  
                            'idade' : aluno['idade'], 
                            'sex' : sex, 
                            'peso' : aluno['peso'], 
                            'altura' : altura,
                            'last' : last}

    if protocol == "Faulkner":
        triciptal = st.number_input("Tricipital (mm)",min_value=0)
        subescapular = st.number_input("Subescapular (mm)",min_value=0)
        suprailiaca = st.number_input("Suprailiaca (mm)",min_value=0)
        abdominal = st.number_input("Abdominal (mm)",min_value=0)
        
        dobras = {
            "triciptal": triciptal,            
            "subescapular": subescapular,
            "suprailiaca": suprailiaca,
            "abdominal": abdominal,
        }

        fat_percent = pollock_7_dobras(dobras)
        muscle_percent = 100 - fat_percent
        body_muscle = aluno['peso'] * (1 - (fat_percent / 100))
        body_fat = aluno['peso'] - body_muscle

        form_avaliação = {'user' : professor,
                        'student_name' : nome_selecionado,
                        'body_fat' : body_fat,
                        'body_muscle' : body_muscle,
                        'fat_percent' : fat_percent,
                        'muscle_percent' : muscle_percent,
                        'chest' : chest,
                        'shoulder1_relax' : shoulder1_relax,
                        'shoulder1_contract' : shoulder1_contract,
                        'shoulder1_braquio' : shoulder1_braquio,
                        'shoulder2_relax' : shoulder2_relax,
                        'shoulder2_contract' : shoulder2_contract,
                        'shoulder2_braquio' : shoulder2_braquio,
                        'waist' : waist,
                        'hip' : hip,
                        'thigh1' : thigh1,
                        'thigh2' : thigh2,
                        'calf1' : calf1,
                        'calf2' : calf2,
                        'abdomen' : abdomen,
                        'protocolo' : protocol,
                        'triciptal' : triciptal,
                        'subescapular' : subescapular,
                        'suprailiaca' : suprailiaca,
                        'abdominal' : abdominal, 
                        'idade' : aluno['idade'], 
                        'sex' : sex, 
                        'peso' : aluno['peso'], 
                        'altura' : altura,
                        'last' : last}
        
    if protocol == "Durnin & Womersley":
        biciptal = st.number_input("Bíceps (mm)",min_value=0)
        triciptal = st.number_input("Tríceps (mm)",min_value=0) 
        subescapular = st.number_input("Subescapular (mm)",min_value=0)
        suprailiaca = st.number_input("Suprailiaca (mm)",min_value=0)
        
        fat_percent = percentual_gordura_durnin_womersley(biciptal, triciptal, subescapular, suprailiaca, aluno['idade'], sex)
        muscle_percent = 100 - fat_percent
        body_muscle = aluno['peso'] * (1 - (fat_percent / 100))
        body_fat = aluno['peso'] - body_muscle

        form_avaliação = {'user' : professor,
                        'student_name' : nome_selecionado,
                        'body_fat' : body_fat,
                        'body_muscle' : body_muscle,
                        'muscle_percent' : muscle_percent,
                        'fat_percent' : fat_percent,
                        'chest' : chest,
                        'shoulder1_relax' : shoulder1_relax,
                        'shoulder1_contract' : shoulder1_contract,
                        'shoulder1_braquio' : shoulder1_braquio,
                        'shoulder2_relax' : shoulder2_relax,
                        'shoulder2_contract' : shoulder2_contract,
                        'shoulder2_braquio' : shoulder2_braquio,
                        'waist' : waist,
                        'hip' : hip,
                        'thigh1' : thigh1,
                        'thigh2' : thigh2,
                        'calf1' : calf1,
                        'calf2' : calf2,
                        'abdomen' : abdomen,
                        'protocolo' : protocol,
                        'triciptal' : triciptal,
                        'subescapular' : subescapular,
                        'suprailiaca' : suprailiaca,
                        'biciptal' : biciptal, 
                        'idade' : aluno['idade'], 
                        'sex' : sex, 
                        'peso' : aluno['peso'], 
                        'altura' : altura,
                        'last' : last}
        
    if st.button('Confirmar avaliação'):
        coll2.insert_one(form_avaliação)
        campos_para_atualizar = {
            "peso": aluno["peso"],
            "idade": aluno["idade"],
            "altura": aluno["altura"]
            # Adicione outros campos, se quiser
        }
        coll1.update_one({"_id": aluno["_id"]}, {"$set": campos_para_atualizar})
            
        print("Documentos inseridos com sucesso")
        st.success(f"✅ Avaliação cadastrada com sucesso")
        
    return form_avaliação

def visualizar_aluno(professor):
    alunos = coll1.find({"user": professor})
    nomes_alunos = [aluno["student_name"] for aluno in alunos]

    if not nomes_alunos:
        st.info("Você ainda não cadastrou nenhum aluno.")
        return

    nome_selecionado = st.selectbox("Selecione um aluno para editar", nomes_alunos)
    aluno = coll1.find_one({"student_name": nome_selecionado, "user": professor})

    if not aluno:
        st.warning("Erro ao carregar os dados do aluno.")
        return
    
    st.divider()

    # Seção 1: Dados Pessoais
    st.subheader("🧍‍♂️ Informações Pessoais")
    col1,col2,col3,col4 = st.columns(4)
    aluno['idade'] = col1.metric("Idade", value=aluno.get("idade"))
    aluno['sex'] = col2.metric("Sexo", aluno.get("sex"))
    aluno['peso'] = col3.metric("Peso (kg)", f'{aluno.get("peso")}')
    aluno['altura'] = col4.metric("Altura (cm)", f'{aluno.get("altura")}')
    aluno['objective'] = st.metric("Objetivo", value=aluno.get("objective", ""))
    aluno['experience'] = st.metric("Experiência", aluno.get("experience"))
    aluno['profession'] = st.metric("Profissão", value=aluno.get("profession"))
    st.markdown("Rotina:")
    aluno['routine'] = st.write(aluno.get("routine"))

    st.divider()
    # Seção 2: Saúde
    st.subheader("🩺 Saúde")
    st.markdown('**Lesões**')
    aluno['lesoes'] = st.write(aluno.get("lesoes"))
    st.markdown('**Doenças**')
    aluno['doencas'] = st.write(aluno.get("doencas"))
    st.markdown('**Aprovação médica**')
    aluno['medical_aprove'] = st.write(aluno.get("medical_aprove"))
    st.markdown('**Medicamentos**')
    aluno['medicines'] = st.write(aluno.get("medicines"))
    st.markdown('**Postura**')
    aluno['postura'] = st.write(aluno.get("postura"))

    st.divider()
    # Seção 3: Treino
    st.subheader("🏋️ Histórico de Treino")
    col1,col2 = st.columns(2)
    aluno['frequency'] = col1.metric("Frequência semanal", value=aluno.get("frequency"))
    aluno['duration'] = col2.metric("Duração por sessão (minutos)", value=aluno.get("duration"))
    st.markdown('**Equipamentos**')
    aluno['equipments'] = st.write(aluno.get("equipments"))
    st.markdown('**Preferência de local**')
    aluno['preferences'] = st.write(aluno.get("preferences"))
    st.markdown('**Gosta / não gosta**')
    aluno['like'] = st.write(aluno.get("like"))
    st.markdown('**Experiência prévia**')
    aluno['exp'] = st.write(aluno.get("exp"))
    st.markdown('**Estilo de treino**')
    aluno['style'] = st.write(aluno.get("style"))
    st.markdown('**Tempo disponível por dia**')
    aluno['time'] = st.write(aluno.get("time"))

def dash_prof(professor):
    col1,col2 = st.columns(2)
    alunos = coll1.find({"user": professor})
    nomes_alunos = [aluno["student_name"] for aluno in alunos]
    col1.metric('Alunos cadastrados', len(nomes_alunos))
    avaliacoes = coll2.find({"user": professor})
    avaliacoes_alunos = [aluno["student_name"] for aluno in avaliacoes]
    col2.metric('Avaliações feitas', len(avaliacoes_alunos))
    treinos = coll3.find({"user": professor})
    treinos_alunos = [aluno["student"] for aluno in treinos]
    col1.metric('Treinos com auxilio do AtlasAI 🌎', len(treinos_alunos))
    analises = coll4.find({"user": professor})
    analise_alunos = [analise["student"] for analise in analises]
    col2.metric('Análises com auxilio do AtlasAI 🌎', len(analise_alunos))

def avaliacao_alunos(student):
    user = coll2.find({"student_name": student})
    avaliacoes_alunos = [aluno["last"] for aluno in user]

    if not avaliacoes_alunos:
        st.info("Você ainda não possui avaliações.")
        return

    alunos = coll1.find_one({"student_name": student})
    dados_aluno = alunos

    st.header('**Ultima Avaliação**')
    st.subheader("As métricas são as diferenças entre sua avaliação mais recente e a anterior")
    st.divider()
    avaliacao_recente = avaliacoes_alunos[-1]
    avaliacao_atual = coll2.find_one({"last": avaliacao_recente, "student_name": student})
    
    if len(avaliacoes_alunos) >= 2:
        avaliacao_comparacao = avaliacoes_alunos[-2]
        avaliacao_anterior = coll2.find_one({"last": avaliacao_comparacao, "student_name": student})
    else:
        avaliacao_comparacao = avaliacao_recente
        avaliacao_anterior = coll2.find_one({"last": avaliacao_comparacao, "student_name": student})

    col1,col2,col3 = st.columns(3)
    col1.metric("Idade", dados_aluno.get("idade"))

    col2.metric('Altura(cm)', dados_aluno.get("altura"))
    
    col3.metric('Peso(KG)', avaliacao_atual.get("peso"),delta=round((avaliacao_atual.get("peso") - avaliacao_anterior.get("peso")),2), delta_color="inverse")

    col1.metric("Quantidade de gordura corporal", f'{round(avaliacao_atual.get("body_fat"),2)} KG',delta=round((avaliacao_atual.get("body_fat") - avaliacao_anterior.get("body_fat")),2), delta_color="inverse")
    col1.metric("Porcentagem de gordura corporal", f'{round(avaliacao_atual.get("fat_percent"),2)} %',delta=round((avaliacao_atual.get("fat_percent") - avaliacao_anterior.get("fat_percent")),2), delta_color="inverse")
    
    col2.metric("Quantidade de massa magra", f'{round(avaliacao_atual.get("body_muscle"),2)} KG',delta=round((avaliacao_atual.get("body_muscle") - avaliacao_anterior.get("body_muscle")),2))
    col2.metric("Porcentagem de massa magra", f'{round(avaliacao_atual.get("muscle_percent"),2)} %',delta=round((avaliacao_atual.get("muscle_percent") - avaliacao_anterior.get("muscle_percent")),2))

    imc = round((avaliacao_atual.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
    imc_anterior = round((avaliacao_anterior.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
    col3.metric("IMC", imc, delta=round((imc - imc_anterior),2), delta_color="inverse")

    st.header('Medidas Corporais')
    col1,col2, col3 = st.columns(3)
    col1.metric("Toráx (cm)",avaliacao_atual.get("chest"), delta=round((avaliacao_atual.get("chest") - avaliacao_anterior.get("chest")),2), delta_color="inverse")
    col2.metric("Abdomen (cm)",avaliacao_atual.get('abdomen'),delta=round((avaliacao_atual.get("abdomen") - avaliacao_anterior.get("abdomen")),2), delta_color="inverse")
    col1.metric("Cintura (cm)",avaliacao_atual.get('waist'),delta=round((avaliacao_atual.get("waist") - avaliacao_anterior.get("abdomen")),2), delta_color="inverse")
    col2.metric("Quadril (cm)",avaliacao_atual.get('hip'),delta=round((avaliacao_atual.get("hip") - avaliacao_anterior.get("hip")),2), delta_color="inverse")
    
    col1.metric("Braço direito relaxado (cm)",avaliacao_atual.get('shoulder1_relax'), delta=round((avaliacao_atual.get("shoulder1_relax") - avaliacao_anterior.get("shoulder1_relax")),2), delta_color="inverse")
    col2.metric("Braço direito contraído (cm)",avaliacao_atual.get('shoulder1_contract'), delta=round((avaliacao_atual.get("shoulder1_contract") - avaliacao_anterior.get("shoulder1_contract")),2), delta_color="inverse")
    col3.metric("Antebraço direito (cm)",avaliacao_atual.get('shoulder1_braquio'), delta=round((avaliacao_atual.get("shoulder1_braquio") - avaliacao_anterior.get("shoulder1_braquio")),2), delta_color="inverse")
    
    col1.metric("Braço esquerdo relaxado (cm)",avaliacao_atual.get('shoulder1_relax'), delta=round((avaliacao_atual.get("shoulder1_relax") - avaliacao_anterior.get("shoulder1_relax")),2), delta_color="inverse")
    col2.metric("Braço esquerdo contraído (cm)",avaliacao_atual.get('shoulder1_contract'), delta=round((avaliacao_atual.get("shoulder1_contract") - avaliacao_anterior.get("shoulder1_contract")),2), delta_color="inverse")
    col3.metric("Antebraço esquerdo (cm)",avaliacao_atual.get('shoulder1_braquio'), delta=round((avaliacao_atual.get("shoulder1_braquio") - avaliacao_anterior.get("shoulder1_braquio")),2), delta_color="inverse")
    
    col1.metric("Coxa direita (cm)",avaliacao_atual.get('thigh1'),delta=round((avaliacao_atual.get("thigh1") - avaliacao_anterior.get("thigh1")),2), delta_color="inverse")
    col2.metric("Coxa esquerda (cm)",avaliacao_atual.get('thigh1'),delta=round((avaliacao_atual.get("thigh2") - avaliacao_anterior.get("thigh2")),2), delta_color="inverse")
    col3.metric("Panturrilha direita (cm)",avaliacao_atual.get('calf1'),delta=round((avaliacao_atual.get("calf1") - avaliacao_anterior.get("calf1")),2), delta_color="inverse")
    col1.metric("Panturrilha esquerda (cm)",avaliacao_atual.get('calf2'),delta=round((avaliacao_atual.get("calf2") - avaliacao_anterior.get("calf2")),2), delta_color="inverse")

    st.divider()
    st.header('Avaliação de composição corporal')
    col1,col2,col3 = st.columns(3)
    st.metric('Protocolo Utilizado', avaliacao_atual.get('protocolo'))
    if avaliacao_atual.get('protocolo') == 'Pollock 7 dobras':
        col1.metric('Tricipital (mm)', avaliacao_atual.get('triciptal'))
        col2.metric('Peitoral (mm)', avaliacao_atual.get('peitoral'))
        col3.metric('Subescapular (mm)', avaliacao_atual.get('subescapular'))
        col1.metric('Axilar média (mm)', avaliacao_atual.get('axilar_media'))
        col2.metric('Suprailiaca (mm)', avaliacao_atual.get('suprailiaca'))
        col3.metric('Abdominal (mm)', avaliacao_atual.get('abdominal'))
        col1.metric('Coxa média (mm)', avaliacao_atual.get('coxa_media'))

    if avaliacao_atual.get('protocolo') == 'Pollock 3 dobras':
        if avaliacao_atual.get('sex') == 'Masculino':
            col1.metric('Peitoral (mm)', avaliacao_atual.get('peitoral'))
            col2.metric('Abdominal (mm)', avaliacao_atual.get('abdominal'))
            col3.metric('Coxa anterior (mm)', avaliacao_atual.get('coxa_anterior'))

        if avaliacao_atual.get('sex') == 'Feminino':
            col1.metric('Tricipital (mm)', avaliacao_atual.get('triciptal'))
            col2.metric('Supra-ilíaca (mm)', avaliacao_atual.get('suprailiaca'))
            col3.metric('Coxa anterior (mm)', avaliacao_atual.get('coxa_anterior'))

    if avaliacao_atual.get('protocolo') == 'Faulkner':
        col1.metric('Tricipital (mm)', avaliacao_atual.get('triciptal'))
        col2.metric("Subescapular (mm)", avaliacao_atual.get('subescapular'))
        col3.metric("Suprailiaca (mm)", avaliacao_atual.get('suprailiaca'))
        col1.metric("Abdominal (mm)", avaliacao_atual.get('abdominal'))


    if avaliacao_atual.get('protocolo') == "Durnin & Womersley":
        col1.metric("Biceps (mm)", avaliacao_atual.get('biciptal'))
        col2.metric("Tríceps (mm)", avaliacao_atual.get('triciptal'))
        col3.metric("Subescapular (mm)", avaliacao_atual.get('subescapular'))
        col1.metric("Suprailiaca (mm)", avaliacao_atual.get('suprailiaca'))

    st.divider()
    st.header('**Avaliações Anteriores**')
    if st.toggle('Buscar avaliações anteriores:'):
        avaliacao_selecionado = st.selectbox("Selecione uma avaliação", avaliacoes_alunos)
        avaliacao = coll2.find_one({"last": avaliacao_selecionado, "student_name": student})
        col1,col2,col3 = st.columns(3)
        col1.metric("Idade", dados_aluno.get("idade"))

        col2.metric('Altura(cm)', dados_aluno.get("altura"))
        
        col3.metric('Peso(KG)', avaliacao.get("peso"))

        col1.metric("Quantidade de gordura corporal", f'{round(avaliacao.get("body_fat"),2)} KG')
        col1.metric("Porcentagem de gordura corporal", f'{round(avaliacao.get("fat_percent"),2)} %')
        
        col2.metric("Quantidade de massa magra", f'{round(avaliacao.get("body_muscle"),2)} KG')
        col2.metric("Porcentagem de massa magra", f'{round(avaliacao.get("muscle_percent"),2)} %')

        imc = round((avaliacao.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
        col3.metric("IMC", imc)

        st.header('Medidas Corporais')
        col1,col2, col3 = st.columns(3)
        col1.metric("Toráx (cm)",avaliacao.get("chest"))
        col2.metric("Abdomen (cm)",avaliacao.get('abdomen'))
        col1.metric("Cintura (cm)",avaliacao.get('waist'))
        col2.metric("Quadril (cm)",avaliacao.get('hip'))
        
        col1.metric("Braço direito relaxado (cm)",avaliacao.get('shoulder1_relax'))
        col2.metric("Braço direito contraído (cm)",avaliacao.get('shoulder1_contract'))
        col3.metric("Antebraço direito (cm)",avaliacao.get('shoulder1_braquio'))
        
        col1.metric("Braço esquerdo relaxado (cm)",avaliacao.get('shoulder1_relax'))
        col2.metric("Braço esquerdo contraído (cm)",avaliacao.get('shoulder1_contract'))
        col3.metric("Antebraço esquerdo (cm)",avaliacao.get('shoulder1_braquio'))
        
        col1.metric("Coxa direita (cm)",avaliacao.get('thigh1'))
        col2.metric("Coxa esquerda (cm)",avaliacao.get('thigh1'))
        col3.metric("Panturrilha direita (cm)",avaliacao.get('calf1'))
        col1.metric("Panturrilha esquerda (cm)",avaliacao.get('calf2'))

        st.divider()
        st.header('Avaliação de composição corporal')
        col1,col2,col3 = st.columns(3)
        st.metric('Protocolo Utilizado', avaliacao.get('protocolo'))
        if avaliacao.get('protocolo') == 'Pollock 7 dobras':
            col1.metric('Tricipital (mm)', avaliacao.get('triciptal'))
            col2.metric('Peitoral (mm)', avaliacao.get('peitoral'))
            col3.metric('Subescapular (mm)', avaliacao.get('subescapular'))
            col1.metric('Axilar média (mm)', avaliacao.get('axilar_media'))
            col2.metric('Suprailiaca (mm)', avaliacao.get('suprailiaca'))
            col3.metric('Abdominal (mm)', avaliacao.get('abdominal'))
            col1.metric('Coxa média (mm)', avaliacao.get('coxa_media'))

        if avaliacao.get('protocolo') == 'Pollock 3 dobras':
            if avaliacao.get('sex') == 'Masculino':
                col1.metric('Peitoral (mm)', avaliacao.get('peitoral'))
                col2.metric('Abdominal (mm)', avaliacao.get('abdominal'))
                col3.metric('Coxa anterior (mm)', avaliacao.get('coxa_anterior'))

            if avaliacao.get('sex') == 'Feminino':
                col1.metric('Tricipital (mm)', avaliacao.get('triciptal'))
                col2.metric('Supra-ilíaca (mm)', avaliacao.get('suprailiaca'))
                col3.metric('Coxa anterior (mm)', avaliacao.get('coxa_anterior'))

        if avaliacao.get('protocolo') == 'Faulkner':
            col1.metric('Tricipital (mm)', avaliacao.get('triciptal'))
            col2.metric("Subescapular (mm)", avaliacao.get('subescapular'))
            col3.metric("Suprailiaca (mm)", avaliacao.get('suprailiaca'))
            col1.metric("Abdominal (mm)", avaliacao.get('abdominal'))


        if avaliacao.get('protocolo') == "Durnin & Womersley":
            col1.metric("Biceps (mm)", avaliacao.get('biciptal'))
            col2.metric("Tríceps (mm)", avaliacao.get('triciptal'))
            col3.metric("Subescapular (mm)", avaliacao.get('subescapular'))
            col1.metric("Suprailiaca (mm)", avaliacao.get('suprailiaca'))
    
def treinos_alunos(student):
    user = coll3.find({"student": student})
    treinos_alunos = [aluno["date"] for aluno in user]

    if not treinos_alunos:
        st.info("Você ainda não possui treinos.")
        return
    
    st.header('**TREINO ATUAL**')
    st.divider()
    data = treinos_alunos[-1]
    ultimo_treino = coll3.find({"date": data, "student": student})
    treino = [treino["treino"] for treino in ultimo_treino]
    st.write(treino[0])

    st.header('**TREINOS ANTERIORES**')
    if st.toggle('Buscar treinos anteriores:'):
        treino_selecionado = st.selectbox("Selecione um treino", treinos_alunos)
        data_selecionada = coll3.find({"date": treino_selecionado, "student": student})
        treino_selecionado = [treino_s["treino"] for treino_s in data_selecionada]
        st.divider()
        st.write(treino_selecionado[0])

def dash_aluno(student):
    alunos = coll1.find({"student_name": student})
    nomes_alunos = [aluno for aluno in alunos]
    
    st.header('Dados corporais:')
    col1,col2 = st.columns(2)
    col1.metric("Idade", nomes_alunos[0].get("idade"))
    col2.metric('Peso(KG)', nomes_alunos[0].get("peso"))
    col1.metric('Altura(cm)', nomes_alunos[0].get("altura"))
    col2.metric("Objetivo", nomes_alunos[0].get("objective"))
    
    st.header('Dados de saúde:')
    col1,col2 = st.columns(2)
    col1.metric("Lesões", nomes_alunos[0].get("lesoes"))
    col2.metric("Doenças", nomes_alunos[0].get("doencas"))
    col1.metric("Aprovação médica", nomes_alunos[0].get("medical_aprove"))
    col2.metric("Medicamentos", nomes_alunos[0].get("medicines"))
    col1.metric("Postura", nomes_alunos[0].get("postura"))

    st.header('Outros dados:')
    col1,col2,col3 = st.columns(3)
    col1.metric("Experiência", nomes_alunos[0].get("experience"))
    #col2.metric("Profissão", nomes_alunos[0].get("profession"))
    #st.markdown("Rotina:")
    #st.write(nomes_alunos[0].get("routine"))
    
    col2.metric("Frequência semanal", nomes_alunos[0].get("frequency"))
    col3.metric("Duração por sessão", nomes_alunos[0].get("duration"))
    #st.markdown("Equipamentos:")
    #st.write(nomes_alunos[0].get("equipments"))
    
    col1.metric("Preferência de local", nomes_alunos[0].get("preferences"))
    #col3.metric("Gosta / não gosta", nomes_alunos[0].get("like"))
    #st.markdown("Experiência prévia:")
    #st.write(nomes_alunos[0].get("exp"))
    
    col2.metric("Estilo de treino", nomes_alunos[0].get("style"))
    col3.metric("Tempo disponível por dia", nomes_alunos[0].get("time"))

def treino_manual(professor):

    st.subheader('Área destinada à montagem de treinos sem o auxílio do AtlasAI 🌎')

    from datetime import datetime
    alunos = coll1.find({"user": professor})
    nomes_alunos = [aluno["student_name"] for aluno in alunos]
    student = st.selectbox('Aluno', nomes_alunos)
    treino = st.text_area("Descreva o treino aqui:")

    doc = {
        "user": professor,
        "student": student,
        "treino": treino,
        "date": datetime.now()
    }

    if st.button('Confirmar treino'):
        coll3.insert_one(doc)
        return st.success("Treino salvo com sucesso.")
    
def carrega_arquivo(tipo_arquivo, arquivo):
    if tipo_arquivo == 'Site':
        documento = carrega_site(arquivo)
    if tipo_arquivo == 'Vídeo Youtube':
        documento = carrega_youtube(arquivo)
    if tipo_arquivo == 'PDF':
        with tempfile.NamedTemporaryFile(suffix= '.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)
    if tipo_arquivo == 'CSV':
        with tempfile.NamedTemporaryFile(suffix= '.csv', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_csv(nome_temp)
    if tipo_arquivo == 'EXCEL':
        with tempfile.NamedTemporaryFile(suffix= '.xlsx', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_xlsx(nome_temp)
    if tipo_arquivo == 'Texto':
        with tempfile.NamedTemporaryFile(suffix= '.docx', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_txt(nome_temp)
    return documento

def pag_arquivos(professor):
    ARQUIVOS = ['Site', 'Vídeo Youtube', 'PDF', 'CSV', 'EXCEL', 'Texto']
    tipo = st.selectbox('Selecione o tipo de arquivo', ARQUIVOS)
    if tipo == 'Site':
        arquivo = st.text_input('Passe o link do site')
    if tipo == 'Vídeo Youtube':
        arquivo = st.text_input('Passe o link do vídeo')
    if tipo == 'PDF':
        arquivo = st.file_uploader('Faça o upload do PDF', type= ['.pdf'])#, accept_multiple_files= True)
    if tipo == 'CSV':
        arquivo = st.file_uploader('Faça o upload do CSV', type= ['.csv'])#, accept_multiple_files= True)
    if tipo == 'EXCEL':
        arquivo = st.file_uploader('Faça o upload do Excel', type= ['.xlsx'])#, accept_multiple_files= True)
    if tipo == 'Texto':
        arquivo = st.file_uploader('Faça o upload de texto', type= ['.docx'])#, accept_multiple_files= True)

    if arquivo:
        if st.button('Carregar arquivo'):
            with st.spinner('Carregando...'):
                doc = carrega_arquivo(tipo, arquivo)

                chunk_size = 500
                chunk_overlap = 50

                char_split = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=['\n\n', '\n', '.', ' ', '']
                )

                arquivo = char_split.split_documents(doc)
                embedding_model = OpenAIEmbeddings(api_key=st.secrets["OPENAI_API_KEY"], model="text-embedding-3-large")

                vector_store = MongoDBAtlasVectorSearch.from_documents(
                documents=arquivo,
                embedding=embedding_model,
                collection=coll5,
                index_name="default"
            )
            
            st.success('Arquivo carregado com sucesso')

def extrair_tags_feedback(mensagem: str) -> list:
    llm = ChatOpenAI(model="gpt-3.5-turbo",api_key=st.secrets["OPENAI_API_KEY"],temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """
        Sua tarefa é extrair palavras-chave relevantes de um feedback de aluno sobre treino.
        Retorne no máximo 5 palavras em uma lista Python, focando em:
        - Sintomas relatados (ex: dor, cansaço)
        - Exercícios mencionados (ex: agachamento, supino)
        - Áreas do corpo (ex: ombro, lombar)
        - Qualquer termo técnico relevante

        Feedback do aluno:
        "{mensagem}"

        Responda apenas com uma lista Python válida. Exemplo: ["ombro", "supino", "dor"]
        """
    )
    
    messages = prompt.format_messages(mensagem=mensagem)
    resposta = llm(messages)
    
    # Garante que a resposta seja interpretada como lista
    try:
        tags = eval(resposta.content.strip())
        if isinstance(tags, list):
            return tags
    except Exception:
        pass

    return []

def feedback(student):
    user = coll1.find({"student_name": student})
    nome_aluno = [aluno for aluno in user]

    st.divider()

    usuario = nome_aluno[0]['student_name']
    esforco = {"0": 'Extremamente Leve',
               "1": 'Muito Leve',
               "2": 'Leve',
               "3": 'Moderadamente Leve',
               "4": 'Pouco pesado',
               "5": 'Pesado',
               "6": 'Pesado',
               "7": 'Muito pesado',
               "8": 'Muito pesado',
               "9": 'Extremamente pesado',
               "10": 'Extremamente pesado'}
    
    list_esforco = []
    for grau in esforco:
        list_esforco.append(grau)
    
    grau_esforco = st.selectbox('Percepção do esforço', list_esforco)
    st.markdown(f'**{esforco[grau_esforco]}**')
    
    recover = {"0": 'Nenhuma recuperação',
               "1": 'Muito pouca recuperação',
               "2": 'Pouca recuperação',
               "3": 'Recuperação moderada',
               "4": 'Boa recuperação',
               "5": 'Muito boa recuperação',
               "6": 'Muito boa recuperação',
               "7": 'Muito, muito boa recuperação',
               "8": 'Muito, muito boa recuperação',
               "9": 'Muito, muito boa recuperação',
               "10": 'Totalmente recuperado'}
    
    list_recover = []
    for level in recover:
        list_recover.append(level)
    
    grau_recover = st.selectbox('Percepção de repouso', list_recover)
    st.markdown(f'**{recover[grau_recover]}**')
    
    message = st.text_input('Mensagem')
    ref = st.text_input('Referência', placeholder='Sobre qual treino você está falando?')

    feedback = {
        "student": usuario,
        "data": datetime.utcnow(),
        "esforco": esforco[grau_esforco],
        "recover": recover[grau_recover],
        "message": message,
        "tags" : extrair_tags_feedback(message),
        "ref": ref
    }

    if st.button('Enviar feedback'):
        coll6.insert_one(feedback)
        st.success('Feedback enviado com sucesso')
