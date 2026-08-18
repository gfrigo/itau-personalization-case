# SOLUTION.md — Personalization Service

## Como rodar o projeto

**Local (sem Docker):**
- `uv sync` — instala dependências
- Copiar `.env.example` para `.env`
- `uv run uvicorn itau_purchase_propensity.main:app --reload`

**Via Docker (recomendado):**
- `make build` — builda a imagem
- `make run` — sobe o container (porta 8000, lê `.env`)
- `make logs` — acompanha os logs
- `make stop` — para o container
- Swagger interativo: `http://localhost:8000/docs`

**Testes:**
- `uv run pytest` — unitários + integração
- `uv run ruff check .` e `uv run ruff format --check .` — lint/formatação (mesmo que o CI roda)

---

## 1. Processamento / ingestão de dados

- Processamento feito em memória, na classe `DataRepository`, executado **uma vez no startup** da API (evento `lifespan` do FastAPI)
- **Por quê nesse formato**: os dados (`events.csv`, `products.csv`) são estáticos e não há fase de treinamento neste case — não há necessidade de um pipeline de ingestão contínuo, nem de banco de dados
- No `__init__`, os CSVs são transformados em estruturas de lookup O(1) (dicts), evitando reprocessar `pandas` a cada requisição:
  - `products`: metadados do produto
  - `interaction_counts`: contagem de interações usuário-produto
  - `user_affinity`: categoria de maior afinidade por usuário
  - `known_users`: quem tem histórico (usado na detecção de cold start)
  - `trending_scores`: popularidade recente ponderada por funil (usado no fallback de cold start)
- **Trade-off assumido**: o cálculo é refeito a cada novo container/restart. Como o volume de dados é pequeno e o dataset é estático, isso não é um problema neste escopo. Uma alternativa (pré-computar os resultados e persistir em S3/Parquet, servindo só leitura no startup) foi considerada e descartada — reduziria custo de CPU no startup, mas adicionaria uma dependência externa (S3, IAM) sem ganho de performance perceptível no request em si, dado o tamanho do dataset
- Peso de funil (`EVENT_WEIGHTS`: view=1, click=2, add_to_cart=3, purchase=5) é uma **convenção**, não uma estimativa treinada — documentado no código

## 2. Cálculo de features

- As 5 features exigidas pelo `model_card.json` são calculadas em `domain/features.py`, na ordem exata esperada pelo modelo (`to_feature_row` respeita `feature_cols` do `model.pkl` — crítico pro `sklearn`, que não valida nomes de coluna)
- `interactions`, `price`, `avg_rating`, `popularity_score`: leitura direta das estruturas pré-processadas
- `user_affinity_match`: derivada de `events.csv` + `products.csv` — para cada usuário, identifica a categoria com maior número de interações históricas (join por `product_id`, `groupby` por categoria, pega a maior contagem); compara com a categoria do produto avaliado
- **Critério de desempate**: nenhum implementado explicitamente (o `pandas` mantém a primeira ocorrência em caso de contagem igual) — variação aceitável dentro do que o model card permite
- Usuário sem histórico naturalmente recebe `user_affinity_match = 0` (comparação com `None` é `False`) — sem `if` especial para esse caso

## 3. Endpoint de recomendação

- `GET /recommendations/{user_id}`: roda o modelo para todos os produtos do catálogo, ranqueia por score (usuário conhecido) e retorna os top N (`TOP_N_RECOMMENDATIONS`, configurável via `.env`)
- `GET /health`: health check simples, usado também pelo target group do ALB na AWS
- Campo `score` é **opcional** (`float | None`) no schema de resposta: em cold start, vem `null` — decisão tomada para não expor ao consumidor um número de baixa confiança calculado sobre features quase todas zeradas

## 4. Cold start

