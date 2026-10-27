# Planejamento da próxima etapa - modelo de classificação e teste adversarial

**Projeto de Bloco - Análise e Segurança de Agentes de IA | TP3**

Este documento define o que será feito nos TP4/TP5: o **modelo candidato** para classificar a intenção das
mensagens, a **representação do texto** com `CountVectorizer` e o **alvo autorizado** para o teste
adversarial.

O problema de classificação foi formalizado na U-Tarefa 2 do notebook [eda_tp3.ipynb](../eda/eda_tp3.ipynb):

> **Dado o texto de uma mensagem de atendimento ao cliente, qual é a intenção do usuário?**

| Elemento   | Definição                                                                                                   |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| Entrada X  | `Ticket Description` - texto livre da mensagem do cliente (em inglês)                                        |
| Alvo y     | `Ticket Type` - 5 classes: `Billing inquiry`, `Cancellation request`, `Product inquiry`, `Refund request`, `Technical issue` |
| Tipo       | Classificação supervisionada **multiclasse**                                                                 |
| Equilíbrio | Classes balanceadas: de 19,29% a 20,69% (razão de 1,07 entre a maior e a menor)                              |

---

## 1. Modelo candidato

### Principal: Regressão Logística multinomial

`sklearn.linear_model.LogisticRegression` (solver `lbfgs`, regularização L2).

Por que é adequada para o problema:

- **Feita para classificação multiclasse.** Estima a probabilidade de cada uma das 5 intenções e escolhe a
  maior. É o oposto da regressão linear da U-Tarefa 1, que produz um número contínuo sem significado de classe.
- **Funciona bem com texto vetorizado.** O `CountVectorizer` gera milhares de colunas esparsas (uma por palavra),
  e modelos lineares regularizados são o padrão consolidado para esse tipo de dado.
- **É interpretável.** Cada palavra tem um coeficiente por classe, então dá para explicar por que uma
  mensagem foi classificada como `Refund request`. Isso ajuda na análise de erros e nos testes adversariais,
  em que será preciso entender quais palavras manipulam a decisão do modelo.
- **Devolve probabilidades** (`predict_proba`). A rota `/predict` poderá retornar a confiança da previsão e
  responder "intenção indefinida" quando a confiança for baixa, em vez de chutar uma classe.
- **Rápida e leve.** Treina em segundos com 8.469 registros e não exige GPU nem infraestrutura extra no Render.
- **Classes balanceadas** dispensam reamostragem ou `class_weight`. O overfitting é controlado pelo
  hiperparâmetro de regularização `C`.

### Comparação: LinearSVC (SVM linear)

`sklearn.svm.LinearSVC` também é um modelo linear forte para texto esparso e será treinado com a mesma
representação para comparação. A desvantagem é não fornecer probabilidades nativamente (seria preciso
`CalibratedClassifierCV`), por isso fica como segunda opção.

### Referência mínima: DummyClassifier

Um `DummyClassifier(strategy="most_frequent")` sempre prevê a classe mais frequente e acerta cerca de
**20,7%**. Qualquer modelo só será considerado útil se superar claramente essa referência.

---

## 2. Representação do texto: CountVectorizer

O `CountVectorizer` (`sklearn.feature_extraction.text`) transforma cada mensagem em um vetor de **contagem de
palavras** (bag-of-words): cada coluna é um termo do vocabulário e o valor é quantas vezes ele aparece na
mensagem.

Motivos da escolha:

- **Simples e transparente.** Cada atributo é uma palavra ou expressão legível, o que combina com a
  interpretação dos coeficientes da Regressão Logística.
- **Matriz esparsa e eficiente.** Guarda só as contagens diferentes de zero, então o vocabulário pode ser
  grande sem estourar a memória.
- **Adequada ao tamanho do dataset.** Com 8.469 mensagens curtas em inglês, uma representação clássica é
  suficiente como primeira abordagem e serve de referência para comparar depois com TF-IDF ou embeddings.
- **Fácil de colocar em produção.** Vetorizador e modelo ficam no mesmo `Pipeline`, salvo em um único arquivo
  e carregado pela API.

Configuração planejada (ajustada por validação cruzada):

| Parâmetro       | Valor inicial      | Motivo                                                                                       |
| --------------- | ------------------ | -------------------------------------------------------------------------------------------- |
| `lowercase`     | `True`             | "Refund" e "refund" viram o mesmo termo                                                      |
| `strip_accents` | `"unicode"`        | Normaliza caracteres acentuados                                                              |
| `stop_words`    | `"english"`        | Remove palavras sem conteúdo (the, and, is). O dataset está em inglês                        |
| `ngram_range`   | `(1, 2)`           | Captura expressões como "cancel subscription" e "not working"                                |
| `min_df`        | `2`                | Ignora termos que aparecem em uma única mensagem (ruído, erros de digitação)                 |
| `max_features`  | `20000`            | Limita o tamanho do vocabulário e o custo de memória                                         |

Cuidados:

- **Sem vazamento de dados:** o vocabulário é aprendido **só no conjunto de treino** (`fit` dentro do
  `Pipeline`) e apenas aplicado (`transform`) no teste e na API.
- **Placeholders do dataset** (`{product_purchased}` etc.) aparecem em todas as classes (EDA, hipótese formal
  2). Eles serão substituídos por um token genérico ou removidos antes da vetorização.
