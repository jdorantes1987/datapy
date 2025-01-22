import os
from calendar import month_name
from datetime import date, datetime

import streamlit as st
from pandas import merge, read_excel
from streamlit import data_editor as de
from streamlit import session_state as ss

from consulta_data import ClsData
from empresa import ClsEmpresa
from facturacion_masiva import FacturacionMasiva
from navigation import make_sidebar

st.set_page_config(
    page_title="DataPy: Facturación masiva", layout="wide", page_icon=":vs:"
)
st.header(
    "📰 Facturación Masiva",
    help="Prepare el archivo excel correpondiente al módulo a trabajar para proceder con las facturación.",
)

make_sidebar()
anio_actual = date.today().year
mes_actual = str(month_name[date.today().month]).upper()
empresa_select = data_base = ClsEmpresa.empresa_seleccionada()
modulo = ClsEmpresa.modulo()

fecha = datetime(
    date.today().year,
    date.today().month,
    date.today().day,
    hour=00,
    minute=0,
    second=0,
    microsecond=0,
)
carpeta = os.getenv("PATH_FOLDER_DESARROLLO_PROFIT")
if ClsEmpresa.modulo() == "Derecha":
    ruta_archivo = f"{carpeta}Planes Facturacion Clientes Derecha.xlsx"
else:
    ruta_archivo = f"{carpeta}Planes Facturacion Clientes Izquierda.xlsx"


if "stage" not in st.session_state or "data_masiva" not in st.session_state:
    st.session_state.stage = 0


def set_stage(i):
    st.session_state.stage = i


if st.button("Refrescar"):
    st.cache_data.clear()
    set_stage(0)


@st.cache_data
def obtener_data(file):
    df = read_excel(file)
    df["facturar"] = df["facturar"].apply(lambda x: x == "SI")
    df = df[(df["razon_social"] != "No existe!") & (df["desc_art"] != "No existe!")]
    clientes = ClsData(empresa_select).clientes()[["co_cli", "cli_des"]]
    articulos = ClsData(empresa_select).articulos()[["co_art", "art_des"]]
    #  Se combina data de facturación con la tabla clientes
    merge_data = merge(df, clientes, how="left", left_on="id_client", right_on="co_cli")
    #  Se combina data de facturación con la tabla artículos
    merge_data2 = merge(
        merge_data, articulos, how="left", left_on="co_art", right_on="co_art"
    )
    merge_data2["buscar_articulo"] = (
        merge_data2["co_art"] + " | " + merge_data2["art_des"]
    )
    merge_data2["buscar_cliente"] = (
        merge_data2["co_cli"] + " | " + merge_data2["cli_des"]
    )
    merge_data2 = merge_data2[
        [
            "buscar_cliente",
            "co_cli",
            "cli_des",
            "enum",
            "razon_social",
            "descrip_encab_fact",
            "buscar_articulo",
            "co_art",
            "desc_art",
            "fecha_fact",
            "cantidad",
            "monto_base",
            "facturar",
            "comentario_l1",
            "comentario_l2",
            "comentario_l3",
        ]
    ]
    return merge_data2


@st.cache_data
def lista_articulos(empresa):
    return ClsData(empresa).articulos()


@st.cache_data
def lista_clientes(empresa):
    return ClsData(empresa).clientes()


if st.session_state.stage == 0:
    st.session_state.disabled = False
    ss.data_masiva = obtener_data(ruta_archivo)
    ss.data_masiva = ss.data_masiva[ss.data_masiva["facturar"]]
    ss.lista_articulos = lista_articulos(ClsEmpresa.empresa_seleccionada())
    ss.lista_clientes = lista_clientes(ClsEmpresa.empresa_seleccionada())
    ss.lista_articulos["articulos"] = (
        ss.lista_articulos["co_art"] + " | " + ss.lista_articulos["art_des"]
    )
    ss.lista_clientes["clientes"] = (
        ss.lista_clientes["co_cli"] + " | " + ss.lista_clientes["cli_des"]
    )
    set_stage(1)

