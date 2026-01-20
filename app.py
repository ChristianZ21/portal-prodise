import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from pyairtable import Api

# ==========================================
# 1. TUS CLAVES (YA CONFIGURADAS)
# ==========================================
AIRTABLE_API_TOKEN = "pat3Ig7rAOvq7JdpN.fbef700fa804ae5692e3880899bba070239e9593f8d6fde958d9bd3d615aca14"
AIRTABLE_BASE_ID = "app2jaysCvPwvrBwI"

# ==========================================
# 2. CONFIGURACIÓN VISUAL
# ==========================================
COLOR_AZUL_OSCURO = "#002B5C"
COLOR_ROJO_VIVO = "#D32F2F"
COLOR_FONDO_TARJETA = "#E1ECF4"

st.set_page_config(page_title="Portal PRODISE", page_icon="🏭", layout="wide")

# ==========================================
# 3. CONEXIÓN AIRTABLE
# ==========================================
def get_airtable_data(table_name):
    try:
        api = Api(AIRTABLE_API_TOKEN)
        table = api.table(AIRTABLE_BASE_ID, table_name)
        records = table.all()
        if not records: return pd.DataFrame(), table
        data = [r['fields'] for r in records]
        df = pd.DataFrame(data)
        for col in df.columns: df[col] = df[col].astype(str)
        return df, table
    except Exception as e:
        # st.error(f"Error conectando a {table_name}: {e}") # Descomentar para depurar
        return pd.DataFrame(), None

