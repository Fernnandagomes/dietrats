# 🗄️ DietRats — Documentação do Banco de Dados (MongoDB + Redis)

O banco de dados do DietRats é **não relacional (NoSQL)**, combinando a persistência no **MongoDB Atlas** com o desempenho e estruturas avançadas em memória no **Redis Cloud**.

---

## 🍃 MongoDB Atlas (Armazenamento Principal)

O banco de dados principal é o `dietrats` no MongoDB Atlas, utilizando o padrão **Embedded Schema (Documentos Embutidos)**.

### Coleções Principais (3 Coleções)

| Coleção | Descrição |
|---|---|
| `usuarios` | Perfis dos atletas cadastrados |
| `grupos` | Grupos de desafio entre amigos |
| `registrosdiarios` | Refeições postadas com `reacoes[]` e `comentarios[]` embutidos |

---

## 🔴 Redis Cloud (Cache, Estruturas Comuns e Probabilísticas)

O Redis é utilizado em memória RAM para otimização de performance e estatísticas em tempo real:

### 1. Estruturas Comuns (Data Structures)
* **STRING (Cache)**:
  - `hall_da_fama`: Guarda em cache por 10 minutos a resposta da agregação global do Top 5 Atletas.
* **ZSET (Sorted Set - Ranking e Frequência)**:
  - `ranking:grupo:<grupo_id>`: Mantém a pontuação em tempo real dos atletas (`ZADD` / `ZREVRANGE`).
  - `freq:refeicoes:grupo:<grupo_id>`: Incrementa a frequência dos tipos de refeição (`ZINCRBY`) para descobrir qual tipo é mais frequente no grupo (Café, Almoço, Jantar, etc).

### 2. Estrutura Probabilística (Probabilistic)
* **HyperLogLog (HLL)**:
  - `hll:variedade:grupo:<grupo_id>`: Utiliza o comando `PFADD` e `PFCOUNT` para estimar a **quantidade de pratos/descrições de refeições únicas** registradas no grupo, gastando apenas ~12KB fixos de memória RAM.


---

## 👤 Coleção: `usuarios`

Armazena o perfil completo de cada atleta cadastrado no app.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único gerado pelo MongoDB |
| `nome` | String | ✅ | Nome completo do usuário |
| `email` | String | ✅ | E-mail (único — usado no login) |
| `senha` | String | ✅ | Senha de acesso |
| `avatar` | String | ✅ | Emoji escolhido como avatar (ex: 💪) |
| `pontos_consistencia` | Int | ✅ | Pontuação total acumulada (cada refeição = +10 pts) |
| `streak_atual` | Int | ✅ | Dias consecutivos com refeição registrada |
| `grupo_id` | ObjectId | ❌ | Referência ao grupo do usuário (pode ser nulo) |
| `foto_url` | String | ❌ | Foto de perfil codificada em Base64 |

**Índice único:** `email`

---

## 👥 Coleção: `grupos`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único do grupo |
| `nome` | String | ✅ | Nome do grupo |
| `descricao` | String | ❌ | Descrição do grupo |
| `codigo_acesso` | String | ✅ | Código secreto para entrar (único) |
| `criador_id` | ObjectId | ✅ | Usuário que criou o grupo |
| `foto_url` | String | ❌ | Foto de capa em Base64 |

---

## 🍽️ Coleção: `registrosdiarios`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único da postagem |
| `usuario_id` | ObjectId | ✅ | Usuário que postou |
| `tipo` | String | ✅ | Café / Almoço / Jantar |
| `descricao` | String | ✅ | O que foi comido |
| `legenda` | String | ❌ | Legenda opcional |
| `foto_url` | String | ✅ | Foto do prato em Base64 (obrigatória) |
| `data` | String | ✅ | Data no formato YYYY-MM-DD |
| `data_criacao` | DateTime | ✅ | Timestamp de criação |

**Regras:** Ao postar, o usuário ganha +10 pontos e o streak é recalculado.

---

## ❤️ Coleção: `reacoes`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único |
| `registro_id` | ObjectId | ✅ | Postagem que recebeu a reação |
| `usuario_id` | ObjectId | ✅ | Usuário que reagiu |
| `tipo` | String | ✅ | Emoji (💪, 🔥, 😍, 👏) |

**Toggle:** clicar no mesmo emoji remove a reação.

---

## 💬 Coleção: `comentarios`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único |
| `registro_id` | ObjectId | ✅ | Postagem comentada |
| `usuario_id` | ObjectId | ✅ | Usuário que comentou |
| `texto` | String | ✅ | Texto do comentário |
| `data_criacao` | DateTime | ✅ | Timestamp |

---

## 🔔 Coleção: `notificacoes`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | ✅ | Identificador único |
| `destinatario_id` | ObjectId | ✅ | Usuário que recebe a notificação |
| `tipo` | String | ✅ | "reacao" ou "comentario" |
| `texto` | String | ✅ | Mensagem da notificação |
| `lida` | Boolean | ✅ | false = não lida, true = lida |
| `data_criacao` | DateTime | ✅ | Timestamp |

---

## ⚙️ Configuração do Atlas

- **Banco:** dietrats
- **String de Conexão:** variável de ambiente `MONGO_URI` ou `st.secrets["MONGO_URI"]`
