import locale

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from consulta_data import ClsData
from empresa import ClsEmpresa
from navigation import make_sidebar

st.set_page_config(page_title="DataPy: Ingresos", layout="wide", page_icon=":vs:")

st.header("Ingresos por año")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")


@st.cache_data
def data_documentos(empresa, usd):
    df = ClsData(empresa).ventas_rsm(anio="all", mes="all", usd=usd)
    locale.setlocale(locale.LC_ALL, "es_ES")
    df["mes_x"] = df["fec_reg"].dt.month_name(locale="es_ES").str[:3]
    locale.setlocale(locale.LC_ALL, "")
    return df


def total_ingresos_anio_anterior(empresa, anio, vendedor, usd):
    return ClsData(empresa).ventas_dicc_x_vendedor(
        anio=anio, vendedor=vendedor, usd=usd
    )


with st.spinner("consultando datos..."):
    make_sidebar()
    select_emp = ClsEmpresa.empresa_seleccionada()
    modulo = ClsEmpresa.modulo()
    conv_usd = ClsEmpresa.convert_usd()
    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("Refrescar"):
            st.cache_data.clear()

    col3, col4, col5 = st.columns(3, gap="small")

    with col3:
        if select_emp == "BANTEL_A":
            moneda = st.selectbox("Seleccione la moneda:", ["USD", "Bs"], 0)
            conv_usd = True if moneda == "USD" else False
            emp = ClsEmpresa(modulo, conv_usd).sel_emp

    #  Obtiene los datos de los ingresos para la empresa seleccionada.
    datos = data_documentos(select_emp, usd=conv_usd)
    # Convierte las columnas año y mes a formato String
    datos[["anio", "mes_x"]] = datos[["anio", "mes_x"]].astype("str")
    #  Agrupa los ingresos por año y mes
    ingresos_por_anio = (
        datos.groupby(["anio", "mes_x", "co_ven", "ven_des"], sort=False)[
            "monto_base_item"
        ]
        .sum()
        .reset_index()
    )
    # Almacena la lista de años
    year_list = ingresos_por_anio["anio"].unique().tolist()

    with col4:
        #  Crea un selectbox que contenga todos los años.
        anio_select = st.selectbox("Elije un año:", year_list, int(len(year_list) - 1))
        sellers_anio = ingresos_por_anio[
            ingresos_por_anio["anio"] == anio_select
        ].copy()

    with col5:
        sellers_anio["buscador_vendedor"] = (
            sellers_anio["co_ven"] + " | " + sellers_anio["ven_des"]
        )
        list_sellers = sellers_anio["buscador_vendedor"].unique().tolist()
        list_sellers = sorted(list_sellers)
        list_sellers.append("Todos")
        #  Crea un selectbox que contenga todos los vendedores.
        seller_select = str.strip(
            st.selectbox(
                "Elije un vendedor:", list_sellers, int(len(list_sellers) - 1)
            ).split("|")[0]
        )

    #  Variable que obtiene el año más bajo o primer año
    anio_min = int(min(year_list))
    # Condición para filtrar el año y vendedor seleccionado.
    if seller_select == "Todos":
        filter_year = ingresos_por_anio["anio"] == anio_select
    else:
        filter_year = (ingresos_por_anio["anio"] == anio_select) & (
            ingresos_por_anio["co_ven"] == seller_select
        )
    #  Se establece un diccionario con formato float
    # para para aplicarlo a las columnas con montos
    format_dict = {
        "monto_base_item": "{:,.2f}",
        "porcentaje": "{:.2%}",
    }  # ejemplo {'sum':'${0:,.0f}', 'date': '{:%m-%Y}', 'pct_of_total': '{:.2%}'}
    # Establece dos colunnas contenedoras del dataframe de ingresos
    # por año y otra para el monto total de ingresos por año.
    col6, col7, col8 = st.columns(3, gap="small")
    df_ing = ingresos_por_anio[filter_year]
    with col6:
        st.write("""#### Por mes """)
        #  Agrupa los ingresos según el año seleccionado
        df_ing_year = (
            df_ing.groupby(["mes_x"], sort=False)["monto_base_item"].sum().reset_index()
        )
        df_ing_year["porcentaje"] = df_ing_year["monto_base_item"].apply(
            lambda x: x / df_ing_year["monto_base_item"].sum()
        )
        cmap = plt.colormaps["YlGn"]
        st.dataframe(
            df_ing_year.style.format(format_dict)
            # hide_index=True oculta el indice del dataframe
            .background_gradient(subset=["monto_base_item"], cmap=cmap),
            hide_index=True,
        )

    #  Monto total de los ingresos del año seleccionado
    total_ing = df_ing_year["monto_base_item"].sum()
    anio_ant = int(anio_select) - 1  # Obtiene el año anterior al seleccionado

    #  Si el año seleccionado es mayor al año minimo coloca el año anterior
    if int(anio_select) > anio_min:
        # monto total de los ingresos del año anterior al seleccionado
        total_ing_anio_ant = total_ingresos_anio_anterior(
            select_emp, anio=anio_ant, vendedor=seller_select, usd=conv_usd
        )
    else:
        total_ing_anio_ant = 0.00

    neto_anio_ant_menos_anio_act = total_ing - total_ing_anio_ant
    with col7:
        st.write("""#### Ingresos de los últimos 6 meses """)
        #  Crea un gráfico de lineas con los ultimos 3 meses de ingresos
        ingresos_ultimos_meses = (
            ingresos_por_anio.groupby(["anio", "mes_x"], sort=False)["monto_base_item"]
            .sum()
            .reset_index()
            .tail(6)
        )
        ingresos_ultimos_meses["anio_mes"] = (
            ingresos_ultimos_meses["anio"] + " " + ingresos_ultimos_meses["mes_x"]
        )
        fig_ium = go.Figure()
        fig_ium = fig_ium.add_trace(
            go.Scatter(
                x=ingresos_ultimos_meses["anio_mes"],
                y=ingresos_ultimos_meses["monto_base_item"],
                mode="lines+markers+text",  # marcadores puntos
                marker=dict(
                    color="#5D69B1", size=6
                ),  # configura tamaño y color del marcador
                line=dict(
                    color="#52BCA3", width=1, dash="dash"
                ),  # configura color y tamaño de la linea
                text=round(
                    ingresos_ultimos_meses["monto_base_item"].apply("${:,.2f}".format),
                    2,
                ),  # texto que se muestra al pasar el mouse
                textposition="top center",  # posición del texto
                name="Ingresos",
            )
        )
        st.plotly_chart(fig_ium, use_container_width=True)

    #  Crea la información que va en la columna dos del primer contenedor
    col8.metric(
        label="Total base imponible",
        value=str("{:,.2f}".format(total_ing)),
        delta=str("{:,.2f}".format(neto_anio_ant_menos_anio_act)),
    )

    with st.expander("Vendedores"):
        col11, col12 = st.columns(2, gap="small")
        with col11:
            df_ing_x_vend = (
                df_ing.groupby(["ven_des"], sort=True)["monto_base_item"]
                .sum()
                .reset_index()
            )
            df_ing_x_vend_sort = df_ing_x_vend.sort_values(
                by=["monto_base_item"], ascending=[False]
            )
            df_ing_x_vend_sort["porcentaje"] = df_ing_x_vend_sort[
                "monto_base_item"
            ].apply(lambda x: x / df_ing_x_vend_sort["monto_base_item"].sum())
            cmap = plt.colormaps["YlGn"]
            format_dict2 = {
                "monto_base_item": "{:,.2f}",
                "porcentaje": "{:.2%}",
            }  # ejemplo {'sum':'${0:,.0f}', 'date': '{:%m-%Y}', 'pct_of_total': '{:.2%}'}
            st.dataframe(
                df_ing_x_vend_sort.style.format(format_dict2).background_gradient(
                    subset=["monto_base_item"], cmap=cmap
                ),
                hide_index=True,
            )

        with col12:
            df_ing_group = (
                df_ing.groupby(["ven_des", "mes_x"], sort=False)["monto_base_item"]
                .sum()
                .reset_index()
            )
            vendedores = df_ing_group["ven_des"].unique().tolist()
            dfs = {
                vendedor: df_ing_group[df_ing_group["ven_des"] == vendedor]
                for vendedor in vendedores
            }  # Crea un diccionario para cada vendedor con sus ingresos por mes
            fig = go.Figure()
            for vendedor, df_ing_group in dfs.items():
                fig = fig.add_trace(
                    go.Scatter(
                        x=df_ing_group["mes_x"],
                        y=df_ing_group["monto_base_item"],
                        text="Monto",
                        name=vendedor,
                    )
                )
            fig.update_traces(textposition="bottom right")
            fig.update_layout(
                title="Ingresos por Vendedores",
                plot_bgcolor="#E6F1F6",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.write("🔍 Por cliente")

    if seller_select == "Todos":
        datos_ingresos_por_client = (
            datos[datos["anio"] == anio_select]
            .groupby(["co_cli", "cli_des"], sort=False)["monto_base_item"]
            .sum()
            .reset_index()
        )
    else:
        datos_ingresos_por_client = (
            datos[(datos["anio"] == anio_select) & (datos["co_ven"] == seller_select)]
            .groupby(["co_cli", "cli_des"], sort=False)["monto_base_item"]
            .sum()
            .reset_index()
        )

    datos_ingresos_por_client["porcentaje"] = datos_ingresos_por_client[
        "monto_base_item"
    ].apply(lambda x: x / datos_ingresos_por_client["monto_base_item"].sum())
    #  Se debe ordenar el df para poder conbinar
    ingresos_por_client = datos_ingresos_por_client.sort_values(
        by=["monto_base_item"], ascending=[False]
    )
    st.dataframe(
        ingresos_por_client.style.format(format_dict).background_gradient(
            subset=["monto_base_item"], cmap=cmap
        ),
        hide_index=True,
    )

    st.write("""#### Por cliente y mes""")
    #  Almacena la lista de meses y clientes
    month_list = df_ing_year["mes_x"].unique().tolist()
    clientes_list = ingresos_por_client["cli_des"].unique().tolist()
    #  Crear dos multiselect que contengan los meses y clientes únicos.
    client_list_select = st.multiselect("Elije uno o varios clientes:", clientes_list)
    mes_list_select = st.multiselect("Elije uno o varios meses:", month_list)

    if seller_select == "Todos":
        ingresos_por_client = (
            datos[datos["anio"] == anio_select]
            .groupby(["mes_x", "co_cli", "cli_des"], sort=False)["monto_base_item"]
            .sum()
            .reset_index()
        )
    else:
        ingresos_por_client = (
            datos[(datos["anio"] == anio_select) & (datos["co_ven"] == seller_select)]
            .groupby(["mes_x", "co_cli", "cli_des"], sort=False)["monto_base_item"]
            .sum()
            .reset_index()
        )

    filter_mes = ingresos_por_client["mes_x"].isin(mes_list_select)
    filter_cliente = ingresos_por_client["cli_des"].isin(client_list_select)

    if len(mes_list_select) != 0:
        ingresos_por_client_filter = ingresos_por_client[
            (filter_mes) & (filter_cliente)
        ][["mes_x", "co_cli", "cli_des", "monto_base_item"]]
    else:
        ingresos_por_client_filter = ingresos_por_client[filter_cliente][
            ["mes_x", "co_cli", "cli_des", "monto_base_item"]
        ]

    st.dataframe(
        ingresos_por_client_filter.style.format(format_dict).background_gradient(
            subset=["monto_base_item"], cmap=cmap
        ),
        hide_index=True,
        width=1200,
    )
