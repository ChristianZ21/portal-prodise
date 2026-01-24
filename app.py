import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import time
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
# 2. DEFINICIÓN DE PERMISOS Y JERARQUÍA
# ==========================================

ROLES_RESTRINGIDOS = [
    'LIDER MECANICO', 'OPERADOR DE GRUA', 'MECANICO', 'SOLDADOR', 
    'RIGGER', 'VIENTERO', 'ALMACENERO', 'CONDUCTOR', 'PSICOLOGA'
]

JERARQUIA = {
    'ADMIN': {'scope': 'ALL'},
    'GERENTE GENERAL': {'scope': 'ALL'},
    'GERENTE MANTENIMIENTO': {'scope': 'ALL'},
    'RESIDENTE': {'scope': 'ALL'},
    'COORDINADOR': {'scope': 'ALL'},
    'PLANNER': {'scope': 'ALL'},
    'PROGRAMADOR': {'scope': 'ALL'},
    
    'COORDINADOR DE SEGURIDAD': {'scope': 'SPECIFIC', 'targets': ['SUPERVISOR DE SEGURIDAD']},
    'VALORIZADORA': {'scope': 'SPECIFIC', 'targets': ['ASISTENTE DE PLANIFICACION', 'ASISTENTE ADMINISTRATIVO', 'PROGRAMADOR', 'PLANNER']},
    
    'SUPERVISOR DE OPERACIONES': {'scope': 'HYBRID', 'targets': ['PLANNER', 'CONDUCTOR']},
    'LIDER MECANICO': {'scope': 'GROUP', 'targets': []}, 
    'OPERADOR DE GRUA': {'scope': 'GROUP', 'targets': []}, 
}

