// Inicializa o Swagger UI do /docs.
// ZAP FINDING 3 (Medium) - "CSP: script-src unsafe-inline" - RESOLVIDO AQUI:
// o /docs padrão do FastAPI inicia o Swagger com um <script> escrito direto no HTML, o que obrigava a CSP
// a liberar 'unsafe-inline'. Com a inicialização neste arquivo separado, a CSP usa só script-src 'self'.
window.ui = SwaggerUIBundle({
  url: "/openapi.json",
  dom_id: "#swagger-ui",
  layout: "BaseLayout",
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
});