edited_df = de(
    ss.data_masiva.reset_index(drop=True),
    column_config={
        "buscar_cliente": st.column_config.SelectboxColumn(
            "buscar cliente",
            help="Busque y seleccione un cliente.",
            width="large",
            options=ss.lista_clientes["clientes"],
            required=True,
        ),
        "enum": st.column_config.NumberColumn(
            "Correl",
            help="Coloque el correlativo para facturar por separado",
            default=0,
            min_value=1,
            max_value=100,
            width="small",
            step=1,
        ),
        "razon_social": None,
        "descrip_encab_fact": st.column_config.TextColumn(
            "Descripción de factura",
            default=f"FACTURACIÓN MES DE {mes_actual} DE {anio_actual}",
            help="Coloque la descripción del enzabezado de factura.",
        ),
        "co_art": None,
        "desc_art": None,
        "co_cli": None,
        "cli_des": None,
        "buscar_articulo": st.column_config.SelectboxColumn(
            "buscar artículo",
            help="Busque y seleccione un artículo.",
            width="large",
            options=ss.lista_articulos["articulos"],
            required=True,
        ),
        "fecha_fact": st.column_config.DatetimeColumn(
            "Fecha Emisión",
            help="Ingrese la fecha de emisión de la factura.",
            width="small",
            default=fecha,
            required=True,
        ),
        "monto_base": st.column_config.NumberColumn(
            "Monto USD",
            default=0,
            help="Coloque el monto de la base imponible sin IVA.",
            format="$ %.2f",
        ),
        "cantidad": st.column_config.NumberColumn(
            "cant",
            help="Coloque las unidades",
            default=1,
            min_value=1,
            max_value=5000,
            step=1,
        ),
        "facturar": st.column_config.CheckboxColumn(
            "facturar",
            help="Indíque si desea procesar esta factura.",
            default=True,
        ),
        "comentario_l1": "coment. lín 1",
        "comentario_l2": "coment. lín 2",
        "comentario_l3": "coment. lín 3",
    },
    #  Permite ajustar el ancho al tama帽o del contenedor
    use_container_width=True,
    disabled=["razon_social"],
    key="editor",
    hide_index=True,
    num_rows="dynamic",
)


def facturar(stage):
    ss.data_masiva = edited_df
    ss.data_masiva["co_cli"] = ss.data_masiva["buscar_cliente"].apply(
        lambda x: str.strip(x.split("|")[0])
    )
    ss.data_masiva["cli_des"] = ss.data_masiva["buscar_cliente"].apply(
        lambda x: str.strip(x.split("|")[1])
    )
    ss.data_masiva["co_art"] = ss.data_masiva["buscar_articulo"].apply(
        lambda x: str.strip(x.split("|")[0])
    )
    ss.data_masiva["desc_art"] = ss.data_masiva["buscar_articulo"].apply(
        lambda x: str.strip(x.split("|")[1])
    )
    ofact = FacturacionMasiva(
        data=ss.data_masiva,
        host=os.getenv("HOST_PRODUCCION_PROFIT"),
        data_base=empresa_select,
    )
    conv_a_usd = modulo == "Derecha"
    es_derecha = modulo != "Derecha"
    ofact.procesar_facturacion_masiva(
        modulo=modulo, a_bs=conv_a_usd, num_fact_format=es_derecha
    )
    set_stage(stage)


def data_validada():
    df = obtener_data(ruta_archivo)
    df = df[df["facturar"]]  # Solo los que se van a facturar
    df_group = (
        df.groupby(["co_cli", "descrip_encab_fact", "fecha_fact"])
        .agg({"monto_base": "sum"})
        .reset_index()
    )
    valores_duplicados = df_group[df_group.duplicated(subset=["co_cli"], keep=False)]
    if not valores_duplicados.empty:
        st.warning("Existe información inconsistente en la data.")
        st.write(valores_duplicados)
        st.stop()


data_validada()


if st.session_state.stage >= 1 and st.session_state.stage != 3:
    st.button("Facturar", on_click=facturar, args=[3])

if st.session_state.stage == 4:
    st.switch_page("pages/page2.py")


if st.session_state.stage >= 3:
    set_stage(0)
    st.success("Facturación procesada!")
    col1, col2 = st.columns([0.1, 0.1])
    with col1:
        col1.button("Ir a estadísticas de facturación", on_click=set_stage, args=[4])
    with col2:
        col2.button("Seguir en esta página?", on_click=set_stage, args=[1])
