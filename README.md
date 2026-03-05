# Glucose Actions — Glucose Monitor & Alert System

Sistema de monitoramento de glicose via [LibreLinkUp](https://librelinkup.com/) com alertas automatizados. Lê dados do sensor de glicose (FreeStyle Libre) remotamente e dispara alertas quando os níveis saem do range seguro.

## Funcionalidades

- **Leitura automática** de glicose via pylibrelinkup (API do LibreLinkUp)
- **Alertas configuráveis** com thresholds de hipo/hiper (padrão: < 70 e > 180 mg/dL)
- **Cooldown inteligente** entre alertas repetidos (padrão: 20 min), com reset ao normalizar
- **Detecção de leitura obsoleta** (ignora readings mais velhos que 15 min)
- **Outputs plugáveis:**
  - Webhook (Alexa via VoiceMonkey)
  - WhatsApp (Meta Cloud API)
- **Persistência de estado** entre execuções (JSON com escrita atômica)
- **File lock** para prevenir execuções sobrepostas do cron
- **Trend data** — seta de tendência incluída nos alertas (↓ ↘ → ↗ ↑)

## Arquitetura

```
cron (cada 5 min)
  └── src/main.py (orquestrador)
        ├── src/glucose_reader.py    → pylibrelinkup → LibreLinkUp API
        ├── src/alert_engine.py      → avaliação de thresholds + cooldown
        ├── src/state.py             → persistência JSON
        └── src/outputs/
              ├── base.py            → BaseOutput (ABC)
              ├── webhook.py         → Alexa/VoiceMonkey
              └── whatsapp.py        → WhatsApp Cloud API
```

## Requisitos

- Python 3.12+
- Conta LibreLinkUp com pelo menos um paciente compartilhado
- (Opcional) Conta Meta Business para WhatsApp alerts
- (Opcional) VoiceMonkey para Alexa alerts

## Instalação

```bash
# Clonar o repositório
git clone git@github.com:SEU_USUARIO/glucose-actions.git
cd glucose-actions

# Criar e ativar virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar config com suas credenciais
cp config.example.yaml config.yaml
chmod 600 config.yaml
# Editar config.yaml com seus dados
```

## Configuração

### Credenciais LibreLinkUp

No `config.yaml`:

```yaml
librelinkup:
  email: "seu-email@example.com"
  password: "sua-senha"
```

Ou via variáveis de ambiente (recomendado):

```bash
export LIBRELINKUP_EMAIL="seu-email@example.com"
export LIBRELINKUP_PASSWORD="sua-senha"
```

### Thresholds de Alerta

```yaml
alerts:
  low_threshold: 70         # mg/dL — abaixo disso: alerta hipo
  high_threshold: 180        # mg/dL — acima disso: alerta hiper
  cooldown_minutes: 20       # minutos entre alertas repetidos do mesmo nível
  max_reading_age_minutes: 15  # ignora leituras mais velhas que isso
```

### Output: Webhook (Alexa/VoiceMonkey)

```yaml
outputs:
  - type: webhook
    enabled: true
    url: "https://api-v2.voicemonkey.io/announcement"
    token: "seu-token-voicemonkey"
    device: "seu-device"
```

### Output: WhatsApp (Meta Cloud API)

```yaml
outputs:
  - type: whatsapp
    enabled: true
    phone_number_id: "SEU_PHONE_NUMBER_ID"
    access_token: ""  # ou use env var WHATSAPP_ACCESS_TOKEN
    recipient: "5511999999999"
    template_name: "glucose_alert"
    language_code: "pt_BR"
```

## Configuração do WhatsApp Cloud API (passo a passo)

### 1. Criar conta no Meta Business Manager

1. Acesse [business.facebook.com](https://business.facebook.com/) e crie uma conta business (ou use existente)
2. Acesse [developers.facebook.com](https://developers.facebook.com/) e faça login com a mesma conta

### 2. Criar App no Meta for Developers

1. Em [developers.facebook.com/apps](https://developers.facebook.com/apps), clique **Criar App**
2. Selecione **Outro** como tipo de app
3. Selecione **Business** como tipo
4. Dê um nome (ex: "Glucose Monitor") e vincule à sua conta business
5. No painel do app, clique **Adicionar produto** e selecione **WhatsApp**

### 3. Configurar número de telefone

1. No menu lateral, vá em **WhatsApp > Configuração da API**
2. Você verá um número de teste fornecido pela Meta para desenvolvimento
3. Para usar seu próprio número:
   - Clique em **Adicionar número de telefone**
   - Use um número que **não esteja** cadastrado no WhatsApp pessoal (ou remova primeiro)
   - Verifique o número via SMS ou chamada de voz
4. Anote o **Phone Number ID** que aparece — é o `phone_number_id` do config

### 4. Gerar Access Token

**Token temporário (para testes):**
1. Na página **Configuração da API**, copie o token temporário gerado
2. Este token expira em 24h

**Token permanente (para produção):**
1. Vá em **Configurações do App > Básico** e anote o App ID
2. No Meta Business Manager, vá em **Configurações > Usuários do sistema**
3. Crie um novo usuário do sistema como **Admin**
4. Clique em **Gerar token** para esse usuário
5. Selecione o app criado e as permissões: `whatsapp_business_messaging`, `whatsapp_business_management`
6. O token gerado **não expira** — guarde com segurança
7. Configure como variável de ambiente:
   ```bash
   export WHATSAPP_ACCESS_TOKEN="seu-token-permanente"
   ```

### 5. Criar Message Template

Os alertas são enviados como template messages (exigência da Meta para mensagens proativas).

1. No Meta Business Manager, vá em **WhatsApp > Gerenciador de Contas > Message Templates**
2. Clique **Criar template**
3. Configure:
   - **Categoria:** Utility
   - **Nome:** `glucose_alert`
   - **Idioma:** Português (BR)
   - **Corpo da mensagem:** `{{1}}`
     - Isso permite que o sistema envie a mensagem completa como parâmetro
     - Exemplo de preview: "Atencao: glicose em 65 mg/dL ↘, nivel baixo"
4. Envie para aprovação — normalmente leva de minutos a 48h
5. Aguarde o status mudar para **Aprovado**

### 6. Registrar destinatários (modo desenvolvimento)

Enquanto o app estiver em modo desenvolvimento:
1. Na página **Configuração da API**, seção **Para**, adicione os números que vão receber mensagens
2. Cada número precisa confirmar recebendo um código de verificação
3. Para enviar para qualquer número, o app precisa estar em **modo produção** (requer verificação do business)

### 7. Ativar cobrança

1. No Meta Business Manager, vá em **Configurações > Pagamento do WhatsApp**
2. Adicione um método de pagamento
3. Custo: por mensagem template entregue (varia por país, ~R$0,05-0,15 por mensagem no Brasil)
4. Para alertas de glicose a cada 5 min com cooldown de 20 min, o custo mensal será muito baixo

### 8. Testar conexão

Rode o script de validação para enviar uma mensagem de teste para o seu próprio número:

```bash
source .venv/bin/activate
python validate_whatsapp.py
```

O script vai:
1. Carregar a configuração do `config.yaml`
2. Validar que todos os campos estão preenchidos
3. Enviar uma mensagem de teste via template para o `recipient` configurado
4. Mostrar `SUCCESS` se a mensagem foi enviada, ou `FAILURE` com dicas de debug

> **Dica:** Coloque seu próprio número como `recipient` para receber a mensagem de teste.

### 9. Validar sistema completo

Após o teste do WhatsApp, valide o fluxo completo:

```bash
python -m src.main
```

## Execução

### Manual

```bash
source .venv/bin/activate
python -m src.main
```

### Via Cron (recomendado)

```bash
# Editar crontab
crontab -e

# Adicionar (executa a cada 5 minutos)
*/5 * * * * cd /caminho/para/glucose-actions && .venv/bin/python -m src.main >> /var/log/librelinkup.log 2>&1
```

## Validação Inicial

Antes de configurar o cron, valide a conexão com o LibreLinkUp:

```bash
source .venv/bin/activate
python validate_lib.py
```

Deve mostrar o nome do paciente, valor de glicose atual, tendência e `SUCCESS`.

## Testes

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Estrutura do Projeto

```
glucose-actions/
├── config.example.yaml       # Template de configuração
├── config.yaml               # Sua configuração (não commitado)
├── requirements.txt           # Dependências Python
├── validate_lib.py            # Validação da conexão LibreLinkUp (Phase 0)
├── validate_whatsapp.py       # Validação da conexão WhatsApp Cloud API
├── src/
│   ├── __init__.py
│   ├── main.py                # Entry point — orquestra read → evaluate → alert
│   ├── glucose_reader.py      # Leitura de glicose via pylibrelinkup
│   ├── alert_engine.py        # Avaliação de thresholds + cooldown + mensagens
│   ├── state.py               # Persistência de estado (JSON atômico)
│   └── outputs/
│       ├── __init__.py
│       ├── base.py            # BaseOutput (ABC)
│       ├── webhook.py         # Output via webhook HTTP POST
│       └── whatsapp.py        # Output via WhatsApp Cloud API
├── tests/
│   ├── __init__.py
│   ├── test_alert_engine.py   # Testes do motor de alertas
│   ├── test_state.py          # Testes da persistência de estado
│   └── test_whatsapp_output.py # Testes do output WhatsApp
├── state.json                 # Estado entre execuções (não commitado)
└── .gitignore
```

## Adicionando Novos Outputs

Crie uma nova classe estendendo `BaseOutput`:

```python
from src.outputs.base import BaseOutput

class MeuOutput(BaseOutput):
    def send_alert(self, message: str, glucose_value: int, level: str) -> bool:
        # Implementar envio
        # Retornar True se sucesso, False se falha
        ...
```

Adicione o tipo no `build_outputs()` em `src/main.py` e a configuração no `config.yaml`.

## Segurança

- `config.yaml` contém credenciais — **nunca commitar** (protegido pelo `.gitignore`)
- Use variáveis de ambiente para segredos em produção
- `chmod 600 config.yaml` para restringir acesso
- Tokens do WhatsApp nunca são logados (redacted no debug output)

## Licença

Uso pessoal.
