# Auditoria final de segurança com OWASP ZAP - TP3

No TP2 o scan passivo do OWASP ZAP encontrou **1 finding High e 4 Medium**, todos documentados como risco
aceito e **não corrigidos**. No TP3 todos eles foram corrigidos e a auditoria foi executada de novo para
comprovar a correção.

| Relatório                                              | Data       | API auditada                    | High  | Medium | Low   | Informational |
| ------------------------------------------------------ | ---------- | ------------------------------- | :---: | :----: | :---: | :-----------: |
| [relatorio_zap_antes.html](relatorio_zap_antes.html)   | 05/10/2026 | `http://127.0.0.1:8000` (TP2)   | **1** | **4**  | 1     | 3             |
| [relatorio_zap_final.html](relatorio_zap_final.html)   | 26/10/2026 | `https://127.0.0.1:8443` (TP3)  | **0** | **0**  | 33    | 11            |

**Resultado final: nenhum finding Medium ou High.** Os Low e Informational que restaram estão explicados no
fim deste documento.

---

## Como a auditoria foi executada

- **Ferramenta:** OWASP ZAP 2.17.0, somente **scan passivo** (o ZAP observa o tráfego, sem ataques).
- **API:** iniciada com HTTPS, a partir da pasta `fastapi/`:

  ```bash
  python run_https.py      # https://127.0.0.1:8443 (certificado autoassinado gerado na 1ª execução)
  ```

- **Tráfego analisado** (mesmo roteiro do TP2, enviado pelo proxy do ZAP):
  - `GET /docs`, os arquivos do Swagger em `/static/...` e `GET /openapi.json`;
  - `GET /health`;
  - `POST /auth/token` com senha errada (**401**) e com senha certa (**200**), com o header
    `Authorization: Basic` que o Swagger envia no fluxo OAuth2 password;
  - `POST /predict` com token (**200**), sem token (**401**) e com campo extra (**422**);
  - `GET /predictions` e `GET /predictions/{id}` do próprio usuário (**200**) e de outro usuário (**404**);
  - além disso, **Spider** do ZAP a partir de `/docs` e importação da definição OpenAPI (`/openapi.json`).
- **Escopo do relatório:** somente o site `https://127.0.0.1:8443`.
- **Testes automatizados:** os controles do `/docs` também são verificados a cada push pelo
  [fastapi/tests/test_headers_seguranca.py](../fastapi/tests/test_headers_seguranca.py) (GitHub Actions).

---

## Finding 1 - Authentication Credentials Captured

| Item                                 | Descrição |
| ------------------------------------ | --------- |
| **Finding**                          | Authentication Credentials Captured (plugin 10105) |
| **Severidade**                       | **High** (confiança Medium) |
| **URL afetada**                      | `POST http://127.0.0.1:8000/auth/token` |
| **O que foi detectado**              | O login recebia usuário e senha por **HTTP**, sem criptografia. O ZAP também detectou o header `Authorization: Basic`, que o Swagger envia no fluxo OAuth2 password. |
| **Por que é um risco**               | Em HTTP, qualquer pessoa na mesma rede (Wi-Fi público, proxy, roteador comprometido) consegue capturar o tráfego e ler usuário, senha e o token JWT devolvido. No Basic Authentication as credenciais estão só em base64, que é trivial de decodificar. Com a senha ou o token, o atacante assume a conta da vítima (CWE-287, OWASP A07:2021 - Identification and Authentication Failures). |
| **Correção realizada**               | A API passou a ser servida **somente com HTTPS (TLS)**. O novo [run_https.py](../fastapi/run_https.py) gera um certificado autoassinado para `localhost`/`127.0.0.1` (pasta `certs/`, ignorada pelo Git) e sobe o uvicorn com `ssl_certfile`/`ssl_keyfile` em `https://127.0.0.1:8443`. Em produção o HTTPS é fornecido pelo Render (`https://tp03-pb.onrender.com`). O header HSTS, que já existia, impede o navegador de voltar para HTTP. |
| **Onde no código**                   | [fastapi/run_https.py](../fastapi/run_https.py) (docstring do topo e `uvicorn.run`) e [fastapi/main.py:95](../fastapi/main.py) (HSTS) - comentário `ZAP FINDING 1`. |
| **Evidência de que não permanece**   | No relatório final **não há nenhum alerta 10105**. O ZAP recebeu as mesmas requisições de login (inclusive com o header `Authorization: Basic`), tanto que elas aparecem no alerta informativo *Authentication Request Identified* (10111), mas agora elas trafegam criptografadas. **Teste de controle:** a mesma requisição enviada em HTTP (`uvicorn main:app`, porta 8000) volta a gerar o alerta High 10105. Isso confirma que a correção é o transporte HTTPS e que rodar a API em HTTP puro só é aceitável em desenvolvimento local. |

