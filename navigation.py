import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import gestion_user.usuarios_roles as ur
from empresa import ClsEmpresa

def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("No se pudo obtener el contexto del script.")

    pages = get_pages("")
    return pages[ctx.page_script_hash]["page_name"]

def make_sidebar():
    with st.sidebar:
        # Custom CSS for changing the sidebar color
        custom_css = """
                    
                    """
        # Apply custom CSS
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: grey;'>DataPy</h1>", 
                    unsafe_allow_html=True
        )
        st.markdown("---")
        
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            _extracted_from_make_sidebar()
        elif get_current_page_name() != "app":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("app.py") 
        
# TODO Rename this here and in `make_sidebar`
def _extracted_from_make_sidebar():
    if ur.ClsUsuariosRoles.roles()['Derecha'] == 1 or ur.ClsUsuariosRoles.roles()['Izquierda'] == 1:
        st.page_link("pages/page1.py", label="Inicio", icon=None)
    if ur.ClsUsuariosRoles.roles()['Ingresos'] == 1:
        st.page_link("pages/page2.py", label="Ingresos", icon=None)
    if ur.ClsUsuariosRoles.roles()['Cxc'] == 1:    
        st.page_link("pages/page3.py", label="Cuentas por cobrar", icon=None)
    if ur.ClsUsuariosRoles.roles()['Facturacion'] == 1:
        st.page_link("pages/page4.py", label="Facturación masiva", icon=None)
    if ur.ClsUsuariosRoles.roles()['Mikrowisp'] == 1:    
        st.page_link("pages/page5.py", label="Mikrowisp", icon=None)
    st.page_link("pages/page6.py", label="Clientes", icon=None)
    st.page_link("pages/page7.py", label="Configuración", icon=None)
  
    st.write("\n" * 2)
    l_modulos = ['Derecha', 'Izquierda']
    # administra el acceso del usuario a los módulos
    if ur.ClsUsuariosRoles.roles()['Derecha'] == 0:
        l_modulos.pop(0)
    elif ur.ClsUsuariosRoles.roles()['Izquierda'] == 0:
        l_modulos.pop(1)        

    indice_mod = l_modulos.index(st.session_state['modulo'])
    empresa_select = st.selectbox('Seleccione la empresa:', l_modulos, 
                                  index=indice_mod, 
                                  on_change=al_cambiar_empresa)
    
    ClsEmpresa(empresa_select, False)
    
    if st.button("Cerrar sesión"):
        logout()


def al_cambiar_empresa():
    st.cache_data.clear()
    st.session_state.stage = 0
    if st.session_state['modulo'] == 'Izquierda':
       st.session_state.modulo = 'Derecha' 
    else:
        st.session_state.modulo = 'Izquierda' 
    
    if 'data_masiva' in st.session_state:
        del st.session_state['data_masiva']
    elif 'datos_clientes_por_sinc_prof' in st.session_state:
        del st.session_state['datos_clientes_por_sinc_prof']
    elif 'datos_clientes_por_sinc_prof' in st.session_state:
        del st.session_state['df_clientes']

def logout():
    st.session_state.logged_in = False
    st.info("Se ha cerrado la sesión con éxito!")
    sleep(0.5)
    st.switch_page("app.py")
