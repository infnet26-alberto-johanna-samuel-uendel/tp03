from pydantic import BaseModel


# Modelo das respostas de erro da API (401, 404). Usado só para documentar as respostas no /docs
class Erro(BaseModel):
    detail: str     # mensagem do erro


# Modelo da resposta 429 do SlowAPI (rate limit). Usado só para documentar a resposta no /docs
class ErroRateLimit(BaseModel):
    error: str      # mensagem do bloqueio


# Respostas reutilizadas nas rotas, para aparecerem no /docs com exemplo
RESPOSTA_401_TOKEN = {
    401: {
        "model": Erro,
        "description": "Token ausente, inválido ou expirado",
        "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
    }
}

RESPOSTA_404_PREDICTION = {
    404: {
        "model": Erro,
        "description": "Prediction não existe ou pertence a outro usuário (controle de ownership / BOLA)",
        "content": {"application/json": {"example": {"detail": "Prediction não encontrada"}}},
    }
}
