import cache
from bson import ObjectId


def get_feed_com_interacoes(db, grupo_id, redis=None):
    """Retorna os registros diários do grupo enriquecidos com dados do autor."""
    group_user_ids = [
        u["_id"]
        for u in db["usuarios"].find({"grupo_id": ObjectId(grupo_id)}, {"_id": 1})
    ]

    pipeline = [
        {"$match": {"usuario_id": {"$in": group_user_ids}}},
        {"$addFields": {
            "reacoes": {"$ifNull": ["$reacoes", []]},
            "comentarios": {"$ifNull": ["$comentarios", []]}
        }},
        {"$lookup": {
            "from": "usuarios",
            "localField": "usuario_id",
            "foreignField": "_id",
            "as": "autor"
        }},
        {"$unwind": "$autor"},
        {"$project": {
            "usuario_id": 1,
            "tipo": 1,
            "descricao": 1,
            "legenda": 1,
            "foto_url": 1,
            "data": 1,
            "data_criacao": 1,
            "reacoes": 1,
            "comentarios": 1,
            "autor._id": 1,
            "autor.nome": 1,
            "autor.avatar": 1,
            "autor.foto_url": 1,
        }},
        {"$sort": {"data_criacao": -1}},
    ]

    return list(db["registrosdiarios"].aggregate(pipeline))


def get_notificacoes_pipeline(db, usuario_id, ultimo_acesso=None):
    """Calcula notificações em tempo real a partir de interações dos posts do usuário."""
    uid = ObjectId(usuario_id) if not isinstance(usuario_id, ObjectId) else usuario_id

    pipeline = [
        {"$match": {"usuario_id": uid}},
        {"$addFields": {
            "reacoes": {"$ifNull": ["$reacoes", []]},
            "comentarios": {"$ifNull": ["$comentarios", []]}
        }},
        {"$project": {
            "tipo": 1,
            "interacoes": {
                "$concatArrays": [
                    {"$map": {
                        "input": "$reacoes",
                        "as": "r",
                        "in": {
                            "tipo_evento": "reacao",
                            "usuario_id": "$$r.usuario_id",
                            "nome_interator": "$$r.nome",
                            "emoji": "$$r.tipo",
                            "texto": {"$concat": [
                                "$$r.nome", " reagiu com ", "$$r.tipo",
                                " na sua postagem de ", "$tipo", "."
                            ]},
                            "data": "$$r.data"
                        }
                    }},
                    {"$map": {
                        "input": "$comentarios",
                        "as": "c",
                        "in": {
                            "tipo_evento": "comentario",
                            "usuario_id": "$$c.usuario_id",
                            "nome_interator": "$$c.nome",
                            "emoji": "💬",
                            "texto": {"$concat": [
                                "$$c.nome", " comentou: \"", "$$c.texto", "\""
                            ]},
                            "data": "$$c.data"
                        }
                    }}
                ]
            }
        }},
        {"$unwind": "$interacoes"},
        {"$match": {"interacoes.usuario_id": {"$ne": uid}}},
        {"$sort": {"interacoes.data": -1}},
        {"$limit": 50},
        {"$project": {
            "_id": 0,
            "tipo_evento": "$interacoes.tipo_evento",
            "texto": "$interacoes.texto",
            "emoji": "$interacoes.emoji",
            "data": "$interacoes.data",
        }},
    ]

    results = list(db["registrosdiarios"].aggregate(pipeline))

    for item in results:
        if ultimo_acesso and item.get("data"):
            item["is_nova"] = item["data"] > ultimo_acesso
        else:
            item["is_nova"] = True

    return results


def get_hall_da_fama(db, redis=None):
    """Retorna os 5 usuários com maior número de refeições (com cache Redis de 10 min)."""
    return cache.get_cached(
        redis, "hall_da_fama", ttl_seconds=600,
        fetch_fn=lambda: _query_hall(db)
    )


def _query_hall(db):
    pipeline = [
        {"$group": {
            "_id": "$usuario_id",
            "total_refeicoes": {"$sum": 1},
        }},
        {"$sort": {"total_refeicoes": -1}},
        {"$limit": 5},
        {"$lookup": {
            "from": "usuarios",
            "localField": "_id",
            "foreignField": "_id",
            "as": "usuario"
        }},
        {"$unwind": "$usuario"},
        {"$lookup": {
            "from": "grupos",
            "localField": "usuario.grupo_id",
            "foreignField": "_id",
            "as": "grupo"
        }},
        {"$unwind": {"path": "$grupo", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "total_refeicoes": 1,
            "pontos_consistencia": "$usuario.pontos_consistencia",
            "streak_atual": "$usuario.streak_atual",
            "nome": "$usuario.nome",
            "avatar": "$usuario.avatar",
            "foto_url": "$usuario.foto_url",
            "grupo_nome": {"$ifNull": ["$grupo.nome", "Sem Grupo"]},
        }},
    ]

    return list(db["registrosdiarios"].aggregate(pipeline))
