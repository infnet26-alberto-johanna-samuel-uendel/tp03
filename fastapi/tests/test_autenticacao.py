from utils import client


# TEST (Autenticação) - Login com credenciais válidas: a API devolve o token
def test_login_valido():
    response = client.post("/auth/token", data={"username": "admin", "password": "admin"})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# TEST (a) - Login com credenciais inválidas: a API nega o acesso
def test_login_invalido():
    response = client.post("/auth/token", data={"username": "admin", "password": "senha-errada"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}
