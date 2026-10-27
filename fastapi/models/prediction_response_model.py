from pydantic import BaseModel, Field

# Modelo que define o formato da resposta que a API devolve
class PredictionResponse(BaseModel):
    message: str = Field(description="Mensagem que foi analisada")
    intent: str = Field(description="Intenção identificada na mensagem", examples=["Technical issue"])
