import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Carrega o token do arquivo .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configura a API dddo Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde ao comando /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Olá, {user.first_name}! Sou o assistente virtual da clínica. Como posso te ajudar com seu agendamento hoje?"
    )

async def responder_com_ia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pega a mensagem do usuário, envia para o Gemini e responde no Telegram"""
    texto_usuario = update.message.text
    
    # Prompt de sistema para dar o contexto à IA
    prompt_clinica = f"Você é um assistente simpático de uma clínica médica. Seu objetivo é ajudar o usuário a marcar consultas. Seja breve e profissional. O usuário disse: {texto_usuario}"

    try:
        # Envia a mensagem para o Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_clinica,
        )
        
        # Envia de volta para o usuário no Telegram
        await update.message.reply_text(response.text)

    except Exception as e:
        print(f"Erro ao acessar a API do Gemini: {e}")
        await update.message.reply_text("Desculpe, tive um probleminha técnico para processar sua mensagem agora.")

def main() -> None:
    """Inicia o bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_com_ia))

    print("Bot com IA rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()