- **Palavras desconhecidas** na API são ignoradas pelo vetorizador. Isso é robusto contra entradas
  estranhas, mas também é uma superfície de ataque (ver seção 5).

---

## 3. Treinamento, avaliação e integração (TP4)

1. Separação **estratificada** treino/teste 80/20 (`random_state=42`).
2. `GridSearchCV` com `StratifiedKFold` (5 folds) sobre `C`, `ngram_range` e `min_df`, otimizando **F1 macro**.
3. Métricas no teste: **acurácia, precisão, recall e F1 por classe e macro, e matriz de confusão**, sempre
   comparadas ao `DummyClassifier`.
4. O `Pipeline` treinado é salvo com `joblib` e carregado pela rota `/predict`, que passa a devolver
   `intent` + `confidence` e a gravar a previsão com o `owner_id` do usuário (mantendo o controle de BOLA).
5. Segurança da integração: o modelo é carregado **somente** de um arquivo versionado no repositório
   (`joblib`/pickle executa código ao carregar, então nunca será aceito um modelo enviado por usuário). Os
   modelos Pydantic continuam com `extra='forbid'`. Também está planejado limitar o tamanho de `message`
   (hoje não há limite), para reduzir o custo de vetorização de entradas muito grandes.

---

## 4. Risco identificado: o texto pode não separar as classes

O EDA já indicava que características simples do texto não diferenciam as intenções: os testes de
Mann-Whitney não encontraram diferença no comprimento nem na quantidade de placeholders entre classes. Uma
**verificação preliminar** (fora do notebook, só para planejamento, não é o modelo final) com
`CountVectorizer` + modelos lineares e separação estratificada 80/20 reforçou esse alerta:

| Entrada → Alvo                          | Modelo              | Acurácia | F1 macro |
| --------------------------------------- | ------------------- | :------: | :------: |
| `Ticket Description` → `Ticket Type`    | DummyClassifier     | 0,207    | 0,069    |
| `Ticket Description` → `Ticket Type`    | Regressão Logística | 0,207    | 0,206    |
| `Ticket Description` → `Ticket Type`    | LinearSVC           | 0,204    | 0,204    |
| `Ticket Subject` → `Ticket Type`        | Regressão Logística | 0,178    | 0,173    |
| `Ticket Description` → `Ticket Subject` | Regressão Logística | 0,074    | 0,073    |

Os modelos ficaram no nível do acaso (1/5 = 20% para `Ticket Type`; 1/16 = 6,25% para `Ticket Subject`). Como
o dataset é **sintético**, o rótulo parece ter sido sorteado de forma independente do texto.

Plano de mitigação:

1. No TP4, confirmar o resultado com validação cruzada e relatar o desempenho com transparência, sempre
   comparado à referência mínima.
2. Se a confirmação se mantiver, discutir com o professor uma destas opções: manter o dataset e focar a
   avaliação no pipeline e na segurança da integração, ou usar um dataset de atendimento com intenções
   rotuladas de forma consistente (por exemplo, o *Bitext Customer Support*, com 27 intenções), mantendo a
   mesma arquitetura (`CountVectorizer` + Regressão Logística + API).

---

## 5. Alvo para o teste adversarial (TP4/TP5)

API da equipe autorizada como alvo das atividades de pentest, disponível em dois endereços:

| Item                    | Render                                                                         | Cloudflare Tunnel                                                         |
| ----------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **URL do alvo**         | **https://tp03-pb.onrender.com**                                               | **https://logic-first-mary-pcs.trycloudflare.com**                        |
| Documentação interativa | https://tp03-pb.onrender.com/docs                                              | https://logic-first-mary-pcs.trycloudflare.com/docs                       |
| Hospedagem              | Render (web service `tp03-pb`, região Oregon), HTTPS fornecido pela plataforma | API da equipe exposta por um túnel da Cloudflare, HTTPS fornecido pela Cloudflare |
| Endereço IP             | Não fixo: o Render usa IPs compartilhados e dinâmicos                          | Não exposto: o tráfego passa pela rede da Cloudflare                      |

Nos dois casos o alvo é identificado pelo **hostname**, não por IP. Código-fonte:
https://github.com/infnet26-alberto-johanna-samuel-uendel/tp03 (o Render faz deploy da branch `main`).

> O endereço `trycloudflare.com` é um *quick tunnel* da Cloudflare: ele só responde enquanto a máquina que
> hospeda a API e o `cloudflared` estiverem ligados, e o subdomínio muda toda vez que o túnel é reiniciado.
> Se o endereço mudar, este documento será atualizado e o novo endereço informado à equipe atacante.

Regras de engajamento:

- **Em escopo:** `GET /health`, `POST /auth/token`, `POST /predict`, `GET /predictions`,
  `GET /predictions/{id}`, `GET /docs` e `GET /openapi.json`, com os usuários de teste documentados no
  README.
- **Vetores esperados:** autenticação e JWT, BOLA/IDOR, validação de entrada, contorno de rate limit e, a
  partir do TP4, ataques ao modelo (mensagens adversariais para forçar uma intenção errada, prompt injection
  no campo de texto).
- **Fora de escopo:** negação de serviço ou testes volumétricos (o `/auth/token` tem limite de 10
  requisições/min por IP), a infraestrutura do Render, da Cloudflare e do GitHub, a máquina que hospeda o
  túnel, contas e dados de terceiros e engenharia social.
- **Janela:** durante as atividades do TP4/TP5. Os findings devem ser reportados à equipe.
