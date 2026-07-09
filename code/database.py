import datetime
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
        "foto_url": foto_b64
    }
    try:
        res = db["usuarios"].insert_one(new_user)
        return res.inserted_id
    except DuplicateKeyError:
        raise Exception("E-mail já está em uso.")

def update_user(db, usuario_id, nome, email, senha, avatar, foto_b64=None):
    """Updates an existing user's profile details."""
    update_data = {
        "nome": nome.strip(),
        "email": email.strip().lower(),
        "senha": senha,
        "avatar": avatar
    }
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
    # Check code availability
    if db["grupos"].find_one({"codigo_acesso": codigo_acesso.strip()}):
        raise Exception("Código de acesso do grupo já está em uso.")
        
    new_group = {
        "nome": nome.strip(),
        "descricao": descricao.strip(),
        "codigo_acesso": codigo_acesso.strip(),
        "criador_id": ObjectId(criador_id),
        "foto_url": foto_b64
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

def get_group_feed(db, grupo_id):
    """Fetches all meal posts from users belonging to the specified group."""
    group_user_ids = [u["_id"] for u in db["usuarios"].find({"grupo_id": ObjectId(grupo_id)}, {"_id": 1})]
    
    meals = list(db["registrosdiarios"].find({"usuario_id": {"$in": group_user_ids}}).sort("data_criacao", -1))
    return meals

def add_meal(db, usuario_id, tipo, descricao, legenda, foto_b64, data_str):
    """Registers a new meal and calculates user consistency points and streaks."""
    user = db["usuarios"].find_one({"_id": ObjectId(usuario_id)})
    if not user:
        raise Exception("Usuário não encontrado.")
        
    new_meal = {
        "usuario_id": ObjectId(usuario_id),
        "tipo": tipo,
        "descricao": descricao.strip(),
        "foto_url": foto_b64,
        "legenda": legenda.strip() if legenda else "",
        "data": data_str,
        "data_criacao": datetime.datetime.now()
    }
    
    # Insert meal
    db["registrosdiarios"].insert_one(new_meal)
    
    # Consistency streak logic
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Get recent meal records
    last_meals = list(db["registrosdiarios"].find({
        "usuario_id": ObjectId(usuario_id),
        "data": {"$in": [yesterday, today]}
    }).sort("data_criacao", -1))
    
    # Filter out current new meal from streak calculations
    other_recent = [m for m in last_meals if m["_id"] != new_meal.get("_id")]
    
    current_streak = user.get("streak_atual", 0)
    
    if not other_recent:
        new_streak = 1
    else:
        has_yesterday = any(m["data"] == yesterday for m in other_recent)
        has_today = any(m["data"] == today for m in other_recent)
        if has_today:
            new_streak = current_streak
        elif has_yesterday:
            new_streak = current_streak + 1
        else:
            new_streak = 1
            
    points_gained = 10
    db["usuarios"].update_one(
        {"_id": ObjectId(usuario_id)},
        {
            "$inc": {"pontos_consistencia": points_gained},
            "$set": {"streak_atual": new_streak}
        }
    )
    return new_streak

def toggle_reaction(db, registro_id, usuario_id, tipo_emoji, autor_post_id, tipo_refeicao, nome_reagente):
    """Toggles (adds or removes) a reaction on a meal post and registers notifications."""
    existing_react = db["reacoes"].find_one({
        "registro_id": ObjectId(registro_id),
        "usuario_id": ObjectId(usuario_id),
        "tipo": tipo_emoji
    })
    
    if existing_react:
        db["reacoes"].delete_one({"_id": existing_react["_id"]})
    else:
        try:
            db["reacoes"].insert_one({
                "registro_id": ObjectId(registro_id),
                "usuario_id": ObjectId(usuario_id),
                "tipo": tipo_emoji
            })
            
            # Send Notification if it's someone else's post
            if ObjectId(autor_post_id) != ObjectId(usuario_id):
                db["notificacoes"].insert_one({
                    "destinatario_id": ObjectId(autor_post_id),
                    "tipo": "reacao",
                    "texto": f"{nome_reagente} reagiu com {tipo_emoji} na sua postagem de {tipo_refeicao}.",
                    "lida": False,
                    "data_criacao": datetime.datetime.now()
                })
        except DuplicateKeyError:
            pass

def add_comment(db, registro_id, usuario_id, texto, autor_post_id, nome_comentador):
    """Adds a new comment on a meal post and triggers a notification to the author."""
    new_comment = {
        "registro_id": ObjectId(registro_id),
        "usuario_id": ObjectId(usuario_id),
        "texto": texto.strip(),
        "data_criacao": datetime.datetime.now()
    }
    db["comentarios"].insert_one(new_comment)
    
    if ObjectId(autor_post_id) != ObjectId(usuario_id):
        db["notificacoes"].insert_one({
            "destinatario_id": ObjectId(autor_post_id),
            "tipo": "comentario",
            "texto": f"{nome_comentador} comentou na sua postagem: '{texto.strip()}'",
            "lida": False,
            "data_criacao": datetime.datetime.now()
        })

def get_ranking(db, grupo_id):
    """Fetches user leaderboard sorted by consistency points and streak."""
    return list(db["usuarios"].find({"grupo_id": ObjectId(grupo_id)}).sort([
        ("pontos_consistencia", -1),
        ("streak_atual", -1)
    ]))

def get_notifications(db, usuario_id):
    """Gets recent notifications for the user."""
    return list(db["notificacoes"].find({"destinatario_id": ObjectId(usuario_id)}).sort("data_criacao", -1))

def mark_notifications_read(db, usuario_id):
    """Marks all notifications as read."""
    db["notificacoes"].update_many(
        {"destinatario_id": ObjectId(usuario_id)},
        {"$set": {"lida": True}}
    )
