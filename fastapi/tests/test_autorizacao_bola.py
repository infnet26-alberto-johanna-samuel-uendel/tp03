import requests
from utils import url, fazer_login


# TEST (b) - Acesso a recurso de outro usuário: a API não pode devolver
def test_autorizacao_bola():
    # jose (id 2) é dono só da prediction 3. A prediction 1 é do admin
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    # jose consegue ver a prediction dele
    response_dele = requests.get(f"{url}/predictions/3", headers=headers)
    assert response_dele.status_code == 200

    # jose tenta ver a prediction do admin: a API responde 404 e não devolve os dados
    response_outro = requests.get(f"{url}/predictions/1", headers=headers)
    assert response_outro.status_code == 404
    assert "text" not in response_outro.json()