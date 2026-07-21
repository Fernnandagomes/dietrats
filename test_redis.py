import redis

HOST     = "arm-hyperlight-cottony-63924.db.redis.io"
PORT     = 18808
PASSWORD = input("Cole sua senha do Redis: ").strip()

print("\nTestando conexao...")
try:
    r = redis.Redis(host=HOST, port=PORT, password=PASSWORD, ssl=False, decode_responses=True, socket_connect_timeout=5)
    r.ping()
    print("CONECTADO com sucesso!")
    
    # Testa escrita e leitura
    r.set("teste_dietrats", "funcionando!", ex=30)
    valor = r.get("teste_dietrats")
    print(f"Escrita/Leitura: {valor}")
    print("Chaves atuais:", r.keys("*"))
    r.delete("teste_dietrats")
    print("\nRedis esta funcionando perfeitamente!")
except Exception as e:
    print(f"ERRO: {e}")
