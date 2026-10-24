from fastapi.testclient import TestClient
from main import app

# Cliente de teste(GitHub Actions): chama a API direto no código, sem precisar subir o servidor
client = TestClient(app)


# FUNCAO - Faz o login e devolve o token do usuário
def fazer_login(username, password):
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]