import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from pyairtable import Api

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(
    page_title="Portal PRODISE", 
    page_icon="🏭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TUS CLAVES ---
AIRTABLE_API_TOKEN = "pat3Ig7rAOvq7JdpN.fbef700fa804ae5692e3880899bba070239e9593f8d6fde958d9bd3d615aca14"
AIRTABLE_BASE_ID = "app2jaysCvPwvrBwI"

# ==========================================
# 2. GENERADOR DE SILUETA
# ==========================================
def get_default_profile_pic():
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#B0BEC5" width="100%" height="100%">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
    </svg>
    """
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

DEFAULT_IMG = get_default_profile_pic()

# ==========================================
# 3. ESTILOS VISUALES (FIX FINAL: MENU OSCURO + RADIO VERTICAL)
# ==========================================
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as file:
            enc = base64.b64encode(file.read())
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url(data:image/jpg;base64,{enc.decode()});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-color: #000000;
            }}
            /* Capa oscura superpuesta */
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background-color: rgba(5, 5, 10, 0.92);
                z-index: -1;
            }}
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #000000; }</style>", unsafe_allow_html=True)

add_bg_from_local('fondo.jpg')
LOGO_FILE = "logo.png"

st.markdown("""
<style>
    /* 1. RESET EXTREMO */
    :root { color-scheme: dark !important; }
    
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        background-color: #000000 !important;
        color: #E0E0E0 !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* ============================================================
       2. FIX SELECTBOX & LISTAS DESPLEGABLES (ELIMINAR FONDO BLANCO)
       ============================================================ */
    
    /* Input seleccionado (Caja cerrada) */
    div[data-baseweb="select"] > div:first-child {
        background-color: #1E1E2E !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }

    /* CONTENEDOR FLOTANTE (POPOVER) - EL CULPABLE DEL BLANCO */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div {
        background-color: #1E1E2E !important;
        color: white !important;
        border: 1px solid #444 !important;
    }

    /* LA LISTA (UL) */
    ul[data-baseweb="menu"],
    ul[role="listbox"] {
        background-color: #1E1E2E !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* LAS OPCIONES (LI) */
    li[data-baseweb="option"],
    li[role="option"] {
        background-color: #1E1E2E !important; /* Fondo oscuro forzado */
        color: #E0E0E0 !important;             /* Texto claro forzado */
    }

    /* HOVER EN LAS OPCIONES */
    li[data-baseweb="option"]:hover, 
    li[data-baseweb="option"][aria-selected="true"],
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #0288D1 !important; /* Azul */
        color: white !important;
    }
    
    /* Forzar color de texto interno en las opciones */
    li[role="option"] * { color: inherit !important; }

    /* ============================================================
       3. FIX RADIO BUTTONS (APILADOS VERTICALMENTE)
       ============================================================ */
    
    /* Contenedor del grupo de opciones */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: column !important; /* FORZAR COLUMNA */
        gap: 10px;
    }

    /* Cada opción individual */
    div[role="radiogroup"] label {
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        color: #ddd !important;
        width: 100% !important; /* Ocupar todo el ancho */
        margin-right: 0 !important;
        display: flex;
        align-items: center;
        padding: 10px 15px;
        border-radius: 8px;
    }

    div[role="radiogroup"] label:hover {
        background-color: rgba(255,255,255,0.1);
        border-color: #4FC3F7;
    }

    /* ============================================================
       4. INPUTS DE TEXTO (BUSCADOR) & ESTILOS GENERALES
       ============================================================ */
    div[data-testid="stTextInput"] > div,
    div[data-baseweb="input"] > div {
        background-color: transparent !important;
        border: none !important;
    }

    .stTextInput input, 
    input[type="text"], 
    input[type="password"] {
        background-color: #1E1E2E !important; 
        color: white !important;
        border: 1px solid #555 !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
    }
    
    /* Autocompletado Chrome */
    input:-webkit-autofill,
    input:-webkit-autofill:hover, 
    input:-webkit-autofill:focus, 
    input:-webkit-autofill:active {
        -webkit-box-shadow: 0 0 0 30px #1E1E2E inset !important;
        -webkit-text-fill-color: white !important;
        border-radius: 50px !important;
    }

    h1, h2 { color: #4FC3F7 !important; text-shadow: 0px 0px 10px rgba(79, 195, 247, 0.4); }
    h3, h4, h5 { color: #FFFFFF !important; }
    p, label, span, li, div { color: #B0BEC5; }

    .css-card {
        background: rgba(20, 20, 30, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    .css-card h2 { color: white !important; }

    div.stButton > button {
        background: linear-gradient(135deg, #0288D1 0%, #01579B 100%);
        color: white !important;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(2, 136, 209, 0.4);
    }

    [data-testid="stSidebar"] {
        background-color: #0a0e14 !important;
        border-right: 1px solid #222;
    }
    
    .podio-emoji { font-size: 3.5rem; display: block; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. CONEXIÓN Y CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    try:
        api = Api(AIRTABLE_API_TOKEN)
        def get_df(t_name):
            try:
                t = api.table(AIRTABLE_BASE_ID, t_name)
                recs = t.all()
                if not recs: return pd.DataFrame(), t
                df = pd.DataFrame([r['fields'] for r in recs])
                for c in df.columns: df[c] = df[c].astype(str)
                return df, t
            except: return pd.DataFrame(), None
            
        df_u, _ = get_df("DB_USUARIOS")
        df_p, _ = get_df("DB_PERSONAL")
        df_r, _ = get_df("CONFIG_ROLES")
        df_h, tbl_h = get_df("DB_HISTORIAL")
        df_c, _ = get_df("CONFIG")
        
        if not df_r.empty and 'PORCENTAJE' in df_r.columns:
            df_r['PORCENTAJE'] = pd.to_numeric(df_r['PORCENTAJE'], errors='coerce').fillna(0)
        if not df_h.empty and 'NOTA_FINAL' in df_h.columns:
            df_h['NOTA_FINAL'] = pd.to_numeric(df_h['NOTA_FINAL'], errors='coerce').fillna(0)
            
        return df_u, df_p, df_r, df_h, tbl_h, df_c
    except:
        return None, None, None, None, None, None

df_users, df_personal, df_roles, df_historial, tbl_historial, df_config = load_data()

# --- VALIDACIÓN DE PARADA ---
parada_actual = "GENERAL"
if df_config is not None and not df_config.empty:
    if 'COD_PARADA' in df_config.columns:
        parada_actual = str(df_config.iloc[0]['COD_PARADA'])
    else:
        parada_actual = str(df_config.iloc[0].values[0])

def get_photo_url(url_raw):
    if not url_raw or str(url_raw).lower() == 'nan' or len(str(url_raw)) < 5:
        return DEFAULT_IMG
    return url_raw

if 'usuario' not in st.session_state:
    st.session_state.update({'usuario': None, 'nombre_real': None, 'rol': None, 'dni_user': None})

# ==========================================
# 5. APLICACIÓN
# ==========================================

# --- LOGIN ---
if not st.session_state.usuario:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,0.8,1])
    with c2:
        st.markdown("""
        <div class="css-card" style="text-align: center;">
            <h1 style="margin:0; font-size: 2.5rem;">🔐 PRODISE</h1>
            <p style="margin-top: 10px;">Acceso Corporativo Seguro</p>
        </div>
        """, unsafe_allow_html=True)
        
        user = st.text_input("ID Usuario", placeholder="Ingrese su usuario")
        pw = st.text_input("Contraseña", type="password", placeholder="••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INICIAR SESIÓN", use_container_width=True):
            if df_users is not None and not df_users.empty:
                u = df_users[df_users['USUARIO'] == user]
                if not u.empty and str(u.iloc[0]['PASS']) == pw and u.iloc[0]['ESTADO'] == 'ACTIVO':
                    st.session_state.usuario = user
                    st.session_state.nombre_real = u.iloc[0]['NOMBRE']
                    st.session_state.rol = str(u.iloc[0]['ID_ROL']).upper().strip()
                    st.session_state.dni_user = str(u.iloc[0]['DNI_TRABAJADOR'])
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
            else: st.error("❌ Error de conexión")

else:
    # --- SIDEBAR ---
    opciones = ["📝 Evaluar Personal", "📂 Mi Historial"]
    if st.session_state.rol == 'ADMIN':
        opciones.insert(1, "🏆 Ranking Global")

    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        st.markdown(f"### 👤 {st.session_state.nombre_real}")
        st.caption(f"{st.session_state.rol}")
        st.info(f"⚙️ Parada Activa:\n**{parada_actual}**")
        seleccion = st.radio("Navegación", opciones)
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    # Filtros Supervisor
    data_view = df_personal[df_personal['ESTADO'] == 'ACTIVO'] if df_personal is not None else pd.DataFrame()
    if st.session_state.rol == 'SUPERVISOR DE OPERACIONES' and not data_view.empty:
        me = data_view[data_view['DNI'] == st.session_state.dni_user]
        if not me.empty:
            grp, trn = me.iloc[0]['ID_GRUPO'], me.iloc[0]['TURNO']
            data_view = data_view[(data_view['ID_GRUPO'] == grp) & (data_view['TURNO'] == trn)]
            data_view = data_view[data_view['DNI'] != st.session_state.dni_user]

    # ----------------------------------------
    # 1. EVALUACIÓN (BÚSQUEDA HÍBRIDA)
    # ----------------------------------------
    if seleccion == "📝 Evaluar Personal":
        st.title(f"📝 Evaluación - {parada_actual}")
        
        st.markdown("##### 🔍 Buscar (Opcional)")
        filtro_texto = st.text_input("Filtro Rápido", placeholder="Escribe para filtrar la lista...", label_visibility="collapsed")
        
        lista_final = []
        indice_defecto = None
        
        if not data_view.empty:
            todas_opciones = data_view['NOMBRE_COMPLETO'].unique().tolist()
            if filtro_texto:
                lista_final = [x for x in todas_opciones if filtro_texto.upper() in x.upper()]
                if not lista_final:
                    st.warning(f"⚠️ No hay coincidencias para: '{filtro_texto}'")
                elif len(lista_final) == 1:
                    indice_defecto = 0
            else:
                lista_final = todas_opciones
                indice_defecto = None 
        
        sel_nombre = None
        if lista_final:
            sel_nombre = st.selectbox(
                "Seleccionar Colaborador:", 
                lista_final,
                index=indice_defecto,
                placeholder="👇 Despliega la lista completa aquí...",
                key="selector_final"
            )
        elif data_view.empty:
            st.warning("⚠️ No tienes personal asignado a tu grupo/turno.")
        
        if sel_nombre:
            p = data_view[data_view['NOMBRE_COMPLETO'] == sel_nombre].iloc[0]
            foto_final = get_photo_url(p.get('URL_FOTO', ''))
            
            st.markdown(f"""
            <div class="css-card" style="display: flex; align-items: center; gap: 20px; margin-top: 15px;">
                <img src="{foto_final}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #4FC3F7; object-fit: cover; background-color: #222;">
                <div>
                    <h2 style="margin:0; color: white !important;">{p['NOMBRE_COMPLETO']}</h2>
                    <p style="margin:0; font-size: 1.2em; color: #4FC3F7;">{p['CARGO_ACTUAL']}</p>
                    <span style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 6px; font-size: 0.9em; margin-top: 5px; display: inline-block;">
                        {p['ID_GRUPO']} - {p['TURNO']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            preguntas = pd.DataFrame()
            if df_roles is not None and not df_roles.empty:
                df_roles['CARGO_NORM'] = df_roles['CARGO'].astype(str).str.upper().str.strip()
                preguntas = df_roles[df_roles['CARGO_NORM'] == str(p['CARGO_ACTUAL']).upper().strip()]

            if preguntas.empty:
                st.warning("⚠️ No hay criterios configurados para este cargo.")
            else:
                with st.form("frm_eval"):
                    score_total = 0
                    notas_save = {}
                    st.markdown("### Criterios de Desempeño")
                    for i, (idx, row) in enumerate(preguntas.iterrows(), 1):
                        st.markdown(f"**{i}. {row['CRITERIO']}** <span style='font-size:0.85em; color:#888'>({row['PORCENTAJE']*100:.0f}%)</span>", unsafe_allow_html=True)
                        opciones = [
                            str(row.get('NIVEL_1', 'Nivel 1')),
                            str(row.get('NIVEL_2', 'Nivel 2')),
                            str(row.get('NIVEL_3', 'Nivel 3')),
                            str(row.get('NIVEL_4', 'Nivel 4')),
                            str(row.get('NIVEL_5', 'Nivel 5'))
                        ]
                        # CAMBIO IMPORTANTE: horizontal=False PARA QUE ESTÉN APILADOS
                        seleccion_texto = st.radio(
                            label=f"r_{i}", 
                            options=opciones, 
                            key=f"rad_{i}", 
                            horizontal=False, # <-- AQUI FORZAMOS VERTICAL
                            label_visibility="collapsed"
                        )
                        nota_numerica = opciones.index(seleccion_texto) + 1
                        score_total += nota_numerica * row['PORCENTAJE']
                        notas_save[f"NOTA_{i}"] = nota_numerica
                        st.divider()
                    
                    obs = st.text_area("Observaciones Generales", height=100)
                    enviar = st.form_submit_button("✅ GUARDAR EVALUACIÓN", use_container_width=True)
                    
                    if enviar:
                        if obs and tbl_historial:
                            record = {
                                "FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "COD_PARADA": parada_actual,
                                "DNI_EVALUADOR": st.session_state.dni_user,
                                "DNI_TRABAJADOR": str(p['DNI']),
                                "CARGO_MOMENTO": str(p['CARGO_ACTUAL']),
                                "GRUPO_MOMENTO": str(p['ID_GRUPO']),
                                "TURNO_MOMENTO": str(p['TURNO']),
                                "NOTA_FINAL": round(score_total, 2),
                                "COMENTARIOS": obs
                            }
                            record.update(notas_save)
                            try:
                                tbl_historial.create(record)
                                st.balloons()
                                st.success(f"¡Registrado! Nota Final: {round(score_total, 2)}")
                            except Exception as e: st.error(f"Error: {e}")
                        else: st.warning("⚠️ La observación es obligatoria.")

    # ----------------------------------------
    # 2. RANKING GLOBAL
    # ----------------------------------------
    elif seleccion == "🏆 Ranking Global" and st.session_state.rol == 'ADMIN':
        st.title("🏆 Tabla de Posiciones")
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            df_personal['DNI'] = df_personal['DNI'].astype(str)
            resumen = df_historial.groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index()
            resumen.columns = ['DNI', 'PROMEDIO']
            ranking = pd.merge(resumen, df_personal, on='DNI', how='left')
            ranking['PROMEDIO'] = ranking['PROMEDIO'].round(2)
            cargos_disp = ["TODOS"] + sorted(ranking['CARGO_ACTUAL'].dropna().unique().tolist())
            filtro_cargo = st.selectbox("Filtrar por Cargo:", cargos_disp)
            if filtro_cargo != "TODOS": ranking = ranking[ranking['CARGO_ACTUAL'] == filtro_cargo]
            ranking = ranking.sort_values('PROMEDIO', ascending=False).reset_index(drop=True)
            
            if len(ranking) >= 3:
                c2, c1, c3 = st.columns([1, 1.2, 1])
                with c2:
                    p2 = ranking.iloc[1]
                    f2 = get_photo_url(p2.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #C0C0C0;">
                        <span class="podio-emoji">🥈</span>
                        <img src="{f2}" style="width:90px; height:90px; border-radius:50%; object-fit:cover; background:#222; margin: 10px 0;">
                        <h4 style="margin:5px 0;">{p2['NOMBRE_COMPLETO']}</h4>
                        <h2 style="color:#C0C0C0;">{p2['PROMEDIO']}</h2>
                    </div>""", unsafe_allow_html=True)
                with c1:
                    p1 = ranking.iloc[0]
                    f1 = get_photo_url(p1.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #FFD700; transform: scale(1.05);">
                        <span class="podio-emoji">🥇</span>
                        <img src="{f1}" style="width:120px; height:120px; border-radius:50%; object-fit:cover; border: 4px solid #FFD700; background:#222; margin: 10px 0;">
                        <h3 style="margin:5px 0; color:#FFD700;">{p1['NOMBRE_COMPLETO']}</h3>
                        <h1 style="color:#FFD700; font-size:3rem;">{p1['PROMEDIO']}</h1>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    p3 = ranking.iloc[2]
                    f3 = get_photo_url(p3.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #CD7F32;">
                        <span class="podio-emoji">🥉</span>
                        <img src="{f3}" style="width:90px; height:90px; border-radius:50%; object-fit:cover; background:#222; margin: 10px 0;">
                        <h4 style="margin:5px 0;">{p3['NOMBRE_COMPLETO']}</h4>
                        <h2 style="color:#CD7F32;">{p3['PROMEDIO']}</h2>
                    </div>""", unsafe_allow_html=True)

            st.markdown("### 📊 Listado Completo")
            st.data_editor(
                ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'PROMEDIO']],
                column_config={"PROMEDIO": st.column_config.ProgressColumn("Nota Global", min_value=0, max_value=5, format="%.2f"), "NOMBRE_COMPLETO": "Colaborador", "CARGO_ACTUAL": "Cargo"},
                hide_index=True, use_container_width=True, disabled=True
            )
        else: st.info("No hay datos de ranking disponibles.")

    # ----------------------------------------
    # 3. HISTORIAL (CON NOMBRE COMPLETO)
    # ----------------------------------------
    elif seleccion == "📂 Mi Historial":
        st.title("📂 Historial de Registros")
        
        if df_historial is not None and not df_historial.empty:
            # LÓGICA DE CRUCE (MERGE) PARA TRAER EL NOMBRE
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            df_personal['DNI'] = df_personal['DNI'].astype(str)
            
            df_merged = pd.merge(
                df_historial, 
                df_personal[['DNI', 'NOMBRE_COMPLETO']], 
                left_on='DNI_TRABAJADOR', 
                right_on='DNI', 
                how='left'
            )
            df_merged['NOMBRE_COMPLETO'] = df_merged['NOMBRE_COMPLETO'].fillna(df_merged['DNI_TRABAJADOR'])
            
            cols_mostrar = ['COD_PARADA', 'NOMBRE_COMPLETO', 'NOTA_FINAL', 'COMENTARIOS']
            cols_existentes = [c for c in cols_mostrar if c in df_merged.columns]
            
            st.dataframe(
                df_merged[cols_existentes], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("No se encontraron registros.")