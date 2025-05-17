# personal_comparator/utils/openai_feedback.py

import openai

def generate_feedback_via_openai(joint_errors, openai_api_key):
    openai.api_key = openai_api_key

    # Monta a descrição dos erros
    errors_description = "\n".join([f"{joint}: diferença de {error:.1f} graus" for joint, error in joint_errors.items()])

    prompt = f"""
        Você é um personal trainer experiente e comunicativo.

        Com base nas diferenças de ângulos articulares abaixo, gere um **feedback claro e prático**, como se estivesse orientando diretamente um aluno durante o treino.

        🔎 Dados:
        {errors_description}

        🎯 Instruções:
        - Aponte de forma objetiva o que precisa ser corrigido (ex: “Você precisa alinhar melhor os ombros”, “Evite estender demais o cotovelo”).
        - Use uma linguagem acessível e direta, sem exagerar em termos técnicos.
        - Sugira **ajustes posturais práticos e fáceis de entender**.
        - O tom deve ser profissional, mas amigável — como um personal trainer atencioso guiando o aluno durante a execução do exercício.
        - Se possível, dê pequenas dicas que o aluno possa aplicar imediatamente (ex: “pense em empurrar o chão com o calcanhar”, “mantenha o peito aberto”).

        Exemplo de estilo:
        "Seu ombro esquerdo está elevando demais, isso pode estar te fazendo perder estabilidade. Tente manter os ombros nivelados e relaxados durante o movimento."

        Agora gere o feedback com base nos dados acima.
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Pode usar "gpt-3.5-turbo" para custo mais baixo
        messages=[
            {"role": "system", "content": "Você é um personal trainer especialista."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=500,
    )

    return response.choices[0].message.content
