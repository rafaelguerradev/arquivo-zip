# Code Review Assistant com IA

Sistema de revisão automática de Pull Requests do GitHub utilizando um modelo de linguagem local. O projeto recebe eventos via webhook, obtém o diff da Pull Request, estrutura as alterações, analisa o código com Ollama/Qwen, armazena o resultado no Supabase/PostgreSQL e publica automaticamente uma revisão como comentário na Pull Request.

O projeto também possui uma API REST para histórico e métricas e um dashboard em React para acompanhamento dos resultados.

> **Importante:** o projeto depende de serviços externos (GitHub, Ollama, Supabase, ngrok). O `.env`, tokens, chaves e o modelo do Ollama não são incluídos no repositório/ZIP — veja a seção [5. Instalação](#5-instalação) em diante.

---

## O que pode ser avaliado sem serviços externos

Dois grupos de testes funcionam com apenas Python e as dependências do `requirements.txt`, sem precisar de GitHub, Ollama, Supabase ou ngrok:

**Diff Parser** — processa e estrutura diffs de Pull Requests:

```bash
python3 -m app.test_diff_parser
```

**Retry e Idempotência** — lógica de estados, prevenção de duplicatas, retry após falhas. Todos os serviços externos são mockados:

```bash
python3 -m unittest app.test_retry_idempotency -v
```

Os demais testes (`test_llm`, `test_github`, `test_github_comment`) exigem serviços reais e são para validação do ambiente completo.

---

## 1. Visão geral

Fluxo principal:

```text
GitHub Pull Request
        │
        │ Webhook
        ▼
      ngrok
        ▼
     FastAPI
        │
        ├── valida assinatura HMAC-SHA256
        │
        └── inicia processamento em background
                     │
                     ▼
                GitHub API
                     │
                     ▼
                    Diff
                     │
                     ▼
                Diff Parser
                     │
                     ▼
              Ollama + Qwen
                     │
                     ▼
          Structured Output / Pydantic
                     │
                     ▼
              Supabase / PostgreSQL
                     │
                     ▼
             Comentário na PR
                     │
                     ▼
              React Dashboard
```

---

## 2. Principais funcionalidades

- Recebimento de Pull Requests por webhook do GitHub
- Validação HMAC-SHA256 do webhook
- Processamento em background
- Consulta de Pull Requests pela GitHub API
- Obtenção e parsing determinístico do diff
- Identificação determinística de arquivo e linha das evidências
- Análise de código com Qwen 2.5 Coder 7B
- Execução local do modelo através do Ollama
- Structured output validado com Pydantic
- Persistência de Pull Requests e análises no PostgreSQL/Supabase
- Histórico de análises por Pull Request e `head_sha`
- Idempotência para evitar análises duplicadas
- Retry após falhas parciais
- Detecção de comentários já existentes por marker
- Publicação automática de comentário em Markdown no GitHub
- API REST de histórico e métricas
- Dashboard em React

---

## 3. Tecnologias

### Backend

- Python 3.12+
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- python-dotenv
- supabase-py

### Inteligência Artificial

- Ollama
- Qwen 2.5 Coder 7B

### Banco de dados

- Supabase
- PostgreSQL

### Frontend

- React
- Vite
- Node.js / npm

### Integração

- GitHub Webhooks
- GitHub REST API
- HMAC-SHA256
- ngrok (túnel público para testes locais do webhook)

---

## 4. Dependências externas

O projeto integra serviços reais. Para execução completa são necessários:

| Dependência | Para que serve | Obrigatório para os testes automáticos |
|---|---|---|
| Python 3.12+ | backend | ✅ sim |
| Node.js / npm | frontend | apenas para o dashboard |
| Ollama + Qwen 2.5 Coder 7B | modelo de IA local | apenas para `test_llm` |
| Supabase (conta gratuita) | banco de dados | apenas para o pipeline completo |
| GitHub + Personal Access Token | integração com PRs | apenas para `test_github` |
| ngrok (ou similar) | túnel público para o webhook durante testes locais | apenas para acionar o webhook via GitHub |

Os testes `test_diff_parser` e `test_retry_idempotency` funcionam sem nenhum desses serviços.

---

## 5. Instalação

### 5.1 Obter o projeto

```bash
cd code-review-assistant
```

Se você recebeu o projeto como ZIP, descompacte-o e abra um terminal (PowerShell, no Windows) dentro da pasta que contém:

```text
app
frontend
database.sql
.env.example
requirements.txt
README.md
```

### 5.2 Criar o ambiente Python

```bash
python3 -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instalar as dependências:

```bash
python3 -m pip install -r requirements.txt
```

(no Windows, use `python -m pip install -r requirements.txt`)

> **Windows:** o `requirements.txt` contém uma condição para que o `uvloop` não seja instalado no Windows, pois essa biblioteca não é suportada nessa plataforma. Isso é esperado e não indica erro.

### 5.3 Validar a instalação com os testes sem dependências externas

```bash
python3 -m app.test_diff_parser
python3 -m unittest app.test_retry_idempotency -v
```

(no Windows, use `python` em vez de `python3`)

Os dois testes devem passar antes de prosseguir.

### 5.4 Instalar as dependências do frontend

```bash
cd frontend
npm install
cd ..
```

---

## 6. Configurar o Supabase

### 6.1 Criar o projeto

Acesse [supabase.com](https://supabase.com) e crie um novo projeto PostgreSQL.

### 6.2 Criar as tabelas

Na raiz do projeto existe o arquivo `database.sql`.

No Supabase: **SQL Editor → New query**, cole o conteúdo de `database.sql` e clique em **Run**.

O script cria as tabelas `pull_requests` e `analises` com suas chaves, constraints e foreign keys.

### 6.3 Obter as credenciais

No Supabase, acesse as configurações de API/keys. Você precisa de:

- **Project URL**
- **Secret Key** (`sb_secret_...`)

Para este backend, use a Secret Key — ela possui privilégios elevados e deve permanecer somente no ambiente do servidor/backend, nunca no frontend nem no GitHub.

---

## 7. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

(no Windows: `Copy-Item .env.example .env` e depois `notepad .env`)

Preencha o `.env`:

```env
GITHUB_WEBHOOK_SECRET=   # segredo do webhook (defina um valor próprio, ex: um texto aleatório)
GITHUB_TOKEN=            # Personal Access Token (Pull requests: Read and write)

SUPABASE_URL=            # URL do projeto Supabase
SUPABASE_SECRET_KEY=     # service role / secret key do Supabase

GITHUB_TEST_REPO=        # repositório usado pelos testes da GitHub API (usuario/repositorio)
GITHUB_TEST_PR=          # número de uma Pull Request real nesse repositório, usada nos testes
```

Exemplo de `GITHUB_TEST_REPO`/`GITHUB_TEST_PR`:

```env
GITHUB_TEST_REPO=rafaelguerradev/code-review-assistant-teste
GITHUB_TEST_PR=1
```

> Nunca publique o `.env`, tokens ou chaves.

---

## 8. Configurar o GitHub

### 8.1 Personal Access Token

Caminho: **Settings → Developer Settings → Personal access tokens → Fine-grained tokens → Generate new token**

Selecione o repositório que será usado no teste e conceda as permissões mínimas:

```text
Pull requests → Read and write
Contents      → Read-only
Metadata      → Read-only
```

Depois de gerar, cole o token em `GITHUB_TOKEN` no `.env`. Ele é usado pelo backend para consultar Pull Requests, obter diffs e publicar comentários.

### 8.2 Definir o secret do webhook

Escolha um valor qualquer para o segredo compartilhado (ex: `Rafael-CodeReview-2026`) e coloque em `GITHUB_WEBHOOK_SECRET` no `.env`. O mesmo valor será informado no webhook do GitHub no passo 11.

### 8.3 Webhook

Esse passo só é concluído depois que o ngrok estiver rodando (seção 11) — a URL pública do túnel é o que você vai usar como Payload URL aqui.

**Settings → Webhooks → Add webhook**

- **Payload URL:** a URL pública do ngrok **seguida de `/webhook/github`**, por exemplo:

  ```text
  https://abc123.ngrok-free.dev/webhook/github
  ```

  > Não use só o endereço base do ngrok — o endpoint do FastAPI é `/webhook/github`, sem isso o GitHub vai enviar para `POST /` e nada vai acontecer.

- **Content type:** `application/json` (não use `application/x-www-form-urlencoded`)
- **Secret:** o mesmo valor definido em `GITHUB_WEBHOOK_SECRET`
- **Eventos:** selecione *Let me select individual events* e marque apenas **Pull requests**
- Deixe **Active** marcado e clique em **Add webhook**

#### Verificar a entrega

Depois de criado: **Settings → Webhooks → seu webhook → Recent Deliveries** mostra as entregas. No terminal do ngrok, a requisição deve aparecer como `POST /webhook/github` (não `POST /`).

---

## 9. Executar o Ollama

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

O `requirements.txt` instala o cliente Python `ollama`, mas não instala o programa Ollama nem baixa o modelo — isso precisa ser feito manualmente.

### 9.1 Verificar se o modelo está disponível

```bash
ollama list
```

O modelo `qwen2.5-coder:7b` deve aparecer na lista.

### 9.2 Erro de porta em uso

Se `ollama serve` retornar algo como:

```text
Error: listen tcp 127.0.0.1:11434:
bind: Only one usage of each socket address
```

isso normalmente significa que a porta `11434` já está sendo usada porque o serviço do Ollama já está em execução (no Windows, ele costuma iniciar automaticamente). Nesse caso, não é necessário iniciar outro `ollama serve` — pode seguir para o próximo passo.

### 9.3 Testar o LLM

Com o ambiente virtual ativado:

```bash
python3 -m app.test_llm
```

(Windows: `python -m app.test_llm`)

---

## 10. Executar o backend

```bash
uvicorn app.main:app --reload
```

Disponível em `http://localhost:8000`. Documentação interativa: `http://localhost:8000/docs`.

Se a documentação Swagger abrir, o backend está funcionando. **Mantenha esse terminal aberto.**

### Endpoints

```text
GET  /
POST /webhook/github

GET /pull-requests
GET /pull-requests/{pr_id}
GET /pull-requests/{pr_id}/analyses
GET /stats
```

---

## 11. Configurar e iniciar o ngrok

O ngrok expõe publicamente o backend local (`localhost:8000`) para que o GitHub consiga entregar o webhook.

### 11.1 Instalar

Windows:

```powershell
winget install ngrok -s msstore
```

Feche e reabra o terminal, depois confirme:

```powershell
ngrok version
```

macOS (Homebrew):

```bash
brew install ngrok/ngrok/ngrok
```

Linux: siga as instruções em [ngrok.com/download](https://ngrok.com/download).

### 11.2 Autenticar

Crie uma conta no ngrok, copie o **Authtoken** e configure:

```bash
ngrok config add-authtoken "SEU_AUTHTOKEN"
```

### 11.3 Iniciar o túnel

Em um novo terminal:

```bash
ngrok http 8000
```

O ngrok mostrará algo como:

```text
Forwarding  https://abc123.ngrok-free.dev -> http://localhost:8000
```

Copie a URL exibida em **Forwarding** — ela é a base do Payload URL usado na seção 8.3 (lembrando de acrescentar `/webhook/github`). **Mantenha esse terminal aberto.**

---

## 12. Executar o frontend

```bash
cd frontend
npm run dev
```

Dashboard em `http://localhost:5173`.

O frontend se comunica com o FastAPI e não acessa o Supabase diretamente. **Mantenha esse terminal aberto.**

---

## 13. Testes

### Sem dependências externas

**Diff Parser:**

```bash
python3 -m app.test_diff_parser
```

**Retry e Idempotência** (GitHub, Ollama e Supabase são mockados):

```bash
python3 -m unittest app.test_retry_idempotency -v
```

### Com Ollama instalado

```bash
python3 -m app.test_llm
```

### Com GitHub configurado

Requer `GITHUB_TOKEN`, `GITHUB_TEST_REPO` e `GITHUB_TEST_PR` preenchidos no `.env` (seção 7):

```bash
python3 -m app.test_github
python3 -m app.test_github_comment
```

> **Atenção:** `test_github_comment` publica um comentário real na Pull Request informada em `GITHUB_TEST_REPO`/`GITHUB_TEST_PR`.

(Windows: use `python` em vez de `python3` em todos os comandos acima)

---

## 14. Ordem recomendada para uma instalação nova

```bash
cd code-review-assistant
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python3 -m pip install -r requirements.txt
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

1. Executar os testes que não exigem serviços externos:

   ```bash
   python3 -m app.test_diff_parser
   python3 -m unittest app.test_retry_idempotency -v
   ```

2. Criar o projeto no Supabase e executar `database.sql` (seção 6).
3. Preencher o `.env`, incluindo `GITHUB_TEST_REPO`/`GITHUB_TEST_PR` (seção 7).
4. Instalar o Ollama e baixar o modelo:

   ```bash
   ollama pull qwen2.5-coder:7b
   ```

5. Executar o teste do LLM:

   ```bash
   python3 -m app.test_llm
   ```

6. Com GitHub configurado:

   ```bash
   python3 -m app.test_github
   python3 -m app.test_github_comment
   ```

7. Iniciar o backend (terminal 1):

   ```bash
   uvicorn app.main:app --reload
   ```

8. Instalar e iniciar o ngrok (terminal 2):

   ```bash
   ngrok http 8000
   ```

9. Criar o webhook no GitHub usando a URL do ngrok + `/webhook/github` (seção 8.3).
10. Iniciar o frontend (terminal 3):

    ```bash
    cd frontend
    npm run dev
    ```

11. Abrir ou atualizar uma Pull Request no repositório configurado e observar o fluxo completo (seção 15).

### Resumo dos 3 terminais em paralelo (+ Ollama)

| Terminal | Comando |
|---|---|
| Ollama (se não estiver já rodando) | `ollama serve` |
| Backend | `.venv\Scripts\Activate.ps1` (ou `source .venv/bin/activate`) → `uvicorn app.main:app --reload` |
| ngrok | `ngrok http 8000` |
| Frontend | `cd frontend` → `npm run dev` |

---

## 15. Checklist de verificação pós-teste

Depois de abrir/atualizar uma Pull Request no repositório configurado, confira:

- **GitHub:** a Pull Request deve receber o comentário automático da revisão.
- **Supabase:** a tabela `pull_requests` deve receber/atualizar o registro da PR; a tabela `analises` deve receber a análise correspondente ao `head_sha`.
- **Dashboard:** o frontend deve mostrar a Pull Request, a análise e as métricas disponíveis.
- **FastAPI:** no terminal do backend devem aparecer mensagens de processamento começando com `[REVIEW]`.
- **ngrok:** no terminal do ngrok, a requisição deve aparecer como `POST /webhook/github`.

---

## 16. Estrutura do projeto

```text
code-review-assistant/
│
├── app/
│   ├── __init__.py
│   ├── db.py                    # persistência no Supabase/PostgreSQL
│   ├── diff_parser.py           # parsing determinístico do diff
│   ├── github_client.py         # comunicação com a GitHub API
│   ├── llm_client.py            # Ollama/Qwen e validação da resposta
│   ├── main.py                  # FastAPI, webhook, CORS, rotas
│   ├── review_formatter.py      # conversão da análise para Markdown
│   ├── review_service.py        # orquestração do pipeline
│   │
│   ├── test_diff_parser.py      # testes do parser (sem deps externas)
│   ├── test_retry_idempotency.py# testes de retry/idempotência (sem deps externas)
│   ├── test_llm.py              # requer Ollama
│   ├── test_github.py           # requer GitHub token
│   └── test_github_comment.py   # requer GitHub token e PR real
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── public/
│   └── package.json
│
├── database.sql                 # script de criação das tabelas
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 17. Arquitetura de responsabilidades

```text
main.py          → HTTP, webhook, CORS, rotas
github_client.py → comunicação com a GitHub API
diff_parser.py   → parsing e localização determinística do diff
llm_client.py    → Ollama/Qwen e validação da resposta
db.py            → persistência no Supabase/PostgreSQL
review_formatter → conversão da análise para Markdown
review_service.py→ orquestração do pipeline e gerenciamento de estados
frontend/        → dashboard e visualização dos dados
```

---

## 18. Princípios técnicos

**Localização determinística** — arquivo e linha são determinados diretamente do diff, não pelo LLM.

**Structured output** — a resposta da IA é validada com Pydantic antes de persistir.

**Idempotência** — a constraint `unique (pr_id, head_sha)` impede análises duplicadas para a mesma versão da PR.

**Retry granular** — falha na análise e falha no comentário são tratadas separadamente. Um erro no comentário não invalida uma análise já concluída.

**Marker de idempotência** — um marcador HTML invisível é embutido em todo comentário publicado. Se o processo falhar após criar o comentário no GitHub mas antes de salvar o ID no banco, o sistema detecta o comentário existente pelo marker e não cria duplicata.

---

## 19. Limitações conhecidas

O modelo pode produzir falsos positivos, falsos negativos e classificações que precisam de revisão humana. A IA não substitui um code review humano.

O projeto possui uma camada de mitigação contra prompt injection (remoção de comentários, mascaramento de strings, localização determinística), mas não representa uma garantia absoluta.

O processamento utiliza `BackgroundTasks` do FastAPI. Para maior volume, uma arquitetura com filas dedicadas seria mais adequada.

---

## 20. Segurança

Nunca publique:

```text
.env
GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET
SUPABASE_SECRET_KEY
```

O repositório contém apenas `.env.example` com placeholders.

Se uma credencial real for exposta acidentalmente, revogue-a imediatamente e gere outra.

---

## 21. Trabalhos futuros

- Comentários inline por arquivo e linha
- Feedback humano sobre as sugestões
- Métricas detalhadas por categoria e severidade
- Histórico visual de evolução do score por commit
- Observabilidade (tempo de processamento por etapa)
- Testes de integração automatizados
- Deploy em ambiente de produção
- Avaliação quantitativa do modelo (precision, recall, falsos positivos)
- Suporte a múltiplos repositórios e usuários
- Migração de Personal Access Token para GitHub App

---

## 22. Status

```text
✅ GitHub Webhook
✅ Validação HMAC-SHA256
✅ FastAPI + background tasks
✅ GitHub API (diff, comentário, listagem de comentários)
✅ Diff Parser determinístico
✅ Ollama + Qwen 2.5 Coder 7B
✅ Structured Output + Pydantic
✅ Supabase / PostgreSQL
✅ Idempotência (pr_id + head_sha)
✅ Retry granular (análise e comentário independentes)
✅ Marker de idempotência no comentário
✅ API de histórico e métricas
✅ Dashboard React
✅ Guia de instalação e teste completo (Windows)
```
