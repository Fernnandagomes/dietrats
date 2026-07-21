import json
import re
import redis as redis_lib
import streamlit as st

STOPWORDS = {"com", "e", "de", "do", "da", "em", "um", "uma", "para", "sem", "a", "o", "os", "as"}


def get_redis():
    """Conecta ao Redis Cloud utilizando as credenciais salvas em st.secrets."""
    try:
        host = st.secrets.get("REDIS_HOST")
        port = int(st.secrets.get("REDIS_PORT", 6379))
        password = st.secrets.get("REDIS_PASSWORD")

        if not host or not password:
            return None

        client = redis_lib.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        return None


def get_cached(redis_client, key, ttl_seconds, fetch_fn):
    """Padrão Cache-Aside genérico para dados serializáveis em JSON."""
    if redis_client:
        try:
            val = redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass

    data = fetch_fn()

    if redis_client and data:
        try:
            redis_client.set(key, json.dumps(data, default=str), ex=ttl_seconds)
        except Exception:
            pass

    return data


def invalidar(redis_client, key):
    """Remove uma chave específica do cache."""
    if redis_client:
        try:
            redis_client.delete(key)
        except Exception:
            pass


def atualizar_pontos_zset(redis_client, grupo_id, usuario_nome, pontos):
    """Atualiza a pontuação do usuário no ZSET do grupo."""
    if not redis_client or not grupo_id or not usuario_nome:
        return
    try:
        key = f"ranking:grupo:{grupo_id}"
        redis_client.zadd(key, {usuario_nome: float(pontos)})
        redis_client.expire(key, 604800)
    except Exception:
        pass


def get_ranking_zset(redis_client, grupo_id):
    """Retorna o ranking do grupo ordenado por pontuação a partir do ZSET."""
    if not redis_client or not grupo_id:
        return None
    try:
        key = f"ranking:grupo:{grupo_id}"
        result = redis_client.zrevrange(key, 0, -1, withscores=True)
        if result:
            return [{"nome": name, "pontos_consistencia": int(score)} for name, score in result]
    except Exception:
        pass
    return None


def registrar_tipo_refeicao(redis_client, grupo_id, tipo_refeicao, descricao):
    """Registra frequência de tipo de refeição (ZSET) e ingredientes únicos (HyperLogLog)."""
    if not redis_client or not grupo_id or not tipo_refeicao:
        return
    try:
        key_freq = f"freq:refeicoes:grupo:{grupo_id}"
        redis_client.zincrby(key_freq, 1, tipo_refeicao)
        redis_client.expire(key_freq, 2592000)

        if descricao:
            # Filtra ingredientes
            words = re.findall(r'\b[a-zA-ZáàâãéèêíóòôõúçÁÀÂÃÉÈÊÍÓÒÔÕÚÇ]+\b', descricao.lower())
            ingredients = [w for w in words if len(w) > 2 and w not in STOPWORDS]
            if ingredients:
                # 1. Adiciona ao HLL de variedade unica
                key_hll = f"hll:variedade:grupo:{grupo_id}"
                redis_client.pfadd(key_hll, *ingredients)
                redis_client.expire(key_hll, 2592000)

                # 2. Adiciona ao ZSET de frequencia de ingredientes do grupo
                key_ing_zset = f"zset:ingredientes:grupo:{grupo_id}"
                for ing in ingredients:
                    redis_client.zincrby(key_ing_zset, 1, ing)
                redis_client.expire(key_ing_zset, 2592000)
    except Exception:
        pass


def get_estatisticas_refeicoes_grupo(redis_client, grupo_id):
    """Retorna o tipo de refeição mais frequente, estimativa de ingredientes únicos e top 3 ingredientes."""
    default_stats = {"mais_frequente": "Nenhum registro", "variedade_hll": 0, "top_3_ingredientes": "Nenhum"}
    if not redis_client or not grupo_id:
        return default_stats
    try:
        # Tipo mais frequente
        key_freq = f"freq:refeicoes:grupo:{grupo_id}"
        top_meal = redis_client.zrevrange(key_freq, 0, 0, withscores=True)
        most_frequent = "Nenhum registro"
        if top_meal:
            name, count = top_meal[0]
            most_frequent = f"{name} ({int(count)}x)"

        # Ingredientes únicos
        key_hll = f"hll:variedade:grupo:{grupo_id}"
        variety_count = redis_client.pfcount(key_hll)

        # Top 3 ingredientes mais comuns
        key_ing_zset = f"zset:ingredientes:grupo:{grupo_id}"
        top_ings = redis_client.zrevrange(key_ing_zset, 0, 2, withscores=True)
        top_3_str = "Nenhum"
        if top_ings:
            top_3_str = " | ".join([f"{name} ({int(score)}x)" for name, score in top_ings])

        return {
            "mais_frequente": most_frequent,
            "variedade_hll": variety_count,
            "top_3_ingredientes": top_3_str
        }
    except Exception:
        return default_stats
