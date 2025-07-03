from io import BytesIO

import streamlit as st

from consulta_data import ClsData
from empresa import ClsEmpresa
from navigation import make_sidebar

st.set_page_config(page_title="DataPy: Clientes", layout="wide", page_icon=":vs:")

st.header("📘 Clientes Profit", help="Clientes registrado en el sistema Profit Plus")

make_sidebar()
company_selected = ClsEmpresa.empresa_seleccionada()


@st.cache_data
def clientes(empresa):
    return ClsData(empresa).clientes()


@st.cache_data
def ultimo_plan_facturado(empresa):
    if empresa == "BANTEL_A":
        return ClsData(empresa).ultimo_plan_facturado_implementacion_imprenta()
    return ClsData(empresa).ultimo_plan_facturado()


if st.button("Refrescar"):
    st.cache_data.clear()

tab1, tab2 = st.tabs(["👨‍🏫 Clientes", "🧾 Planes facturados"])

with tab1:
    st.markdown(
        """
    :blue[Información de los datos de clientes]."""
    )
    st.session_state.df_clientes = clientes(company_selected)
    st.dataframe(
        st.session_state.df_clientes, use_container_width=True, hide_index=True
    )
    st.session_state.df_clientes.to_excel(buf := BytesIO())
    st.download_button(
        "Download file",
        buf.getvalue(),
        f"Clientes {ClsEmpresa.modulo()}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab2:
    st.markdown(
        """
    :blue[Información de la última facturación]."""
    )
    st.df_ultimo_plan_facturado = ultimo_plan_facturado(company_selected)
    st.dataframe(
        st.df_ultimo_plan_facturado,
        column_config={
            "doc_num": st.column_config.TextColumn(
                "documento",
                width="small",
            ),
            "fec_emis": st.column_config.TextColumn(
                "fecha",
                width="small",
            ),
            "co_cli": st.column_config.TextColumn(
                "cliente",
                width="small",
            ),
            "cli_des": st.column_config.TextColumn(
                "razón social",
                width="large",
            ),
            "co_art": st.column_config.TextColumn(
                "artículo",
                width="medium",
            ),
            "art_des": st.column_config.TextColumn(
                "descripción artículo",
                width="large",
            ),
        },
        use_container_width=False,
        hide_index=True,
    )
