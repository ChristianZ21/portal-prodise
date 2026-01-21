import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from pyairtable import Api

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="ProDise Executive", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLAVES (Ocultar en producción) ---
AIRTABLE_API_TOKEN = "pat3Ig7rAOvq7JdpN.fbef700fa804ae5692e3880899bba070239e9593f8d6fde958d9bd3d615aca14"
AIRTABLE_BASE_ID = "app2jaysCvPwvrBwI"

# --- PALETA DE COLORES EJECUTIVA ---
COLOR_PRIMARIO = "#0F172A"       # Azul Marino Profundo (Navy)
COLOR_SECUNDARIO = "#334155"     # Gris Pizarra
COLOR_ACCENTO = "#3B82F6"        # Azul Brillante (Botones)
COLOR_FONDO = "#F8FAFC"          # Blanco Hielo (Fondo limpio)
COLOR_TEXTO = "#1E293B"          # Gris Oscuro (Lectura fácil)

# --- CSS PERSONALIZADO (Look & Feel) ---
st.markdown(f"""
<style>
    /* Fondo General */
    .stApp {{ background-color: {COLOR_FONDO}; }}
    
    /* Títulos Elegantes */
    h1, h2, h3 {{ color: {COLOR_PRIMARIO} !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }}
    
    /* Tarjetas (Cards) */
    .css-card {{
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
    }}
    
    /* Botones Premium */
    div.stButton > button {{
        background: linear-gradient(90deg, {COLOR_PRIMARIO} 0%, {COLOR_SECUNDARIO} 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }}

    /* Sidebar limpio */
    [data-testid="stSidebar"] {{ background-color: white; border-right: 1px solid #E2E8F0; }}
    
    /* Ajustes de métricas */
    div[data-testid="metric-container"] {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN OPTIMIZADA (CACHÉ)
# ==========================================
# Usamos cache para que no recargue Airtable a cada click (SOLUCIÓN A PANTALLA BLANCA)
@st.cache_data(ttl=60) # Recarga datos cada 60 segundos automáticamente
def load_data():
    try:
        api = Api(AIRTABLE_API_TOKEN)
        
        def get_df(table_name):
            t = api.table(AIRTABLE_BASE_ID, table_name)
            records = t.all()
            if not records: return pd.DataFrame(), t
            df = pd.DataFrame([r['fields'] for r in records])
            # Limpieza de datos
            for c in df.columns: 
                df[c] = df[c].astype(str).str.strip() # Quita espacios extra
            return df, t

        df_u, _ = get_df("DB_USUARIOS")
        df_p, _ = get_df("DB_PERSONAL")
        df_r, _ = get_df("CONFIG_ROLES")
        df_h, tbl_h = get_df("DB_HISTORIAL")
        df_c, _ = get_df("CONFIG")
        
        # Conversiones numéricas seguras
        if not df_r.empty and 'PORCENTAJE' in df_r.columns:
            df_r['PORCENTAJE'] = pd.to_numeric(df_r['PORCENTAJE'], errors='coerce').fillna(0)
        
        if not df_h.empty and 'NOTA_FINAL' in df_h.columns:
            df_h['NOTA_FINAL'] = pd.to_numeric(df_h['NOTA_FINAL'], errors='coerce').fillna(0)
            
        return df_u, df_p, df_r, df_h, tbl_h, df_c
        
    except Exception as e:
        return None, None, None, None, None, None

# Cargar Datos
with st.spinner("Conectando con la base de datos..."):
    df_users, df_personal, df_roles, df_historial, tbl_historial, df_config = load_data()

# Verificación de Seguridad (Si falla la carga)
if df_personal is None:
    st.error("🚨 Error crítico de conexión. Verifica tu internet o las claves de Airtable.")
    st.stop()

# Parada Actual
parada_actual = df_config.iloc[0].values[0] if not df_config.empty else "P-GEN"

# Session State
if 'usuario' not in st.session_state:
    st.session_state.update({'usuario': None, 'nombre_real': None, 'rol': None, 'dni_user': None})

# ==========================================
# 3. LÓGICA DE LOGIN
# ==========================================
if not st.session_state.usuario:
    col1, col2, col3 = st.columns([1, 0.8, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <h1 style="color:{COLOR_PRIMARIO}; margin-bottom: 0;">Portal PRODISE</h1>
            <p style="color: grey;">Acceso Corporativo</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        user = st.text_input("ID Usuario", placeholder="Ej. jperez")
        pw = st.text_input("Contraseña", type="password", placeholder="••••••")
        
        if st.button("INICIAR SESIÓN", use_container_width=True):
            if not df_users.empty:
                u = df_users[df_users['USUARIO'] == user]
                if not u.empty and u.iloc[0]['PASS'] == pw and u.iloc[0]['ESTADO'] == 'ACTIVO':
                    st.session_state.usuario = user
                    st.session_state.nombre_real = u.iloc[0]['NOMBRE']
                    st.session_state.rol = u.iloc[0]['ID_ROL'].upper()
                    st.session_state.dni_user = u.iloc[0]['DNI_TRABAJADOR']
                    st.rerun()
                else: st.error("Credenciales incorrectas")
            else: st.error("Error de base de datos")

else:
    # ==========================================
    # 4. INTERFAZ PRINCIPAL (DASHBOARD)
    # ==========================================
    
    # --- Sidebar ---
    with st.sidebar:
        st.image("logo.png", use_container_width=True) if os.path.exists("logo.png") else st.title("🏭")
        st.markdown(f"**Hola, {st.session_state.nombre_real.split()[0]}**")
        st.caption(f"{st.session_state.rol}")
        
        # Menú con estilo de Botones (Pills)
        opciones = ["Evaluar Personal", "Mi Historial"]
        if st.session_state.rol == 'ADMIN': opciones.insert(1, "Ranking Gerencial")
        
        seleccion = st.radio("Navegación", opciones, label_visibility="collapsed")
        
        st.markdown("---")
        st.info(f"🔧 Parada: **{parada_actual}**")
        if st.button("Cerrar Sesión", type="secondary"):
            st.session_state.usuario = None
            st.rerun()

    # --- Lógica de Filtros (Supervisor) ---
    data_view = df_personal[df_personal['ESTADO'] == 'ACTIVO']
    if st.session_state.rol == 'SUPERVISOR DE OPERACIONES':
        me = df_personal[df_personal['DNI'] == st.session_state.dni_user]
        if not me.empty:
            grp, trn = me.iloc[0]['ID_GRUPO'], me.iloc[0]['TURNO']
            data_view = data_view[(data_view['ID_GRUPO'] == grp) & (data_view['TURNO'] == trn)]
            data_view = data_view[data_view['DNI'] != st.session_state.dni_user]

    # ----------------------------------------
    # VISTA 1: EVALUACIÓN (REDISEÑADA)
    # ----------------------------------------
    if seleccion == "Evaluar Personal":
        st.title("📝 Centro de Evaluación")
        
        # Selector Principal (Limpio)
        col_sel, col_info = st.columns([1, 2])
        with col_sel:
            # Dropdown robusto
            lista_nombres = data_view['NOMBRE_COMPLETO'].unique().tolist() if not data_view.empty else []
            if not lista_nombres:
                st.warning("⚠️ No hay personal asignado a tu grupo/turno.")
                target_person = None
            else:
                target_person = st.selectbox("Seleccionar Colaborador:", lista_nombres)

        if target_person:
            p = data_view[data_view['NOMBRE_COMPLETO'] == target_person].iloc[0]
            
            # --- TARJETA DE IDENTIDAD (VISUAL) ---
            with col_info:
                st.markdown(f"""
                <div class="css-card" style="display: flex; align-items: center; gap: 20px;">
                    <img src="{p.get('URL_FOTO', '')}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid {COLOR_ACCENTO};">
                    <div>
                        <h3 style="margin:0; color:{COLOR_PRIMARIO};">{p['NOMBRE_COMPLETO']}</h3>
                        <p style="margin:0; color:grey; font-weight:bold;">{p['CARGO_ACTUAL']}</p>
                        <span style="background-color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">{p['ID_GRUPO']} - {p['TURNO']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- FORMULARIO DE ESTRELLAS (STAR RATING) ---
            # Filtramos preguntas
            preguntas = pd.DataFrame()
            if not df_roles.empty:
                df_roles['CARGO_NORM'] = df_roles['CARGO'].str.upper().str.strip()
                target_cargo = p['CARGO_ACTUAL'].upper().strip()
                preguntas = df_roles[df_roles['CARGO_NORM'] == target_cargo]

            if preguntas.empty:
                st.info(f"ℹ️ No hay criterios de evaluación definidos para el cargo: {p['CARGO_ACTUAL']}")
            else:
                with st.form("frm_eval"):
                    st.markdown("### 🎯 Criterios de Desempeño")
                    score_total = 0
                    notas_guardar = {}
                    
                    # Iteramos preguntas
                    for i, (idx, row) in enumerate(preguntas.iterrows(), 1):
                        col_preg, col_star = st.columns([2, 1])
                        with col_preg:
                            st.markdown(f"**{i}. {row['CRITERIO']}**")
                            st.caption(f"Peso: {row['PORCENTAJE']*100:.0f}%")
                        with col_star:
                            # AQUÍ ESTÁ LA MAGIA VISUAL: st.feedback (Estrellas)
                            # Nota: st.feedback devuelve 0-4 (índice), por eso sumamos +1
                            val = st.feedback("stars", key=f"star_{i}")
                            nota_real = (val + 1) if val is not None else 0
                            
                            score_total += nota_real * row['PORCENTAJE']
                            notas_guardar[f"NOTA_{i}"] = nota_real
                        st.divider()

                    observacion = st.text_area("💬 Observaciones / Feedback", placeholder="Escribe un comentario constructivo...")
                    
                    # Botón de Guardado
                    c_submit = st.columns([1, 2, 1])
                    with c_submit[1]:
                        submitted = st.form_submit_button("💾 GUARDAR EVALUACIÓN", use_container_width=True)
                        
                    if submitted:
                        if observacion and tbl_historial:
                            record = {
                                "FECHA_HORA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "COD_PARADA": parada_actual,
                                "DNI_EVALUADOR": st.session_state.dni_user,
                                "DNI_TRABAJADOR": p['DNI'],
                                "CARGO_MOMENTO": p['CARGO_ACTUAL'],
                                "GRUPO_MOMENTO": p['ID_GRUPO'],
                                "TURNO_MOMENTO": p['TURNO'],
                                "NOTA_FINAL": round(score_total, 2),
                                "COMENTARIOS": observacion
                            }
                            record.update(notas_guardar)
                            try:
                                tbl_historial.create(record)
                                st.success("✅ Evaluación registrada correctamente")
                                st.balloons()
                            except Exception as e: st.error(f"Error técnico: {e}")
                        else:
                            st.warning("⚠️ Por favor completa las estrellas y añade un comentario.")

    # ----------------------------------------
    # VISTA 2: RANKING GERENCIAL (PODIO)
    # ----------------------------------------
    elif seleccion == "Ranking Gerencial" and st.session_state.rol == 'ADMIN':
        st.title("🏆 Ranking de Desempeño Global")
        
        if df_historial.empty:
            st.info("No hay datos suficientes para generar el ranking.")
        else:
            # Procesamiento de datos
            resumen = df_historial.groupby('DNI_TRABAJADOR')['NOTA_FINAL'].mean().reset_index()
            resumen.columns = ['DNI', 'PROMEDIO']
            ranking = pd.merge(resumen, df_personal, on='DNI', how='left')
            ranking['PROMEDIO'] = ranking['PROMEDIO'].round(2)
            ranking = ranking.sort_values('PROMEDIO', ascending=False).reset_index(drop=True)
            
            # --- PODIO VISUAL ---
            if len(ranking) >= 3:
                c2, c1, c3 = st.columns([1, 1.2, 1]) # El 1ro al centro y más grande
                
                # Top 2
                with c2:
                    p2 = ranking.iloc[1]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid silver;">
                        <h1>🥈</h1>
                        <img src="{p2.get('URL_FOTO','')}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
                        <h4>{p2['NOMBRE_COMPLETO'].split()[0]}</h4>
                        <h2 style="color:grey;">{p2['PROMEDIO']}</h2>
                    </div>
                    """, unsafe_allow_html=True)

                # Top 1 (Centro)
                with c1:
                    p1 = ranking.iloc[0]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid gold; transform: scale(1.05);">
                        <h1>👑</h1>
                        <img src="{p1.get('URL_FOTO','')}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border: 4px solid gold;">
                        <h3>{p1['NOMBRE_COMPLETO'].split()[0]}</h3>
                        <h1 style="color:#DAA520;">{p1['PROMEDIO']}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Top 3
                with c3:
                    p3 = ranking.iloc[2]
                    st.markdown(f"""
                    <div class="css-card" style="text-align:center; border-top: 5px solid #CD7F32;">
                        <h1>🥉</h1>
                        <img src="{p3.get('URL_FOTO','')}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;">
                        <h4>{p3['NOMBRE_COMPLETO'].split()[0]}</h4>
                        <h2 style="color:grey;">{p3['PROMEDIO']}</h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("### 📊 Tabla General")
            st.dataframe(
                ranking[['NOMBRE_COMPLETO', 'CARGO_ACTUAL', 'PROMEDIO', 'ID_GRUPO']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PROMEDIO": st.column_config.ProgressColumn("Puntaje", min_value=0, max_value=5, format="%.2f"),
                    "URL_FOTO": st.column_config.ImageColumn("Foto")
                }
            )

    # ----------------------------------------
    # VISTA 3: HISTORIAL SIMPLE
    # ----------------------------------------
    elif seleccion == "Mi Historial":
        st.title("📂 Historial de Registros")
        st.dataframe(df_historial, use_container_width=True)