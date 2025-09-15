import os

import streamlit as st

from consulta_data import ClsData
from empresa import ClsEmpresa
from mikrowisp.controller.gestor_clientes import GestionarClientes
from navigation import make_sidebar

st.set_page_config(page_title="DataPy: Mikrowisp", layout="wide", page_icon=":vs:")

st.header(
    "🔄 Sincronización de datos",
    help="Esta sección permite mantener los datos sincronizados en las bases de datos Profit Plus y Microwisp",
)

make_sidebar()
company_selected = ClsEmpresa.empresa_seleccionada()
modulo = ClsEmpresa.modulo()


def set_stage(i):
    st.session_state.stage5 = i


if (
    "stage5" not in st.session_state
    or "client_x_reg" not in st.session_state
    # or "datos_x_sinc" not in st.session_state
    or "oGestionarClientes" not in st.session_state
    or "click_agregar" not in st.session_state
):
    st.session_state.oGestionarClientes = GestionarClientes(company_selected)
    set_stage(0)


if st.button("Refrescar"):
    st.cache_data.clear()
    set_stage(0)


@st.cache_data
def clientes(empresa):
    return ClsData(empresa).clientes()


@st.cache_data
def datos_clientes_por_sinc_profit_mikrowisp():
    return (
        st.session_state.oGestionarClientes.datos_clientes_por_sinc_profit_mikrowisp()
    )


@st.cache_data
def datos_clientes_por_registrar():
    return st.session_state.oGestionarClientes.datos_clientes_por_registrar()


@st.cache_data
def datos_clientes_nodo_por_sinc_mikrowisp_profit():
    return (
        st.session_state.oGestionarClientes.datos_clientes_nodo_por_sinc_mikrowisp_profit()
    )


@st.cache_data
def sinc_datos_clientes_nodos():
    return st.session_state.oGestionarClientes.sinc_datos_clientes_nodos()


if st.session_state.stage5 == 0:
    st.session_state.client_x_reg = datos_clientes_por_registrar()
    st.session_state.click_agregar = 0
    st.session_state.click_actualizar = 0
    # st.session_state.clientes_por_act_nodo = (
    #     datos_clientes_nodo_por_sinc_mikrowisp_profit()
    # )
    set_stage(1)


def lista_grupos_clientes(empresa):
    gp_clientes = clientes(empresa)
    # Filtra los registros que no son nulos
    gp_clientes = gp_clientes[gp_clientes["tipo_adi"] == 2]
    gp_clientes = gp_clientes.sort_values(by="cli_des", ascending=True)
    gp_clientes["buscar_cliente"] = (
        gp_clientes["co_cli"] + " | " + gp_clientes["cli_des"]
    )
    return gp_clientes["buscar_cliente"].tolist()


with st.expander("🔍 Grupos por cliente"):
    data_lista_clientes = lista_grupos_clientes(empresa=company_selected)
    grupo_select = str(st.selectbox("Elije un grupo:", data_lista_clientes, 0)).replace(
        " ", ""
    )
    if len(data_lista_clientes) > 0:
        df_clientes = clientes(company_selected)
        id_grupo = grupo_select.split("|")[0]
        grupo_filtrado = df_clientes[df_clientes["matriz"] == id_grupo].copy()
        if company_selected == os.getenv("DB_NAME_IZQUIERDA_PROFIT"):
            grupo_filtrado["co_cli_sort"] = grupo_filtrado["co_cli"].str.split(
                "-", expand=True
            )[1]
            grupo_filtrado["co_cli_sort"] = grupo_filtrado["co_cli_sort"].astype(
                "int64"
            )
            grupo = grupo_filtrado.sort_values(by="co_cli_sort", ascending=False)
        else:
            grupo = grupo_filtrado

        st.write(f":blue[{len(grupo)} cliente(s)]")
        st.dataframe(grupo, use_container_width=True, hide_index=True)


def state_click_add():
    st.session_state.click_agregar += 1


def state_click_update():
    st.session_state.click_actualizar += 1


# ETAPA 1: CLIENTES POR REGISTRAR EN MIKROWISP
if st.session_state.stage5 == 1:
    if len(st.session_state.client_x_reg) > 0:
        st.write("📗 Clientes en Profit por registrar en Mikrowisp")
        with st.expander("detalle"):
            st.dataframe(
                st.session_state.client_x_reg,
                use_container_width=True,
                hide_index=True,
            )
            if st.button("agregar", on_click=state_click_add):
                set_stage(2)


@st.fragment
def add_clientes():
    if st.session_state.click_agregar < 2:
        st.session_state.oGestionarClientes.add_clientes_en_mikrowisp()
        st.session_state.oGestionarClientes.add_notificaciones()


if st.session_state.stage5 == 2:
    if st.session_state.click_agregar < 2:
        with st.spinner("Registrando clientes en Mikrowisp..."):
            add_clientes()
            st.toast("Clientes registrados con éxito en Mikrowisp!", icon="✅")
            set_stage(3)
            st.rerun()
    elif st.session_state.click_agregar > 1:
        st.toast("Debes hacer click solo una vez!", icon="⚠️")
        set_stage(0)
        st.rerun()


# ETAPA 2: CLIENTES POR SINCRONIZAR EN MIKROWISP
if st.session_state.stage5 == 3:
    st.session_state.datos_x_sinc = datos_clientes_por_sinc_profit_mikrowisp()
    if len(st.session_state.datos_x_sinc) > 0:
        clientes_a_ignorar = set(st.session_state.client_x_reg["co_cli"])
        datos_clientes_por_sinc_sin_clientes_por_agregar = (
            st.session_state.datos_x_sinc[
                ~st.session_state.datos_x_sinc["co_cli"].isin(clientes_a_ignorar)
            ]
        )
        datos_clientes_por_sinc_prof = datos_clientes_por_sinc_sin_clientes_por_agregar
        if len(datos_clientes_por_sinc_prof) > 0:
            st.write("⚡ Clientes por actualizar en Mikrowisp desde Profit")
            with st.expander("detalle"):
                st.dataframe(
                    datos_clientes_por_sinc_prof,
                    use_container_width=True,
                    hide_index=True,
                )
                if st.button("agregar", on_click=state_click_update):
                    set_stage(4)


if st.session_state.stage5 == 4:
    if st.session_state.click_actualizar < 2:
        with st.spinner("Actualizando clientes en Mikrowisp..."):
            st.session_state.oGestionarClientes.sinc_datos_clientes_profit_mikrowisp()
            st.toast("Cliente actualizado con éxito en Mikrowisp!", icon="✅")
            set_stage(5)
            st.rerun()

#     if len(st.session_state.clientes_por_act_nodo) > 0:
#         st.write("🔄 Clientes por actualizar nodo en Profit")
#         with st.expander("detalle"):
#             st.dataframe(
#                 st.session_state.clientes_por_act_nodo,
#                 use_container_width=True,
#                 hide_index=True,
#             )
#             if st.button("Actualizar"):
#                 g.sinc_datos_clientes_nodos()
#                 st.info("Cliente actualizado con éxito en Profit!")
#                 set_stage(0)
