from pydantic import BaseModel, ConfigDict, Field

# Modelo que define o formato dos dados que chegam na requisição de previsão
class PredictionRequest(BaseModel):
    # Não aceita campos extras além dos definidos aqui (se mandar outro campo, dá erro)
    model_config = ConfigDict(extra="forbid")

    # Texto da mensagem que vai ser analisada (description e examples aparecem no /docs)
    message: str = Field(
        description="Texto da mensagem do cliente que terá a intenção classificada",
        examples=["Meu produto chegou com defeito e quero devolver"],
    )
