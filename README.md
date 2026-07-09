# DietRats

https://dietrats.streamlit.app/
DietRats

**DietRats** é uma rede social fitness voltada para consistência alimentar em grupo. Construído com **Streamlit**, **Python** e **MongoDB (PyMongo)**, o projeto permite que usuários postem suas refeições diárias, reajam com emojis, comentem e acompanhem um ranking de consistência dentro do próprio grupo.
A plataforma combina acompanhamento alimentar com competição entre amigos, incentivando os usuários a manterem consistência com hábitos saudáveis.

## 🚀 Tecnologias
* **Python 3.10+**
* **Streamlit** (Interface Visual)
* **MongoDB Atlas** (Banco de Dados NoSQL)
* **PyMongo** (Driver do MongoDB)

## 📁 Estrutura do Projeto
O projeto segue uma estrutura de 3 arquivos principais de código:
* `app.py`: O arquivo principal com a lógica do CRUD e interface Streamlit.
* `seed.py`: Script para resetar e popular o banco com dados de teste.
* `requirements.txt`: Dependências necessárias para a aplicação.

---

## Instalação e Execução

### 1. Clonar o repositório
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd dietratsNOSQL
```

### 2. Instalar dependências
Recomenda-se criar um ambiente virtual antes:
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Executar o Script de População (Seed)
Caso utilize o MongoDB local (`mongodb://localhost:27017/`):
```bash
python seed.py
```
Caso utilize o **MongoDB Atlas**, passe a string de conexão como argumento:
```bash
python seed.py "sua_string_de_conexao_mongodb_atlas"
```

### 4. Executar o Aplicativo Streamlit
```bash
streamlit run app.py
```

---
