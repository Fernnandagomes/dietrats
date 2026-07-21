import datetime
from neo4j import GraphDatabase
import streamlit as st


def get_neo4j_driver():
    """Retorna o driver de conexão com o Neo4j AuraDB usando st.secrets."""
    try:
        uri = st.secrets.get("NEO4J_URI")
        user = st.secrets.get("NEO4J_USER", "neo4j")
        password = st.secrets.get("NEO4J_PASSWORD")

        if not uri or not password:
            return None

        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


def sync_usuario_grupo_neo4j(driver, usuario_id, nome, grupo_id, grupo_nome):
    """Garante que o Usuário e seu Grupo existam no Grafo e estejam conectados."""
    if not driver:
        return
    query = """
    MERGE (u:Usuario {id: $usuario_id})
    SET u.nome = $nome
    
    WITH u
    WHERE $grupo_id IS NOT NULL
    MERGE (g:Grupo {id: $grupo_id})
    SET g.nome = $grupo_nome
    MERGE (u)-[:MEMBRO_DE]->(g)
    """
    try:
        with driver.session() as session:
            session.run(
                query,
                usuario_id=str(usuario_id),
                nome=nome,
                grupo_id=str(grupo_id) if grupo_id else None,
                grupo_nome=grupo_nome if grupo_nome else ""
            )
    except Exception:
        pass


def registrar_alimento_consumido_neo4j(driver, usuario_id, ingredientes):
    """Conecta o usuário aos alimentos/ingredientes que ele consome."""
    if not driver or not ingredientes:
        return
    query = """
    MATCH (u:Usuario {id: $usuario_id})
    UNWIND $ingredientes AS ing_nome
    MERGE (i:Alimento {nome: ing_nome})
    MERGE (u)-[r:CONSUMIU]->(i)
    ON CREATE SET r.vezes = 1
    ON MATCH SET r.vezes = r.vezes + 1
    """
    try:
        with driver.session() as session:
            session.run(query, usuario_id=str(usuario_id), ingredientes=ingredientes)
    except Exception:
        pass


def obter_recomendacoes_compatibilidade(driver, usuario_id):
    """
    Recomenda usuários de outros grupos que consomem ingredientes parecidos (Jaccard Similarity).
    """
    if not driver:
        return []
    query = """
    MATCH (u1:Usuario {id: $usuario_id})-[:CONSUMIU]->(i:Alimento)<-[:CONSUMIU]-(u2:Usuario)
    WHERE u1 <> u2
    
    // Filtra pessoas que não estão no mesmo grupo
    OPTIONAL MATCH (u1)-[:MEMBRO_DE]->(g:Grupo)<-[:MEMBRO_DE]->(u2)
    WITH u1, u2, count(i) AS intersecao, g
    WHERE g IS NULL
    
    // Calcula união de alimentos consumidos
    MATCH (u1)-[:CONSUMIU]->(i1:Alimento)
    WITH u1, u2, intersecao, count(distinct i1) AS total_u1
    MATCH (u2)-[:CONSUMIU]->(i2:Alimento)
    WITH u2, intersecao, total_u1, count(distinct i2) AS total_u2
    
    WITH u2, (toInteger(intersecao) * 1.0) / (total_u1 + total_u2 - intersecao) AS jaccard_score
    WHERE jaccard_score > 0.0
    RETURN u2.id AS id, u2.nome AS nome, jaccard_score
    ORDER BY jaccard_score DESC
    LIMIT 5
    """
    try:
        with driver.session() as session:
            result = session.run(query, usuario_id=str(usuario_id))
            return [
                {
                    "id": record["id"],
                    "nome": record["nome"],
                    "compatibilidade": int(record["jaccard_score"] * 100)
                }
                for record in result
            ]
    except Exception:
        return []


def criar_desafio_duelo(driver, desafiante_id, desafiado_id):
    """Cria um relacionamento de DESAFIO pendente entre dois usuários."""
    if not driver:
        return
    query = """
    MATCH (u1:Usuario {id: $desafiante_id}), (u2:Usuario {id: $desafiado_id})
    MERGE (u1)-[r:DESAFIOU]->(u2)
    SET r.status = "pendente",
        r.data_criacao = datetime()
    """
    try:
        with driver.session() as session:
            session.run(query, desafiante_id=str(desafiante_id), desafiado_id=str(desafiado_id))
    except Exception:
        pass


def aceitar_desafio_duelo(driver, desafiado_id, desafiante_id):
    """Aceita um duelo pendente, ativando-o por 3 dias."""
    if not driver:
        return
    data_fim = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    query = """
    MATCH (u1:Usuario {id: $desafiante_id})-[r:DESAFIOU]->(u2:Usuario {id: $desabiado_id})
    SET r.status = "ativo",
        r.data_inicio = datetime(),
        r.data_fim = $data_fim,
        r.pontos_u1 = 0,
        r.pontos_u2 = 0
    """
    try:
        with driver.session() as session:
            session.run(query, desafiante_id=str(desafiante_id), desabiado_id=str(desabiado_id), data_fim=data_fim)
    except Exception:
        pass