# ==========================================
# 3. GENERADOR DE SILUETA
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
# 4. ESTILOS VISUALES (BLINDADO)
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
                background-position: top center; 
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-color: #000000;
            }}
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
    :root { color-scheme: dark !important; }
    html, body { margin: 0 !important; padding: 0 !important; background-color: #000000 !important; color: #E0E0E0 !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none !important; }

    /* INPUTS & CONTENEDORES */
    div[data-testid="stTextInput"] > div, div[data-testid="stTextArea"] > div,
    div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
        background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important;
    }

    /* INPUTS REALES */
    .stTextInput input, input[type="text"], input[type="password"] {
        background-color: #1E1E2E !important; color: white !important; border: 1px solid #555 !important;
        border-radius: 50px !important; padding: 10px 20px !important;
    }

    /* TEXT AREA SOLIDO */
    div[data-baseweb="textarea"] {
        background-color: #262730 !important; border: 2px solid #4FC3F7 !important;
        border-radius: 12px !important; padding: 5px !important;
    }
    .stTextArea textarea {
        background-color: #262730 !important; color: white !important; caret-color: #4FC3F7 !important; border: none !important;
    }
    div[data-baseweb="textarea"]:focus-within { box-shadow: 0 0 15px rgba(79, 195, 247, 0.5) !important; }

    /* AUTOCOMPLETE FIX */
    input:-webkit-autofill, textarea:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 30px #1E1E2E inset !important; -webkit-text-fill-color: white !important;
        transition: background-color 5000s ease-in-out 0s;
    }

    /* LISTAS & SELECTORES */
    div[data-baseweb="select"] > div:first-child {
        background-color: #1E1E2E !important; color: white !important; border: 1px solid #444 !important; border-radius: 8px !important;
    }
    div[data-baseweb="select"] span { color: white !important; }
    div[data-baseweb="select"] svg { fill: #B0BEC5 !important; }
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div { background-color: #1E1E2E !important; border: 1px solid #444 !important; }
    ul[data-baseweb="menu"] { background-color: #1E1E2E !important; padding: 0 !important; }
    li[data-baseweb="option"], li[role="option"] { background-color: #1E1E2E !important; color: #E0E0E0 !important; }
    li[data-baseweb="option"]:hover, li[role="option"][aria-selected="true"] { background-color: #0288D1 !important; color: white !important; }
    li[role="option"] * { color: inherit !important; }

    /* RADIO BUTTONS AZULES */
    div[role="radiogroup"] { display: flex; flex-direction: column !important; gap: 10px; }
    div[role="radiogroup"] label {
        background-color: #131720 !important; border: 1px solid #0288D1 !important; color: #E0E0E0 !important;
        width: 100% !important; padding: 12px 15px !important; border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important; transition: all 0.2s ease !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: #1E2A3A !important; border-color: #4FC3F7 !important; transform: translateX(5px); cursor: pointer;
    }

    /* BOTONES */
    button[kind="primaryFormSubmit"], div[data-testid="stFormSubmitButton"] > button, div.stButton > button {
        background: linear-gradient(135deg, #0288D1 0%, #01579B 100%) !important; color: white !important;
        border: none !important; font-weight: 600; border-radius: 8px; padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(2, 136, 209, 0.5); }
    
    .css-card {
        background: rgba(20, 20, 30, 0.75); backdrop-filter: blur(12px); border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08); padding: 24px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    h1, h2 { color: #4FC3F7 !important; text-shadow: 0px 0px 10px rgba(79, 195, 247, 0.4); }
    h3, h4, h5 { color: #FFFFFF !important; }
    p, label, span, li, div { color: #B0BEC5; }
    [data-testid="stSidebar"] { background-color: #0a0e14 !important; border-right: 1px solid #222; }
    .podio-emoji { font-size: 3.5rem; display: block; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. CONEXIÓN Y CARGA DE DATOS
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
                
                # --- LIMPIEZA INTELIGENTE ---
                for c in df.columns:
                    df[c] = df[c].astype(str).str.strip()
                    # NO TOCAR MAYÚSCULAS DE CONTRASEÑA
                    if c != 'PASS':
                        df[c] = df[c].str.upper()
                    # FIX GRUPOS (2.0 -> 2)
                    if c in ['ID_GRUPO', 'GRUPO']:
                        df[c] = df[c].str.replace('.0', '', regex=False)
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
# 6. APLICACIÓN
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
                # Busqueda exacta normalizada (Usuario Uppercase, Pass Original)
                u = df_users[df_users['USUARIO'] == user.strip().upper()]
                if not u.empty and str(u.iloc[0]['PASS']) == pw and u.iloc[0]['ESTADO'] == 'ACTIVO':
                    st.session_state.usuario = user
                    st.session_state.nombre_real = u.iloc[0]['NOMBRE']
                    st.session_state.rol = str(u.iloc[0]['ID_ROL']).upper().strip()
                    st.session_state.dni_user = str(u.iloc[0]['DNI_TRABAJADOR'])
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
            else: st.error("❌ Error de conexión")

else:
    # --- SIDEBAR (CON RESTRICCIONES) ---
    rol_actual = st.session_state.rol
    opciones = ["📝 Evaluar Personal"]
    
    if rol_actual not in ROLES_RESTRINGIDOS:
        if rol_actual == 'ADMIN':
            opciones = ["📝 Evaluar Personal", "🏆 Ranking Global", "📂 Mi Historial"]
        else:
            opciones = ["📝 Evaluar Personal", "📂 Mi Historial"]

    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        st.markdown(f"### 👤 {st.session_state.nombre_real}")
        st.caption(f"{rol_actual}")
        st.info(f"⚙️ Parada Activa:\n**{parada_actual}**")
        seleccion = st.radio("Navegación", opciones)
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    # ==============================================================
    # LÓGICA DE FILTRADO MAESTRA
    # ==============================================================
    data_view = df_personal[df_personal['ESTADO'] == 'ACTIVO'] if df_personal is not None else pd.DataFrame()
    
    if not data_view.empty:
        permisos = JERARQUIA.get(rol_actual, {'scope': 'GROUP', 'targets': []}) 
        scope = permisos.get('scope', 'GROUP')
        targets = permisos.get('targets', [])
        
        me = data_view[data_view['DNI'] == st.session_state.dni_user]
        grp_supervisor = str(me.iloc[0]['ID_GRUPO']).replace('.0','').strip() if not me.empty else ""
        trn = me.iloc[0]['TURNO'] if not me.empty else ""

        def check_grupo_match(grupos_trabajador, grupo_buscado):
            if not grupo_buscado: return False
            lista = [g.replace('.0','').strip() for g in str(grupos_trabajador).split(',')]
            return grupo_buscado in lista

        if scope == 'ALL':
            pass 
        elif scope == 'SPECIFIC':
            data_view = data_view[data_view['CARGO_ACTUAL'].isin(targets)]
        elif scope == 'GROUP':
            mask_grupo = data_view['ID_GRUPO'].apply(lambda x: check_grupo_match(x, grp_supervisor))
            mask_turno = data_view['TURNO'] == trn
            data_view = data_view[mask_grupo & mask_turno]
        elif scope == 'HYBRID':
            mask_cargos = data_view['CARGO_ACTUAL'].isin(targets)
            mask_grupo = data_view['ID_GRUPO'].apply(lambda x: check_grupo_match(x, grp_supervisor))
            mask_turno = data_view['TURNO'] == trn
            data_view = data_view[mask_cargos | (mask_grupo & mask_turno)]

        data_view = data_view[data_view['DNI'] != st.session_state.dni_user]

    # ----------------------------------------
    # 1. EVALUACIÓN
    # ----------------------------------------
    if seleccion == "📝 Evaluar Personal":
        st.title(f"📝 Evaluación - {parada_actual}")
        
        dnis_ya_evaluados = []
        if df_historial is not None and not df_historial.empty:
            filtro_historial = df_historial[
                (df_historial['DNI_EVALUADOR'] == st.session_state.dni_user) &
                (df_historial['COD_PARADA'] == parada_actual)
            ]
            dnis_ya_evaluados = filtro_historial['DNI_TRABAJADOR'].unique().tolist()
        
        if not data_view.empty:
            data_view = data_view[~data_view['DNI'].isin(dnis_ya_evaluados)]

        if data_view.empty:
            st.balloons()
            st.success("✅ Has completado todas las evaluaciones disponibles.")
        else:
            lista_final = data_view['NOMBRE_COMPLETO'].unique().tolist()
            sel_nombre = st.selectbox(
                f"Seleccionar Colaborador ({len(lista_final)} pendientes):", 
                lista_final, index=None, placeholder="👇 Haz clic aquí para desplegar la lista...", key="selector_final"
            )
            
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
                            opciones = [str(row.get(f'NIVEL_{j}')) for j in range(1, 6)]
                            seleccion_texto = st.radio(label=f"r_{i}", options=opciones, key=f"rad_{i}", horizontal=False, label_visibility="collapsed")
                            nota_numerica = opciones.index(seleccion_texto) + 1
                            score_total += nota_numerica * row['PORCENTAJE']
                            notas_save[f"NOTA_{i}"] = nota_numerica
                            st.divider()
                        
                        obs = st.text_area("Sustento de la Nota Final", height=100)
                        enviar = st.form_submit_button("✅ GUARDAR EVALUACIÓN", use_container_width=True)
                        
                        if enviar:
                            if obs and tbl_historial:
                                record = {
                                    "FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "COD_PARADA": parada_actual,
                                    "DNI_EVALUADOR": st.session_state.dni_user,
                                    "NOMBRE_EVALUADOR": st.session_state.nombre_real, # <--- NUEVO CAMPO
                                    "DNI_TRABAJADOR": str(p['DNI']),
                                    "NOMBRE_TRABAJADOR": str(p['NOMBRE_COMPLETO']),   # <--- NUEVO CAMPO
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
                                    st.success(f"¡Evaluación Guardada! Nota: {round(score_total, 2)}")
                                    time.sleep(2) 
                                    st.cache_data.clear() 
                                    st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                            else: st.warning("⚠️ La observación es obligatoria.")

    # ----------------------------------------
    # 2. RANKING GLOBAL
    # ----------------------------------------
    elif seleccion == "🏆 Ranking Global" and st.session_state.rol not in ROLES_RESTRINGIDOS:
        st.title("🏆 Tabla de Posiciones")
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            df_personal['DNI'] = df_personal['DNI'].astype(str)
            
            datos_actuales = df_historial[df_historial['COD_PARADA'] == parada_actual]
            datos_historicos = df_historial[df_historial['COD_PARADA'] != parada_actual]
            
            prom_actual = datos_actuales.groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index()
            prom_actual.columns = ['DNI', 'MEDIA_ACTUAL']
            
            prom_historico = datos_historicos.groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index()
            prom_historico.columns = ['DNI', 'MEDIA_HISTORICA']
            
            score_df = pd.merge(prom_actual, prom_historico, on='DNI', how='outer')
            
            def calcular_ponderado(row):
                actual = row['MEDIA_ACTUAL']
                hist = row['MEDIA_HISTORICA']
                if pd.notna(actual) and pd.notna(hist): return (actual * 0.70) + (hist * 0.30)
                elif pd.notna(actual): return actual
                elif pd.notna(hist): return hist
                else: return 0.0

            score_df['PROMEDIO_FINAL'] = score_df.apply(calcular_ponderado, axis=1)
            score_df['PROMEDIO_FINAL'] = score_df['PROMEDIO_FINAL'].round(2)
            
            ranking = pd.merge(score_df, df_personal, on='DNI', how='left')
            cargos_disp = ["TODOS"] + sorted(ranking['CARGO_ACTUAL'].dropna().unique().tolist())
            filtro_cargo = st.selectbox("Filtrar por Cargo:", cargos_disp)
            if filtro_cargo != "TODOS": ranking = ranking[ranking['CARGO_ACTUAL'] == filtro_cargo]
            
            ranking = ranking.sort_values('PROMEDIO_FINAL', ascending=False).reset_index(drop=True)
            
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
                        <h2 style="color:#C0C0C0;">{p2['PROMEDIO_FINAL']}</h2>
                    </div>""", unsafe_allow_html=True)
                with c1:
                    p1 = ranking.iloc[0]
                    f1 = get_photo_url(p1.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #FFD700; transform: scale(1.05);">
                        <span class="podio-emoji">🥇</span>
                        <img src="{f1}" style="width:120px; height:120px; border-radius:50%; object-fit:cover; border: 4px solid #FFD700; background:#222; margin: 10px 0;">
                        <h3 style="margin:5px 0; color:#FFD700;">{p1['NOMBRE_COMPLETO']}</h3>
                        <h1 style="color:#FFD700; font-size:3rem;">{p1['PROMEDIO_FINAL']}</h1>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    p3 = ranking.iloc[2]
                    f3 = get_photo_url(p3.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #CD7F32;">
                        <span class="podio-emoji">🥉</span>
                        <img src="{f3}" style="width:90px; height:90px; border-radius:50%; object-fit:cover; background:#222; margin: 10px 0;">
                        <h4 style="margin:5px 0;">{p3['NOMBRE_COMPLETO']}</h4>
                        <h2 style="color:#CD7F32;">{p3['PROMEDIO_FINAL']}</h2>
                    </div>""", unsafe_allow_html=True)

            st.markdown("### 📊 Listado Completo")
            st.data_editor(
                ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'PROMEDIO_FINAL']],
                column_config={
                    "PROMEDIO_FINAL": st.column_config.ProgressColumn("Nota Global (Ponderada)", min_value=0, max_value=5, format="%.2f"), 
                    "NOMBRE_COMPLETO": "Colaborador", 
                    "CARGO_ACTUAL": "Cargo"
                }, hide_index=True, use_container_width=True, disabled=True
            )
        else: st.info("No hay datos de ranking disponibles.")

    # ----------------------------------------
    # 3. HISTORIAL
    # ----------------------------------------
    elif seleccion == "📂 Mi Historial" and st.session_state.rol not in ROLES_RESTRINGIDOS:
        st.title("📂 Historial de Registros")
        
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            df_personal['DNI'] = df_personal['DNI'].astype(str)
            
            if not data_view.empty:
                dnis_permitidos = data_view['DNI'].unique().tolist()
                df_historial = df_historial[df_historial['DNI_TRABAJADOR'].isin(dnis_permitidos)]
            
            df_merged = pd.merge(df_historial, df_personal[['DNI', 'NOMBRE_COMPLETO']], left_on='DNI_TRABAJADOR', right_on='DNI', how='left')
            df_merged['NOMBRE_COMPLETO'] = df_merged['NOMBRE_COMPLETO'].fillna(df_merged['DNI_TRABAJADOR'])
            
            cols_mostrar = ['COD_PARADA', 'NOMBRE_COMPLETO', 'NOTA_FINAL', 'COMENTARIOS']
            cols_existentes = [c for c in cols_mostrar if c in df_merged.columns]
            
            st.dataframe(df_merged[cols_existentes], use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron registros.")