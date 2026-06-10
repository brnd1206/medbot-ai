import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Inicializa o cliente do Grok apontando para o servidor da xAI
grok_client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde ao comando /start"""
    user = update.effective_user
    await update.message.reply_text(f"Olá, {user.first_name}! Sou o assistente virtual da clínica. Como posso te ajudar hoje?")

async def responder_com_ia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pega a mensagem do usuário, envia para o Grok e responde no Telegram"""
    texto_usuario = update.message.text

    try:
        # Envia a mensagem para o Grok
        response = grok_client.chat.completions.create(
            model="grok-4.1-fast", # Modelo rápido e ideal para chatbots textuais
            messages=[
                {
                    "role": "system", 
                    "content": "Você é um assistente simpático de uma clínica médica. Seu objetivo é ajudar o usuário a marcar consultas. Seja breve e profissional."
                },
                {"role": "user", "content": texto_usuario}
            ]
        )
        
        # Pega a resposta em texto da IA
        resposta_ia = response.choices[0].message.content
        
        # Envia de volta para o usuário no Telegram
        await update.message.reply_text(resposta_ia)

    except Exception as e:
        print(f"Erro ao acessar a API do Grok: {e}")
        await update.message.reply_text("Desculpe, tive um probleminha técnico para processar sua mensagem agora.")

def main() -> None:
    """Inicia o bot"""
    # Cria a aplicação e passa o token
    application = Application.builder().token(TOKEN).build()

    # Adiciona os manipuladores de comandos e mensagens
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_com_ia))

    # Roda o bot até você apertar Ctrl-C
    print("Bot rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()