from fastapi import APIRouter

# Grupo de rotas de verificação da API
router = APIRouter(tags=["Saúde"])


# ROTA - GET - /health - usa-se para verificAR se a API está no ar e funcionando
@router.get(
    "/health",
    summary="Status da Aplicação",
    description="Verifica se a API está no ar. Rota **pública**, não exige autenticação.",
    responses={200: {"description": "API ativa", "content": {"application/json": {"example": {"status": "ok"}}}}},
)
def health_check():
    return {"status": "ok"}
