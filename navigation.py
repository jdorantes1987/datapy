from time import sleep

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from empresa import ClsEmpresa

# Removed import of 'get_pages' as it is no longer available in Streamlit


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("No se pudo obtener el contexto del script.")

    return ctx.page_script_hash.split("/")[-1]  # type: ignore


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
    st.page_link("pages/page1.py", label="Inicio", icon=None)
    # Verificar permisos
    if st.session_state.rol_user.has_permission("Estadísticas", "read"):
        st.page_link("pages/page2.py", label="Ingresos", icon=None)
        st.page_link("pages/page3.py", label="Cuentas por cobrar", icon=None)

    if st.session_state.rol_user.has_permission("Fact_Masiva", "create"):
        st.page_link("pages/page4.py", label="Facturación masiva", icon=None)
    if st.session_state.rol_user.has_permission("Mikrowisp", "read"):
        st.page_link("pages/page5.py", label="Mikrowisp", icon=None)
    st.page_link("pages/page6.py", label="Clientes", icon=None)
    st.page_link("pages/page7.py", label="Configuración", icon=None)

    st.write("\n" * 2)
    l_modulos = ["Izquierda", "Derecha"]

    # administra el acceso del usuario a los módulos
    es_admin = st.session_state.rol_user.has_permission("Administrador", "read")
    tiene_mod_der = st.session_state.rol_user.has_permission("Mod_der", "read")
    tiene_mod_izq = st.session_state.rol_user.has_permission("Mod_izq", "read")

    if not es_admin:
        if not tiene_mod_der and "Derecha" in l_modulos:
            l_modulos.remove("Derecha")
        if not tiene_mod_izq and "Izquierda" in l_modulos:
            l_modulos.remove("Izquierda")

    if not l_modulos:
        st.warning("No tienes acceso a ningun modulo.")
        return

    st.radio(
        "Seleccione la empresa:",
        l_modulos,
        index=l_modulos.index(ClsEmpresa.modulo()),
        key="emp_select",
        on_change=al_cambiar_empresa,
        horizontal=True,
    )

    if st.button(
        "Cerrar sesión",
        type="primary",
    ):
        logout()

    st.cache_data.clear()


def logout():
    ClsEmpresa.limpiar_usuario(st.session_state.get("usuario", ""))
    st.session_state.logged_in = False
    st.info("Se ha cerrado la sesión con éxito!")
    sleep(0.5)
    st.switch_page("app.py")


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
        ClsEmpresa(st.session_state.usuario, st.session_state.emp_select, False)
        del st.session_state["emp_select"]
