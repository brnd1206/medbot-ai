import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()
CALENDAR_ID = os.getenv("CLINICA_CALENDAR_ID")
# Define o escopo necessário para ler e escrever na agenda
SCOPES = ['https://www.googleapis.com/auth/calendar']

def obter_servico_agenda():
    """Autentica o bot usando o arquivo credentials.json"""
    # Procura pelo arquivo credentials.json na raiz do projeto
    credenciais = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    return build('calendar', 'v3', credentials=credenciais)

def agendar_consulta(nome_paciente, data_hora_iso, especialidade, resumo_caso="Consulta Médica"):
    """
    Cria um evento na agenda da clínica. Verifica se o horário está disponível.
    data_hora_iso deve estar no formato: 'YYYY-MM-DDTHH:MM:SS'
    """
    try:
        service = obter_servico_agenda()
        
        start_time = data_hora_iso
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        # Se for naive (sem timezone), assumimos fuso -03:00 (Brasília)
        if start_datetime.tzinfo is None:
            tz_br = timezone(timedelta(hours=-3))
            start_datetime = start_datetime.replace(tzinfo=tz_br)
            
        end_datetime = start_datetime + timedelta(hours=1)
        
        time_min = start_datetime.isoformat()
        time_max = end_datetime.isoformat()

        # Verifica se já existe algum evento neste horário
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True
        ).execute()

        eventos_existentes = events_result.get('items', [])
        if eventos_existentes:
            print(f"Conflito de horário: já existe evento entre {time_min} e {time_max}.")
            return "conflito"

        evento = {
            'summary': f'Consulta ({especialidade}): {nome_paciente}',
            'description': f'Especialidade: {especialidade}\n{resumo_caso}',
            'start': {
                'dateTime': time_min,
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': time_max,
                'timeZone': 'America/Sao_Paulo',
            },
        }

        # Executa a inserção na agenda configurada
        evento_criado = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
        print(f"Evento criado com sucesso: {evento_criado.get('htmlLink')}")
        return "sucesso"
        
    except Exception as e:
        print(f"Erro ao interagir com o Google Calendar: {e}")
        return "erro"