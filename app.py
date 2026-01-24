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
# 2. ESTILOS VISUALES PREMIUM (Corrección de Barra y Fondo)
# ==========================================
st.markdown("""
<style>
    /* --- MODO OSCURO GLOBAL --- */
    :root { color-scheme: dark !important; }
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #000000 !important; color: #E0E0E0 !important;
    }
    
    /* --- LIMPIEZA VISUAL (SOLO LO NECESARIO) --- */
    /* Ocultamos el menú de 3 puntos y el pie de página */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* IMPORTANTE: NO ocultamos el header completo para que la flecha de la barra lateral funcione */
    /* Solo ocultamos la decoración de colores de arriba si molesta */
    [data-testid="stDecoration"] {visibility: hidden;}
    
    .block-container {padding-top: 1rem !important;}

    /* --- ESTILO DE TARJETAS PARA RADIO BUTTONS (INTERACTIVO) --- */
    div[role="radiogroup"] { gap: 12px; }
    div[role="radiogroup"] label {
        background-color: #131720 !important;
        border: 1px solid #333 !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        margin-bottom: 5px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #4FC3F7 !important;
        background-color: #1E2530 !important;
        transform: scale(1.01) !important;
        box-shadow: 0 4px 10px rgba(79, 195, 247, 0.2) !important;
        cursor: pointer;
    }
    /* Bolita seleccionada azul */
    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        background-color: #4FC3F7 !important;
    }

    /* --- INPUTS --- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1E1E2E !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }
    
    /* --- BOTONES AZULES --- */
    div.stButton > button {
        background: linear-gradient(135deg, #0288D1 0%, #01579B 100%) !important;
        color: white !important; border: none !important;
        font-weight: bold; border-radius: 8px; padding: 0.7rem 1.5rem;
        box-shadow: 0 4px 15px rgba(2, 136, 209, 0.4);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(2, 136, 209, 0.6);
    }

    /* --- TARJETAS DE CONTENIDO --- */
    .css-card {
        background: rgba(20, 20, 30, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #222;
    }
    h1, h2, h3 { color: #4FC3F7 !important; text-shadow: 0 0 10px rgba(79,195,247,0.3); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CARGA DE FONDO (SIN FILTROS NI OPACIDAD)
# ==========================================
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as file:
            enc = base64.b64encode(file.read())
        # Aquí insertamos la imagen DIRECTAMENTE, sin capas oscuras extra
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpg;base64,{enc.decode()});
            background-size: cover;          /* Cubre toda la pantalla */
            background-position: center top; /* Alineado al centro-arriba */
            background-repeat: no-repeat;
            background-attachment: fixed;    /* Fijo al hacer scroll */
        }}
        </style>
        """, unsafe_allow_html=True)
    else:
        # Si falla, fondo negro limpio
        st.markdown("<style>.stApp { background-color: #000000; }</style>", unsafe_allow_html=True)

add_bg_from_local('fondo.jpg')
LOGO_FILE = "logo.png"

# ==========================================
# 4. CONEXIÓN AIRTABLE Y CARGA DE DATOS
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

