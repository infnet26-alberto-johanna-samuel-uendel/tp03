import base64, hashlib
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()  # Rota da documentação interativa (Swagger UI)

# Pasta com os arquivos estáticos (servida pelo main.py em /static)
PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"


# FUNCAO, calcula o hash SRI (Subresource Integrity) de um arquivo
# O navegador recalcula o hash do arquivo baixado e só usa o arquivo se o hash for igual
def calcular_sri(caminho: Path):
    digest = hashlib.sha384(caminho.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


# ZAP FINDING 5 (Medium) - "Sub Resource Integrity Attribute Missing" - RESOLVIDO AQUI:
# o /docs padrão do FastAPI carrega o CSS e o JS do Swagger do CDN cdn.jsdelivr.net sem o atributo integrity.
# Agora os arquivos do Swagger UI (swagger-ui-dist 5.33.2) ficam na própria API (fastapi/static/swagger-ui)
# e cada <link>/<script> leva o atributo integrity com o hash SHA-384 do arquivo
SRI_CSS = calcular_sri(PASTA_STATIC / "swagger-ui" / "swagger-ui.css")
SRI_BUNDLE = calcular_sri(PASTA_STATIC / "swagger-ui" / "swagger-ui-bundle.js")
SRI_INIT = calcular_sri(PASTA_STATIC / "swagger-init.js")

# HTML do /docs: sem nenhum <script> ou estilo inline (ZAP FINDINGS 3 e 4) e sem recursos de outros domínios
HTML_DOCS = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>API de Atendimento ao Cliente - Swagger UI</title>
<link rel="icon" type="image/png" href="/static/swagger-ui/favicon-32x32.png">
<link rel="stylesheet" href="/static/swagger-ui/swagger-ui.css" integrity="{SRI_CSS}" crossorigin="anonymous">
</head>
<body>
<div id="swagger-ui"></div>
<script src="/static/swagger-ui/swagger-ui-bundle.js" integrity="{SRI_BUNDLE}" crossorigin="anonymous"></script>
<script src="/static/swagger-init.js" integrity="{SRI_INIT}" crossorigin="anonymous"></script>
</body>
</html>
"""


# ROTA - GET /docs - documentação interativa (Swagger UI) servida pela própria API
@router.get("/docs", include_in_schema=False)
def swagger_ui():
    return HTMLResponse(HTML_DOCS)