def recusar_desafio_duelo(driver, desafiado_id, desafiante_id):
    """Exclui o relacionamento de desafio pendente."""
    if not driver:
        return
    query = """
    MATCH (u1:Usuario {id: $desafiante_id})-[r:DESAFIOU]->(u2:Usuario {id: $desabiado_id})
    WHERE r.status = "pendente"
    DELETE r
    """
    try:
        with driver.session() as session:
            session.run(query, desafiante_id=str(desafiante_id), desabiado_id=str(desabiado_id))
    except Exception:
        pass


def obter_duelos_usuario(driver, usuario_id):
    """Retorna os duelos pendentes, ativos e concluídos relacionados ao usuário."""
    duelos = {"pendentes": [], "ativos": [], "concluidos": []}
    if not driver:
        return duelos

    query = """
    MATCH (u1:Usuario)-[r:DESAFIOU]-(u2:Usuario)
    WHERE u1.id = $usuario_id
    RETURN r.status AS status,
           r.data_fim AS data_fim,
           r.pontos_u1 AS pontos_u1,
           r.pontos_u2 AS pontos_u2,
           r.vencedor AS vencedor,
           u1.id AS u1_id, u1.nome AS u1_nome,
           u2.id AS u2_id, u2.nome AS u2_nome,
           startNode(r) = u1 AS sou_desafiante
    """
    try:
        with driver.session() as session:
            result = session.run(query, usuario_id=str(usuario_id))
            for record in result:
                status = record["status"]
                oponente_nome = record["u2_nome"]
                oponente_id = record["u2_id"]

                info = {
                    "oponente_id": oponente_id,
                    "oponente_nome": oponente_nome,
                    "sou_desafiante": record["sou_desafiante"],
                    "data_fim": record["data_fim"],
                    "pontos_meus": record["pontos_u1"] if record["sou_desafiante"] else record["pontos_u2"],
                    "pontos_deles": record["pontos_u2"] if record["sou_desafiante"] else record["pontos_u1"],
                    "vencedor": record["vencedor"]
                }

                if status == "pendente":
                    duelos["pendentes"].append(info)
                elif status == "ativo":
                    duelos["ativos"].append(info)
                elif status == "concluido":
                    duelos["concluidos"].append(info)
    except Exception:
        pass
    return duelos


def atualizar_duelos_ativos(driver, db):
    """Atualiza a pontuação e encerra duelos vencidos com base nas refeições do MongoDB."""
    if not driver or not db:
        return
    from bson import ObjectId
    query_ativos = """
    MATCH (u1:Usuario)-[r:DESAFIOU]->(u2:Usuario)
    WHERE r.status = "ativo"
    RETURN r.data_fim AS data_fim, r.data_inicio AS data_inicio, u1.id AS u1_id, u2.id AS u2_id, id(r) AS rel_id
    """
    try:
        with driver.session() as session:
            result = session.run(query_ativos)
            hoje = datetime.datetime.now()

            for record in result:
                u1_id = record["u1_id"]
                u2_id = record["u2_id"]
                rel_id = record["rel_id"]
                data_inicio = record["data_inicio"]
                
                data_inicio_dt = datetime.datetime.fromisoformat(str(data_inicio)[:10])

                pontos_u1 = db["registrosdiarios"].count_documents({
                    "usuario_id": ObjectId(u1_id),
                    "data_criacao": {"$gte": data_inicio_dt}
                }) * 10

                pontos_u2 = db["registrosdiarios"].count_documents({
                    "usuario_id": ObjectId(u2_id),
                    "data_criacao": {"$gte": data_inicio_dt}
                }) * 10

                data_fim_dt = datetime.datetime.strptime(record["data_fim"], "%Y-%m-%d")
                
                if hoje > data_fim_dt:
                    vencedor = "Empate"
                    if pontos_u1 > pontos_u2:
                        vencedor = u1_id
                    elif pontos_u2 > pontos_u1:
                        vencedor = u2_id

                    session.run(
                        """
                        MATCH ()-[r]->() WHERE id(r) = $rel_id
                        SET r.status = "concluido",
                            r.pontos_u1 = $p1,
                            r.pontos_u2 = $p2,
                            r.vencedor = $vencedor
                        """,
                        rel_id=rel_id, p1=pontos_u1, p2=pontos_u2, vencedor=vencedor
                    )
                else:
                    session.run(
                        """
                        MATCH ()-[r]->() WHERE id(r) = $rel_id
                        SET r.pontos_u1 = $p1,
                            r.pontos_u2 = $p2
                        """,
                        rel_id=rel_id, p1=pontos_u1, p2=pontos_u2
                    )
    except Exception:
        pass
