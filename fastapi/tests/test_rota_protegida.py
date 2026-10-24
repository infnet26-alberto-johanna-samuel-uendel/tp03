from utils import client

# TEST (Rota protegid) - Acesso sem token
def test_rota_protegida():
    # Chama a rota protegida sem mandar o header Authorization
    response = client.post("/predict", json={"message": "Meu produto chegou com defeito"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# TEST (e) - Acesso com token inválido
def test_rota_protegida_token_invalido():
    headers = {"Authorization": "Bearer token-falso"}

    response = client.post("/predict", json={"message": "Meu produto chegou com defeito"}, headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "Token inválido ou expirado"}
