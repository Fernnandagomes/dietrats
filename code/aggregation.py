"""
aggregation.py
==============
Todos os pipelines de aggregation do MongoDB para o DietRats.

Pipelines disponíveis:
  1. get_feed_com_interacoes   - Feed do grupo com reacoes e comentarios embutidos
  2. get_notificacoes_pipeline - Notificacoes em tempo real via aggregation
  3. get_hall_da_fama          - Top 5 atletas mais consistentes do app inteiro

Cache:
  Pipelines 1 e 3 usam Redis Cloud como cache (Cache-Aside pattern).
  Se o Redis estiver indisponivel, buscam diretamente no MongoDB.
"""

import datetime
import cache
from bson import ObjectId


# PIPELINE 1 - Feed do Grupo com Interacoes Embutidas

def get_feed_com_interacoes(db, grupo_id, redis=None):
    """
    Retorna os registros diarios do grupo enriquecidos com dados do autor.
    Usa Redis como cache por 30 segundos por grupo (cache miss -> MongoDB).
    """
    key = f"feed:grupo:{grupo_id}"
    return cache.get_cached(
        redis, key, ttl_segundos=30,
        fn_busca=lambda: _query_feed(db, grupo_id)
    )


def _query_feed(db, grupo_id):
    """Query MongoDB diretamente — chamada apenas em cache miss."""
    group_user_ids = [
        u["_id"]
        for u in db["usuarios"].find({"grupo_id": ObjectId(grupo_id)}, {"_id": 1})
    ]

    pipeline = [
        {"$match": {"usuario_id": {"$in": group_user_ids}}},
        {"$addFields": {
            "reacoes":    {"$ifNull": ["$reacoes", []]},
            "comentarios": {"$ifNull": ["$comentarios", []]}
        }},
        {"$lookup": {
            "from":         "usuarios",
            "localField":   "usuario_id",
            "foreignField": "_id",
            "as":           "autor"
        }},
        {"$unwind": "$autor"},
        {"$project": {
            "usuario_id":   1,
            "tipo":         1,
            "descricao":    1,
            "legenda":      1,
            "foto_url":     1,
            "data":         1,
            "data_criacao": 1,
            "reacoes":      1,
            "comentarios":  1,
            "autor.nome":     1,
            "autor.avatar":   1,
            "autor.foto_url": 1,
        }},
        {"$sort": {"data_criacao": -1}},
    ]

    return list(db["registrosdiarios"].aggregate(pipeline))


# PIPELINE 2 - Notificacoes Computadas em Tempo Real

def get_notificacoes_pipeline(db, usuario_id, ultimo_acesso=None):
    """
    Calcula notificacoes em tempo real buscando reacoes e comentarios
    feitos por outras pessoas nos registros do usuario logado.
    """
    uid = ObjectId(usuario_id) if not isinstance(usuario_id, ObjectId) else usuario_id

    pipeline = [
        {"$match": {"usuario_id": uid}},
        {"$addFields": {
            "reacoes":    {"$ifNull": ["$reacoes", []]},
            "comentarios": {"$ifNull": ["$comentarios", []]}
        }},
        {"$project": {
            "tipo": 1,
            "interacoes": {
                "$concatArrays": [
                    {"$map": {
                        "input": "$reacoes",
                        "as":    "r",
                        "in": {
                            "tipo_evento":    "reacao",
                            "usuario_id":     "$$r.usuario_id",
                            "nome_interator": "$$r.nome",
                            "emoji":          "$$r.tipo",
                            "texto": {"$concat": [
                                "$$r.nome", " reagiu com ", "$$r.tipo",
                                " na sua postagem de ", "$tipo", "."
                            ]},
                            "data": "$$r.data"
                        }
                    }},
                    {"$map": {
                        "input": "$comentarios",
                        "as":    "c",
                        "in": {
                            "tipo_evento":    "comentario",
                            "usuario_id":     "$$c.usuario_id",
                            "nome_interator": "$$c.nome",
                            "emoji":          "💬",
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
            "_id":         0,
            "tipo_evento": "$interacoes.tipo_evento",
            "texto":       "$interacoes.texto",
            "emoji":       "$interacoes.emoji",
            "data":        "$interacoes.data",
        }},
    ]

    resultados = list(db["registrosdiarios"].aggregate(pipeline))

    for n in resultados:
        if ultimo_acesso and n.get("data"):
            n["is_nova"] = n["data"] > ultimo_acesso
        else:
            n["is_nova"] = True

    return resultados


# PIPELINE 3 - Hall da Fama (Top 5 do App Inteiro)

def get_hall_da_fama(db, redis=None):
    """
    Retorna os 5 usuarios com maior numero total de refeicoes.
    Usa Redis como cache por 10 minutos (muda raramente).
    """
    return cache.get_cached(
        redis, "hall_da_fama", ttl_segundos=600,
        fn_busca=lambda: _query_hall(db)
    )


def _query_hall(db):
    """Query MongoDB diretamente — chamada apenas em cache miss."""
    pipeline = [
        {"$group": {
            "_id":             "$usuario_id",
            "total_refeicoes": {"$sum": 1},
        }},
        {"$sort": {"total_refeicoes": -1}},
        {"$limit": 5},
        {"$lookup": {
            "from":         "usuarios",
            "localField":   "_id",
            "foreignField": "_id",
            "as":           "usuario"
        }},
        {"$unwind": "$usuario"},
        {"$lookup": {
            "from":         "grupos",
            "localField":   "usuario.grupo_id",
            "foreignField": "_id",
            "as":           "grupo"
        }},
        {"$unwind": {"path": "$grupo", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id":                 1,
            "total_refeicoes":     1,
            "pontos_consistencia": "$usuario.pontos_consistencia",
            "streak_atual":        "$usuario.streak_atual",
            "nome":                "$usuario.nome",
            "avatar":              "$usuario.avatar",
            "foto_url":            "$usuario.foto_url",
            "grupo_nome":          {"$ifNull": ["$grupo.nome", "Sem Grupo"]},
        }},
    ]

    return list(db["registrosdiarios"].aggregate(pipeline))
