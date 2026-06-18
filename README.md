# ChatBot de Agendamento - Clínica Multidisciplinar

Este é um assistente virtual (ChatBot) desenvolvido em Python para o Telegram. O objetivo do bot é automatizar o agendamento de consultas de uma clínica médica multidisciplinar. O bot utiliza Inteligência Artificial por meio da nova SDK do **Google Gemini (`google-genai`)** para conduzir o diálogo de forma profissional e objetiva, coletando os dados necessários do paciente e, em seguida, utiliza **Function Calling** para marcar as consultas diretamente no **Google Calendar**.

## Funcionalidades

- **Atendimento Automatizado e Inteligente:** O bot conduz o paciente, perguntando de forma direta:
  1. A especialidade desejada (Psicologia, Terapia Ocupacional, Fisioterapia, Nutrição ou Fonoaudiologia).
  2. O nome completo do paciente.
  3. A data e horário desejados.
- **Integração com Google Calendar:** Ao obter os 3 dados, o bot verifica se o horário está disponível e agenda automaticamente a consulta no calendário.
- **Prevenção de Conflitos de Agenda:** Se o paciente tentar marcar em um horário já ocupado, o bot negará educadamente e pedirá para que o paciente escolha outro horário.

## Tecnologias Utilizadas

- **Python 3**
- **python-telegram-bot:** Para interagir com a API do Telegram.
- **google-genai:** Nova SDK do Gemini para processamento de linguagem natural e Function Calling.
- **google-api-python-client** e **google-auth:** Para interagir com a API do Google Calendar.
- **python-dotenv:** Para gerenciamento de variáveis de ambiente de forma segura.

## Como instalar e executar o projeto

### 1. Preparar os arquivos
Certifique-se de que todos os arquivos do projeto (como `bot.py` e `agenda.py`) estão na mesma pasta.

### 2. Criar e ativar um ambiente virtual (Recomendado)
Para evitar conflito de versões de pacotes no seu computador, crie um ambiente virtual:
```bash
python -m venv venv

# Para ativar no Windows:
venv\Scripts\activate

# Para ativar no Mac/Linux:
source venv/bin/activate
```

### 3. Instalar as dependências do Python (pip)
Com o ambiente virtual ativado, instale todos os pacotes necessários de uma vez copiando e colando o comando abaixo:
```bash
pip install python-dotenv google-genai python-telegram-bot google-auth google-api-python-client
```

### 4. Configurar as Credenciais e o arquivo `.env`
O projeto precisa de algumas chaves para funcionar. Crie um arquivo chamado `.env` na raiz do projeto e preencha com as suas chaves reais:

```env
TELEGRAM_TOKEN=seu_token_do_botfather_do_telegram
GEMINI_API_KEY=sua_chave_do_google_ai_studio
CLINICA_CALENDAR_ID=id_do_calendario@group.calendar.google.com
```

Você também precisará autorizar o código a ler e gravar na agenda do Google:
1. Acesse o Google Cloud Console, crie um projeto e ative a **Google Calendar API**.
2. Crie uma **Conta de Serviço (Service Account)** e gere uma chave em formato JSON.
3. Baixe e salve esse arquivo na raiz do projeto com o nome de `credentials.json`.
4. Vá no seu Google Calendar original, acesse as Configurações da sua clínica e compartilhe a agenda com o *e-mail da conta de serviço* que você criou, dando permissões de fazer alterações em eventos.

### 5. Executar o Bot
Para ligar o assistente, digite no terminal (com o ambiente virtual ainda ativado):
```bash
python bot.py
```
Se tudo estiver correto, você verá no terminal: `Bot rodando! Pressione Ctrl+C para parar.`. Pronto! Basta buscar o seu bot no Telegram e mandar um "Olá" para agendar uma consulta.

## Estrutura de Arquivos
- `bot.py`: Código principal responsável por conectar ao Telegram e engajar na IA (Gemini).
- `agenda.py`: Código focado apenas em conversar e validar com o Google Calendar.
- `credentials.json`: Arquivo de autorização da conta de serviço do Google (você deve gerar e adicionar).
- `.env`: Variáveis sensíveis do seu projeto (você deve criar e adicionar).
