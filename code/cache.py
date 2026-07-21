"""
cache.py
========
Camada de cache usando Redis Cloud (redis-py).
Implementa o padrao Cache-Aside para as aggregations do DietRats.

Se o Redis estiver indisponivel, o app continua funcionando
normalmente buscando direto no MongoDB (fallback silencioso).
"""

import json
import redis as redis_lib
import streamlit as st


def get_redis():
    """
    Conecta ao Redis Cloud usando credenciais do st.secrets.
    Retorna None silenciosamente se Redis estiver indisponivel.
    """
    try:
        host     = st.secrets["REDIS_HOST"]
        port     = int(st.secrets["REDIS_PORT"])
        password = st.secrets["REDIS_PASSWORD"]

        r = redis_lib.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        return r
    except Exception:
        return None


def get_cached(r, key, ttl_segundos, fn_busca):
    """
    Padrao Cache-Aside generico.

    Parametros:
      r             -- conexao Redis (pode ser None)
      key           -- chave unica no Redis (ex: "feed:grupo:abc123")
      ttl_segundos  -- tempo de vida do cache
      fn_busca      -- funcao que busca dados reais no MongoDB (so chamada em cache miss)
    """
    if r:
        try:
            cached_val = r.get(key)
            if cached_val:
                return json.loads(cached_val)  # Cache HIT
        except Exception:
            pass

    # Cache MISS -- busca no MongoDB
    resultado = fn_busca()

    if r and resultado:
        try:
            r.set(key, json.dumps(resultado, default=str), ex=ttl_segundos)
        except Exception:
            pass

    return resultado


def invalidar(r, key):
    """Apaga uma chave do cache (chamado apos mudanca de dados)."""
    if r:
        try:
            r.delete(key)
        except Exception:
            pass


def invalidar_feed_grupo(r, grupo_id):
    """Atalho para invalidar o cache do feed de um grupo especifico."""
    invalidar(r, f"feed:grupo:{grupo_id}")


def invalidar_hall(r):
    """Atalho para invalidar o cache do Hall da Fama."""
    invalidar(r, "hall_da_fama")


# ── Cache de Sessão de Usuário ────────────────────────────────────────────────

def cache_usuario(r, user):
    """
    Salva os dados do usuario no Redis apos o login.
    TTL: 30 minutos. Nao armazena foto_url (grande) nem senha.
    Chave: user:{user_id}
    """
    if not r or not user:
        return
    try:
        user_id = str(user["_id"])
        payload = {
            "_id":                    user_id,
            "nome":                   user.get("nome", ""),
            "email":                  user.get("email", ""),
            "avatar":                 user.get("avatar", "💪"),
            "pontos_consistencia":    user.get("pontos_consistencia", 0),
            "streak_atual":           user.get("streak_atual", 0),
            "grupo_id":               str(user["grupo_id"]) if user.get("grupo_id") else None,
            "ultimo_acesso_notificacoes": str(user["ultimo_acesso_notificacoes"]) if user.get("ultimo_acesso_notificacoes") else None,
        }
        r.set(f"user:{user_id}", json.dumps(payload), ex=1800)  # 30 minutos
    except Exception:
        pass


def get_usuario_cache(r, user_id):
    """
    Tenta buscar os dados do usuario no Redis.
    Retorna dict com os dados ou None se nao encontrado.
    """
    if not r:
        return None
    try:
        val = r.get(f"user:{user_id}")
        return json.loads(val) if val else None
    except Exception:
        return None


def invalidar_usuario(r, user_id):
    """
    Apaga o cache do usuario (chamado ao atualizar perfil ou fazer logout).
    Proxima chamada vai buscar dados frescos do MongoDB.
    """
    invalidar(r, f"user:{user_id}")
