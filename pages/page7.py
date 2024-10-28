import time
import streamlit as st
from navigation import make_sidebar
import gestion_user.usuarios as u
from gestion_user.control_usuarios import aut_user, change_password

st.set_page_config(page_title='DataPy: Reiniciar clave', 
                   layout='centered', 
                   page_icon=':vs:')
make_sidebar()
st.title("Cambiar clave de usuario")
current_password = st.text_input("clave actual", type="password")
new_password = st.text_input("nueva clave", type="password")
rep_new_password = st.text_input("repetir clave", type="password")

if st.button("cambiar", type="primary"):
    user = u.ClsUsuarios.id_usuario()
    aut = aut_user(user, current_password)
    if aut:
       if new_password==rep_new_password:
          change_password(user, new_password) 
          st.success("La clave fue cambiada con éxito!")
          time.sleep(1)
          st.switch_page("pages/page1.py")
       else:
          st.error("La nueva clave ingresada no coincide con la confirmación.")
    else:
        st.error("La clave ingresada no coincide con la anterior.")

