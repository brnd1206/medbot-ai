"""
main.py - Ponto de entrada do MedBot AI.

Responsabilidades:
  - Carregar as variáveis de ambiente.
  - Inicializar o banco de dados.
  - Registrar os handlers no bot do Telegram.
  - Iniciar o polling.
"""

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from database import inicializar_banco
from bot_handlers import comando_start, responder_mensagem


def main() -> None:
    # 1. Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_TOKEN")

    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN não encontrado. Verifique o seu arquivo .env")

    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY não encontrada. Verifique o seu arquivo .env")

    # 2. Inicializa o banco de dados SQLite (cria tabela se não existir)
    inicializar_banco()

    # 3. Cria a aplicação do Telegram
    application = Application.builder().token(telegram_token).build()

    # 4. Registra os handlers
    application.add_handler(CommandHandler("start", comando_start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem)
    )

    # 5. Inicia o bot em modo polling
    print("MedBot AI rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
