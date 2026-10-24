from utils import client, fazer_login


# TEST - Acesso a recurso de outro usuário
def test_autorizacao_bola():
    # jose (id 2) é dono só da prediction 3. A prediction 1 é do admin
    token = fazer_login("jose", "1234")
    headers = {"Authorization": f"Bearer {token}"}

    # jose consegue ver a prediction dele
    response_dele = client.get("/predictions/3", headers=headers)
    assert response_dele.status_code == 200

    # jose tenta ver a prediction do admin: a API responde 404 e não devolve os dados
    response_outro = client.get("/predictions/1", headers=headers)
    assert response_outro.status_code == 404
    assert "text" not in response_outro.json()