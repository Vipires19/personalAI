import streamlit as st
from pymongo import MongoClient
import streamlit as st
import urllib.parse
from utils.createUsers import hash_passwords
import datetime

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
    chest = st.number_input("Peito (cm)",min_value=0, placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    shoulder = st.number_input("Braço (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    waist = st.number_input("Cintura (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    hip = st.number_input("Quadril (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    thigh = st.number_input("Coxa (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
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
                       'shoulder' : shoulder,
                       'waist' : waist,
                       'hip' : hip,
                       'thigh' : thigh, 
                       'idade' : idade, 
                       'sex' : sex, 
                       'peso' : peso, 
                       'altura' : altura,
                       'date' : last_datetime}
    
    hash_passwords(password)
    hashed_passwords = hash_passwords(password)

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
    
    
    aluno['peso'] = st.number_input('Peso do aluno (KG)')
    aluno['idade'] = st.number_input("Idade", value=aluno.get("idade", 0))
    sex = aluno.get("sex")
    altura = st.number_input('Altura do aluno (cm)', min_value=0)
    body_fat = st.number_input("Porcentagem de gordura corporal")
    chest = st.number_input("Peito (cm)",min_value=0, placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    shoulder = st.number_input("Braço (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    waist = st.number_input("Cintura (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    hip = st.number_input("Quadril (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    thigh = st.number_input("Coxa (cm)",min_value=0,placeholder='Utilize . inves de , caso numero quebrado. EX: 81.2')
    last = datetime.date.today()
    last_datetime = datetime.datetime.combine(last, datetime.time())

    form_avaliação = {'user' : professor,
                       'student_name' : nome_selecionado,
                       'body_fat' : body_fat,
                       'chest' : chest,
                       'shoulder' : shoulder,
                       'waist' : waist,
                       'hip' : hip,
                       'thigh' : thigh, 
                       'idade' : aluno['idade'], 
                       'sex' : sex, 
                       'peso' : aluno['peso'], 
                       'altura' : altura,
                       'last' : last_datetime}
    
    if st.button('Confirmar avaliação'):
        coll2.insert_one(form_avaliação)
        coll1.update_one({"_id": aluno["_id"]}, {"$set": aluno})
        
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

    col2.metric('Peso(KG)', avaliacao_atual.get("peso"),delta=round((avaliacao_atual.get("peso") - avaliacao_anterior.get("peso")),2), delta_color="inverse")

    col1.metric('Altura(cm)', dados_aluno.get("altura"))

    col2.metric("Porcentagem de gordura corporal", avaliacao_atual.get("body_fat"),delta=round((avaliacao_atual.get("body_fat") - avaliacao_anterior.get("body_fat")),2), delta_color="inverse")
    imc = round((avaliacao_atual.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
    imc_anterior = round((avaliacao_anterior.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
    col3.metric("IMC", imc, delta=round((imc - imc_anterior),2), delta_color="inverse")

    st.header('Medidas Corporais')
    col1,col2,col3 = st.columns(3)
    col1.metric("Peito (cm)",avaliacao_atual.get("chest"), delta=round((avaliacao_atual.get("chest") - avaliacao_anterior.get("chest")),2), delta_color="inverse")
    col2.metric("Braço (cm)",avaliacao_atual.get('shoulder'), delta=round((avaliacao_atual.get("shoulder") - avaliacao_anterior.get("shoulder")),2), delta_color="inverse")
    col1.metric("Cintura (cm)",avaliacao_atual.get('waist'),delta=round((avaliacao_atual.get("waist") - avaliacao_anterior.get("waist")),2), delta_color="inverse")
    col2.metric("Quadril (cm)",avaliacao_atual.get('hip'),delta=round((avaliacao_atual.get("hip") - avaliacao_anterior.get("hip")),2), delta_color="inverse")
    col3.metric("Coxa (cm)",avaliacao_atual.get('thigh'),delta=round((avaliacao_atual.get("thigh") - avaliacao_anterior.get("thigh")),2), delta_color="inverse")

    st.divider()
    st.header('**Avaliações Anteriores**')
    if st.toggle('Buscar avaliações anteriores:'):
        avaliacao_selecionado = st.selectbox("Selecione uma avaliação", avaliacoes_alunos)
        avaliacao = coll2.find_one({"last": avaliacao_selecionado, "student_name": student})
        col1,col2,col3 = st.columns(3)
        col1.metric("Idade", dados_aluno.get("idade"))
        col2.metric('Peso(KG)', avaliacao.get("peso"))
        col1.metric('Altura(cm)', dados_aluno.get("altura"))
        col2.metric("Porcentagem de gordura corporal", avaliacao.get("body_fat"))
        imc = round((avaliacao.get("peso") / ((dados_aluno.get("altura")/100) * (dados_aluno.get("altura")/100))),2)
        col3.metric("IMC", imc)
        st.header('Medidas Corporais')
        col1,col2,col3 = st.columns(3)
        col1.metric("Peito (cm)",avaliacao.get("chest"))
        col2.metric("Braço (cm)",avaliacao.get('shoulder'))
        col1.metric("Cintura (cm)",avaliacao.get('waist'))
        col2.metric("Quadril (cm)",avaliacao.get('hip'))
        col3.metric("Coxa (cm)",avaliacao.get('thigh'))
    
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