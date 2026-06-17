import os
from datetime import datetime, timedelta
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

def agendar_consulta(nome_paciente, data_hora_iso, resumo_caso="Consulta Médica"):
    """
    Cria um evento na agenda da clínica.
    data_hora_iso deve estar no formato: 'YYYY-MM-DDTHH:MM:SS'
    """
    try:
        service = obter_servico_agenda()
        
        # Define o início e assume que cada consulta dura 1 hora
        start_time = data_hora_iso
        start_datetime = datetime.fromisoformat(start_time)
        end_datetime = start_datetime + timedelta(hours=1)
        end_time = end_datetime.isoformat()

        evento = {
            'summary': f'Consulta: {nome_paciente}',
            'description': resumo_caso,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Sao_Paulo', # Ajuste para o fuso horário da clínica
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Sao_Paulo',
            },
        }

        # Executa a inserção na agenda configurada
        evento_criado = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
        print(f"Evento criado com sucesso: {evento_criado.get('htmlLink')}")
        return True
        
    except Exception as e:
        print(f"Erro ao interagir com o Google Calendar: {e}")
        return False