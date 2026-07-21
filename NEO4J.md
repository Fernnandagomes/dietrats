# Neo4j no DietRats — Documentação Técnica do Grafo e Desafios

O DietRats utiliza o Neo4j AuraDB para gerenciar a rede de relacionamentos dos atletas e implementar o sistema social de recomendações de compatibilidade e duelos de consistência.

---

## 1. Modelagem do Grafo (Nós e Relacionamentos)

O grafo é composto pelas seguintes entidades e conexões:

* **Nós (Nodes)**:
  - `Usuario`: Identificado por `id` (ObjectId do MongoDB) e `nome`.
  - `Grupo`: Identificado por `id` (ObjectId do MongoDB) e `nome`.
  - `Alimento`: Identificado pelo `nome` do ingrediente.

* **Relacionamentos (Edges/Relationships)**:
  - `(Usuario)-[:MEMBRO_DE]->(Grupo)`: Indica o grupo a que o atleta pertence.
  - `(Usuario)-[:CONSUMIU {vezes: Integer}]->(Alimento)`: Mapeia o comportamento alimentar a partir das postagens.
  - `(Usuario)-[:DESAFIOU {status: String, data_inicio: Date, data_fim: Date, pontos_u1: Integer, pontos_u2: Integer, vencedor: String}]->(Usuario)`: Mapeia os duelos ativados entre atletas.

---

## 2. Recomendação por Similaridade (Jaccard Similarity)

A busca por usuários compatíveis ("Pessoas parecidas com você") utiliza a biblioteca Graph Data Science (GDS) de forma implícita através de consultas Cypher para calcular o índice de Jaccard:

$$\text{Jaccard}(U_1, U_2) = \frac{|I(U_1) \cap I(U_2)|}{|I(U_1) \cup I(U_2)|}$$

Onde $I(U)$ representa o conjunto de alimentos consumidos pelo usuário $U$.

* **Algoritmo**: O sistema encontra usuários de outros grupos que compartilham alimentos consumidos, calcula a interseção dos ingredientes dividida pela união dos ingredientes cadastrados de ambos, gerando uma pontuação de compatibilidade de 0 a 100%.

---

## 3. Fluxo de Negócio: Duelo de Consistência (3 dias)

1. **Desafio**: Um usuário envia uma proposta. Um relacionamento `DESAFIOU` com `status: "pendente"` é criado no grafo.
2. **Aceitação**: O desafiado aceita, o status passa para `ativo`, registrando a data de início e configurando o fim para 3 dias à frente.
3. **Sincronização**: O sistema verifica continuamente o número de refeições cadastradas no MongoDB para computar os pontos dos duelistas no Neo4j.
4. **Resolução**: Ao expirar os 3 dias, o vencedor é registrado e o duelo é marcado como `concluido`.
