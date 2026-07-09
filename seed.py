import os
import datetime
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
import sys

# Base64 string representing a simple 1x1 green/gray pixel PNG image for mock photos
MOCK_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

def seed_database():
    # Retrieve connection string from command-line argument, env or use default local URI
    if len(sys.argv) > 1:
        mongo_uri = sys.argv[1]
    else:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    print(f"Tentando conectar ao MongoDB em: {mongo_uri}")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.server_info() # Test connection
    except Exception:
        if mongo_uri == "mongodb://localhost:27017/":
            print("\n⚠️ Não foi possível conectar ao MongoDB local (localhost:27017).")
            print("Se você estiver usando o MongoDB Atlas, precisaremos da sua String de Conexão.")
            mongo_uri = input("👉 Digite ou cole sua String de Conexão do MongoDB Atlas e aperte Enter: ").strip()
            if not mongo_uri:
                print("String vazia. Encerrando script.")
                sys.exit(1)
            print(f"Tentando conectar ao MongoDB Atlas em: {mongo_uri}")
            try:
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                client.server_info()
            except Exception as e:
                print(f"❌ Erro ao conectar ao MongoDB Atlas: {e}")
                sys.exit(1)
        else:
            print(f"❌ Erro ao conectar ao MongoDB fornecido ({mongo_uri}).")
            sys.exit(1)
            
    db = client["dietrats"]
    
    # 1. Clean collections
    collections_to_clean = ["usuarios", "grupos", "registrosdiarios", "reacoes", "comentarios", "notificacoes"]
    for col in collections_to_clean:
        db[col].drop()
        print(f"Dropped collection: {col}")
        
    # 2. Create indexes
    # unique index on usuarios(email)
    db["usuarios"].create_index([("email", ASCENDING)], unique=True)
    print("Created unique index on usuarios.email")
    
    # unique index on grupos(codigo_acesso)
    db["grupos"].create_index([("codigo_acesso", ASCENDING)], unique=True)
    print("Created unique index on grupos.codigo_acesso")
    
    # composite unique index on reacoes(registro_id, usuario_id, tipo)
    db["reacoes"].create_index([
        ("registro_id", ASCENDING),
        ("usuario_id", ASCENDING),
        ("tipo", ASCENDING)
    ], unique=True)
    print("Created composite unique index on reacoes(registro_id, usuario_id, tipo)")

    # 3. Insert mock data
    user_maromba_id = ObjectId()
    user_frango_id = ObjectId()
    user_nutri_id = ObjectId()
    
    group_academia_id = ObjectId()
    group_foco_id = ObjectId()
    
    # Create Groups
    groups = [
        {
            "_id": group_academia_id,
            "nome": "Ratos de Academia",
            "descricao": "Foco no ganho de massa, treino pesado e dieta limpa.",
            "codigo_acesso": "FIT123",
            "criador_id": user_maromba_id,
            "foto_url": MOCK_IMAGE_BASE64
        },
        {
            "_id": group_foco_id,
            "nome": "Foco Total",
            "descricao": "Grupo para consistência máxima na reeducação alimentar.",
            "codigo_acesso": "FOCO99",
            "criador_id": user_nutri_id,
            "foto_url": MOCK_IMAGE_BASE64
        }
    ]
    db["grupos"].insert_many(groups)
    print("Inserted mock groups")
    
    # Create Users
    users = [
        {
            "_id": user_maromba_id,
            "nome": "Maromba Silva",
            "email": "maromba@dietrats.com",
            "senha": "123",
            "avatar": "💪",
            "pontos_consistencia": 150,
            "streak_atual": 5,
            "grupo_id": group_academia_id,
            "foto_url": None
        },
        {
            "_id": user_frango_id,
            "nome": "Frango de Calça",
            "email": "frango@dietrats.com",
            "senha": "123",
            "avatar": "🍗",
            "pontos_consistencia": 40,
            "streak_atual": 2,
            "grupo_id": group_academia_id,
            "foto_url": None
        },
        {
            "_id": user_nutri_id,
            "nome": "Nutri Sábia",
            "email": "nutri@dietrats.com",
            "senha": "123",
            "avatar": "🥗",
            "pontos_consistencia": 300,
            "streak_atual": 12,
            "grupo_id": group_foco_id,
            "foto_url": None
        }
    ]
    db["usuarios"].insert_many(users)
    print("Inserted mock users")
    
    # Create Registros Diários (Meals)
    meal_1_id = ObjectId()
    meal_2_id = ObjectId()
    meal_3_id = ObjectId()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    meals = [
        {
            "_id": meal_1_id,
            "usuario_id": user_maromba_id,
            "tipo": "Almoço",
            "descricao": "Arroz integral, batata doce, peito de frango grelhado e brócolis.",
            "foto_url": MOCK_IMAGE_BASE64,
            "legenda": "Almoço padrão de campeão! 💪🏼🔥",
            "data": today_str,
            "data_criacao": datetime.datetime.now()
        },
        {
            "_id": meal_2_id,
            "usuario_id": user_frango_id,
            "tipo": "Jantar",
            "descricao": "Omelete de 3 ovos com salada de alface e tomate.",
            "foto_url": MOCK_IMAGE_BASE64,
            "legenda": "",  # Optional Caption test
            "data": today_str,
            "data_criacao": datetime.datetime.now() - datetime.timedelta(minutes=30)
        },
        {
            "_id": meal_3_id,
            "usuario_id": user_nutri_id,
            "tipo": "Café",
            "descricao": "Panqueca de banana com aveia e whey protein + café preto.",
            "foto_url": MOCK_IMAGE_BASE64,
            "legenda": "Começando o dia com nutrientes de qualidade!",
            "data": yesterday_str,
            "data_criacao": datetime.datetime.now() - datetime.timedelta(days=1)
        }
    ]
    db["registrosdiarios"].insert_many(meals)
    print("Inserted mock meals")
    
    # Create Reações
    reactions = [
        {
            "registro_id": meal_1_id,
            "usuario_id": user_frango_id,
            "tipo": "💪"
        },
        {
            "registro_id": meal_1_id,
            "usuario_id": user_frango_id,
            "tipo": "🔥"
        },
        {
            "registro_id": meal_2_id,
            "usuario_id": user_maromba_id,
            "tipo": "🥗"
        }
    ]
    db["reacoes"].insert_many(reactions)
    print("Inserted mock reactions")
    
    # Create Comentários
    comments = [
        {
            "registro_id": meal_1_id,
            "usuario_id": user_frango_id,
            "texto": "Monstro demais! Faltou o carbo?",
            "data_criacao": datetime.datetime.now() - datetime.timedelta(minutes=15)
        },
        {
            "registro_id": meal_1_id,
            "usuario_id": user_maromba_id,
            "texto": "Tem batata doce ali escondida kkk tmj!",
            "data_criacao": datetime.datetime.now() - datetime.timedelta(minutes=10)
        }
    ]
    db["comentarios"].insert_many(comments)
    print("Inserted mock comments")
    
    # Create Notificações
    notifications = [
        {
            "destinatario_id": user_maromba_id,
            "tipo": "comentario",
            "texto": "Frango de Calça comentou na sua postagem: 'Monstro demais! Faltou o carbo?'",
            "lida": False,
            "data_criacao": datetime.datetime.now() - datetime.timedelta(minutes=15)
        },
        {
            "destinatario_id": user_maromba_id,
            "tipo": "reacao",
            "texto": "Frango de Calça reagiu com 💪 na sua postagem.",
            "lida": False,
            "data_criacao": datetime.datetime.now() - datetime.timedelta(minutes=5)
        }
    ]
    db["notificacoes"].insert_many(notifications)
    print("Inserted mock notifications")
    
    print("\nDatabase seeded successfully!")

if __name__ == "__main__":
    seed_database()
