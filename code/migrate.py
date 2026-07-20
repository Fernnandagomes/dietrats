"""
migrate.py
==========
Migra dados das colecoes antigas (reacoes, comentarios, notificacoes)
para o novo schema embutido dentro de registrosdiarios.

Execute UMA UNICA VEZ depois de fazer o deploy do novo codigo.
"""

import os
import sys
import datetime
from pymongo import MongoClient
from bson import ObjectId


def get_db(uri):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=6000)
        client.server_info()
        return client["dietrats"]
    except Exception as e:
        print(f"[ERRO] Nao foi possivel conectar: {e}")
        sys.exit(1)


def migrate(db):
    print("=" * 55)
    print("  DietRats — Migracao de Schema")
    print("=" * 55)

    # ── 1. Garante que todos os registros tem os arrays ──────────
    print("\n[1/4] Inicializando arrays reacoes[] e comentarios[] nos registros sem eles...")
    result = db["registrosdiarios"].update_many(
        {"reacoes": {"$exists": False}},
        {"$set": {"reacoes": [], "comentarios": []}}
    )
    print(f"      {result.modified_count} registros atualizados com arrays vazios.")

    # ── 2. Migra reacoes ────────────────────────────────────────
    print("\n[2/4] Migrando colecao 'reacoes' para arrays embutidos...")
    reacoes = list(db["reacoes"].find({}))
    ok, skip = 0, 0

    for r in reacoes:
        registro_id = r.get("registro_id")
        usuario_id  = r.get("usuario_id")
        tipo        = r.get("tipo", "")

        if not registro_id or not usuario_id:
            skip += 1
            continue

        # Busca nome do usuario que reagiu
        user = db["usuarios"].find_one({"_id": usuario_id}, {"nome": 1})
        nome = user["nome"] if user else "Desconhecido"

        # Verifica se ja foi migrado (evita duplicatas)
        already = db["registrosdiarios"].find_one({
            "_id":    registro_id,
            "reacoes": {"$elemMatch": {"usuario_id": usuario_id, "tipo": tipo}}
        })

        if already:
            skip += 1
            continue

        db["registrosdiarios"].update_one(
            {"_id": registro_id},
            {"$push": {"reacoes": {
                "usuario_id": usuario_id,
                "nome":       nome,
                "tipo":       tipo,
                "data":       r.get("data_criacao", datetime.datetime.now()),
            }}}
        )
        ok += 1

    print(f"      {ok} reacoes migradas | {skip} ignoradas (ja existentes ou invalidas).")

    # ── 3. Migra comentarios ────────────────────────────────────
    print("\n[3/4] Migrando colecao 'comentarios' para arrays embutidos...")
    comentarios = list(db["comentarios"].find({}))
    ok2, skip2 = 0, 0

    for c in comentarios:
        registro_id = c.get("registro_id")
        usuario_id  = c.get("usuario_id")
        texto       = c.get("texto", "")

        if not registro_id or not usuario_id:
            skip2 += 1
            continue

        user = db["usuarios"].find_one({"_id": usuario_id}, {"nome": 1})
        nome = user["nome"] if user else "Desconhecido"

        # Verifica duplicatas por texto + usuario_id
        already = db["registrosdiarios"].find_one({
            "_id":        registro_id,
            "comentarios": {"$elemMatch": {"usuario_id": usuario_id, "texto": texto}}
        })

        if already:
            skip2 += 1
            continue

        db["registrosdiarios"].update_one(
            {"_id": registro_id},
            {"$push": {"comentarios": {
                "usuario_id": usuario_id,
                "nome":       nome,
                "texto":      texto,
                "data":       c.get("data_criacao", datetime.datetime.now()),
            }}}
        )
        ok2 += 1

    print(f"      {ok2} comentarios migrados | {skip2} ignorados.")

    # ── 4. Adiciona campo ultimo_acesso_notificacoes nos usuarios ──
    print("\n[4/4] Adicionando campo 'ultimo_acesso_notificacoes' nos usuarios...")
    result2 = db["usuarios"].update_many(
        {"ultimo_acesso_notificacoes": {"$exists": False}},
        {"$set": {"ultimo_acesso_notificacoes": None}}
    )
    print(f"      {result2.modified_count} usuarios atualizados.")

    print("\n" + "=" * 55)
    print("  Migracao concluida com sucesso!")
    print("  As colecoes antigas (reacoes, comentarios, notificacoes)")
    print("  foram preservadas no Atlas mas nao sao mais usadas.")
    print("=" * 55)


if __name__ == "__main__":
    uri = os.environ.get("MONGO_URI", "")
    if not uri:
        uri = input("Cole sua String de Conexao MongoDB Atlas: ").strip()
    db = get_db(uri)
    migrate(db)
