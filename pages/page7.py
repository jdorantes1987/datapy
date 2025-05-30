import time

import streamlit as st
from pandas import DataFrame

import gestion_user.usuarios as u
from gestion_user.control_roles import dict_users_rols, insert_roles, modulos
from gestion_user.control_usuarios import (
    aut_user,
    change_password,
    existe_user,
    get_users,
    insert_user,
)
from gestion_user.usuarios_roles import ClsUsuariosRoles
from navigation import make_sidebar

st.set_page_config(
    page_title="DataPy: Reiniciar clave", layout="centered", page_icon=":vs:"
)
make_sidebar()


@st.cache_data
def roles_user():
    return ClsUsuariosRoles.roles()


def usuarios():
    return get_users()


if "stage7" not in st.session_state:
    st.session_state.stage7 = 0


def set_stage(i):
    st.session_state.stage7 = i


if st.session_state.stage7 == 0:
    st.session_state.w_id = ""
    st.session_state.w_nombre = ""
    st.session_state.w_pw = ""
    df_users = usuarios()
    set_stage(1)

st.title("Gestion de Usuarios")

df_users = usuarios()


def agregar_usuario(id_user, nombre, password, stage):
    insert_user(user=id_user, nombre=nombre, pw=password)
    set_stage(stage)


def agregar_roles(user, data_roles):
    data = data_roles.reset_index()
    insert_roles(user=user, data_roles=data)


with st.expander("Cambiar clave de usuario"):
    current_password = st.text_input("clave actual", type="password")
    new_password = st.text_input("nueva clave", type="password")
    rep_new_password = st.text_input("repetir clave", type="password")
    if st.button("cambiar", type="primary"):
        user = u.ClsUsuarios.id_usuario()
        aut = aut_user(user, current_password)
        if aut:
            if new_password == rep_new_password:
                change_password(user, new_password)
                st.success("La clave fue cambiada con éxito!")
                time.sleep(1)
                st.switch_page("pages/page1.py")
            else:
                st.error("La nueva clave ingresada no coincide con la confirmación.")
        else:
            st.error("La clave ingresada no coincide con la anterior.")

roles = roles_user()
df_roles = DataFrame.from_dict(
    roles, orient="index", columns=["usuario", "habilitado", "id"]
)

if roles.get("Admin", 0)[1] == 1:
    with st.expander("agregar nuevo usuario"):
        id_user = st.text_input(
            label="id usuario",
            disabled=False,
            key="w_id",
            placeholder="ingrese el id. usuario",
        )
        if len(id_user) > 0:
            existe_usuario = existe_user(id_user)
            if not existe_usuario:
                nombre = st.text_input(
                    label="nombre",
                    disabled=False,
                    key="w_nombre",
                    placeholder="Ingrese el nombre y apellido",
                )

                password = st.text_input(
                    "Enter a password",
                    type="password",
                    key="w_pw",
                )

                if len(id_user) and len(nombre) and len(password):
                    st.button(
                        "agregar nuevo usuario",
                        on_click=agregar_usuario,
                        args=[id_user, nombre, password, 0],
                    )
                    st.badge(
                        label="Datos ingresados correctamente",
                        color="green",
                    )
                else:
                    st.badge(
                        label="Usuario disponible",
                        color="blue",
                    )
                    st.warning("Debe ingresar los demás datos solicitados.")
            else:
                st.badge(
                    label=f"⚠️ {id_user} ya existe en la base de datos",
                    color="orange",
                )

    if roles.get("Admin", 0)[1] == 1:
        with st.expander("agregar roles usuario"):
            df_users["buscador_usuarios"] = (
                df_users["idusuario"] + " | " + df_users["nombre"]
            )
            list_users = df_users["buscador_usuarios"].unique().tolist()
            list_users = sorted(list_users)
            #  Crea un selectbox que contenga todos los vendedores.
            user_select = str.strip(
                st.selectbox(
                    "Elije un usuario:", list_users, int(len(list_users) - 1)
                ).split("|")[0]
            )
            dit_user_select_roles = dict_users_rols(user_select)
            df_dit_user_select = DataFrame.from_dict(
                dit_user_select_roles,
                orient="index",
                columns=["usuario", "habilitado", "id"],
            )
            if len(df_dit_user_select):
                df_roles = df_dit_user_select
                df_roles.insert(0, "idusuario", user_select)
                df_roles.reset_index(inplace=True, names="modulo")
            else:
                df_roles = modulos()
                df_roles.insert(0, "idusuario", user_select)
                df_roles.insert(1, "habilitado", False)

            df_roles.set_index("modulo", inplace=True)
            de_roles = st.data_editor(
                df_roles[["habilitado", "idusuario"]],
                column_config={
                    "habilitado": st.column_config.CheckboxColumn(
                        "habilitado?",
                        help="clic para habilitar modulo ",
                        default=False,
                    ),
                    "idusuario": st.column_config.TextColumn(
                        "usuario",
                    ),
                },
                disabled=["modulo"],
                hide_index=False,
            )
            if st.button(
                "agregar roles", on_click=agregar_roles, args=[user_select, de_roles]
            ):
                st.success("Roles agregados!")
                set_stage(0)