## Finding 2 - CSP: Failure to Define Directive with No Fallback

| Item                                 | Descrição |
| ------------------------------------ | --------- |
| **Finding**                          | CSP: Failure to Define Directive with No Fallback (plugin 10055) |
| **Severidade**                       | **Medium** (confiança High) |
| **URL afetada**                      | `GET http://127.0.0.1:8000/docs` |
| **O que foi detectado**              | A Content-Security-Policy não definia a diretiva `form-action`. Ela (assim como `base-uri` e `frame-ancestors`) **não herda** o valor do `default-src`, então, sem ser definida, fica tudo liberado. |
| **Por que é um risco**               | Se algum conteúdo malicioso for injetado na página, um formulário pode enviar os dados digitados (por exemplo, usuário e senha do Authorize) para um site do atacante. Sem `base-uri`, um `<base>` injetado redireciona todos os caminhos relativos da página (CWE-693, falha no mecanismo de proteção). |
| **Correção realizada**               | O middleware de headers passou a definir explicitamente `form-action 'self'` e `base-uri 'self'` no `/docs`, e `form-action 'none'` e `base-uri 'none'` nas rotas da API (que só devolvem JSON). Também foi adicionado `object-src 'none'`. |
| **Onde no código**                   | [fastapi/main.py:105](../fastapi/main.py) (CSP do `/docs`) e [fastapi/main.py:124](../fastapi/main.py) (CSP das rotas da API) - comentário `ZAP FINDINGS 2, 3, 4 e 5` / `ZAP FINDING 2`. |
| **Evidência de que não permanece**   | Header devolvido agora pelo `/docs`: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`. O relatório final não tem nenhum alerta 10055, e os testes `test_csp_docs` e `test_headers_seguranca_api` verificam as diretivas. |

## Finding 3 - CSP: script-src unsafe-inline

| Item                                 | Descrição |
| ------------------------------------ | --------- |
| **Finding**                          | CSP: script-src unsafe-inline (plugin 10055) |
| **Severidade**                       | **Medium** (confiança High) |
| **URL afetada**                      | `GET http://127.0.0.1:8000/docs` |
| **O que foi detectado**              | A CSP do `/docs` tinha `'unsafe-inline'` em `script-src`, porque o HTML do `/docs` padrão do FastAPI inicia o Swagger com um `<script>` escrito direto na página. |
| **Por que é um risco**               | Com `'unsafe-inline'` a CSP deixa de proteger contra Cross-Site Scripting (XSS): qualquer script injetado na página seria executado e poderia, por exemplo, roubar o token JWT digitado no Authorize (CWE-693). |
| **Correção realizada**               | O `/docs` padrão foi desligado (`FastAPI(docs_url=None, redoc_url=None)`) e substituído por uma rota própria ([routes/docs.py](../fastapi/routes/docs.py)) cujo HTML **não tem nenhum script inline**. A inicialização do Swagger foi movida para o arquivo [static/swagger-init.js](../fastapi/static/swagger-init.js), servido pela API, e a CSP passou a ser `script-src 'self'`. O `/redoc` também foi desligado, porque carrega o ReDoc de um CDN e depende de estilos inline. |
| **Onde no código**                   | [fastapi/static/swagger-init.js:2](../fastapi/static/swagger-init.js), [fastapi/routes/docs.py:27](../fastapi/routes/docs.py), [fastapi/main.py:43](../fastapi/main.py) e [fastapi/main.py:105](../fastapi/main.py) - comentários `ZAP FINDING 3`. |
| **Evidência de que não permanece**   | A CSP final não contém `unsafe-inline` e o relatório final não tem alerta 10055. O `/docs` foi aberto no navegador com essa CSP: o Swagger carregou, o Authorize gerou o token e as chamadas funcionaram, **sem nenhuma violação de CSP** registrada (evento `securitypolicyviolation` vazio). O teste `test_docs_sem_cdn_e_com_sri` verifica que o HTML não tem `<script>` inline. |

## Finding 4 - CSP: style-src unsafe-inline

| Item                                 | Descrição |
| ------------------------------------ | --------- |
| **Finding**                          | CSP: style-src unsafe-inline (plugin 10055) |
| **Severidade**                       | **Medium** (confiança High) |
| **URL afetada**                      | `GET http://127.0.0.1:8000/docs` |
| **O que foi detectado**              | A CSP do `/docs` tinha `'unsafe-inline'` em `style-src`, liberando estilos escritos direto no HTML. |
| **Por que é um risco**               | Estilos inline liberados permitem injeção de CSS, usada para alterar a página e enganar o usuário (por exemplo, esconder ou sobrepor o formulário de login) ou para vazar informações da página por seletores CSS (CWE-693). |
| **Correção realizada**               | O HTML do novo `/docs` não tem `<style>` nem atributos `style=`; todo o visual vem do `swagger-ui.css` servido pela própria API. A CSP passou a ser `style-src 'self'`. |
| **Onde no código**                   | [fastapi/routes/docs.py:27](../fastapi/routes/docs.py) e [fastapi/main.py:105](../fastapi/main.py) - comentários `ZAP FINDINGS 3 e 4`. |
| **Evidência de que não permanece**   | A CSP final não contém `unsafe-inline`, o relatório final não tem alerta 10055, o Swagger renderiza normalmente sem violação de CSP e o teste `test_docs_sem_cdn_e_com_sri` verifica que o HTML não tem `style=`. |

