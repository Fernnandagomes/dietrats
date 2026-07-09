# 🗄️ DietRats — Documentação do Banco de Dados (MongoDB)

O banco de dados do DietRats é **não relacional (NoSQL)**, hospedado no **MongoDB Atlas**.
O nome do banco é `dietrats` e ele contém **6 coleções (collections)**.

---

## 📁 Visão Geral das Coleções

| Coleção | Descrição |
|---|---|
| `usuarios` | Perfis dos atletas cadastrados |
| `grupos` | Grupos de desafio entre amigos |
| `registrosdiarios` | Refeições postadas pelos usuários |
| `reacoes` | Reações de emoji em postagens |
| `comentarios` | Comentários em postagens |
| `notificacoes` | Alertas e notificações do sistema |

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