ROLES_RESTRINGIDOS = ['LIDER MECANICO', 'OPERADOR DE GRUA', 'MECANICO', 'SOLDADOR', 'RIGGER', 'VIENTERO', 'ALMACENERO', 'CONDUCTOR', 'PSICOLOGA']
ROLES_GERENCIALES = ['ADMIN', 'GERENTE GENERAL', 'GERENTE MANTENIMIENTO', 'RESIDENTE', 'COORDINADOR', 'PLANNER']
JERARQUIA = {
    'ADMIN': {'scope': 'ALL'}, 'GERENTE GENERAL': {'scope': 'ALL'}, 'GERENTE MANTENIMIENTO': {'scope': 'ALL'},
    'RESIDENTE': {'scope': 'ALL'}, 'COORDINADOR': {'scope': 'ALL'}, 'PLANNER': {'scope': 'ALL'}, 'PROGRAMADOR': {'scope': 'ALL'},
    'COORDINADOR DE SEGURIDAD': {'scope': 'SPECIFIC', 'targets': ['SUPERVISOR DE SEGURIDAD']},
    'VALORIZADORA': {'scope': 'SPECIFIC', 'targets': ['ASISTENTE DE PLANIFICACION', 'ASISTENTE ADMINISTRATIVO', 'PROGRAMADOR', 'PLANNER']},
    'SUPERVISOR DE OPERACIONES': {'scope': 'HYBRID', 'targets': ['PLANNER', 'CONDUCTOR']},
    'LIDER MECANICO': {'scope': 'GROUP', 'targets': []}, 'OPERADOR DE GRUA': {'scope': 'GROUP', 'targets': []}, 
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
    opciones = ["📝 Evaluar Personal"]
    if rol_actual not in ROLES_RESTRINGIDOS:
        if rol_actual in ROLES_GERENCIALES: opciones = ["📝 Evaluar Personal", "📊 Dashboard Gerencial", "🏆 Ranking Global", "📂 Mi Historial"]
        else: opciones = ["📝 Evaluar Personal", "📂 Mi Historial"]

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
    # 1. DASHBOARD GERENCIAL
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
                    # Heatmap
                    hm = alt.Chart(heatmap_data).mark_rect().encode(
                        x=alt.X('TURNO_MOMENTO:N', title='Turno'),
                        y=alt.Y('GRUPO_MOMENTO:N', title='Grupo'),
                        color=alt.Color('NOTA_FINAL', scale=alt.Scale(domain=[1, 5], scheme='yellowgreenblue'), title='Promedio'),
                        tooltip=['GRUPO_MOMENTO', 'TURNO_MOMENTO', 'NOTA_FINAL']
                    ).properties(height=300)
                    text_hm = hm.mark_text().encode(text=alt.Text('NOTA_FINAL', format='.2f'), color=alt.value('black'))
                    st.altair_chart(hm + text_hm, use_container_width=True)
                except Exception as e: st.error(f"Error cargando mapa de calor: {e}")

                st.divider()
                c_izq, c_der = st.columns([2, 1])
                with c_izq:
                    st.subheader("📊 (3) Rendimiento por Cargo")
                    try:
                        chart_cargo = df_dash.groupby('CARGO_MOMENTO')['NOTA_FINAL'].mean().reset_index()
                        bar = alt.Chart(chart_cargo).mark_bar().encode(
                            x=alt.X('NOTA_FINAL', scale=alt.Scale(domain=[0, 5]), title='Nota (0-5)'),
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
    # 2. EVALUACIÓN
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
            sel_nombre = st.selectbox(f"Pendientes ({len(lista)}):", lista, index=None, placeholder="Seleccione colaborador...")
            if sel_nombre:
                p = data_view[data_view['NOMBRE_COMPLETO'] == sel_nombre].iloc[0]
                st.markdown(f"""
                <div class="css-card" style="display: flex; align-items: center; gap: 20px;">
                    <img src="{p.get('URL_FOTO', DEFAULT_IMG)}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #4FC3F7;">
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
                                try: tbl_historial.create(rec); st.success(f"Guardado. Nota: {round(score, 2)}"); time.sleep(1.5); st.cache_data.clear(); st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                            else: st.warning("⚠️ Falta observación.")

    # ==============================================================================
    # 3. RANKING Y HISTORIAL
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
            ranking = pd.merge(score_df, df_personal, left_on='DNI_TRABAJADOR', right_on='DNI', how='left').sort_values('FINAL', ascending=False)
            st.data_editor(ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'FINAL']], column_config={"FINAL": st.column_config.ProgressColumn("Nota", min_value=0, max_value=5, format="%.2f")}, hide_index=True, use_container_width=True)
        else: st.info("Sin datos.")

    elif seleccion == "📂 Mi Historial":
        st.title("📂 Historial")
        if df_historial is not None and not df_historial.empty:
            df_historial['DNI_TRABAJADOR'] = df_historial['DNI_TRABAJADOR'].astype(str)
            if not data_view.empty: df_historial = df_historial[df_historial['DNI_TRABAJADOR'].isin(data_view['DNI'].unique())]
            merged = pd.merge(df_historial, df_personal[['DNI', 'NOMBRE_COMPLETO']], left_on='DNI_TRABAJADOR', right_on='DNI', how='left')
            merged['NOMBRE_COMPLETO'] = merged['NOMBRE_COMPLETO'].fillna(merged['DNI_TRABAJADOR'])
            cols = ['FECHA_HORA', 'NOMBRE_COMPLETO', 'NOTA_FINAL', 'COMENTARIOS']
            st.dataframe(merged[[c for c in cols if c in merged.columns]], use_container_width=True, hide_index=True)
            csv = merged.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Excel", csv, "Reporte.csv", "text/csv")
        else: st.info("Sin registros.")