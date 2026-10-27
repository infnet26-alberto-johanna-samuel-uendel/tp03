import os, runpy, time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlmodel import SQLModel
from database.connection import engine, DATABASE_NAME
from routes import health, auth, predict, docs
from routes.auth import limiter

# Pasta fastapi/ (usada para localizar os arquivos estáticos do Swagger)
BASE_DIR = Path(__file__).resolve().parent

# Se o arquivo do banco ainda não existe
if not os.path.exists(DATABASE_NAME):  
    # Roda script, cria e popula banco
    runpy.run_path("sqlite_database.py")  
    

# Texto exibido no topo do /docs
DESCRICAO_API = """
API do sistema de atendimento ao cliente que classifica a intenção de mensagens de clientes.

### Autenticação
1. Gere o token em **POST /auth/token** (ou clique em **Authorize** e informe usuário e senha).
2. Envie o token nas rotas protegidas no header `Authorization: Bearer <token>`.

O token é um JWT assinado com HS256 e vale por 30 minutos.

### Controles de segurança
- Modelos Pydantic com `extra='forbid'`: campos não previstos -> **422**.
- Ownership (BOLA): cada usuário só acessa as próprias predictions -> **404** para recurso de outro usuário.
- Rate limit em **POST /auth/token**: 10 requisições por minuto por IP -> **429**.
- Headers de segurança (HSTS, CSP, X-Frame-Options, X-Content-Type-Options) em todas as respostas.
"""

app = FastAPI(
    title="API de Atendimento ao Cliente - Classificação de Intenções",
    description=DESCRICAO_API,
    version="3.0.0",
    # O /docs padrão do FastAPI é desligado e substituído pelo routes/docs.py (ZAP FINDINGS 3, 4 e 5)
    docs_url=None,
    # O /redoc também é desligado: ele carrega o ReDoc de CDN e depende de estilos inline
    redoc_url=None,
)
SQLModel.metadata.create_all(engine)  # Cria as tabelas no banco se ainda não existirem

# Arquivos estáticos do Swagger UI servidos pela própria API (sem CDN externo - ZAP FINDING 5)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# RATE LIMITING - Guarda o limitador no estado da aplicação
app.state.limiter = limiter
# Quando o limite estoura, devolve erro 429 (Too Many Requests) com mensagem para o usuário
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# CORS - Origens que podem acessar a API pelo navegador
origens_permitidas = [
    "http://localhost:3000",
    "http://localhost:8501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,  # Só essas origens são liberadas
    allow_credentials=True,            # Permite enviar credenciais (cookies, headers de autenticação)
    allow_methods=["*"],               # Libera todos os métodos HTTP
    allow_headers=["*"],               # Libera todos os headers enviados pelo frontend
)


# MIDDLEWARE - Tempo de processamento em todas as requisições
@app.middleware("http")
async def process_time(request: Request, call_next):
    start = time.time()  # Marca o início
    response = await call_next(request)  # Executa a rota e recebe a resposta
    final = time.time()  # Marca o fim
    response.headers["X-Process-Time"] = str(final - start)  # Tempo gasto no header da resposta
    return response


# MIDDLEWARE - Headers de segurança em todas as respostas
@app.middleware("http")
async def security_headers(request: Request, call_next):

    response = await call_next(request)  # Executa a rota e recebe a resposta

    # HSTS: obriga o navegador a usar HTTPS (1 ano, incluindo subdomínios)
    # ZAP FINDING 1 (High) - "Authentication Credentials Captured": a API passa a ser servida com HTTPS
    # (run_https.py localmente; HTTPS do Render em produção) e o HSTS impede o navegador de voltar para HTTP
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Impede que a página seja colocada dentro de um iframe
    response.headers["X-Frame-Options"] = "DENY"
    # Evita MIME sniffing (navegador adivinhar o tipo do arquivo e tentar executar)
    response.headers["X-Content-Type-Options"] = "nosniff"

    # CSP (Content-Security-Policy): diz ao navegador de onde a página pode carregar conteúdo
    if request.url.path == "/docs":
        # ZAP FINDINGS 2, 3, 4 e 5 - RESOLVIDOS AQUI (CSP do /docs):
        # - Finding 2 "Failure to Define Directive with No Fallback": form-action e base-uri não herdam o
        #   default-src, então agora são definidos explicitamente
        # - Finding 3 "script-src unsafe-inline": removido; o Swagger é iniciado por /static/swagger-init.js
        # - Finding 4 "style-src unsafe-inline": removido; a página não tem estilos inline
        # - Finding 5 "SRI Attribute Missing": não há mais https://cdn.jsdelivr.net, tudo vem da própria API
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "   # data: = ícones SVG embutidos no CSS do Swagger
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
    else:
        # As rotas da API só devolvem JSON, então nada pode ser carregado
        # ZAP FINDING 2: form-action e base-uri definidos também aqui (não têm fallback no default-src)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        )

    return response


# Registra as rotas na aplicação
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(docs.router)
