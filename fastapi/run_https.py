"""Executa a API com HTTPS (TLS) em https://127.0.0.1:8443

ZAP FINDING 1 (High) - "Authentication Credentials Captured" - RESOLVIDO AQUI:
o ZAP detectou que o POST /auth/token recebia usuário e senha (e o header Authorization: Basic que o Swagger
envia no fluxo OAuth2 password) por HTTP, sem criptografia. Este script sobe a API somente com HTTPS:
as credenciais e o token JWT trafegam criptografados e não podem ser lidos por quem monitora a rede.

Na primeira execução é gerado um certificado autoassinado (pasta certs/, ignorada pelo Git) válido para
localhost e 127.0.0.1. Em produção (Render) o HTTPS é fornecido pela própria plataforma.

Uso (de dentro da pasta fastapi/):  python run_https.py
"""
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

BASE_DIR = Path(__file__).resolve().parent
PASTA_CERTS = BASE_DIR / "certs"
CERTIFICADO = PASTA_CERTS / "cert.pem"
CHAVE = PASTA_CERTS / "key.pem"


# FUNCAO, gera um certificado TLS autoassinado para localhost / 127.0.0.1 (válido por 1 ano)
def gerar_certificado():
    PASTA_CERTS.mkdir(exist_ok=True)

    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    agora = datetime.now(timezone.utc)

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)  # autoassinado: emissor = próprio certificado
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(chave, hashes.SHA256())
    )

    CHAVE.write_bytes(chave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))
    CERTIFICADO.write_bytes(certificado.public_bytes(serialization.Encoding.PEM))
    print(f"Certificado autoassinado gerado em {PASTA_CERTS}")


if __name__ == "__main__":
    if not CERTIFICADO.exists() or not CHAVE.exists():
        gerar_certificado()

    uvicorn.run(
        "main:app",
        app_dir=str(BASE_DIR),
        host="127.0.0.1",
        port=8443,
        ssl_certfile=str(CERTIFICADO),  # HTTPS: certificado TLS
        ssl_keyfile=str(CHAVE),         # HTTPS: chave privada do certificado
        server_header=False,            # não expõe "server: uvicorn" nas respostas
    )
