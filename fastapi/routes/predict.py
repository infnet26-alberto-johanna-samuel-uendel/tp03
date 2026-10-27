from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session, select
from database.connection import get_session
from models.error_models import RESPOSTA_401_TOKEN, RESPOSTA_404_PREDICTION
from models.prediction_request_model import PredictionRequest
from models.prediction_response_model import PredictionResponse
from models.prediction_sql_model import Prediction
from models.user_sql_model import User
from security.dependencies import get_current_user

router = APIRouter(tags=["Predições"])  # Grupo de rotas de previsão

# ROTA - Busca previsão pelo ID
@router.get(
    "/predictions/{prediction_id}",
    summary="Obter previsão pelo ID",
    response_model=Prediction,
    description=(
        "Retorna uma prediction **somente se ela pertencer ao usuário logado**.\n\n"
        "- **Autenticação:** exige token JWT no header `Authorization: Bearer <token>`.\n"
        "- **Ownership (BOLA):** a busca filtra pelo `owner_id` do usuário do token. Prediction de outro "
        "usuário responde **404**, sem revelar se o recurso existe."
    ),
    responses={**RESPOSTA_401_TOKEN, **RESPOSTA_404_PREDICTION},
)
def get_prediction(prediction_id: int = Path(description="ID da prediction"),
                   session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)
):
    # seleciona pelo id da previsao e pelo usuario logado
    statement = select(Prediction).where(
        Prediction.id == prediction_id,
        Prediction.owner_id == current_user.id
    )

    prediction = session.exec(statement).first()  # primeira previsao encontrada
    # Se não achou, ou se a previsão é de outro usuário
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction não encontrada")

    return prediction


# ROTA - Faz a previsão da intenção (protegida)
@router.post(
    "/predict",
    summary="Fazer previsão pela intenção da mensagem",
    response_model=PredictionResponse,
    description=(
        "Recebe a mensagem do cliente e devolve a intenção prevista.\n\n"
        "- **Corpo:** JSON com o campo `message` (texto da mensagem). Campos extras são "
        "rejeitados com **422** (`extra='forbid'`).\n"
        "- **Autenticação:** exige token JWT no header `Authorization: Bearer <token>`.\n"
        "- **Observação:** por enquanto a intenção é fixa (`Technical issue`); o classificador "
        "será implementado na próxima etapa do projeto."
    ),
    responses=RESPOSTA_401_TOKEN,
)
def predict(predictionRequest: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    predictionResponse = PredictionResponse(
        message=predictionRequest.message,  # Devolve a mesma mensagem recebida
        intent="Technical issue"  # Intenção fixa por enquanto, sem modelo de verdade
    )

    # Resposta com mensagem e intenção
    return predictionResponse


# ROTA - Lista as previsões do usuário logado
@router.get(
    "/predictions",
    summary="Obtém todas as previsões do usuário logado",
    response_model=list[Prediction],
    description=(
        "Lista **somente** as predictions do usuário dono do token (filtro por `owner_id`).\n\n"
        "- **Autenticação:** exige token JWT no header `Authorization: Bearer <token>`."
    ),
    responses=RESPOSTA_401_TOKEN,
)
def get_all_predictions(session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
    ):
    # Só as previsões do usuário logado
    statement = select(Prediction).where(
        Prediction.owner_id == current_user.id
    )

    # Devolve a lista de previsões
    return session.exec(statement).all()
