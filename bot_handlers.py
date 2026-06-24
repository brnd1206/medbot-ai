"""
bot_handlers.py - Rotas e manipuladores de mensagens do Telegram.

Responsabilidades:
  - Definir os handlers de comandos (/start opcional) e de mensagens de texto.
  - Iniciar a conversa automaticamente na primeira mensagem do usuário.
  - Delegar o processamento da mensagem ao ai_service.
  - Enviar a resposta de volta ao usuário no Telegram.
"""

from telegram import Update
from telegram.ext import ContextTypes

from ai_service import processar_mensagem, resetar_historico, memoria_usuarios

MENSAGEM_BOAS_VINDAS = (
    "Olá! Sou o assistente virtual da clínica. 👋\n\n"
    "Estou aqui para ajudar com o agendamento de consultas.\n"
    "Para começar, qual especialidade você está buscando?\n\n"
    "• Psicologia\n"
    "• Terapia Ocupacional\n"
    "• Fisioterapia\n"
    "• Nutrição\n"
    "• Fonoaudiologia"
)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para o comando /start (opcional).
    Reseta o histórico e reenvia a saudação inicial.
    """
    resetar_historico(update.effective_user.id)
    await update.message.reply_text(MENSAGEM_BOAS_VINDAS)


async def responder_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para mensagens de texto comuns.

    - Se for a primeira mensagem do usuário (sem histórico), envia a saudação
      automaticamente antes de processar a mensagem pela IA.
    - Encaminha o texto ao serviço de IA e devolve a resposta ao usuário.
    """
    texto_usuario = update.message.text
    user_id = update.effective_user.id
    primeira_mensagem = user_id not in memoria_usuarios

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    try:
        # Envia boas-vindas automaticamente na primeira interação
        if primeira_mensagem:
            await update.message.reply_text(MENSAGEM_BOAS_VINDAS)

        resposta = await processar_mensagem(user_id, texto_usuario)
        await update.message.reply_text(resposta)

    except Exception as exc:
        print(f"[HANDLER] Erro ao processar mensagem do usuário {user_id}: {exc}")
        await update.message.reply_text(
            "Desculpe, ocorreu um problema ao processar a sua mensagem. "
            "Por favor, tente novamente em instantes."
        )