- **Detecção**: `user_id` fora do conjunto de usuários conhecidos em `events.csv`
- **Estratégia**: ranking por popularidade agregada ponderada por funil (últimos 30 dias, ancorados no último timestamp do dataset — não em `now()`, já que o dado é um snapshot estático), combinada com uma **cota de diversidade por categoria** (garante ao menos 1 produto de cada categoria antes de completar com os demais mais populares)
- **Por quê essa estratégia**: não há formulário de onboarding, cookies de terceiros ou integração com redes sociais disponíveis para inferir interesse — popularidade agregada é o único sinal existente no dado fornecido
- O modelo **não é executado** para usuários em cold start — o ranking não usa o score, então calcular seria custo de CPU sem uso real

## 5. Testes

- **Unitários**: cálculo de features (`test_features.py`), estruturas do repositório (`test_repository.py`), lógica de ranking e cold start (`test_recommender.py`), endpoint isolado (`test_recommendations_endpoint.py`)
- **Integração** (`test_integration.py`): sobe a aplicação real via `TestClient`, sem mockar camadas internas — valida `/health`, usuário conhecido e cold start ponta a ponta
- Fixture de dados (`conftest.py`) desenhada propositalmente para que o ranking puro por trending divirja do ranking com cota de categoria — evita que o teste passe "por acaso"

## 6. Observabilidade

**Hoje:**
- Logs estruturados em JSON (`core/logging.py`), incluindo `user_id`, `cold_start` e `duration_ms` na requisição principal
- Métricas expostas em `/metrics`, formato Prometheus (`prometheus_client`):
  - `http_requests_total` / `http_request_duration_seconds` — contagem e latência por rota (label de path é o template da rota, ex: `/recommendations/{user_id}`, evitando alta cardinalidade)
  - `recommendations_total` e `recommendations_cold_start_total` — permite calcular taxa de cold start
  - `model_score` — distribuição dos scores do modelo (só para usuários conhecidos)

**O que adicionaria com mais tempo:**
- Log estruturado também no caminho de erro (hoje só o caminho de sucesso é logado — uma exceção não gera log específico)
- Tracing distribuído (ex: OpenTelemetry) para correlacionar logs/métricas por request-id entre múltiplos serviços
- Alertas sobre taxa de erro e p95 de latência (hoje a métrica existe, mas não há regra de alerta configurada)
- Métrica de drift do modelo (comparar distribuição de scores/features ao longo do tempo)

## 7. Infraestrutura (CI/CD + AWS)

- **CI/CD** (`.github/workflows/deploy.yaml`): disparo manual (`workflow_dispatch`), roda lint + testes antes de qualquer deploy; build/push da imagem para ECR; Terraform aplica primeiro só o ECR (bootstrap, resolve o "ovo e galinha" entre imagem e repositório) e depois o restante da infra
- **Arquitetura AWS** (Terraform em `infra/`): ALB público → ECS Fargate (Task com 1 execução, sem servidor gerenciado) → ECR. Usa VPC/subnets default da conta para simplificar
- Diagrama da arquitetura: `[inserir imagem/link do Excalidraw aqui]`

**Trade-offs assumidos na infra:**
- `desired_count = 1` no ECS — sem redundância; aceitável no escopo do case, mas geraria downtime em caso de falha da task em produção real
- Sem HTTPS no ALB (só porta 80) — precisaria de um listener 443 + certificado ACM
- Task com IP público direto (sem NAT Gateway) — simplifica a rede, mas não é o padrão recomendado de produção (subnet privada + NAT)
- Uma única IAM role (`execution_role`) — suficiente porque a aplicação não acessa outros serviços AWS; se precisasse, seria necessária uma `task_role` separada

## O que eu faria diferente com mais tempo

- Redundância (`desired_count >= 2`) e HTTPS no ALB
- Persistir as features pré-processadas fora do container (ex: S3/Parquet), para não recalcular a cada novo container subindo
- Tracing distribuído e alertas sobre as métricas já expostas
- Validar a versão do `scikit-learn` usada no ambiente de serving contra a versão usada no treino do modelo (hoje há um `InconsistentVersionWarning` nos logs — modelo treinado em 1.8.0, ambiente com 1.9.0)
