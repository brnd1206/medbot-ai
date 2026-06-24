"""
calendar_service.py - Módulo de integração com a API do Google Calendar.

Responsabilidades:
  - Autenticar via conta de serviço (credentials.json).
  - Verificar disponibilidade de horário.
  - Criar eventos na agenda da clínica.
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

CALENDAR_ID   = os.getenv("CLINICA_CALENDAR_ID")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _obter_servico():
    """Autentica usando o arquivo credentials.json e retorna o serviço Calendar."""
    credenciais = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build("calendar", "v3", credentials=credenciais)


def criar_evento(nome_paciente: str, especialidade: str, data_hora_iso: str) -> dict:
    """
    Cria um evento na agenda da clínica após verificar a disponibilidade.

    Args:
        nome_paciente: Nome completo do paciente.
        especialidade: Especialidade da consulta.
        data_hora_iso: Data/hora no formato ISO 8601 (ex: 2026-07-15T14:00:00).

    Returns:
        Dict com chaves:
          - "status": "sucesso" | "conflito" | "erro"
          - "link"  : URL do evento criado (apenas quando status == "sucesso")
          - "mensagem": descrição do resultado
    """
    if not CALENDAR_ID:
        return {
            "status": "erro",
            "mensagem": "CLINICA_CALENDAR_ID não configurado no arquivo .env.",
        }

    try:
        service = _obter_servico()

        start_dt = datetime.fromisoformat(data_hora_iso.replace("Z", "+00:00"))

        # Se não tiver fuso, assume Brasília (UTC-3)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone(timedelta(hours=-3)))

        end_dt = start_dt + timedelta(hours=1)
        time_min = start_dt.isoformat()
        time_max = end_dt.isoformat()

        # Verifica conflitos de horário
        result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
        ).execute()

        if result.get("items"):
            print(f"[CALENDAR] Conflito de horário entre {time_min} e {time_max}.")
            return {
                "status": "conflito",
                "mensagem": f"Horário entre {time_min} e {time_max} já está ocupado.",
            }

        evento = {
            "summary": f"Consulta ({especialidade}): {nome_paciente}",
            "description": f"Especialidade: {especialidade}",
            "start": {"dateTime": time_min, "timeZone": "America/Sao_Paulo"},
            "end":   {"dateTime": time_max, "timeZone": "America/Sao_Paulo"},
        }

        evento_criado = service.events().insert(
            calendarId=CALENDAR_ID, body=evento
        ).execute()

        link = evento_criado.get("htmlLink", "")
        event_id = evento_criado.get("id", "")
        print(f"[CALENDAR] Evento criado: {link}")
        return {"status": "sucesso", "link": link, "event_id": event_id, "mensagem": "Evento criado no Google Calendar."}

    except FileNotFoundError:
        msg = "Arquivo service_account.json não encontrado na raiz do projeto."
        print(f"[CALENDAR] ERRO: {msg}")
        return {"status": "erro", "mensagem": msg}
    except Exception as exc:
        msg = f"Erro ao interagir com o Google Calendar: {exc}"
        print(f"[CALENDAR] ERRO: {msg}")
        return {"status": "erro", "mensagem": msg}


def cancelar_evento(event_id: str) -> dict:
    """
    Remove um evento do Google Calendar pelo seu ID.

    Args:
        event_id: ID do evento a ser cancelado.

    Returns:
        Dict com "status": "sucesso" | "erro" e "mensagem".
    """
    if not CALENDAR_ID or not event_id:
        return {"status": "erro", "mensagem": "CALENDAR_ID ou event_id não fornecido."}

    try:
        service = _obter_servico()
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        print(f"[CALENDAR] Evento {event_id} cancelado com sucesso.")
        return {"status": "sucesso", "mensagem": "Evento cancelado no Google Calendar."}
    except Exception as exc:
        msg = f"Erro ao cancelar evento no Google Calendar: {exc}"
        print(f"[CALENDAR] ERRO: {msg}")
        return {"status": "erro", "mensagem": msg}

