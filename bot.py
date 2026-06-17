import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from agenda import agendar_consulta

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Armazena o histórico de conversa de cada usuário
memoria_usuarios = {}

# Schema da função de agendamento para o Gemini
ferramenta_agendar = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="agendar_consulta",
            description="Cria um evento na agenda médica da clínica.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "nome_paciente": types.Schema(
                        type=types.Type.STRING, 
                        description="Nome completo do paciente"
                    ),
                    "data_hora_iso": types.Schema(
                        type=types.Type.STRING, 
                        description="Data e hora no formato ISO 8601 (ex: 2026-06-18T14:00:00)"
                    ),
                },
                required=["nome_paciente", "data_hora_iso"],
            )
        )
    ]
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # Reseta o histórico se o usuário recomeçar a conversa
    if user.id in memoria_usuarios:
        del memoria_usuarios[user.id]
        
    await update.message.reply_text(
        f"Olá, {user.first_name}! Sou o assistente virtual da clínica. Como posso ajudar com o seu agendamento hoje?"
    )

async def responder_com_ia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto_usuario = update.message.text
    user_id = update.effective_user.id

    hoje = datetime.now().strftime("%Y-%m-%d")

    config = types.GenerateContentConfig(
        system_instruction=(
            "Você é um assistente simpático de uma clínica médica. O seu objetivo é ajudar o utilizador a marcar consultas. "
            "Para fazer um agendamento, você DEVE perguntar e obter: o nome do paciente, a data e o horário. "
            "Quando tiver estes dados, utilize a ferramenta 'agendar_consulta' para fixar o compromisso. "
            f"Importante: Hoje é {hoje}. Converta termos como 'amanhã' ou 'terça' para o formato ISO correto usando esta data base."
        ),
        tools=[ferramenta_agendar] 
    )

    # Cria uma nova sessão de chat se o usuário não tiver uma
    if user_id not in memoria_usuarios:
        memoria_usuarios[user_id] = client.chats.create(
            model='gemini-2.5-flash',
            config=config
        )

    chat = memoria_usuarios[user_id]

    try:
        response = chat.send_message(texto_usuario)
        
        # Verifica se a IA decidiu chamar a função
        if response.function_calls:
            for call in response.function_calls:
                if call.name == "agendar_consulta":
                    
                    args = call.args
                    nome = args.get("nome_paciente")
                    data_hora = args.get("data_hora_iso")
                    
                    # Executa a integração com o Google Calendar
                    sucesso = agendar_consulta(nome_paciente=nome, data_hora_iso=data_hora)
                    
                    if sucesso:
                        await update.message.reply_text(
                            f"Confirmado! Consulta agendada com sucesso para {nome}.\n"
                            f"Data/Hora: {data_hora}"
                        )
                        # Limpa o histórico após concluir o agendamento
                        del memoria_usuarios[user_id] 
                    else:
                        await update.message.reply_text(
                            "Tive uma dificuldade técnica ao acessar a agenda. Por favor, tente novamente."
                        )
                    return 

        # Envia a resposta de texto normal
        await update.message.reply_text(response.text)

    except Exception as e:
        print(f"Erro: {e}")
        await update.message.reply_text("Desculpe, tive um problema para processar a sua mensagem.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_com_ia))

    print("Bot rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()