import os
import time

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
g = GestionarClientes(company_selected)
col1, col2 = st.columns(2, gap="small")
with col1:
    if st.button("Refrescar"):
        st.cache_data.clear()


@st.cache_data
def clientes(empresa):
    return ClsData(empresa).clientes()


@st.cache_data
def datos_clientes_por_sinc_profit_mikrowisp():
    return g.datos_clientes_por_sinc_profit_mikrowisp()


@st.cache_data
def datos_clientes_por_registrar():
    return g.datos_clientes_por_registrar()


@st.cache_data
def datos_clientes_nodo_por_sinc_mikrowisp_profit():
    return g.datos_clientes_nodo_por_sinc_mikrowisp_profit()


@st.cache_data
def sinc_datos_clientes_nodos():
    return g.sinc_datos_clientes_nodos()


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

#  CLIENTES POR REGISTRAR EN MIKROWISP
datos_clientes_por_sinc_mkwsp = datos_clientes_por_registrar()
if len(datos_clientes_por_sinc_mkwsp) > 0:
    st.write("📗 Clientes en Profit por registrar en Mikrowisp")
    with st.expander("agregar"):
        st.dataframe(
            datos_clientes_por_sinc_mkwsp,
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Agregar"):
            g.add_clientes_en_mikrowisp()
            g.add_notificaciones()
            st.info("Cliente registrado con éxito!")
            time.sleep(1)
            st.cache_data.clear()
            st.rerun()

#  DATOS POR ACTUALIZAR EN MIKROWISP
clientes_a_ignorar = set(datos_clientes_por_sinc_mkwsp["co_cli"])
datos_clientes_por_sinc = datos_clientes_por_sinc_profit_mikrowisp()
datos_clientes_por_sinc_sin_clientes_por_agregar = datos_clientes_por_sinc[
    ~datos_clientes_por_sinc["co_cli"].isin(clientes_a_ignorar)
]
datos_clientes_por_sinc_prof = datos_clientes_por_sinc_sin_clientes_por_agregar
if len(datos_clientes_por_sinc_prof) > 0:
    st.write("⚡ Clientes por actualizar en Mikrowisp desde Profit")
    with st.expander("datos"):
        st.dataframe(
            datos_clientes_por_sinc_prof,
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Actualizar datos básicos"):
            g.sinc_datos_clientes_profit_mikrowisp()
            st.info("Cliente actualizado con éxito en Mikrowisp!")
            time.sleep(1)
            st.cache_data.clear()
            st.rerun()

datos_clientes_por_act_nodo = datos_clientes_nodo_por_sinc_mikrowisp_profit()
if len(datos_clientes_por_act_nodo) > 0:
    st.write("🔄 Clientes por actualizar nodo en Profit")
    with st.expander("datos"):
        st.dataframe(
            datos_clientes_por_act_nodo,
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Actualizar"):
            g.sinc_datos_clientes_nodos()
            st.info("Cliente actualizado con éxito en Profit!")
            st.cache_data.clear()
            st.rerun()
