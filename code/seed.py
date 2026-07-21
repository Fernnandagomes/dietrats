import os
import sys
import datetime
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

MOCK_IMG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def seed():
    import streamlit as st
    try:
        mongo_uri = st.secrets["MONGO_URI"]
    except Exception:
        mongo_uri = os.environ.get("MONGO_URI", "")

    if not mongo_uri:
        mongo_uri = input("Cole sua String de Conexao MongoDB Atlas: ").strip()

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=4000)
        client.server_info()
        db = client["dietrats"]
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        sys.exit(1)

    print("Conectado ao MongoDB. Limpando colecoes antigas...")
    db["usuarios"].drop()
    db["grupos"].drop()
    db["registrosdiarios"].drop()

    db["usuarios"].create_index([("email", ASCENDING)], unique=True)
    db["grupos"].create_index([("codigo_acesso", ASCENDING)], unique=True)

    import redis_cache
    import graph_db

    redis_client = redis_cache.get_redis()
    neo4j_driver = graph_db.get_neo4j_driver()

    if redis_client:
        print("Redis conectado. Limpando base de cache...")
        redis_client.flushall()

    if neo4j_driver:
        print("Neo4j conectado. Limpando grafo antigo...")
        with neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    print("\nCriando dados de teste...")

    grupo1_id = db["grupos"].insert_one({
        "nome": "Projeto Verão",
        "descricao": "Foco na consistência alimentar e treinos intensos.",
        "codigo_acesso": "12345678",
        "criador_id": ObjectId(),
    }).inserted_id

    grupo2_id = db["grupos"].insert_one({
        "nome": "Foco Total",
        "descricao": "Outro grupo para gerar compatibilidades cruzadas.",
        "codigo_acesso": "87654321",
        "criador_id": ObjectId(),
    }).inserted_id

    atletas = [
        {
            "nome": "Ana Clara",
            "email": "ana@gmail.com",
            "senha": "123",
            "avatar": "🥗",
            "grupo_id": grupo1_id,
            "alimentos": ["frango", "arroz", "batata", "salada", "ovo", "whey"],
            "streak": 5, "pontos": 120
        },
        {
            "nome": "João Silva",
            "email": "joao@gmail.com",
            "senha": "123",
            "avatar": "💪",
            "grupo_id": grupo1_id,
            "alimentos": ["arroz", "carne", "feijao", "banana", "aveia", "ovo"],
            "streak": 3, "pontos": 80
        },
        {
            "nome": "Carlos Reis",
            "email": "carlos@gmail.com",
            "senha": "123",
            "avatar": "🔥",
            "grupo_id": grupo2_id,
            "alimentos": ["frango", "arroz", "batata", "ovo", "salada", "creatina"],
            "streak": 10, "pontos": 250
        },
        {
            "nome": "Mariana Souza",
            "email": "mariana@gmail.com",
            "senha": "123",
            "avatar": "🥦",
            "grupo_id": grupo2_id,
            "alimentos": ["peixe", "mandioca", "salada", "maça", "abacate", "chia"],
            "streak": 2, "pontos": 40
        }
    ]

    for a in atletas:
        u_doc = {
            "nome": a["nome"],
            "email": a["email"],
            "senha": a["senha"],
            "avatar": a["avatar"],
            "pontos_consistencia": a["pontos"],
            "streak_atual": a["streak"],
            "grupo_id": a["grupo_id"],
            "foto_url": None,
            "ultimo_acesso_notificacoes": None
        }
        u_id = db["usuarios"].insert_one(u_doc).inserted_id

        g_name = "Projeto Verão" if a["grupo_id"] == grupo1_id else "Foco Total"
        graph_db.sync_usuario_grupo_neo4j(neo4j_driver, u_id, a["nome"], a["grupo_id"], g_name)
        graph_db.registrar_alimento_consumido_neo4j(neo4j_driver, u_id, a["alimentos"])

        if redis_client:
            redis_cache.atualizar_pontos_zset(redis_client, a["grupo_id"], a["nome"], a["pontos"])

        print(f"   Criando refeições para {a['nome']}...")
        for i, alimento in enumerate(a["alimentos"][:3]):
            data_criacao = datetime.datetime.now() - datetime.timedelta(days=i)
            tipo_ref = "Café" if i == 0 else "Almoço" if i == 1 else "Jantar"
            
            db["registrosdiarios"].insert_one({
                "usuario_id": u_id,
                "tipo": tipo_ref,
                "descricao": f"Consumindo {alimento} e arroz para bater os macros.",
                "foto_url": MOCK_IMG,
                "legenda": "Foco na dieta!",
                "data": data_criacao.strftime("%Y-%m-%d"),
                "data_criacao": data_criacao,
                "reacoes": [],
                "comentarios": []
            })

            if redis_client:
                redis_cache.registrar_tipo_refeicao(redis_client, a["grupo_id"], tipo_ref, f"{alimento} arroz")

    print("\n" + "=" * 55)
    print("  Banco MongoDB e estruturas do Redis/Neo4j populados!")
    print("  Use as seguintes credenciais para testar no App:")
    print("  - Ana Clara: ana@gmail.com  | senha: 123")
    print("  - João Silva: joao@gmail.com | senha: 123")
    print("  - Carlos Reis: carlos@gmail.com | senha: 123")
    print("  - Mariana Souza: mariana@gmail.com | senha: 123")
    print("=" * 55)


if __name__ == "__main__":
    seed()
