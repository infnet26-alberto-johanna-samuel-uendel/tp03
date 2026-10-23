import requests
from utils import url


# TEST - Acesso sem token
def test_rota_protegida():
    # Chama a rota protegida sem mandar o header Authorization
    response = requests.get(f"{url}/predictions/3")
 
    assert response.status_code == 401
