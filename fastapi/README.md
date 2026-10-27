# EXCUTAR APLICAÇÃO COMPLETO

```bash
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
fastapi dev main.py
```

## Rodar Testes Automatizados

```bash
# Dentro do ambiEnte virtual .venv
py -m pytest -v
```

## Pré-requisitos

- VS Code
- Python 3.10 ou superior
- pip
- **Só no Windows:** permitir execução de scripts no PowerShell (necessário só uma vez)

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Instruções de instalação

1. Clone o repositório:

```bash
git clone https://github.com/infnet26-alberto-johanna-samuel-uendel/tp03.git
cd tp03/fastapi
```

2. Abra o projeto e acesse a pasta da API:

```bash
cd .\fastapi
```

3. Crie e ative um ambiente virtual:
   - Verifique se está dentro da pasta "fastapi"

```bash
python -m venv .venv

# Windows - Ative o ambiente virtual
.venv\Scripts\Activate.ps1

# Linux/Mac - Ative o ambiente virtual
source .venv/bin/activate
```

4. Instale as dependências a partir do arquivo requirements.txt:

```bash
python -m pip install -r requirements.txt

# Verifique se foi instalado corretamente (deve aparecer name, location e outras informações sobre o pacote)
python -m pip show fastapi
```

## Instruções de execução

1. Acesse a pasta da API e certifique-se de que o ambiente virtual está ativado (veja passo 3 da instalação, caso tenha aberto um novo terminal):

```bash
cd .\fastapi
```

2. Execute a aplicação:

```bash
fastapi dev main.py
# ou
uvicorn main:app --reload
```

3. A API estará disponível em:
   http://127.0.0.1:8000/docs

# Extras

1. Apagar tudo e recriar o ambiente virtual

   **Windows (PowerShell):**

```bash
deactivate
Remove-Item -Recurse -Force .venv
# Apagar pastas __pycache__
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

**Linux/Mac:**

```bash
deactivate
rm -rf .venv
```

2. Criar requirements.txt

```bash
python -m pip freeze > requirements.txt
```
