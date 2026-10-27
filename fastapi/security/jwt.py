from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import encode, decode, InvalidTokenError

SECRET_KEY = "minha-chave-secreta"  # Chave usada para assinar e validar os tokens

# Pega o token do cabeçalho Authorization e indica a rota de login
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    # Texto que aparece no botão "Authorize" do /docs
    description="Token JWT obtido em `POST /auth/token`, enviado no header `Authorization: Bearer <token>`."
)

# FUNCAO, cria o token JWT
def gerar_token(username: str):
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=30)  # Token vale por 30 minutos

    # no toke (usuário + Data e horan expiracao)
    dados = {"sub": username, "exp": expiracao}

    return encode(dados, SECRET_KEY, algorithm="HS256")


# FUNCAO, confere se o token é válido
def validar_token(  
    token: str = Depends(oauth2_scheme)  # Recebe o token enviado na requisição
):
    erro = HTTPException(
        status_code=401,  # Erro de não autorizado
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"}  # Avisa o cliente que precisa de um token Bearer
    )

    try:
        # Decodifica e confere a assinatura e a validade do token
        payload = decode(token, SECRET_KEY, algorithms=["HS256"])

        username = payload.get("sub")  # Pega o nome do usuário de dentro do token

        if username is None:  # Se o token não tem usuário, é inválido
            raise erro

    except InvalidTokenError:  # Se o token foi alterado, está mal formado ou expirou
        raise erro

    # Devolve o nome do usuário do token
    return username  