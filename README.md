# MedBot AI

Assistente virtual para o **Telegram** que automatiza o gerenciamento de consultas de uma clínica médica multidisciplinar. O bot utiliza **Inteligência Artificial via API do Groq** com **Tool Use (Function Calling)** para conduzir diálogos profissionais e realizar ações reais: agendar, consultar, remarcar e cancelar consultas, integrando **SQLite** e **Google Calendar** simultaneamente.

---

## Funcionalidades

- **Agendar consulta** — o bot coleta especialidade, nome do paciente e data/hora, confirma com o usuário e registra a consulta
- **Consultar agendamento** — o paciente pode verificar qual consulta possui agendada
- **Remarcar consulta** — cancela o horário antigo e agenda um novo, tanto no banco quanto no Google Calendar
- **Cancelar (desmarcar) consulta** — remove o registro do banco e o evento do Google Calendar
- **Prevenção de conflitos** — verifica disponibilidade no Google Calendar antes de confirmar qualquer agendamento
- **Histórico de conversa por usuário** — cada usuário tem seu próprio contexto de chat
- **Conversa iniciada via `/start`** — o bot só responde após o usuário iniciar a sessão

---

## Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | Interface com a API do Telegram |
| [groq](https://pypi.org/project/groq/) | Cliente oficial da API do Groq (LLM + Tool Use) |
| sqlite3 | Banco de dados local (já incluso no Python) |
| [google-api-python-client](https://pypi.org/project/google-api-python-client/) | Integração com o Google Calendar |
| [google-auth](https://pypi.org/project/google-auth/) | Autenticação via Conta de Serviço |
| python-dotenv | Gerenciamento seguro de variáveis de ambiente |

---

## Estrutura de Arquivos

```
medbot-ai/
├── main.py              # Ponto de entrada — inicializa o banco e o bot
├── bot_handlers.py      # Rotas e handlers do Telegram
├── ai_service.py        # Comunicação com a API do Groq + Tool Use (4 ferramentas)
├── database.py          # Funções SQLite (inicializar, inserir, buscar, deletar)
├── calendar_service.py  # Integração com o Google Calendar (criar, cancelar eventos)
├── requirements.txt     # Dependências do projeto
├── .env.example         # Modelo do arquivo de configuração
├── service_account.json # Credenciais da Conta de Serviço Google (você deve gerar)
└── agendamentos.db      # Gerado automaticamente na primeira execução
```

---

## Arquitetura — Tool Use (Function Calling)

O Groq decide qual ferramenta acionar com base na intenção do usuário:

| Ferramenta | Quando é acionada |
|---|---|
| `agendar_consulta` | Usuário quer marcar uma nova consulta |
| `consultar_agendamento` | Usuário quer ver o horário agendado |
| `remarcar_agendamento` | Usuário quer mudar data/hora |
| `cancelar_agendamento` | Usuário quer desmarcar a consulta |

---

## Como instalar e executar

### 1. Clone o repositório e entre na pasta

```bash
git clone https://github.com/brnd1206/medbot-ai
cd medbot-ai
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Edite o arquivo `.env`:

```env
TELEGRAM_TOKEN=seu_token_do_botfather_aqui
GROQ_API_KEY=sua_chave_groq_aqui
GROQ_MODEL=llama-3.3-70b-versatile
CLINICA_CALENDAR_ID=id_do_calendario@group.calendar.google.com
```

> **Como obter a GROQ_API_KEY:**
> 1. Acesse [console.groq.com](https://console.groq.com)
> 2. Crie uma conta gratuita
> 3. Vá em **API Keys → Create API Key** e copie a chave gerada

> **Como obter o TELEGRAM_TOKEN:**
> 1. Abra o Telegram e procure por `@BotFather`
> 2. Envie `/newbot` e siga as instruções
> 3. Copie o token gerado

### 5. Configure a integração com o Google Calendar

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto e ative a **Google Calendar API**
3. Vá em **IAM & Admin → Contas de serviço → Criar conta de serviço**
4. Gere uma chave em formato **JSON** e salve na raiz do projeto como `service_account.json`
5. No Google Calendar, acesse as **Configurações** da agenda da clínica
6. Em **Compartilhar com pessoas específicas**, adicione o e-mail da conta de serviço com permissão para **fazer alterações em eventos**
7. Copie o **ID do calendário** (em "Integrar agenda") e cole no `.env`

> O `CLINICA_CALENDAR_ID` é opcional. Se não configurado, o bot continua funcionando e salva apenas no SQLite local.

### 6. Execute o bot

```bash
python main.py
```

Se tudo estiver correto, você verá no terminal:

```
[DB] Banco de dados inicializado com sucesso.
MedBot AI rodando! Pressione Ctrl+C para parar.
```

Pronto! Abra o Telegram, envie `/start` e converse com o assistente.
