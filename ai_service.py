"""
ai_service.py - Módulo de comunicação com a API do Groq (LLM) e definição do prompt de sistema.

Responsabilidades:
  - Configurar o cliente Groq.
  - Definir o prompt de sistema e as ferramentas (Tool Use / Function Calling).
  - Manter o histórico de conversa por usuário.
  - Processar a resposta da IA, acionando o banco de dados quando necessário.
"""

import os
import json
from datetime import datetime

from groq import Groq

from database import (
    inserir_agendamento,
    deletar_agendamento,
    buscar_agendamentos_por_nome,
    buscar_agendamento_por_id,
)
from calendar_service import criar_evento, cancelar_evento

# ---------------------------------------------------------------------------
# Configuração do cliente
# ---------------------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=GROQ_API_KEY)

# Histórico de conversa por user_id do Telegram  {user_id: [messages]}
memoria_usuarios: dict[int, list[dict]] = {}

# ---------------------------------------------------------------------------
# Definição das ferramentas (Tool Use no formato Groq / OpenAI-compatible)
# ---------------------------------------------------------------------------

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "agendar_consulta",
            "description": (
                "Cria um novo agendamento de consulta para o paciente no banco de dados da clínica. "
                "Só deve ser chamada quando o nome do paciente, a especialidade e a data/hora "
                "tiverem sido confirmados pelo usuário."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_paciente": {
                        "type": "string",
                        "description": "Nome completo do paciente.",
                    },
                    "especialidade": {
                        "type": "string",
                        "description": (
                            "Especialidade desejada. Valores aceitos: "
                            "Psicologia, Terapia Ocupacional, Fisioterapia, Nutrição, Fonoaudiologia."
                        ),
                    },
                    "data_hora_iso": {
                        "type": "string",
                        "description": (
                            "Data e hora da consulta no formato ISO 8601 "
                            "(ex: 2026-07-15T14:00:00). Converta expressões como "
                            "'amanhã', 'próxima terça' usando a data de hoje como base."
                        ),
                    },
                },
                "required": ["nome_paciente", "especialidade", "data_hora_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_agendamento",
            "description": (
                "Busca agendamentos existentes pelo nome do paciente. "
                "Use quando o usuário quiser verificar horário agendado ou antes de remarcar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_paciente": {
                        "type": "string",
                        "description": "Nome completo ou parcial do paciente.",
                    },
                },
                "required": ["nome_paciente"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remarcar_agendamento",
            "description": (
                "Cancela um agendamento existente e cria um novo com nova data/hora. "
                "Deve ser chamada somente após confirmar o agendamento atual com o usuário "
                "e obter a nova data/hora desejada."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agendamento_id": {
                        "type": "integer",
                        "description": "ID interno do agendamento a ser remarcado (obtido via consultar_agendamento).",
                    },
                    "nova_data_hora_iso": {
                        "type": "string",
                        "description": "Nova data e hora no formato ISO 8601.",
                    },
                },
                "required": ["agendamento_id", "nova_data_hora_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancelar_agendamento",
            "description": (
                "Cancela e remove definitivamente um agendamento existente. "
                "Deve ser chamada somente após confirmar com o usuário qual agendamento será cancelado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agendamento_id": {
                        "type": "integer",
                        "description": "ID interno do agendamento a ser cancelado (obtido via consultar_agendamento).",
                    },
                },
                "required": ["agendamento_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Prompt de sistema
# ---------------------------------------------------------------------------

def _prompt_sistema() -> str:
    hoje = datetime.now().strftime("%Y-%m-%d")
    return (
        "Você é o assistente virtual de uma clínica médica multidisciplinar. "
        "Comunique-se de forma direta, objetiva e profissional. Evite textos longos. "
        "Você pode realizar as seguintes ações:\n"
        "  • Agendar uma nova consulta\n"
        "  • Consultar um agendamento existente (verificar horário)\n"
        "  • Remarcar um agendamento existente\n"
        "  • Cancelar (desmarcar) um agendamento existente\n\n"
        "Para AGENDAR, colete os 3 dados:\n"
        "  1. Especialidade (Psicologia, Terapia Ocupacional, Fisioterapia, Nutrição ou Fonoaudiologia)\n"
        "  2. Nome completo do paciente\n"
        "  3. Data e horário desejados\n\n"
        "Para CONSULTAR, REMARCAR ou CANCELAR, peça o nome do paciente e use 'consultar_agendamento' "
        "para localizar o registro. Ao remarcar, confirme o agendamento encontrado e pergunte a nova "
        "data/hora antes de chamar 'remarcar_agendamento'. Ao cancelar, confirme com o usuário qual "
        "agendamento será removido antes de chamar 'cancelar_agendamento'.\n\n"
        "IMPORTANTE sobre datas: converta internamente qualquer expressão de data "
        "(ex.: 'amanhã', 'na sexta', 'semana que vem') para o formato correto. "
        "NUNCA mencione formatos técnicos como ISO 8601 para o usuário. "
        "NUNCA adicione lembretes ou dicas sobre como o usuário deve escrever a data. "
        "Aceite a data/hora da forma que o usuário informar e converta silenciosamente.\n"
        "NUNCA exponha detalhes técnicos internos como IDs de banco de dados, links de sistema "
        "ou mensagens de retorno de ferramentas. Comunique apenas o resultado final de forma natural.\n"
        f"Referência: hoje é {hoje}."
    )


# ---------------------------------------------------------------------------
# Funções auxiliares de histórico
# ---------------------------------------------------------------------------

def _obter_historico(user_id: int) -> list[dict]:
    """Retorna o histórico de mensagens do usuário, inicializando se necessário."""
    if user_id not in memoria_usuarios:
        memoria_usuarios[user_id] = [
            {"role": "system", "content": _prompt_sistema()}
        ]
    return memoria_usuarios[user_id]


def resetar_historico(user_id: int) -> None:
    """Reinicializa o histórico de conversa do usuário (usado no /start).

    Recria a entrada com apenas o prompt de sistema, garantindo que
    o usuário seja reconhecido como 'sessão iniciada' para mensagens seguintes.
    """
    memoria_usuarios[user_id] = [
        {"role": "system", "content": _prompt_sistema()}
    ]


# ---------------------------------------------------------------------------
# Execução local das ferramentas
# ---------------------------------------------------------------------------

def _executar_ferramenta(nome: str, argumentos: dict) -> str:
    """
    Executa a ferramenta solicitada pela IA e retorna o resultado como string JSON.
    """

    # ------------------------------------------------------------------
    # AGENDAR CONSULTA
    # ------------------------------------------------------------------
    if nome == "agendar_consulta":
        nome_paciente = argumentos.get("nome_paciente", "")
        especialidade = argumentos.get("especialidade", "")
        data_hora_iso = argumentos.get("data_hora_iso", "")

        # 1. Tenta criar o evento no Google Calendar (verifica conflitos)
        resultado_calendar = criar_evento(nome_paciente, especialidade, data_hora_iso)

        if resultado_calendar["status"] == "conflito":
            return json.dumps({
                "status": "conflito",
                "mensagem": (
                    "Horário indisponível no calendário da clínica. "
                    "Informe ao paciente e peça para escolher outro horário ou data."
                ),
            }, ensure_ascii=False)

        # 2. Grava no banco de dados SQLite
        google_event_id = resultado_calendar.get("event_id") if resultado_calendar["status"] == "sucesso" else None
        try:
            inserir_agendamento(nome_paciente, especialidade, data_hora_iso, google_event_id)
        except Exception as exc:
            return json.dumps({
                "status": "erro",
                "mensagem": f"Falha ao gravar no banco de dados: {exc}",
            }, ensure_ascii=False)

        return json.dumps({"status": "sucesso"}, ensure_ascii=False)

    # ------------------------------------------------------------------
    # CONSULTAR AGENDAMENTO
    # ------------------------------------------------------------------
    if nome == "consultar_agendamento":
        nome_paciente = argumentos.get("nome_paciente", "")
        registros = buscar_agendamentos_por_nome(nome_paciente)

        if not registros:
            return json.dumps({
                "status": "nao_encontrado",
                "mensagem": f"Nenhum agendamento encontrado para '{nome_paciente}'.",
            }, ensure_ascii=False)

        # Retorna os dados para a IA formatar — ID incluído para uso interno na remarcação
        return json.dumps({
            "status": "sucesso",
            "agendamentos": [
                {
                    "id": r["id"],
                    "nome_paciente": r["nome_paciente"],
                    "especialidade": r["especialidade"],
                    "data_hora": r["data_hora"],
                }
                for r in registros
            ],
        }, ensure_ascii=False)

    # ------------------------------------------------------------------
    # REMARCAR AGENDAMENTO
    # ------------------------------------------------------------------
    if nome == "remarcar_agendamento":
        agendamento_id   = argumentos.get("agendamento_id")
        nova_data_hora   = argumentos.get("nova_data_hora_iso", "")

        # 1. Recupera o registro original
        registro = buscar_agendamento_por_id(agendamento_id)
        if not registro:
            return json.dumps({
                "status": "erro",
                "mensagem": f"Agendamento ID {agendamento_id} não encontrado.",
            }, ensure_ascii=False)

        nome_paciente    = registro["nome_paciente"]
        especialidade    = registro["especialidade"]
        google_event_id  = registro.get("google_event_id")

        # 2. Cancela o evento antigo no Google Calendar
        if google_event_id:
            cancelar_evento(google_event_id)

        # 3. Remove o registro antigo do banco
        deletar_agendamento(agendamento_id)

        # 4. Cria novo evento no Google Calendar
        resultado_calendar = criar_evento(nome_paciente, especialidade, nova_data_hora)

        if resultado_calendar["status"] == "conflito":
            # Reagenda falhou por conflito — devolve status para a IA informar o usuário
            return json.dumps({
                "status": "conflito",
                "mensagem": (
                    "O novo horário escolhido já está ocupado na agenda da clínica. "
                    "Peça para o paciente escolher outro horário."
                ),
            }, ensure_ascii=False)

        # 5. Insere novo registro no banco
        novo_event_id = resultado_calendar.get("event_id") if resultado_calendar["status"] == "sucesso" else None
        try:
            inserir_agendamento(nome_paciente, especialidade, nova_data_hora, novo_event_id)
        except Exception as exc:
            return json.dumps({
                "status": "erro",
                "mensagem": f"Falha ao gravar nova data no banco: {exc}",
            }, ensure_ascii=False)

        return json.dumps({"status": "sucesso"}, ensure_ascii=False)

    # ------------------------------------------------------------------
    # CANCELAR AGENDAMENTO
    # ------------------------------------------------------------------
    if nome == "cancelar_agendamento":
        agendamento_id = argumentos.get("agendamento_id")

        # 1. Recupera o registro para obter o google_event_id
        registro = buscar_agendamento_por_id(agendamento_id)
        if not registro:
            return json.dumps({
                "status": "erro",
                "mensagem": f"Agendamento ID {agendamento_id} não encontrado.",
            }, ensure_ascii=False)

        google_event_id = registro.get("google_event_id")

        # 2. Cancela o evento no Google Calendar (se houver)
        if google_event_id:
            cancelar_evento(google_event_id)

        # 3. Remove o registro do banco de dados
        deletar_agendamento(agendamento_id)

        return json.dumps({"status": "sucesso"}, ensure_ascii=False)

    return json.dumps({"status": "erro", "mensagem": f"Ferramenta '{nome}' não reconhecida."})


# ---------------------------------------------------------------------------
# Função principal de processamento
# ---------------------------------------------------------------------------

async def processar_mensagem(user_id: int, texto_usuario: str) -> str:
    """
    Envia a mensagem do usuário para o Groq, gerencia o loop de Tool Use
    e retorna o texto final que deve ser enviado ao paciente no Telegram.

    Args:
        user_id:       ID do usuário no Telegram.
        texto_usuario: Mensagem digitada pelo usuário.

    Returns:
        Texto de resposta a ser enviado pelo bot.
    """
    historico = _obter_historico(user_id)
    historico.append({"role": "user", "content": texto_usuario})

    # Loop de agentic: continua enquanto a IA devolver tool_calls
    while True:
        resposta = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=historico,
            tools=FERRAMENTAS,
            tool_choice="auto",
        )

        mensagem_ia = resposta.choices[0].message

        # Adiciona a mensagem da IA ao histórico (pode conter tool_calls)
        historico.append(mensagem_ia.model_dump(exclude_unset=True))

        # Se não há chamadas de ferramenta, retorna o texto normalmente
        if not mensagem_ia.tool_calls:
            return mensagem_ia.content or "Desculpe, não consegui gerar uma resposta."

        # Processa cada tool_call retornado pela IA
        for tool_call in mensagem_ia.tool_calls:
            nome_ferramenta = tool_call.function.name
            try:
                argumentos = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                argumentos = {}

            resultado = _executar_ferramenta(nome_ferramenta, argumentos)

            # Insere o resultado da ferramenta no histórico
            historico.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": nome_ferramenta,
                "content": resultado,
            })

        # Após processar todos os tool_calls, o loop volta ao topo
        # para que a IA gere a resposta final em texto natural.
