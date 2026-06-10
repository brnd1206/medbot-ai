import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde ao comando /start"""
    user = update.effective_user
    await update.message.reply_text(f"Olá, {user.first_name}! Sou o assistente virtual da clínica. Como posso te ajudar hoje?")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repete a mensagem do usuário (apenas para teste de integração)"""
    await update.message.reply_text(f"Você disse: {update.message.text}")

def main() -> None:
    """Inicia o bot"""
    # Cria a aplicação e passa o token
    application = Application.builder().token(TOKEN).build()

    # Adiciona os manipuladores de comandos e mensagens
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Roda o bot até você apertar Ctrl-C
    print("Bot rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()