# ==========================================
# 4. ESTILOS Y FONDO
# ==========================================
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as file:
            enc = base64.b64encode(file.read())
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url(data:image/jpg;base64,{enc.decode()}); 
            background-size: cover; background-position: top center; }}
            .stApp::before {{ content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background-color: rgba(14, 17, 23, 0.85); z-index: -1; }}
            </style>""", unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #0E1117; }</style>", unsafe_allow_html=True)

add_bg_from_local('fondo.jpg')
LOGO_FILE = "logo.png"

st.markdown(f"""
<style>
html, body, p, span, div, label {{ color: #E6E6E6; }}
h1, h2, h3, h4 {{ color: #64B5F6 !important; text-shadow: 2px 2px 4px #000; }}
div.stButton > button {{ background-color: {COLOR_AZUL_OSCURO} !important; color: white !important; border: 1px solid {COLOR_AZUL_OSCURO}; }}
div.stButton > button:hover {{ background-color: {COLOR_ROJO_VIVO} !important; border-color: {COLOR_ROJO_VIVO} !important; }}
[data-testid="stSidebar"] {{ background-color: rgba(244, 244, 244, 0.95); }}
[data-testid="stSidebar"] * {{ color: #000000 !important; text-shadow: none !important; }}
div[role="radiogroup"] > label {{ background-color: {COLOR_FONDO_TARJETA} !important; color: #000 !important; border-left: 8px solid {COLOR_AZUL_OSCURO}; }}
div[role="radiogroup"] > label:hover {{ background-color: #FFF !important; border-left: 8px solid {COLOR_ROJO_VIVO} !important; }}
div[role="radiogroup"] > label[data-checked="true"] {{ background-color: #FFF !important; border: 2px solid {COLOR_ROJO_VIVO} !important; border-left: 12px solid {COLOR_ROJO_VIVO} !important; color: {COLOR_AZUL_OSCURO} !important; font-weight: bold; }}
div[role="radiogroup"] p {{ color: #000 !important; }}
input {{ color: #000 !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. CARGA DE DATOS
# ==========================================
df_users, _ = get_airtable_data("DB_USUARIOS")
df_personal, _ = get_airtable_data("DB_PERSONAL")
df_roles, _ = get_airtable_data("CONFIG_ROLES")
df_historial, tbl_historial = get_airtable_data("DB_HISTORIAL")
df_config, _ = get_airtable_data("CONFIG")

# Ajustes de tipos
if not df_roles.empty:
    if 'PORCENTAJE' in df_roles.columns:
        df_roles['PORCENTAJE'] = pd.to_numeric(df_roles['PORCENTAJE'], errors='coerce').fillna(0)
    # Mapeo de seguridad para los roles
    map_cols = {'CARGO':'CARGO', 'CRITERIO':'CRITERIO', 'PORCENTAJE':'PORCENTAJE', 
                'NIVEL 1':'NIVEL_1', 'NIVEL 2':'NIVEL_2', 'NIVEL 3':'NIVEL_3', 'NIVEL 4':'NIVEL_4', 'NIVEL 5':'NIVEL_5'}
    df_roles.rename(columns=map_cols, inplace=True)

if not df_historial.empty and 'NOTA_FINAL' in df_historial.columns:
    df_historial['NOTA_FINAL'] = pd.to_numeric(df_historial['NOTA_FINAL'], errors='coerce').fillna(0)

# Parada
parada_actual = "No Configurada"
if not df_config.empty:
    # Intenta tomar el primer valor
    parada_actual = str(df_config.iloc[0].values[0])

if 'usuario' not in st.session_state:
    st.session_state.update({'usuario': None, 'nombre_real': None, 'rol': None, 'dni_user': None})

# ==========================================
# 6. APP LOGIC
# ==========================================
if not st.session_state.usuario:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center; color: white !important;'>PORTAL PRODISE</h1>", unsafe_allow_html=True)
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR", type="primary", use_container_width=True):
            if not df_users.empty:
                u = df_users[df_users['USUARIO'] == user]
                if not u.empty and str(u.iloc[0]['PASS']) == pw and u.iloc[0]['ESTADO'] == 'ACTIVO':
                    st.session_state.usuario = user
                    st.session_state.nombre_real = u.iloc[0]['NOMBRE']
                    st.session_state.rol = str(u.iloc[0]['ID_ROL']).upper().strip()
                    st.session_state.dni_user = str(u.iloc[0]['DNI_TRABAJADOR']).split('.')[0]
                    st.rerun()
                else: st.error("Acceso denegado")
            else: st.error("Error conectando a la base de usuarios. Revisa tu internet o Airtable.")
else:
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        st.markdown(f"### {st.session_state.nombre_real}")
        st.caption(f"Rol: {st.session_state.rol}")
        st.info(f"Parada: {parada_actual}")
        menu = st.radio("Menú", ["📝 Evaluar", "📈 Historial"], label_visibility="collapsed")
        if st.button("Salir"): 
            st.session_state.usuario = None
            st.rerun()

    # Filtros
    data_view = df_personal[df_personal['ESTADO'] == 'ACTIVO'] if not df_personal.empty else pd.DataFrame()
    if st.session_state.rol == 'SUPERVISOR DE OPERACIONES' and not df_personal.empty:
        me = df_personal[df_personal['DNI'] == st.session_state.dni_user]
        if not me.empty:
            grp, trn = me.iloc[0]['ID_GRUPO'], me.iloc[0]['TURNO']
            data_view = data_view[(data_view['ID_GRUPO'] == grp) & (data_view['TURNO'] == trn) & (data_view['DNI'] != st.session_state.dni_user)]
            st.success(f"Filtro: Grupo {grp} - Turno {trn}")

    if menu == "📝 Evaluar":
        st.title("Evaluación de Personal")
        sel = st.selectbox("Seleccionar:", data_view['NOMBRE_COMPLETO'].unique()) if not data_view.empty else None
        
        if sel:
            p = data_view[data_view['NOMBRE_COMPLETO'] == sel].iloc[0]
            st.markdown(f"**Cargo:** {p['CARGO_ACTUAL']} | **DNI:** {p['DNI']}")
            
            # Preguntas
            preguntas = pd.DataFrame()
            if not df_roles.empty:
                df_roles['CARGO_NORM'] = df_roles['CARGO'].astype(str).str.upper().str.strip()
                target = str(p['CARGO_ACTUAL']).upper().strip()
                preguntas = df_roles[df_roles['CARGO_NORM'] == target]

            with st.form("frm"):
                if preguntas.empty:
                    st.warning("No hay preguntas para este cargo")
                    st.form_submit_button("Volver")
                else:
                    score = 0
                    notas = {}
                    for i, (idx, row) in enumerate(preguntas.iterrows(), 1):
                        st.markdown(f"**{row['CRITERIO']}** ({row['PORCENTAJE']*100:.0f}%)")
                        ops = [str(row[f'NIVEL_{k}']) for k in range(1,6)]
                        ans = st.radio(f"p{i}", ops, key=f"r{i}", label_visibility="collapsed")
                        val = ops.index(ans) + 1
                        score += val * row['PORCENTAJE']
                        notas[f"NOTA_{i}"] = val
                    
                    obs = st.text_area("Observaciones")
                    if st.form_submit_button("GUARDAR EN NUBE"):
                        if obs and tbl_historial:
                            # MAPEO A TUS COLUMNAS DE LA ÚLTIMA CAPTURA
                            record = {
                                "FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "COD_PARADA": parada_actual,              
                                "DNI_EVALUADOR": st.session_state.dni_user,
                                "DNI_TRABAJADOR": str(p['DNI']),
                                "CARGO_MOMENTO": str(p['CARGO_ACTUAL']), 
                                "GRUPO_MOMENTO": str(p['ID_GRUPO']),     
                                "TURNO_MOMENTO": str(p['TURNO']),        
                                "NOTA_FINAL": round(score, 2),
                                "COMENTARIOS": obs
                            }
                            # Añadir notas 1-5 si creaste las columnas NOTA_1, etc.
                            record.update(notas)
                            
                            try:
                                tbl_historial.create(record)
                                st.success("¡Guardado exitosamente!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Error Airtable: {e}")
                        else: st.error("Falta comentario o conexión")

    elif menu == "📈 Historial":
        st.title("Historial")
        sel = st.selectbox("Ver a:", data_view['NOMBRE_COMPLETO'].unique()) if not data_view.empty else None
        if sel and not df_historial.empty:
            dni = data_view[data_view['NOMBRE_COMPLETO'] == sel].iloc[0]['DNI']
            h = df_historial[df_historial['DNI_TRABAJADOR'] == dni]
            if not h.empty:
                # Mostrar columnas si existen
                cols_to_show = [c for c in ['FECHA_HORA', 'NOTA_FINAL', 'COMENTARIOS'] if c in h.columns]
                st.dataframe(h[cols_to_show])
            else: st.info("Sin registros")