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
# 2. ESTILOS VISUALES
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
                background-attachment: fixed;
            }}
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background-color: rgba(0, 0, 0, 0.6); 
                z-index: -1;
            }}
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background: linear-gradient(to right, #141e30, #243b55); }</style>", unsafe_allow_html=True)

add_bg_from_local('fondo.jpg')
LOGO_FILE = "logo.png"

st.markdown("""
<style>
    h1, h2, h3, p, label, span, div { color: #E0E0E0; }
    h1, h2 { color: #4FC3F7 !important; text-shadow: 2px 2px 4px #000; }
    
    .css-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        color: white;
    }
    
    div.stButton > button { background: #0288D1; color: white; border: none; font-weight: bold; transition: 0.3s; }
    div.stButton > button:hover { background: #03A9F4; transform: scale(1.02); }
    [data-testid="stSidebar"] { background-color: rgba(20, 30, 48, 0.95); border-right: 1px solid #333; }
    div[data-testid="metric-container"] { background-color: rgba(0,0,0,0.5); border: 1px solid #444; padding: 10px; border-radius: 8px; }
    div[data-testid="stFeedback"] span { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CONEXIÓN Y CARGA DE DATOS
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

# --- LÓGICA DE PARADA ACTUAL ---
# Intenta buscar una columna llamada 'COD_PARADA' o 'VALOR' en la tabla CONFIG.
# Si no, toma la primera celda disponible.
parada_actual = "GENERAL"
if df_config is not None and not df_config.empty:
    if 'COD_PARADA' in df_config.columns:
        parada_actual = str(df_config.iloc[0]['COD_PARADA'])
    else:
        # Toma el primer valor que encuentre si no existe la columna exacta
        parada_actual = str(df_config.iloc[0].values[0])

if 'usuario' not in st.session_state:
    st.session_state.update({'usuario': None, 'nombre_real': None, 'rol': None, 'dni_user': None})

# ==========================================
# 4. APLICACIÓN
# ==========================================

# --- LOGIN ---
if not st.session_state.usuario:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("""
        <div class="css-card" style="text-align: center;">
            <h1 style="margin:0;">🔐 PRODISE</h1>
            <p>Acceso Seguro</p>
        </div>
        """, unsafe_allow_html=True)
        
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        
        if st.button("INGRESAR", use_container_width=True):
            if df_users is not None and not df_users.empty:
                u = df_users[df_users['USUARIO'] == user]
                if not u.empty and str(u.iloc[0]['PASS']) == pw and u.iloc[0]['ESTADO'] == 'ACTIVO':
                    st.session_state.usuario = user
                    st.session_state.nombre_real = u.iloc[0]['NOMBRE']
                    st.session_state.rol = str(u.iloc[0]['ID_ROL']).upper().strip()
                    st.session_state.dni_user = str(u.iloc[0]['DNI_TRABAJADOR'])
                    st.rerun()
                else: st.error("❌ Datos incorrectos")
            else: st.error("❌ Sin conexión a base de datos")

else:
    # --- SIDEBAR ---
    opciones = ["📝 Evaluar Personal", "📂 Mi Historial"]
    if st.session_state.rol == 'ADMIN':
        opciones.insert(1, "🏆 Ranking Global")

    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        st.markdown(f"### 👤 {st.session_state.nombre_real.split()[0]}")
        st.caption(f"Rol: {st.session_state.rol}")
        
        # Muestra la parada actual activa
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
    # VISTA 1: EVALUACIÓN
    # ----------------------------------------
    if seleccion == "📝 Evaluar Personal":
        st.title(f"📝 Evaluación - {parada_actual}")
        
        sel_nombre = st.selectbox("Seleccionar Trabajador:", data_view['NOMBRE_COMPLETO'].unique()) if not data_view.empty else None
        
        if sel_nombre:
            p = data_view[data_view['NOMBRE_COMPLETO'] == sel_nombre].iloc[0]
            
            st.markdown(f"""
            <div class="css-card" style="display: flex; align-items: center; gap: 20px;">
                <img src="{p.get('URL_FOTO','')}" style="width: 90px; height: 90px; border-radius: 50%; border: 3px solid #4FC3F7; object-fit: cover;">
                <div>
                    <h2 style="margin:0; color: white !important;">{p['NOMBRE_COMPLETO']}</h2>
                    <p style="margin:0; font-size: 1.1em; color: #B3E5FC;">{p['CARGO_ACTUAL']}</p>
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 5px; font-size: 0.9em;">
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
                    
                    st.markdown("### Calificación de Desempeño")
                    for i, (idx, row) in enumerate(preguntas.iterrows(), 1):
                        c_txt, c_star = st.columns([2, 1])
                        with c_txt:
                            st.markdown(f"**{i}. {row['CRITERIO']}**")
                            st.caption(f"Importancia: {row['PORCENTAJE']*100:.0f}%")
                        with c_star:
                            val = st.feedback("stars", key=f"s_{i}")
                            nota = (val + 1) if val is not None else 0
                            score_total += nota * row['PORCENTAJE']
                            notas_save[f"NOTA_{i}"] = nota
                        st.divider()
                    
                    obs = st.text_area("Observaciones")
                    enviar = st.form_submit_button("✅ GUARDAR EVALUACIÓN", use_container_width=True)
                    
                    if enviar:
                        if obs and tbl_historial:
                            # AQUÍ SE GUARDA LA PARADA ACTUAL (CONSTANTE)
                            record = {
                                "FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "COD_PARADA": parada_actual,  # <--- SE GUARDA EL DATO DE CONFIG
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
                                st.success(f"¡Guardado en {parada_actual}! Nota: {round(score_total, 2)}")
                            except Exception as e: st.error(f"Error: {e}")
                        else:
                            st.warning("⚠️ Debes poner una observación.")

    # ----------------------------------------
    # VISTA 2: RANKING
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
            ranking = ranking.sort_values('PROMEDIO', ascending=False).reset_index(drop=True)
            
            if len(ranking) >= 3:
                c2, c1, c3 = st.columns([1, 1.2, 1])
                with c2:
                    p2 = ranking.iloc[1]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #C0C0C0;">
                        <h1 style="margin:0;">🥈</h1>
                        <img src="{p2.get('URL_FOTO','')}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
                        <h3>{p2['NOMBRE_COMPLETO'].split()[0]}</h3>
                        <h2 style="color:#C0C0C0;">{p2['PROMEDIO']}</h2>
                    </div>""", unsafe_allow_html=True)
                with c1:
                    p1 = ranking.iloc[0]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #FFD700; transform: scale(1.05);">
                        <h1 style="margin:0; font-size: 3em;">👑</h1>
                        <img src="{p1.get('URL_FOTO','')}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border: 4px solid #FFD700;">
                        <h2>{p1['NOMBRE_COMPLETO'].split()[0]}</h2>
                        <h1 style="color:#FFD700;">{p1['PROMEDIO']}</h1>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    p3 = ranking.iloc[2]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #CD7F32;">
                        <h1 style="margin:0;">🥉</h1>
                        <img src="{p3.get('URL_FOTO','')}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
                        <h3>{p3['NOMBRE_COMPLETO'].split()[0]}</h3>
                        <h2 style="color:#CD7F32;">{p3['PROMEDIO']}</h2>
                    </div>""", unsafe_allow_html=True)

            st.markdown("### 📊 Listado General")
            st.data_editor(
                ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'PROMEDIO']],
                column_config={"PROMEDIO": st.column_config.ProgressColumn("Nota", min_value=0, max_value=5, format="%.2f")},
                hide_index=True, use_container_width=True, disabled=True
            )
        else: st.info("No hay datos de ranking aún.")

    # ----------------------------------------
    # VISTA 3: HISTORIAL (MODIFICADA)
    # ----------------------------------------
    elif seleccion == "📂 Mi Historial":
        st.title("📂 Registro de Evaluaciones")
        if df_historial is not None and not df_historial.empty:
            # Seleccionamos columnas: COD_PARADA primero, quitamos FECHA_HORA si deseas
            cols_mostrar = ['COD_PARADA', 'DNI_TRABAJADOR', 'NOTA_FINAL', 'COMENTARIOS']
            
            # Filtramos solo las que existan para evitar errores
            cols_finales = [c for c in cols_mostrar if c in df_historial.columns]
            
            st.dataframe(
                df_historial[cols_finales], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Sin registros.")