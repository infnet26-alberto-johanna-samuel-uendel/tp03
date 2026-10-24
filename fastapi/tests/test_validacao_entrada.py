import requests
from utils import url, fazer_login


# TEST (Validação de entrada) - Campo extra no body
def test_validacao_entrada():
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    # "admin" não existe no PredictionRequest, então deve ser rejeitado
    body = {
        "message": "Meu produto chegou com defeito",
        "admin": True
    }

    response = requests.post(f"{url}/predict", json=body, headers=headers)

    assert response.status_code == 422