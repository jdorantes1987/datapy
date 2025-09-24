from time import sleep

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Removed import of 'get_pages' as it is no longer available in Streamlit

import gestion_user.usuarios_roles as ur
from empresa import ClsEmpresa


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("No se pudo obtener el contexto del script.")


def make_sidebar():
    with st.sidebar:
        # Centrar el título
        # quitar margenes
        st.markdown(
            "<h1 style='text-align: center; margin: 0;'>DataPy</h1>",
            unsafe_allow_html=True,
        )
        # imagen desde URL
        # Quitar margenes
        image_url = "images/svg3.svg"

        st.image(image_url, use_container_width=True)
        # imagen local
        st.markdown("---")

        # chequea si el usuario está logueado
        if st.session_state.get("logged_in", False):
            _extracted_from_make_sidebar()  # llama a la función que crea el sidebar
        elif get_current_page_name() != "app":
            # si no está logueado y no está en la página de login, redirige a la página de login
            st.switch_page("app.py")


def _extracted_from_make_sidebar():
    if (
        ur.ClsUsuariosRoles.roles().get("Derecha", 0)[1] == 1
        or ur.ClsUsuariosRoles.roles().get("Izquierda")[1] == 1
    ):
        st.page_link("pages/page1.py", label="Inicio", icon=None)
    if ur.ClsUsuariosRoles.roles().get("Ingresos", 0)[1] == 1:
        st.page_link("pages/page2.py", label="Ingresos", icon=None)
    if ur.ClsUsuariosRoles.roles().get("Cxc", 0)[1] == 1:
        st.page_link("pages/page3.py", label="Cuentas por cobrar", icon=None)
    if ur.ClsUsuariosRoles.roles().get("Facturacion", 0)[1] == 1:
        st.page_link("pages/page4.py", label="Facturación masiva", icon=None)
    if ur.ClsUsuariosRoles.roles().get("Mikrowisp", 0)[1] == 1:
        st.page_link("pages/page5.py", label="Mikrowisp", icon=None)
    st.page_link("pages/page6.py", label="Clientes", icon=None)
    st.page_link("pages/page7.py", label="Configuración", icon=None)

    st.write("\n" * 2)
    l_modulos = ["Derecha", "Izquierda"]

    # administra el acceso del usuario a los módulos
    if ur.ClsUsuariosRoles.roles().get("Derecha", 0)[1] == 0:
        l_modulos.pop(0)
    elif ur.ClsUsuariosRoles.roles().get("Izquierda", 0)[1] == 0:
        l_modulos.pop(1)

    st.radio(
        "Seleccione la empresa:",
        l_modulos,
        index=l_modulos.index(ClsEmpresa.modulo()),
        key="emp_select",
        on_change=al_cambiar_empresa,
        horizontal=True,
    )
    # ClsEmpresa(empresa_select, False)

    def logout():
        st.session_state.logged_in = False
        st.info("Se ha cerrado la sesión con éxito!")
        sleep(0.5)
        st.switch_page("app.py")

    if st.button("Cerrar sesión", type="primary"):
        logout()


def al_cambiar_empresa():
    # Reinicia las variables de sesión relacionadas con las paginas
    st.session_state.stage2 = 0
    st.session_state.stage5 = 0
    st.session_state.stage4 = 0
    st.cache_data.clear()

    # Limpia las variables de sesión específicas de las páginas
    for key in ["data_masiva", "client_x_reg", "datos_x_sinc"]:
        if key in st.session_state:
            del st.session_state[key]

    # Actualiza la empresa seleccionada y limpia variables de sesión relacionadas
    if "emp_select" in st.session_state:
        ClsEmpresa(st.session_state.emp_select, False)
        del st.session_state["emp_select"]
