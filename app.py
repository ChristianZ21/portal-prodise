import streamlit as st
import pandas as pd
import altair as alt
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

# ==========================================
# 2. ESTILOS VISUALES (EL QUE FUNCIONÓ PERFECTO)
# ==========================================
st.markdown("""
<style>
    /* --- 1. AJUSTES GENERALES --- */
    [data-testid="stAppViewContainer"] {
        background-color: transparent !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #E0E0E0 !important;
    }
    
    h1 { 
        color: #4FC3F7 !important; 
        text-shadow: 0 0 20px rgba(79,195,247,0.6);
        font-weight: 800 !important;
        font-size: 3rem !important;
        text-transform: uppercase;
    }

    /* --- 2. HEADER Y SIDEBAR --- */
    header[data-testid="stHeader"] { background-color: transparent !important; }
    #MainMenu, .stDeployButton, footer, [data-testid="stDecoration"] { display: none; }
    
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #333;
    }
    [data-testid="collapsedControl"] { top: 1rem !important; color: white !important; }

    /* --- 3. MENÚ DESPLEGABLE (LISTA AZUL OSCURA) --- */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] {
        background-color: #0E1117 !important;
        border: 1px solid #4FC3F7 !important;
    }
    
    li[data-baseweb="option"] {
        background-color: #0E1117 !important;
        color: white !important;
    }
    
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #4FC3F7 !important;
        color: black !important;
        font-weight: bold !important;
    }
    
    li[data-baseweb="option"]:hover div, li[aria-selected="true"] div {
        color: black !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #0E1117 !important;
        border: 1px solid #555 !important;
        color: white !important;
    }
    
    /* --- 4. ALTERNATIVAS COMO TARJETAS (MÁS JUNTAS) --- */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px !important;
    }
    
    div[role="radiogroup"] label {
        background-color: rgba(30, 35, 45, 0.8) !important;
        padding: 12px 20px !important;
        border-radius: 12px !important;
        border: 1px solid #444 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: all 0.2s ease;
        margin-bottom: 0px !important;
    }
    
    div[role="radiogroup"] label:hover {
        border-color: #4FC3F7 !important;
        background-color: rgba(40, 50, 60, 1) !important;
        transform: translateX(5px);
        cursor: pointer;
    }
    
    div[role="radiogroup"] p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }

    /* --- 5. TARJETAS DE DATOS --- */
    .css-card {
        background: rgba(14, 17, 23, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }

    /* --- 6. BOTONES PRINCIPALES --- */
    div.stButton > button {
        background: linear-gradient(90deg, #0288D1 0%, #01579B 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem !important;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 15px rgba(2, 136, 209, 0.6);
        transform: scale(1.02);
    }
    
    .podio-emoji { font-size: 3rem; display: block; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CARGA DE FONDO
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
            background-position: center top;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.75);
            z-index: -1;
        }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ AVISO: Sube '{image_file}' a GitHub.")

add_bg_from_local('fondo.jpg')
LOGO_FILE = "logo.png"

# ==========================================
# 4. CONEXIÓN AIRTABLE
# ==========================================
try:
    AIRTABLE_API_TOKEN = st.secrets["AIRTABLE_API_TOKEN"]
    AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
except:
    st.error("⚠️ Error: Configura las claves en Secrets.")
    st.stop()

def get_default_profile_pic():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#B0BEC5" width="100%" height="100%"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>"""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"
DEFAULT_IMG = get_default_profile_pic()

def get_photo_url(url_raw):
    if not url_raw or str(url_raw).lower() == 'nan' or len(str(url_raw)) < 5:
        return DEFAULT_IMG
    return str(url_raw).strip()

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
                cols_upper = ['USUARIO', 'ID_ROL', 'ESTADO', 'TURNO', 'COD_PARADA', 'DNI', 'DNI_TRABAJADOR', 'DNI_EVALUADOR', 'CARGO', 'CARGO_ACTUAL', 'CARGO_MOMENTO', 'TURNO_MOMENTO', 'NOMBRE_COMPLETO']
                cols_grupo = ['ID_GRUPO', 'GRUPO', 'GRUPO_MOMENTO']
                for c in df.columns:
                    df[c] = df[c].astype(str).str.strip()
                    if c in cols_upper: df[c] = df[c].str.upper()
                    if c in cols_grupo: df[c] = df[c].str.upper().str.replace('.0', '', regex=False)
                return df, t
            except: return pd.DataFrame(), None
            
        df_u, _ = get_df("DB_USUARIOS")
        df_p, _ = get_df("DB_PERSONAL")
        df_r, _ = get_df("CONFIG_ROLES")
        df_h, tbl_h = get_df("DB_HISTORIAL")
        df_c, _ = get_df("CONFIG")
        
        if not df_r.empty and 'PORCENTAJE' in df_r.columns: df_r['PORCENTAJE'] = pd.to_numeric(df_r['PORCENTAJE'], errors='coerce').fillna(0)
        if not df_h.empty and 'NOTA_FINAL' in df_h.columns: df_h['NOTA_FINAL'] = pd.to_numeric(df_h['NOTA_FINAL'], errors='coerce').fillna(0)
        return df_u, df_p, df_r, df_h, tbl_h, df_c
    except: return None, None, None, None, None, None

df_users, df_personal, df_roles, df_historial, tbl_historial, df_config = load_data()

# Definimos la jerarquía para filtrar a quién puede evaluar cada uno
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

parada_actual = "GENERAL"
if df_config is not None and not df_config.empty:
    parada_actual = str(df_config.iloc[0].get('COD_PARADA', df_config.iloc[0].values[0]))

if 'usuario' not in st.session_state: st.session_state.update({'usuario': None, 'nombre_real': None, 'rol': None, 'dni_user': None})

# ==========================================
# 5. LÓGICA DE APLICACIÓN
# ==========================================
if not st.session_state.usuario:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,0.8,1])
    with c2:
        st.markdown("""<div class="css-card" style="text-align: center;"><h1 style="margin:0; font-size: 2.5rem;">🔐 PRODISE</h1><p style="margin-top: 10px;">Acceso Corporativo Seguro</p></div>""", unsafe_allow_html=True)
        user = st.text_input("ID Usuario", placeholder="Ingrese su usuario")
        pw = st.text_input("Contraseña", type="password", placeholder="••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INICIAR SESIÓN", use_container_width=True):
            if df_users is not None and not df_users.empty:
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
    rol_actual = st.session_state.rol
    
    # --- LÓGICA DE PERMISOS DE PESTAÑAS ---
    if rol_actual == 'ADMIN':
        opciones = ["📝 Evaluar Personal", "📊 Dashboard Gerencial", "🏆 Ranking Global", "📂 Mi Historial"]
    elif rol_actual == 'SUPERVISOR DE OPERACIONES':
        opciones = ["📝 Evaluar Personal", "📂 Mi Historial"]
    else:
        # Para todos los demás (Lideres, Operadores, etc.)
        opciones = ["📝 Evaluar Personal"]

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

    data_view = df_personal[df_personal['ESTADO'] == 'ACTIVO'] if df_personal is not None else pd.DataFrame()
    if not data_view.empty:
        permisos = JERARQUIA.get(rol_actual, {'scope': 'GROUP', 'targets': []}) 
        scope = permisos.get('scope', 'GROUP')
        targets = permisos.get('targets', [])
        me = data_view[data_view['DNI'] == st.session_state.dni_user]
        grp_supervisor = str(me.iloc[0]['ID_GRUPO']).replace('.0','').strip() if not me.empty else ""
        trn = me.iloc[0]['TURNO'] if not me.empty else ""

        def check_grupo(grupos, buscado):
            if not buscado: return False
            return buscado in [g.replace('.0','').strip() for g in str(grupos).split(',')]

        if scope == 'ALL': pass 
        elif scope == 'SPECIFIC': data_view = data_view[data_view['CARGO_ACTUAL'].isin(targets)]
        elif scope == 'GROUP': data_view = data_view[data_view['ID_GRUPO'].apply(lambda x: check_grupo(x, grp_supervisor)) & (data_view['TURNO'] == trn)]
        elif scope == 'HYBRID':
            mask_cargos = data_view['CARGO_ACTUAL'].isin(targets)
            mask_grupo = data_view['ID_GRUPO'].apply(lambda x: check_grupo(x, grp_supervisor)) & (data_view['TURNO'] == trn)
            data_view = data_view[mask_cargos | mask_grupo]
        data_view = data_view[data_view['DNI'] != st.session_state.dni_user]

    # ==============================================================================
    # 1. DASHBOARD GERENCIAL (SOLO ADMIN)
    # ==============================================================================
    if seleccion == "📊 Dashboard Gerencial":
        st.title(f"📊 Control Tower - {parada_actual}")
        if df_historial is not None and not df_historial.empty:
            df_dash = df_historial[df_historial['COD_PARADA'] == parada_actual].copy()
            if df_dash.empty: st.warning("⚠️ Aún no hay datos suficientes.")
            else:
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Evaluaciones", len(df_dash))
                k2.metric("Personas", df_dash['DNI_TRABAJADOR'].nunique())
                k3.metric("Promedio Planta", f"{df_dash['NOTA_FINAL'].mean():.2f}")
                try: top_grp = df_dash.groupby('GRUPO_MOMENTO')['NOTA_FINAL'].mean().idxmax()
                except: top_grp = "N/A"
                k4.metric("Grupo Líder", top_grp)
                st.divider()

                st.subheader("🔥 (1) Mapa de Riesgo: Grupos vs. Turnos")
                try:
                    heatmap_data = df_dash.groupby(['GRUPO_MOMENTO', 'TURNO_MOMENTO'])['NOTA_FINAL'].mean().reset_index()
                    hm = alt.Chart(heatmap_data).mark_rect().encode(
                        x=alt.X('TURNO_MOMENTO:N', title='Turno'),
                        y=alt.Y('GRUPO_MOMENTO:N', title='Grupo'),
                        color=alt.Color('NOTA_FINAL', scale=alt.Scale(domain=[1, 5], scheme='yellowgreenblue'), title='Promedio'),
                        tooltip=['GRUPO_MOMENTO', 'TURNO_MOMENTO', 'NOTA_FINAL']
                    ).properties(height=300)
                    text_hm = hm.mark_text().encode(text=alt.Text('NOTA_FINAL', format='.2f'), color=alt.value('black'))
                    st.altair_chart(hm + text_hm, use_container_width=True)
                except: st.error("Error en mapa de calor.")

                st.divider()
                c_izq, c_der = st.columns([2, 1])
                with c_izq:
                    st.subheader("📊 (3) Rendimiento por Cargo")
                    try:
                        chart_cargo = df_dash.groupby('CARGO_MOMENTO')['NOTA_FINAL'].mean().reset_index()
                        bar = alt.Chart(chart_cargo).mark_bar().encode(
                            x=alt.X('NOTA_FINAL', scale=alt.Scale(domain=[0, 5]), title='Nota'),
                            y=alt.Y('CARGO_MOMENTO', sort='-x', title='Cargo'),
                            color=alt.value('#4FC3F7'),
                            tooltip=['CARGO_MOMENTO', 'NOTA_FINAL']
                        ).properties(height=300)
                        st.altair_chart(bar, use_container_width=True)
                    except: st.warning("Datos insuficientes.")

                with c_der:
                    st.subheader("🍩 (4) Distribución")
                    try:
                        def clasificar(n):
                            if n >= 4.5: return "Excelente"
                            elif n >= 3.5: return "Bueno"
                            elif n >= 2.5: return "Regular"
                            else: return "Bajo"
                        df_dash['Cat'] = df_dash['NOTA_FINAL'].apply(clasificar)
                        donut = df_dash['Cat'].value_counts().reset_index()
                        donut.columns = ['Categoria', 'Cantidad']
                        base = alt.Chart(donut).encode(theta=alt.Theta("Cantidad", stack=True))
                        pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(
                            color=alt.Color("Categoria", scale=alt.Scale(scheme='category20b')),
                            order=alt.Order("Cantidad", sort="descending"),
                            tooltip=["Categoria", "Cantidad"]
                        )
                        txt = base.mark_text(radius=120).encode(text=alt.Text("Cantidad"), order=alt.Order("Cantidad", sort="descending"), color=alt.value("white"))
                        st.altair_chart(pie + txt, use_container_width=True)
                    except: st.warning("Datos insuficientes.")
        else: st.info("No hay datos históricos cargados.")

    # ==============================================================================
    # 2. EVALUACIÓN (CON BUSCADOR Y TARJETAS RECUPERADAS)
    # ==============================================================================
    elif seleccion == "📝 Evaluar Personal":
        st.title(f"📝 Evaluación - {parada_actual}")
        dnis_ya_evaluados = []
        if df_historial is not None and not df_historial.empty:
            filtro = df_historial[(df_historial['DNI_EVALUADOR'] == st.session_state.dni_user) & (df_historial['COD_PARADA'] == parada_actual)]
            dnis_ya_evaluados = filtro['DNI_TRABAJADOR'].unique().tolist()
        if not data_view.empty: data_view = data_view[~data_view['DNI'].isin(dnis_ya_evaluados)]

        if data_view.empty:
            st.balloons()
            st.success("✅ Todo el personal asignado ha sido evaluado.")
        else:
            lista = data_view['NOMBRE_COMPLETO'].unique().tolist()
            # BUSCADOR GOOGLE STYLE (VACÍO AL INICIO)
            sel_nombre = st.selectbox(
                f"Pendientes ({len(lista)}):", 
                lista, 
                index=None, 
                placeholder="🔍 Escribe para buscar colaborador..."
            )
            
            if sel_nombre:
                p = data_view[data_view['NOMBRE_COMPLETO'] == sel_nombre].iloc[0]
                foto_p = get_photo_url(p.get('URL_FOTO', ''))
                st.markdown(f"""
                <div class="css-card" style="display: flex; align-items: center; gap: 20px;">
                    <img src="{foto_p}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #4FC3F7;">
                    <div>
                        <h3 style="margin:0; color: white;">{p['NOMBRE_COMPLETO']}</h3>
                        <p style="margin:0; color:#4FC3F7; font-weight:bold;">{p['CARGO_ACTUAL']}</p>
                        <span style="font-size:0.8rem; color:#888;">{p['ID_GRUPO']} - {p['TURNO']}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

                preguntas = pd.DataFrame()
                if df_roles is not None and not df_roles.empty:
                    df_roles['CARGO_NORM'] = df_roles['CARGO'].astype(str).str.upper().str.strip()
                    preguntas = df_roles[df_roles['CARGO_NORM'] == str(p['CARGO_ACTUAL']).upper().strip()]

                if preguntas.empty: st.warning("⚠️ Sin criterios configurados.")
                else:
                    with st.form("frm_eval"):
                        score = 0; notas_save = {}
                        for i, (idx, row) in enumerate(preguntas.iterrows(), 1):
                            st.markdown(f"#### {i}. {row['CRITERIO']}")
                            st.caption(f"Peso: {row['PORCENTAJE']*100:.0f}%")
                            
                            # BOTONES ESTILO TARJETA (RECUPERADOS)
                            ops = [str(row.get(f'NIVEL_{j}')) for j in range(1, 6)]
                            sel = st.radio(f"Nivel {i}", ops, key=f"r{i}", label_visibility="collapsed")
                            
                            nota = ops.index(sel) + 1
                            score += nota * row['PORCENTAJE']
                            notas_save[f"NOTA_{i}"] = nota
                            st.divider()
                        
                        obs = st.text_area("Observaciones (Obligatorio)", height=100)
                        if st.form_submit_button("💾 GUARDAR EVALUACIÓN", use_container_width=True):
                            if obs and tbl_historial:
                                rec = {"FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "COD_PARADA": parada_actual, "DNI_EVALUADOR": st.session_state.dni_user, "NOMBRE_EVALUADOR": st.session_state.nombre_real, "DNI_TRABAJADOR": str(p['DNI']), "NOMBRE_TRABAJADOR": str(p['NOMBRE_COMPLETO']), "CARGO_MOMENTO": str(p['CARGO_ACTUAL']), "GRUPO_MOMENTO": str(p['ID_GRUPO']), "TURNO_MOMENTO": str(p['TURNO']), "NOTA_FINAL": round(score, 2), "COMENTARIOS": obs}
                                rec.update(notas_save)
                                try: 
                                    tbl_historial.create(rec)
                                    st.balloons() # <-- ¡GLOBOS!
                                    st.success(f"Guardado. Nota: {round(score, 2)}")
                                    time.sleep(1.5)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                            else: st.warning("⚠️ Falta observación.")

    # ==============================================================================
    # 3. RANKING GLOBAL
    # ==============================================================================
    elif seleccion == "🏆 Ranking Global":
        st.title("🏆 Ranking Global")
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            actual = df_historial[df_historial['COD_PARADA'] == parada_actual].groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index(name='MEDIA_ACTUAL')
            hist = df_historial[df_historial['COD_PARADA'] != parada_actual].groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index(name='MEDIA_HIST')
            score_df = pd.merge(actual, hist, left_on='DNI_TRABAJADOR', right_on='DNI_TRABAJADOR', how='outer')
            def calc(row):
                a, h = row['MEDIA_ACTUAL'], row['MEDIA_HIST']
                if pd.notna(a) and pd.notna(h): return a*0.7 + h*0.3
                return a if pd.notna(a) else h if pd.notna(h) else 0
            score_df['FINAL'] = score_df.apply(calc, axis=1).round(2)
            ranking = pd.merge(score_df, df_personal, left_on='DNI_TRABAJADOR', right_on='DNI', how='left')
            
            # FILTRO
            cargos_disp = ["TODOS"] + sorted(ranking['CARGO_ACTUAL'].unique().tolist())
            filtro_cargo = st.selectbox("🔍 Filtrar por Cargo:", cargos_disp)
            if filtro_cargo != "TODOS":
                ranking = ranking[ranking['CARGO_ACTUAL'] == filtro_cargo]
            
            ranking = ranking.sort_values('FINAL', ascending=False).reset_index(drop=True)
            
            # PODIO
            if len(ranking) >= 3:
                c_2, c_1, c_3 = st.columns([1, 1.2, 1])
                with c_2:
                    p2 = ranking.iloc[1]
                    f2 = get_photo_url(p2.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #C0C0C0; margin-top: 20px;">
                        <span class="podio-emoji">🥈</span>
                        <img src="{f2}" style="width:90px; height:90px; border-radius:50%; object-fit:cover; margin-bottom:10px; border:3px solid #C0C0C0;">
                        <h4 style="margin:0; font-size:1rem;">{p2['NOMBRE_COMPLETO']}</h4>
                        <h2 style="color:#C0C0C0;">{p2['FINAL']}</h2>
                    </div>""", unsafe_allow_html=True)
                with c_1:
                    p1 = ranking.iloc[0]
                    f1 = get_photo_url(p1.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #FFD700; transform: scale(1.05);">
                        <span class="podio-emoji">🥇</span>
                        <img src="{f1}" style="width:120px; height:120px; border-radius:50%; object-fit:cover; margin-bottom:10px; border:4px solid #FFD700;">
                        <h3 style="margin:0; font-size:1.1rem; color:#FFD700;">{p1['NOMBRE_COMPLETO']}</h3>
                        <h1 style="color:#FFD700; font-size:3rem; margin:0;">{p1['FINAL']}</h1>
                    </div>""", unsafe_allow_html=True)
                with c_3:
                    p3 = ranking.iloc[2]
                    f3 = get_photo_url(p3.get('URL_FOTO', ''))
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #CD7F32; margin-top: 20px;">
                        <span class="podio-emoji">🥉</span>
                        <img src="{f3}" style="width:90px; height:90px; border-radius:50%; object-fit:cover; margin-bottom:10px; border:3px solid #CD7F32;">
                        <h4 style="margin:0; font-size:1rem;">{p3['NOMBRE_COMPLETO']}</h4>
                        <h2 style="color:#CD7F32;">{p3['FINAL']}</h2>
                    </div>""", unsafe_allow_html=True)
                st.divider()

            st.markdown("### 📊 Listado Completo")
            st.data_editor(ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'FINAL']], column_config={"FINAL": st.column_config.ProgressColumn("Nota", min_value=0, max_value=5, format="%.2f")}, hide_index=True, use_container_width=True)
        else: st.info("Sin datos.")

    # ==============================================================================
    # 4. HISTORIAL
    # ==============================================================================
    elif seleccion == "📂 Mi Historial":
        st.title("📂 Historial")
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            if not data_view.empty: df_historial = df_historial[df_historial['DNI_TRABAJADOR'].isin(data_view['DNI'].unique())]
            merged = pd.merge(df_historial, df_personal[['DNI', 'NOMBRE_COMPLETO']], left_on='DNI_TRABAJADOR', right_on='DNI', how='left')
            merged['NOMBRE_COMPLETO'] = merged['NOMBRE_COMPLETO'].fillna(merged['DNI_TRABAJADOR'])
            cols = ['COD_PARADA', 'NOMBRE_COMPLETO', 'NOTA_FINAL', 'COMENTARIOS']
            st.dataframe(merged[[c for c in cols if c in merged.columns]], use_container_width=True, hide_index=True)
            csv = merged.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Excel", csv, "Reporte.csv", "text/csv")
        else: st.info("Sin registros.")