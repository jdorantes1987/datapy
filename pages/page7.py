import time

import streamlit as st
from pandas import DataFrame
from navigation import make_sidebar

st.set_page_config(
    page_title="DataPy: Reiniciar clave", layout="centered", page_icon=":vs:"
)
make_sidebar()


if "stage7" not in st.session_state:
    st.session_state.stage7 = 0


def set_stage(i):
    st.session_state.stage7 = i


if st.session_state.stage7 == 0:
    st.session_state.w_id = ""
    st.session_state.w_nombre = ""
    st.session_state.w_pw = ""
    set_stage(1)

st.title("Gestion de Usuarios")

with st.expander("Cambiar clave de usuario"):
    current_password = st.text_input("clave actual", type="password")
    new_password = st.text_input("nueva clave", type="password")
    rep_new_password = st.text_input("repetir clave", type="password")
    if st.button("cambiar", type="primary"):
        user = st.session_state.user
        flag, msg = st.session_state.auth_manager.autenticar(user, current_password)
        if flag:
            if new_password == rep_new_password:
                st.session_state.auth_manager.modificar_clave(user, new_password)
                st.success(msg)
                time.sleep(1)
                st.switch_page("pages/page1.py")
            else:
                st.error("La nueva clave ingresada no coincide con la confirmación.")
        else:
            st.error(msg)
