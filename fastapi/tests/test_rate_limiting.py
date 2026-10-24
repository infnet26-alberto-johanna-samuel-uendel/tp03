from utils import client


# TEST - o /auth/token aceita 10 requisições por minuto
def test_rate_limiting():
    dados = {"username": "admin", "password": "admin"}

    # As 10 primeiras respondem normal
    for i in range(10):
        response = client.post("/auth/token", data=dados)
        assert response.status_code == 200

    # A 11ª passa do limite e é bloqueada
    response = client.post("/auth/token", data=dados)

    assert response.status_code == 429
    assert response.json() == {"error": "Rate limit exceeded: 10 per 1 minute"}
