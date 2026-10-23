import requests

# O app precisa estar rodando antes dos testes
url = "http://127.0.0.1:8000"


# FUNCAO - Faz o login e devolve o token do usuário
def fazer_login(username, password):
    response = requests.post(
        f"{url}/auth/token",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]