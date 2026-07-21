import streamlit as st
import os
import base64
import datetime
import textwrap
from PIL import Image
from io import BytesIO
from bson import ObjectId

# Import MongoDB helper functions
import database
import cache

# --- page config ---
st.set_page_config(
    page_title="DietRats - Social Fitness Network",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- advanced custom CSS for Dark Purple Premium theme ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Dark Purple Premium Reset */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #110E26 !important;
        color: #F3F4F6 !important;
        font-size: 16px !important;
    }
    
    /* Remove any browser text shadow outline */
    * {
        text-shadow: none !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1C1936 !important;
        border-right: 1px solid #2A264D !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #F3F4F6 !important;
    }
    
    /* App Title / Header Banner */
    .app-title-container {
        background: linear-gradient(135deg, #1C1936 0%, #2A264D 100%);
        padding: 25px;
        border-radius: 20px;
        color: #F3F4F6;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        text-align: center;
        border: 1px solid #2A264D;
    }
    
    /* Native Containers Override to act as Dark Premium Cards */
    div[data-testid="stContainer"] {
        background-color: #1C1936 !important;
        border: 1px solid #2A264D !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 25px !important;
    }
    
    /* Avatar layout */
    .user-avatar-img {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #22C55E;
    }
    
    .user-avatar-emoji {
        font-size: 26px;
        background-color: #2A264D;
        width: 52px;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        border: 2px solid #22C55E;
    }
    
    /* Meal type badge */
    .meal-type-tag {
        background-color: #2A264D;
        color: #22C55E;
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 0.85em;
        font-weight: 800;
        text-transform: uppercase;
        border: 1px solid #22C55E;
        letter-spacing: 0.05em;
    }
    
    /* Text settings (no broad !important overrides to avoid styling conflicts) */
    h1, h2, h3, h4, h5, h6, p, li {
        color: #F3F4F6;
    }
    
    /* Highly readable input fields with dark backgrounds and white text */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], div[data-baseweb="select"] {
        background-color: #1C1936 !important;
        color: #FFFFFF !important;
        border: 1px solid #2A264D !important;
        border-radius: 8px !important;
    }
    
    /* Ensure the inner HTML input element text color is white and background is dark */
    input, textarea, select {
        color: #FFFFFF !important;
        background-color: #1C1936 !important;
    }
    
    /* Input element text adjustments */
    input[data-baseweb="input"], .stTextInput input {
        background-color: #1C1936 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
    }
    
    div[data-baseweb="input"] input {
        background-color: #1C1936 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
    }
    
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #1C1936 !important;
        border: 1px solid #2A264D !important;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: #22C55E !important;
    }
    
    /* Streamlit File Uploader Box Dark Style */
    div[data-testid="stFileUploader"] {
        background-color: #1C1936 !important;
        border: 1px dashed #2A264D !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }
    
    div[data-testid="stFileUploader"] * {
        color: #F3F4F6 !important;
        background-color: transparent !important;
    }
      /* Password Visibility Eye Button Icon customizer and its parent container */
    div[data-baseweb="input"] button, 
    div[data-baseweb="input"] button:hover,
    div[data-baseweb="input"] > div {
        background-color: transparent !important;
        color: #22C55E !important;
        border: none !important;
    }
    
    button[title="Show password"], button[title="Hide password"] {
        background-color: transparent !important;
        color: #22C55E !important;
        border: none !important;
    }
    
    /* Dropdown Selectbox container values and expanded menu styling */
    div[role="listbox"], div[role="combobox"], div[data-baseweb="select"] > div, div[data-baseweb="select"] * {
        background-color: #1C1936 !important;
        color: #FFFFFF !important;
    }
    
    ul[role="listbox"], li[role="option"] {
        background-color: #1C1936 !important;
        color: #FFFFFF !important;
        border-color: #2A264D !important;
    }
    
    li[role="option"]:hover {
        background-color: #22C55E !important;
        color: #110E26 !important;
    }
    
    /* File Uploader inner button customizer */
    div[data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #15803D 0%, #22C55E 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    /* Native Form Container Overrides to remove stark white background */
    div[data-testid="stForm"] {
        background-color: transparent !important;
        border: 1px solid #2A264D !important;
        border-radius: 12px !important;
        padding: 18px !important;
    }
    
    /* Labels styling */
    label, .stWidgetLabel p {
        color: #22C55E !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
    }
    
    /* Navigation Tabs customization */
    div[data-baseweb="tab-list"] {
        background-color: #1C1936 !important;
        border-radius: 12px !important;
        padding: 6px !important;
        border: 1px solid #2A264D !important;
        margin-bottom: 25px !important;
        justify-content: space-around !important;
    }
    
    button[data-baseweb="tab"] {
        font-weight: 800 !important;
        font-size: 1.25em !important; /* Large main tabs */
        color: #9CA3AF !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        background-color: transparent !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Target inner text of tabs directly to bypass Streamlit style sheets overrides */
    button[data-baseweb="tab"] *, 
    button[data-baseweb="tab"] p, 
    button[data-baseweb="tab"] span {
        font-size: 15px ;
        font-weight: 600;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: transparent !important;
        color: #22C55E !important;
    }
    
    /* Neon Green active tab underline line override (removes the default orange line) */
    div[data-baseweb="tab-highlight-bar"] {
        background-color: #22C55E !important;
    }
    
    /* Primary buttons (Form Submits) - Green solid gradient */
    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #15803D 0%, #22C55E 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2) !important;
        font-size: 15px !important;
    }
    
    div.stFormSubmitButton > button:hover {
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4) !important;
        transform: translateY(-2px);
    }
    
    /* Secondary buttons & Reaction Pill Buttons - Transparent with Purple Outline */
    div.stButton > button {
        background: transparent !important;
        color: #F3F4F6 !important;
        border: 1px solid #2A264D !important;
        border-radius: 20px !important; /* Pill style */
        padding: 5px 14px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease-in-out !important;
        font-size: 14px !important;
    }
    
    div.stButton > button:hover {
        background-color: #2A264D !important;
        border-color: #22C55E !important;
        color: #22C55E !important;
        transform: translateY(-1px);
    }
    
    /* Leaderboard custom styles */
    .ranking-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #1C1936;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 15px;
        border: 1px solid #2A264D;
        border-left: 6px solid #22C55E;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }
    
    .ranking-position {
        font-size: 1.6em;
        font-weight: 800;
        color: #22C55E;
        width: 45px;
    }
</style>
""", unsafe_allow_html=True)

# --- helper functions ---
def load_logo_base64(filepath):
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

logo_b64 = load_logo_base64("LOGO.png")

def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_bytes(b64_str):
    return base64.b64decode(b64_str)

# --- mongo configuration (automatic — reads from st.secrets or environment) ---
mongo_uri = None
try:
    if "MONGO_URI" in st.secrets:
        mongo_uri = st.secrets["MONGO_URI"]
except Exception:
    pass

if not mongo_uri:
    mongo_uri = os.environ.get("MONGO_URI", "")

db = database.get_db(mongo_uri)

# Inicializa Redis (fallback silencioso se indisponivel)
redis_client = cache.get_redis()

if db is None:
    st.error("❌ Não foi possível conectar ao banco de dados.")
    st.info("Configure a variável **MONGO_URI** nos Secrets do Streamlit Cloud (Settings → Secrets).")
    st.stop()

# --- auth system state ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

def get_current_user():
    if st.session_state["user_id"]:
        uid = st.session_state["user_id"]
        # Tenta Redis primeiro (evita query ao MongoDB em todo rerun)
        cached = cache.get_usuario_cache(redis_client, uid)
        if cached:
            return cached
        # Cache miss — busca no MongoDB e guarda no Redis
        user = db["usuarios"].find_one({"_id": ObjectId(uid)})
        if user:
            cache.cache_usuario(redis_client, user)
        return user
    return None

current_user = get_current_user()

if "tab_key" not in st.session_state:
    st.session_state["tab_key"] = "tabs_v1"

if not current_user:
    if logo_b64:
        st.markdown(f"""
        <div style='display: flex; justify-content: center; margin-top: 15px; margin-bottom: 25px;'>
            <img src='data:image/png;base64,{logo_b64}' style='width: 600px; max-width: 100%; object-fit: contain;'>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align:center; color:#22C55E;'>DietRats 🥗💪</h2>", unsafe_allow_html=True)
    
    auth_action = st.radio("Escolha uma opção:", ["Login", "Registrar-se"], horizontal=True)
    
    if auth_action == "Login":
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar no DietRats")
            
            if submitted:
                user = database.authenticate_user(db, email, senha)
                if user:
                    st.session_state["user_id"] = str(user["_id"])
                    cache.cache_usuario(redis_client, user)  # salva no Redis
                    st.success(f"Bem-vindo, {user['nome']}!")
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos. Tente novamente.")
                    
    else:
        with st.form("cadastro_form"):
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha (mínimo 3 caracteres)", type="password")
            avatar_emoji = st.selectbox("Escolha um Emoji Avatar", ["💪", "🍗", "🥗", "🏃", "🥦", "🍎", "🔥"])
            
            uploaded_user_photo = st.file_uploader("Foto de Perfil (Opcional - substitui o Emoji)", type=["jpg", "jpeg", "png"])
            
            grupo_opcao = st.radio("Entrar em um Grupo:", ["Criar Novo Grupo", "Entrar em Grupo Existente", "Sem Grupo por enquanto"])
            
            st.markdown("---")
            st.markdown("### Configurações de Grupo")
            g_nome = st.text_input("Nome do Grupo (para Criar)")
            g_desc = st.text_input("Descrição do Grupo (para Criar)")
            g_codigo = st.text_input("Código de Acesso do Grupo (Criar ou Entrar)")
            uploaded_group_photo = st.file_uploader("Foto do Grupo (Opcional - Apenas se for Criar)", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Cadastrar e Iniciar")
            
            if submitted:
                if not nome or not email or not senha:
                    st.error("Por favor, preencha todos os campos obrigatórios (Nome, E-mail e Senha).")
                else:
                    user_photo_b64 = None
                    if uploaded_user_photo:
                        try:
                            img_user = Image.open(uploaded_user_photo)
                            img_user.thumbnail((300, 300))
                            user_photo_b64 = img_to_base64(img_user)
                        except Exception as e:
                            st.error(f"Erro ao processar foto de perfil: {e}")
                            st.stop()
                            
                    grupo_id = None
                    if grupo_opcao == "Criar Novo Grupo":
                        if not g_nome or not g_codigo:
                            st.error("Preencha o nome e o código de acesso para criar o grupo.")
                            st.stop()
                        
                        group_photo_b64 = None
                        if uploaded_group_photo:
                            try:
                                img_grp = Image.open(uploaded_group_photo)
                                img_grp.thumbnail((400, 400))
                                group_photo_b64 = img_to_base64(img_grp)
                            except Exception as e:
                                st.error(f"Erro ao processar foto do grupo: {e}")
                                st.stop()
                        
                        temp_user_id = ObjectId()
                        try:
                            grupo_id = database.create_group(
                                db, g_nome, g_desc, g_codigo, temp_user_id, group_photo_b64
                            )
                        except Exception as e:
                            st.error(str(e))
                            st.stop()
                            
                    elif grupo_opcao == "Entrar em Grupo Existente":
                        if not g_codigo:
                            st.error("Digite o código de acesso do grupo.")
                            st.stop()
                        grp = db["grupos"].find_one({"codigo_acesso": g_codigo.strip()})
                        if not grp:
                            st.error("Grupo não encontrado com este código de acesso.")
                            st.stop()
                        grupo_id = grp["_id"]
                        
                    try:
                        new_uid = database.create_user(
                            db, nome, email, senha, avatar_emoji, grupo_id, user_photo_b64
                        )
                        if grupo_opcao == "Criar Novo Grupo":
                            db["usuarios"].update_one(
                                {"email": email.strip().lower()},
                                {"$set": {"_id": temp_user_id}}
                            )
                            st.session_state["user_id"] = str(temp_user_id)
                        else:
                            st.session_state["user_id"] = str(new_uid)
                            
                        st.success("Cadastro realizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    st.stop()

# --- user logged in ---
# Sidebar details card
st.sidebar.markdown("<div style='background-color:#1C1936; padding:16px; border-radius:14px; border:1px solid #2A264D; margin-bottom:15px; text-align:center;'>", unsafe_allow_html=True)
if current_user.get("foto_url"):
    try:
        u_img = base64_to_bytes(current_user["foto_url"])
        st.sidebar.image(u_img, width=120)
    except Exception:
        st.sidebar.markdown(f"<div class='user-avatar-emoji' style='margin: 0 auto 10px auto;'>{current_user['avatar']}</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"<div class='user-avatar-emoji' style='margin: 0 auto 10px auto;'>{current_user['avatar']}</div>", unsafe_allow_html=True)

st.sidebar.markdown(f"<h3 style='margin:0; color:#F3F4F6;'>{current_user['nome']}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='margin:4px 0 0 0; color:#9CA3AF; font-size:0.9em;'>🔥 {current_user.get('streak_atual', 0)} dias de Streak</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='margin:2px 0 0 0; color:#22C55E; font-weight:700; font-size:1.05em;'>🏆 {current_user.get('pontos_consistencia', 0)} Pts</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Display group info
user_group = None
if current_user.get("grupo_id"):
    user_group = db["grupos"].find_one({"_id": current_user["grupo_id"]})
    if user_group:
        st.sidebar.markdown("<div style='background-color:#1C1936; padding:14px; border-radius:12px; border:1px solid #2A264D; margin-bottom:15px;'>", unsafe_allow_html=True)
        if user_group.get("foto_url"):
            try:
                g_img = base64_to_bytes(user_group["foto_url"])
                st.sidebar.image(g_img, width=100)
            except Exception:
                pass
        st.sidebar.markdown(f"<strong style='color:#22C55E; font-size:1.05em;'>Grupo: {user_group['nome']}</strong>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<code style='background-color:#2A264D; color:#22C55E; padding:2px 6px; border-radius:4px;'>Código: {user_group['codigo_acesso']}</code>", unsafe_allow_html=True)
        st.sidebar.caption(user_group["descricao"])
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    else:
        st.sidebar.warning("Você foi associado a um grupo inexistente.")
else:
    st.sidebar.warning("Você não está em nenhum grupo.")

# Sidebar - Edit Profile
with st.sidebar.expander("⚙️ Editar Perfil"):
    with st.form("edit_profile_form"):
        new_nome = st.text_input("Nome", value=current_user["nome"])
        new_email = st.text_input("E-mail", value=current_user["email"])
        new_senha = st.text_input("Nova Senha (deixe em branco para manter a atual)", value="", type="password")
        new_avatar = st.selectbox("Emoji Avatar", ["💪", "🍗", "🥗", "🏃", "🥦", "🍎", "🔥"], index=["💪", "🍗", "🥗", "🏃", "🥦", "🍎", "🔥"].index(current_user["avatar"]))
        new_photo = st.file_uploader("Alterar Foto de Perfil", type=["jpg", "jpeg", "png"])
        
        save_profile = st.form_submit_button("Salvar Alterações")
        if save_profile:
            p_b64 = None
            if new_photo:
                try:
                    img_edit = Image.open(new_photo)
                    img_edit.thumbnail((300, 300))
                    p_b64 = img_to_base64(img_edit)
                except Exception as e:
                    st.error(f"Erro ao processar foto: {e}")
            try:
                database.update_user(
                    db, current_user["_id"], new_nome, new_email, new_senha, new_avatar, p_b64
                )
                # Invalida cache do usuario — proximo rerun busca dados frescos
                cache.invalidar_usuario(redis_client, str(current_user["_id"]))
                st.success("Perfil atualizado!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

if not user_group:
    with st.sidebar.expander("🔑 Entrar ou Criar Grupo"):
        grp_act = st.radio("Escolha uma opção:", ["Entrar", "Criar"], key="sidebar_grp_act_new")
        if grp_act == "Entrar":
            code = st.text_input("Código de Acesso")
            if st.button("Entrar no Grupo"):
                try:
                    grp = database.join_group(db, current_user["_id"], code)
                    st.success(f"Você entrou no grupo {grp['nome']}!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            g_n = st.text_input("Nome do Grupo")
            g_d = st.text_input("Descrição do Grupo")
            g_c = st.text_input("Código de Acesso")
            uploaded_grp_pic = st.file_uploader("Foto do Grupo (Opcional)", type=["jpg", "jpeg", "png"], key="sidebar_grp_pic")
            
            if st.button("Criar Grupo"):
                if g_n and g_c:
                    g_pic_b64 = None
                    if uploaded_grp_pic:
                        try:
                            img_grp = Image.open(uploaded_grp_pic)
                            img_grp.thumbnail((400, 400))
                            g_pic_b64 = img_to_base64(img_grp)
                        except Exception as e:
                            st.error(str(e))
                            st.stop()
                    try:
                        g_id = database.create_group(db, g_n, g_d, g_c, current_user["_id"], g_pic_b64)
                        db["usuarios"].update_one(
                            {"_id": current_user["_id"]},
                            {"$set": {"grupo_id": g_id}}
                        )
                        st.success(f"Grupo {g_n} criado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("Log Out", use_container_width=True):
    cache.invalidar_usuario(redis_client, str(st.session_state["user_id"]))  # limpa cache
    st.session_state["user_id"] = None
    st.rerun()

# --- Main App Header Banner ---
if logo_b64:
    st.markdown(f"""
    <div style='display: flex; justify-content: center; margin-bottom: 25px;'>
        <img src='data:image/png;base64,{logo_b64}' style='width: 300px; max-width: 100%; object-fit: contain;'>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align:center; color:#22C55E;'>DietRats 🥗💪</h2>", unsafe_allow_html=True)

# --- Navigation tabs ---
tabs = st.tabs(["Feed Principal", "Registrar Refeição", "Ranking dos Atletas", "Notificações"], key=st.session_state["tab_key"])

# --- TAB 1: FEED PRINCIPAL ---
with tabs[0]:
    if not user_group:
        st.info("Entre em um grupo existente ou crie o seu na barra lateral para ver o feed de postagens!")
    else:
        meals = database.get_group_feed(db, user_group["_id"], redis=redis_client)
        
        if not meals:
            st.info("Ainda não há postagens neste grupo. Registre sua primeira refeição para começar!")
            
        for idx, meal in enumerate(meals):
            # Usa dados do autor ja embutidos pela aggregation (sem query extra)
            meal_user = meal.get("autor", {})
            if not meal_user:
                continue

            # Header Avatar
            avatar_html = ""
            if meal_user.get("foto_url"):
                avatar_html = f"<img class='user-avatar-img' src='data:image/png;base64,{meal_user['foto_url']}'>"
            else:
                avatar_html = f"<div class='user-avatar-emoji'>{meal_user['avatar']}</div>"
            
            # Setup Card container natively to fix size/rendering bugs
            with st.container():
                header_html = f"""\
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid #2A264D; padding-bottom:10px;'>
                    <div style='display:flex; align-items:center;'>
                        {avatar_html}
                        <div style='font-weight:700; color:#F3F4F6; font-size:1.3em; margin-left:12px;'>{meal_user['nome']}</div>
                    </div>
                    <span class='meal-type-tag'>{meal['tipo']}</span>
                </div>
                """
                st.markdown(textwrap.dedent(header_html), unsafe_allow_html=True)
                
                # Legend / Description with enlarged sizes
                if meal.get("legenda"):
                    st.markdown(f"<div style='font-size:1.35em; font-weight:700; color:#F3F4F6; margin-bottom:10px; font-style:italic; border-left:4px solid #22C55E; padding-left:12px;'>\"{meal['legenda']}\"</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='color:#E5E7EB; font-size:1.15em; margin-bottom:18px; line-height:1.6;'>{meal['descricao']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.9em; color:#9CA3AF; margin-top:-8px; margin-bottom:16px;'>Postado em: {meal['data']}</div>", unsafe_allow_html=True)
                
                # Display post image using native st.image inside container to handle large uploads smoothly
                if meal.get("foto_url"):
                    try:
                        img_bytes = base64_to_bytes(meal["foto_url"])
                        st.image(img_bytes, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro ao carregar imagem: {e}")
                
                st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
                
                # Reações — lidas diretamente do array embutido no documento
                reacoes_embutidas = meal.get("reacoes", [])
                react_counts = {}
                for r in reacoes_embutidas:
                    react_counts[r["tipo"]] = react_counts.get(r["tipo"], 0) + 1

                react_cols = st.columns(6)
                emojis = ["💪", "🔥", "🥗", "❤️", "🍗", "😮"]

                for e_idx, emoji in enumerate(emojis):
                    count = react_counts.get(emoji, 0)
                    btn_label = f"{emoji} {count}"
                    if react_cols[e_idx].button(btn_label, key=f"react_{meal['_id']}_{emoji}_{idx}"):
                        database.toggle_reaction(
                            db, meal["_id"], current_user["_id"], emoji, current_user["nome"]
                        )
                        st.rerun()

                # Comentários — lidos diretamente do array embutido no documento
                comments_list = meal.get("comentarios", [])
                if comments_list:
                    st.markdown("<div style='background-color:#110E26; padding:12px 18px; border-radius:10px; margin-top:14px; border:1px solid #2A264D;'>", unsafe_allow_html=True)
                    st.markdown("<strong style='font-size:0.9em; color:#22C55E;'>Comentários:</strong>", unsafe_allow_html=True)
                    for c in comments_list:
                        c_nome = c.get("nome", "Atleta")
                        c_avatar = ""
                        # Converte usuario_id para ObjectId para buscar no banco
                        try:
                            from bson import ObjectId
                            c_uid = c["usuario_id"] if isinstance(c["usuario_id"], ObjectId) else ObjectId(str(c["usuario_id"]))
                            c_user = db["usuarios"].find_one({"_id": c_uid}, {"avatar": 1, "foto_url": 1})
                        except Exception:
                            c_user = None
                        if c_user and c_user.get("foto_url"):
                            c_avatar = f"<img style='width:24px; height:24px; border-radius:50%; object-fit:cover; display:inline-block; vertical-align:middle; margin-right:6px;' src='data:image/png;base64,{c_user['foto_url']}'>"
                        elif c_user:
                            c_avatar = f"<span style='font-size:1.1em; margin-right:6px; vertical-align:middle;'>{c_user['avatar']}</span>"
                        st.markdown(f"<div style='margin-bottom:8px; font-size:0.93em; color:#F3F4F6;'>{c_avatar} <strong>{c_nome}:</strong> <span style='color:#9CA3AF;'>{c['texto']}</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # Formulário para adicionar comentário
                with st.form(key=f"comment_form_{meal['_id']}_{idx}"):
                    comment_text = st.text_input("Escreva um comentário...", label_visibility="collapsed")
                    c_submit = st.form_submit_button("Comentar")
                    if c_submit and comment_text.strip():
                        database.add_comment(
                            db, meal["_id"], current_user["_id"], comment_text.strip(), current_user["nome"]
                        )
                        st.success("Comentário adicionado!")
                        st.rerun()

# --- TAB 2: REGISTRAR REFEIÇÃO ---
with tabs[1]:
    st.subheader("Registrar Nova Refeição 📸")
    st.info("💡 Cada refeição registrada aumenta em **+10** seus pontos de consistência e mantém seu streak diário!")
    
    if not user_group:
        st.warning("Você precisa fazer parte de um grupo para poder registrar refeições.")
    else:
        with st.form("meal_register_form_new"):
            tipo = st.selectbox("Tipo de Refeição", ["Café", "Almoço", "Jantar"])
            descricao = st.text_area("O que você comeu? (Ingredientes/Descrição)*")
            legenda = st.text_input("Legenda para a postagem (Opcional)")
            data_refeicao = st.date_input("Data da Refeição", value=datetime.date.today())
            uploaded_file = st.file_uploader("Foto do seu prato (Obrigatória)*", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Postar no Feed")
            
            if submitted:
                if not uploaded_file:
                    st.error("Você precisa carregar uma foto da sua refeição.")
                elif not descricao.strip():
                    st.error("Descreva o que comeu para que outros atletas possam ver.")
                else:
                    try:
                        img = Image.open(uploaded_file)
                        img.thumbnail((800, 800))
                        meal_b64 = img_to_base64(img)
                        
                        date_str = data_refeicao.strftime("%Y-%m-%d")
                        
                        new_streak = database.add_meal(
                            db, current_user["_id"], tipo, descricao, legenda, meal_b64, date_str
                        )
                        
                        st.success(f"Refeição registrada com sucesso! Você ganhou +10 pontos. Streak atual: {new_streak} dias 🔥")
                        st.session_state["tab_key"] = f"tabs_v{datetime.datetime.now().timestamp()}"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar refeição: {e}")

# --- TAB 3: RANKING DOS ATLETAS ---
with tabs[2]:
    st.subheader("Ranking de Consistência do Grupo 🏆")

    if not user_group:
        st.info("Entre ou crie um grupo na barra lateral para ver o ranking dos atletas.")
    else:
        ranking_users = database.get_ranking(db, user_group["_id"])

        for pos, u in enumerate(ranking_users, 1):
            medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else "🏃"

            u_avatar_html = ""
            if u.get("foto_url"):
                u_avatar_html = f"<img style='width:56px; height:56px; border-radius:50%; object-fit:cover; border:2px solid #22C55E;' src='data:image/png;base64,{u['foto_url']}'>"
            else:
                u_avatar_html = f"<span style='font-size: 1.7em; background-color: #2A264D; width:56px; height:56px; border-radius:50%; display:flex; align-items:center; justify-content:center; border: 2px solid #22C55E;'>{u['avatar']}</span>"

            st.markdown(f"""
            <div class="ranking-card" style="background-color:#1C1936; border:1px solid #2A264D; border-left:6px solid #22C55E;">
                <div style="display: flex; align-items: center; gap: 18px;">
                    <span class="ranking-position">{medal} {pos}</span>
                    {u_avatar_html}
                    <div>
                        <strong style="color: #F3F4F6; font-size: 1.35em; font-weight:700;">{u['nome']}</strong>
                        <div style="font-size: 1.05em; color: #9CA3AF; margin-top:4px;">Streak: {u.get('streak_atual', 0)} dias 🔥</div>
                    </div>
                </div>
                <div style="text-align: right; min-width:80px;">
                    <span style="font-size: 1.8em; font-weight: 800; color: #22C55E; display:block;">{u.get('pontos_consistencia', 0)}</span>
                    <div style="font-size: 0.85em; color: #9CA3AF; font-weight:700; text-transform:uppercase; margin-top:-2px;">pontos</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Hall da Fama — Top 5 do App Inteiro ──────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1C1936 0%, #2A1A4A 100%);
                border: 1px solid #6D28D9; border-radius: 20px; padding: 28px;
                margin-top: 10px; box-shadow: 0 0 30px rgba(109,40,217,0.25);'>
        <div style='text-align:center; margin-bottom: 20px;'>
            <div style='font-size:2.5em;'>🌟</div>
            <h2 style='color:#F3F4F6; font-size:1.7em; font-weight:900; margin:6px 0 4px;'>Hall da Fama</h2>
            <p style='color:#9CA3AF; font-size:1em; margin:0;'>Os 5 atletas mais dedicados do DietRats</p>
            <div style='width:60px; height:3px; background:#22C55E; margin:12px auto 0;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    hall = database.get_hall_da_fama(db, redis=redis_client)

    if not hall:
        st.info("Ainda não há registros suficientes para o Hall da Fama.")
    else:
        crowns = ["👑", "🥈", "🥉", "4️⃣", "5️⃣"]
        border_colors = ["#F59E0B", "#94A3B8", "#CD7F32", "#2A264D", "#2A264D"]
        glow_colors  = ["rgba(245,158,11,0.3)", "rgba(148,163,184,0.2)",
                        "rgba(205,127,50,0.2)", "rgba(0,0,0,0)", "rgba(0,0,0,0)"]

        for pos, h in enumerate(hall, 1):
            crown = crowns[pos - 1]
            bc    = border_colors[pos - 1]
            gc    = glow_colors[pos - 1]

            if h.get("foto_url"):
                h_avatar = f"<img style='width:60px; height:60px; border-radius:50%; object-fit:cover; border:3px solid {bc};' src='data:image/png;base64,{h['foto_url']}'>"
            else:
                h_avatar = f"<span style='font-size:1.9em; background-color:#2A264D; width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:3px solid {bc};'>{h['avatar']}</span>"

            st.markdown(f"""
            <div style='display:flex; align-items:center; justify-content:space-between;
                        background-color:#1C1936; padding:18px 24px; border-radius:16px;
                        margin-bottom:12px; border:1px solid {bc};
                        box-shadow: 0 0 18px {gc};'>
                <div style='display:flex; align-items:center; gap:16px;'>
                    <span style='font-size:2em; min-width:40px; text-align:center;'>{crown}</span>
                    {h_avatar}
                    <div>
                        <div style='font-weight:800; color:#F3F4F6; font-size:1.25em;'>{h['nome']}</div>
                        <div style='font-size:0.9em; color:#9CA3AF; margin-top:3px;'>🏠 {h.get('grupo_nome','Sem Grupo')}</div>
                        <div style='font-size:0.85em; color:#6D28D9; margin-top:2px; font-weight:700;'>🔥 {h.get('streak_atual',0)} dias de streak</div>
                    </div>
                </div>
                <div style='text-align:right; min-width:90px;'>
                    <span style='font-size:2em; font-weight:900; color:{bc}; display:block;'>{h.get('total_refeicoes',0)}</span>
                    <div style='font-size:0.78em; color:#9CA3AF; font-weight:700; text-transform:uppercase;'>refeições</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style='margin-top:20px; background:linear-gradient(135deg,#15803D,#22C55E);
                    border-radius:14px; padding:20px 24px; text-align:center;
                    box-shadow: 0 4px 20px rgba(34,197,94,0.25);'>
            <div style='font-size:1.6em; margin-bottom:6px;'>🎁</div>
            <div style='color:#fff; font-size:1.1em; font-weight:800; margin-bottom:4px;'>Parabéns aos campeões!</div>
            <div style='color:rgba(255,255,255,0.85); font-size:0.95em;'>
                Os atletas no Top 5 serão reconhecidos pela comunidade DietRats.
                Continue registrando suas refeições e mantenha o foco! 💪
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 4: NOTIFICAÇÕES ---
with tabs[3]:
    st.subheader("Suas Notificações 🔔")

    notifications = database.get_notifications(db, current_user["_id"])

    if not notifications:
        st.info("Nenhuma notificação por aqui no momento. Quando alguém reagir ou comentar nas suas postagens, aparecerá aqui! 💬")
    else:
        col_n1, col_n2 = st.columns([3, 1])
        with col_n2:
            if st.button("✅ Marcar como lidas", use_container_width=True):
                database.mark_notifications_read(db, current_user["_id"])
                st.success("Marcadas como lidas!")
                st.rerun()

        novas   = sum(1 for n in notifications if n.get("is_nova"))
        with col_n1:
            if novas:
                st.markdown(f"<span style='color:#22C55E; font-weight:700;'>🟢 {novas} nova(s) interação(ões) nos seus posts</span>", unsafe_allow_html=True)

        for n in notifications:
            is_nova      = n.get("is_nova", False)
            badge        = "🟢 Nova" if is_nova else "⚪ Vista"
            bg_color     = "#1C1936" if is_nova else "#15132a"
            border_color = "#22C55E" if is_nova else "#2A264D"
            emoji        = n.get("emoji", "🔔")
            data_fmt     = n["data"].strftime("%d/%m/%Y %H:%M") if n.get("data") else ""

            st.markdown(f"""
            <div style="background-color:{bg_color}; border:1px solid {border_color};
                        padding:14px 20px; border-radius:12px; margin-bottom:12px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="font-size:0.8em; font-weight:700; color:#22C55E; text-transform:uppercase;">{badge}</span>
                    <span style="font-size:0.75em; color:#9CA3AF;">{data_fmt}</span>
                </div>
                <div style="font-size:1em; color:#F3F4F6;">{emoji} {n['texto']}</div>
            </div>
            """, unsafe_allow_html=True)
