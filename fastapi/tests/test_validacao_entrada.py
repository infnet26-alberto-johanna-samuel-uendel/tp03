# fastapi/tests/test_validacao_entrada.py
from utils import client, fazer_login

#-------------------------------------------------------------------------
# TEST (Validação de entrada) - Campo extra no body
def test_validacao_entrada():
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    # "admin" não existe no PredictionRequest, então deve ser rejeitado
    body = {
        "message": "Meu produto chegou com defeito",
        "admin": True
    }

    response = client.post("/predict", json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


#-------------------------------------------------------------------------
# TEST (Validação de entrada) - Body sem o campo obrigatório "message"
def test_validacao_sem_message():
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/predict", json={}, headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"


#-------------------------------------------------------------------------
# TEST (Validação de entrada) - "message" que não é texto
def test_validacao_message_tipo_errado():
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/predict", json={"message": 123}, headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_type"


#-------------------------------------------------------------------------
# TEST (Validação de entrada) - ID da prediction que não é número
def test_validacao_id_invalido():
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/predictions/abc", headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "int_parsing"