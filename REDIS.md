# Redis no DietRats — Documentação Técnica

O DietRats utiliza o Redis Cloud em memória RAM para otimizar o desempenho do sistema e fornecer métricas em tempo real sem sobrecarregar a base de dados principal (MongoDB Atlas).

---

## 1. Cache de Leituras (Estrutura: STRING)

* **Uso no Sistema**: Cache da agregação do Hall da Fama (`get_hall_da_fama`).
* **Tipo de Dado**: STRING (JSON serializado).
* **Comandos Utilizados**: `GET`, `SET ex 600`.
* **Justificativa**: A lista dos 5 atletas mais consistentes do aplicativo requer a execução de uma agregação com `$group`, `$sort` e `$lookup`. O Redis armazena o resultado por 10 minutos (Cache-Aside). A resposta é servida em 2ms via Redis em vez de 500ms no MongoDB.

---

## 2. Estruturas Comuns (Estrutura: ZSET - Sorted Set)

### A. Ranking de Consistência do Grupo
* **Uso**: Ordenação e atualização da pontuação dos membros do grupo.
* **Chave**: `ranking:grupo:<grupo_id>`
* **Comandos Utilizados**: `ZADD`, `ZREVRANGE`.
* **Justificativa**: Mantém os membros ordenados por pontuação nativamente. Cada refeição registrada incrementa a pontuação via `ZADD`. O ranking é consultado em complexidade O(log N + M) sem realizar varreduras no MongoDB.

### B. Frequência dos Tipos de Refeição
* **Uso**: Identifica o tipo de refeição mais frequente no grupo.
* **Chave**: `freq:refeicoes:grupo:<grupo_id>`
* **Comandos Utilizados**: `ZINCRBY`, `ZREVRANGE`.
* **Justificativa**: Evita a execução repetida de agrupamentos por tipo no MongoDB a cada carregamento de página, incrementando a contagem de forma atômica no Redis.

---

## 3. Estrutura Probabilística (Estrutura: HyperLogLog)

* **Uso**: Estimativa da quantidade de ingredientes e alimentos distintos consumidos no grupo.
* **Chave**: `hll:variedade:grupo:<grupo_id>`
* **Comandos Utilizados**: `PFADD`, `PFCOUNT`.
* **Funcionamento**: 
  1. A descrição do prato é processada para extrair os termos relevantes (ingredientes).
  2. Cada ingrediente é inserido no HyperLogLog via `PFADD`.
  3. `PFCOUNT` retorna a estimativa de cardinalidade de alimentos distintos.
* **Justificativa Técnica**: Um `SET` convencional armazenaria todas as strings na memória RAM, escalando o consumo desproporcionalmente. O HyperLogLog estima a cardinalidade com taxa de erro de ~0,81% mantendo consumo de memória constante fixado em no máximo 12KB.

---

## 4. Resumo de Comandos Redis

| Recurso | Estrutura | Comandos Redis |
|---|---|---|
| Hall da Fama | STRING | `GET`, `SET` |
| Ranking do Grupo | ZSET | `ZADD`, `ZREVRANGE` |
| Refeição Frequente | ZSET | `ZINCRBY`, `ZREVRANGE` |
| Alimentos Únicos | HYPERLOGLOG | `PFADD`, `PFCOUNT` |
