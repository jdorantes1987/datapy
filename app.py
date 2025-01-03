from datetime import datetime
from time import sleep

import streamlit as st

from empresa import ClsEmpresa
from gestion_user.control_usuarios import aut_user
from gestion_user.usuarios_roles import ClsUsuariosRoles

st.set_page_config(
    page_title="DataPy",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon=":vs:",
)

MENU_INICIO = "pages/page1.py"


def roles():
    return ClsUsuariosRoles.roles()


st.title("Inicio de sesión")
st.write("Por favor ingrese su usuario y clave.")
username = st.text_input("usuario")
password = st.text_input("clave", type="password")

if st.button("Log in", type="primary"):
    if is_valid := aut_user(username, password):
        date = datetime.now()
        print(f"{date} Usuario {username} ha iniciado sesión.")
        st.session_state.logged_in = True
        st.success("Sesión iniciada exitosamente!")
        st.cache_data.clear()
        st.session_state["refrescar_facturacion"] = False
        sleep(0.5)
        roles = roles()
        modulo = "Izquierda" if roles.get("Izquierda", 0)[1] == 1 else "Derecha"
        st.session_state.modulo = modulo
        ClsEmpresa(modulo, False)
        st.switch_page(MENU_INICIO)
    else:
        st.error("usuario o clave incorrecta")
