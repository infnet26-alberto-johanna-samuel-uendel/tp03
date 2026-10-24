import pytest
from routes.auth import limiter


# Zera o rate limit antes de cada teste. O SlowAPI guarda a contagem na memória,
# então sem isso os logins de um teste somam com os de outro e dão 429.
@pytest.fixture(autouse=True)   # autouse=True = roda antes de TODOS os testes, sozinho,
def zerar_rate_limit():
    limiter.reset()               # zera a contagem: cada teste