## Finding 5 - Sub Resource Integrity Attribute Missing

| Item                                 | Descrição |
| ------------------------------------ | --------- |
| **Finding**                          | Sub Resource Integrity Attribute Missing (plugin 90003) |
| **Severidade**                       | **Medium** (confiança High) |
| **URL afetada**                      | `GET http://127.0.0.1:8000/docs` (2 ocorrências: `swagger-ui.css` e `swagger-ui-bundle.js` do `cdn.jsdelivr.net`) |
| **O que foi detectado**              | O `/docs` carregava o CSS e o JavaScript do Swagger de um CDN externo, sem o atributo `integrity` nas tags `<link>` e `<script>`. |
| **Por que é um risco**               | Sem o `integrity`, o navegador não confere se o arquivo baixado é o original. Se o CDN ou o pacote fossem comprometidos (ataque de cadeia de suprimentos), o JavaScript alterado rodaria na página da API e teria acesso às credenciais e ao token digitados no Swagger (CWE-345). |
| **Correção realizada**               | Os arquivos do Swagger UI (pacote oficial `swagger-ui-dist` **5.33.2**, integridade conferida com o hash publicado no npm) passaram a ser **servidos pela própria API** em [fastapi/static/swagger-ui/](../fastapi/static/swagger-ui/), montada em `/static`. Não há mais nenhum recurso de outro domínio, e cada `<link>`/`<script>` leva o atributo `integrity` com o hash **SHA-384** do arquivo, calculado quando a API inicia. |
| **Onde no código**                   | [fastapi/routes/docs.py:19](../fastapi/routes/docs.py) (cálculo do SRI e HTML) e [fastapi/main.py:50](../fastapi/main.py) (`app.mount("/static", ...)`) - comentários `ZAP FINDING 5`. |
| **Evidência de que não permanece**   | HTML devolvido agora: `<script src="/static/swagger-ui/swagger-ui-bundle.js" integrity="sha384-gNnU..." crossorigin="anonymous">`. O relatório final não tem alerta 90003 e também deixou de ter o Low *Cross-Domain JavaScript Source File Inclusion* (10017), que existia no TP2. O teste `test_docs_sem_cdn_e_com_sri` verifica a ausência de CDN e a presença do `integrity`. |

---

## Ajuste extra durante a auditoria - Vulnerable JS Library (Low)

Na primeira execução do scan final, com o `swagger-ui-dist` **5.33.1**, o ZAP apontou um **Low**:
*Vulnerable JS Library* (plugin 10003). O bundle trazia o **DOMPurify 3.4.13**, com vulnerabilidades
corrigidas na versão 3.4.16 (CVE-2026-109344 e CVE-2026-109345). Os arquivos foram atualizados para o
`swagger-ui-dist` **5.33.2**, que traz o DOMPurify 3.4.16, e o scan foi refeito do zero. No relatório final
esse alerta não aparece mais.

## Findings restantes (Low e Informational)

Não há Medium nem High. Os alertas que restaram foram analisados e não representam risco para a API:

| Alerta                                      | Severidade    | Análise |
| ------------------------------------------- | ------------- | ------- |
| Timestamp Disclosure - Unix (33)            | Low           | **Falso positivo.** Todas as ocorrências estão no `swagger-ui-bundle.js`, que é JavaScript minificado. O ZAP confunde constantes numéricas do código com datas: por exemplo, `1518500249` é `0x5A827999`, constante do algoritmo SHA-1. Nenhuma resposta da API expõe data ou hora interna. |
| Re-examine Cache-control Directives (6)     | Informational | As respostas JSON não definem `Cache-Control`. Não há cookies e o token só trafega no header `Authorization`. Melhoria futura: `Cache-Control: no-store` nas respostas autenticadas. |
| Authentication Request Identified (3)       | Informational | O ZAP só identifica que `POST /auth/token` é a rota de login. É a evidência de que o login foi analisado no scan. |
| Session Management Response Identified (1)  | Informational | O ZAP identifica o `access_token` devolvido pelo login (JWT). Comportamento esperado. |
| Modern Web Application (1)                  | Informational | O `/docs` é uma aplicação JavaScript (Swagger UI). Apenas informativo. |
