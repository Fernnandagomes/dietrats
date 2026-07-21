import datetime
import aggregation
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
from pymongo.errors import DuplicateKeyError


def get_db(uri):
    """Establishes connection to MongoDB and checks if server is active."""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        client.server_info()  # Test connection
        return client["dietrats"]
    except Exception:
        return None


def authenticate_user(db, email, password):
    """Checks user credentials and returns the user document if valid."""
    return db["usuarios"].find_one({"email": email.strip().lower(), "senha": password})


def create_user(db, nome, email, senha, avatar, grupo_id=None, foto_b64=None):
    """Inserts a new user into the database."""
    new_user = {
        "nome": nome.strip(),
        "email": email.strip().lower(),
        "senha": senha,
        "avatar": avatar,
        "pontos_consistencia": 0,
        "streak_atual": 0,
        "grupo_id": grupo_id,
        "foto_url": foto_b64,
        "ultimo_acesso_notificacoes": None,
    }
    try:
        res = db["usuarios"].insert_one(new_user)
        return res.inserted_id
    except DuplicateKeyError:
        raise Exception("E-mail já está em uso.")


def update_user(db, usuario_id, nome, email, senha, avatar, foto_b64=None):
    """Updates an existing user's profile details."""
    update_data = {
        "nome":   nome.strip(),
        "email":  email.strip().lower(),
        "avatar": avatar,
    }
    # So atualiza senha se uma nova for fornecida
    if senha and senha.strip():
        update_data["senha"] = senha.strip()
    if foto_b64:
        update_data["foto_url"] = foto_b64

    try:
        db["usuarios"].update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": update_data}
        )
    except DuplicateKeyError:
        raise Exception("Este e-mail já está em uso por outro usuário.")


def create_group(db, nome, descricao, codigo_acesso, criador_id, foto_b64=None):
    """Creates a new group and returns its ID."""
    if db["grupos"].find_one({"codigo_acesso": codigo_acesso.strip()}):
        raise Exception("Código de acesso do grupo já está em uso.")

    new_group = {
        "nome": nome.strip(),
        "descricao": descricao.strip(),
        "codigo_acesso": codigo_acesso.strip(),
        "criador_id": ObjectId(criador_id),
        "foto_url": foto_b64,
    }
    res = db["grupos"].insert_one(new_group)
    return res.inserted_id


def join_group(db, usuario_id, codigo_acesso):
    """Associates an existing user to a group based on access code."""
    grp = db["grupos"].find_one({"codigo_acesso": codigo_acesso.strip()})
    if not grp:
        raise Exception("Grupo não encontrado com este código de acesso.")

    db["usuarios"].update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"grupo_id": grp["_id"]}}
    )
    return grp


def get_group_feed(db, grupo_id, redis=None):
    """
    Fetches all meal posts from the group using the aggregation pipeline.
    Passes redis connection for Cache-Aside caching (30s TTL per group).
    """
    return aggregation.get_feed_com_interacoes(db, grupo_id, redis=redis)


def add_meal(db, usuario_id, tipo, descricao, legenda, foto_b64, data_str):
    """Registers a new meal with embedded empty arrays for reactions and comments."""
    user = db["usuarios"].find_one({"_id": ObjectId(usuario_id)})
    if not user:
        raise Exception("Usuário não encontrado.")

    new_meal = {
        "usuario_id":  ObjectId(usuario_id),
        "tipo":        tipo,
        "descricao":   descricao.strip(),
        "foto_url":    foto_b64,
        "legenda":     legenda.strip() if legenda else "",
        "data":        data_str,
        "data_criacao": datetime.datetime.now(),
        "reacoes":     [],   # embedded — array de reações
        "comentarios": [],   # embedded — array de comentários
    }

    db["registrosdiarios"].insert_one(new_meal)

    # Consistency streak logic
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    today     = datetime.date.today().strftime("%Y-%m-%d")

    last_meals = list(db["registrosdiarios"].find({
        "usuario_id": ObjectId(usuario_id),
        "data": {"$in": [yesterday, today]}
    }).sort("data_criacao", -1))

    other_recent  = [m for m in last_meals if m["_id"] != new_meal.get("_id")]
    current_streak = user.get("streak_atual", 0)

    if not other_recent:
        new_streak = 1
    else:
        has_yesterday = any(m["data"] == yesterday for m in other_recent)
        has_today     = any(m["data"] == today     for m in other_recent)
        if has_today:
            new_streak = current_streak
        elif has_yesterday:
            new_streak = current_streak + 1
        else:
            new_streak = 1

    db["usuarios"].update_one(
        {"_id": ObjectId(usuario_id)},
        {
            "$inc": {"pontos_consistencia": 10},
            "$set": {"streak_atual": new_streak},
        }
    )
    return new_streak


def toggle_reaction(db, registro_id, usuario_id, tipo_emoji, nome_reagente):
    """
    Toggles a reaction inside the meal document's 'reacoes' array.
    Uses $pull to remove or $push to add — no separate collection needed.
    """
    rid = ObjectId(registro_id)
    uid = ObjectId(usuario_id)

    # Verifica se a reação já existe no array embutido
    existing = db["registrosdiarios"].find_one({
        "_id":    rid,
        "reacoes": {"$elemMatch": {"usuario_id": uid, "tipo": tipo_emoji}}
    })

    if existing:
        # Remove a reação do array
        db["registrosdiarios"].update_one(
            {"_id": rid},
            {"$pull": {"reacoes": {"usuario_id": uid, "tipo": tipo_emoji}}}
        )
    else:
        # Adiciona a reação no array
        db["registrosdiarios"].update_one(
            {"_id": rid},
            {"$push": {"reacoes": {
                "usuario_id": uid,
                "nome":       nome_reagente,
                "tipo":       tipo_emoji,
                "data":       datetime.datetime.now(),
            }}}
        )


def add_comment(db, registro_id, usuario_id, texto, nome_comentador):
    """
    Adds a comment directly into the meal document's 'comentarios' array.
    No separate collection needed.
    """
    db["registrosdiarios"].update_one(
        {"_id": ObjectId(registro_id)},
        {"$push": {"comentarios": {
            "usuario_id": ObjectId(usuario_id),
            "nome":       nome_comentador,
            "texto":      texto.strip(),
            "data":       datetime.datetime.now(),
        }}}
    )


def get_ranking(db, grupo_id):
    """Fetches user leaderboard sorted by consistency points and streak."""
    return list(db["usuarios"].find({"grupo_id": ObjectId(grupo_id)}).sort([
        ("pontos_consistencia", -1),
        ("streak_atual", -1),
    ]))


def get_hall_da_fama(db, redis=None):
    """
    Returns the top 5 users with the most meal registrations across the entire app.
    Passes redis connection for Cache-Aside caching (10 min TTL).
    """
    return aggregation.get_hall_da_fama(db, redis=redis)


def get_notifications(db, usuario_id):
    """
    Gets real-time notifications via aggregation pipeline.
    Reads the user's last_access timestamp to flag new vs seen notifications.
    """
    user = db["usuarios"].find_one({"_id": ObjectId(usuario_id)}, {"ultimo_acesso_notificacoes": 1})
    ultimo_acesso = user.get("ultimo_acesso_notificacoes") if user else None
    return aggregation.get_notificacoes_pipeline(db, usuario_id, ultimo_acesso)


def mark_notifications_read(db, usuario_id):
    """
    Marks notifications as 'read' by saving the current timestamp on the user document.
    Next time get_notifications() runs, only interactions after this timestamp are 'new'.
    """
    db["usuarios"].update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"ultimo_acesso_notificacoes": datetime.datetime.now()}}
    )
