from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, select
from database.connection import get_session
from models.auth_models import Token
from models.error_models import Erro, ErroRateLimit
from models.user_sql_model import User
from security.jwt import gerar_token


router = APIRouter(prefix="/auth", tags=["Autenticação"])   # Grupo de rotas de autenticação
limiter = Limiter(key_func=get_remote_address)

# ROTA - gerar o token (POST /auth/token)
# RATE LIMIT: no máximo 10 requisições por minuto por cliente (IP). A 11ª recebe erro 429.
# Justificativa: um usuário de verdade dificilmente erra a senha mais de 10 vezes em 1 minuto,
# então o limite não atrapalha o uso normal. Já um ataque de força bruta precisa testar muitas
# senhas bem rápido. Com o limite, o atacante fica preso a 10 tentativas por minuto.
@router.post(
    "/token",
    summary="Gerar token",
    response_model=Token,
    description=(
        "Autentica o usuário e devolve um **token JWT** (HS256, validade de 30 minutos).\n\n"
        "- **Corpo:** `application/x-www-form-urlencoded` com `username` e `password` "
        "(padrão OAuth2 password flow).\n"
        "- **Autenticação:** rota pública; é ela que gera o token usado nas rotas protegidas.\n"
        "- **Rate limit:** 10 requisições por minuto por IP; a 11ª recebe **429**.\n"
        "- **Transporte:** as credenciais só devem trafegar por **HTTPS** (ver `run_https.py`)."
    ),
    responses={
        200: {
            "description": "Login válido: token gerado",
            "content": {"application/json": {"example": {"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer"}}},
        },
        401: {
            "model": Erro,
            "description": "Usuário ou senha inválidos",
            "content": {"application/json": {"example": {"detail": "Usuário ou senha inválidos"}}},
        },
        429: {
            "model": ErroRateLimit,
            "description": "Limite de 10 tentativas por minuto excedido",
            "content": {"application/json": {"example": {"error": "Rate limit exceeded: 10 per 1 minute"}}},
        },
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,  # Obrigatório: o SlowAPI precisa da requisição para saber o IP do cliente
    # Recebe usuário e senha do formulário de login
    form_data: OAuth2PasswordRequestForm = Depends(),  
    session: Session = Depends(get_session) 
):
    statement = select(User).where(
        User.username == form_data.username  # Busca o usuário pelo nome
    )

    user = session.exec(statement).first()  # Busca e pega o primeiro resultado
    
    # Se o usuário existe e se a senha está correta
    if user is None or user.password != form_data.password:  
        raise HTTPException(
            status_code=401, 
            detail="Usuário ou senha inválidos"
        )

    token = gerar_token(user.username)  # Gera o token JWT para o usuário

    return {"access_token": token, "token_type": "bearer"}