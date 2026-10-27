from utils import client


#-------------------------------------------------------------------------
# TEST (ZAP findings 2, 3, 4 e 5) - CSP do /docs sem 'unsafe-inline' e com form-action/base-uri
def test_csp_docs():
    response = client.get("/docs")

    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in csp            # findings 3 e 4
    assert "form-action 'self'" in csp           # finding 2
    assert "base-uri 'self'" in csp              # finding 2
    assert "cdn.jsdelivr.net" not in csp         # finding 5


#-------------------------------------------------------------------------
# TEST (ZAP finding 5) - /docs carrega o Swagger da própria API, com integrity (SRI), sem CDN externo
def test_docs_sem_cdn_e_com_sri():
    html = client.get("/docs").text

    assert "cdn.jsdelivr.net" not in html
    assert '<script src="/static/swagger-ui/swagger-ui-bundle.js" integrity="sha384-' in html
    assert '<link rel="stylesheet" href="/static/swagger-ui/swagger-ui.css" integrity="sha384-' in html
    assert "<script>" not in html                # nenhum script inline (finding 3)
    assert "style=" not in html                  # nenhum estilo inline (finding 4)

    # Os arquivos referenciados existem e são servidos pela API
    assert client.get("/static/swagger-ui/swagger-ui-bundle.js").status_code == 200
    assert client.get("/static/swagger-ui/swagger-ui.css").status_code == 200
    assert client.get("/static/swagger-init.js").status_code == 200


#-------------------------------------------------------------------------
# TEST - Rotas da API devolvem os headers de segurança
def test_headers_seguranca_api():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "form-action 'none'" in response.headers["Content-Security-Policy"]
