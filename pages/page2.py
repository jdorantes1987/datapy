import locale
from datetime import date
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from consulta_data import ClsData
from empresa import ClsEmpresa
from navigation import make_sidebar

st.set_page_config(page_title="DataPy: Ingresos", layout="wide", page_icon=":vs:")

st.title("Ingresos")
anio_actual = date.today().year


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")

# Inicialización de estado
for k, v in {
    "anio_select_ventas": date.today().year,
    "ingresos_anios_anteriores": 0.00,
    "documentos": None,
    "stage2": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def set_stage(i):
    st.session_state.stage2 = i


@st.cache_data(show_spinner="Cargando datos de ventas...")
def data_documentos(empresa, usd):
    df = ClsData(empresa).ventas_rsm(anio="all", mes="all", usd=usd)
    # Solo cambia el locale si es necesario
    try:
        locale.setlocale(locale.LC_TIME, "es_ES")
        df["mes_x"] = df["fec_reg"].dt.month_name(locale="es_ES").str[:3]
    except locale.Error:
        df["mes_x"] = df["fec_reg"].dt.month_name().str[:3]
    finally:
        locale.setlocale(locale.LC_TIME, "")
    return df


def total_ingresos_anio_anterior(empresa, anio, vendedor, usd):
    return ClsData(empresa).ventas_dicc_x_vendedor(
        anio=anio, vendedor=vendedor, usd=usd
    )


make_sidebar()
select_emp = ClsEmpresa.empresa_seleccionada()
modulo = ClsEmpresa.modulo()
conv_usd = ClsEmpresa.convert_usd()

col1, col2 = st.columns(2, gap="small")
with col1:
    if st.button("Refrescar"):
        st.cache_data.clear()
        set_stage(0)
        st.rerun()

col3, col4, col5 = st.columns(3, gap="small")
with col3:
    if select_emp == "BANTEL_A":
        moneda = st.selectbox(
            "Seleccione la moneda:", ["USD", "Bs"], 0, on_change=set_stage, args=(0,)
        )
        conv_usd = moneda == "USD"
        emp = ClsEmpresa(modulo, conv_usd).sel_emp

if st.session_state.stage2 == 0:
    st.session_state.documentos = data_documentos(select_emp, usd=conv_usd)
    set_stage(1)

datos = st.session_state.documentos
datos[["anio", "mes_x"]] = datos[["anio", "mes_x"]].astype(str)

# Agrupación principal
ingresos_por_anio = (
    datos.groupby(["anio", "mes_x", "co_ven", "ven_des"], sort=False)["monto_base_item"]
    .sum()
    .reset_index()
)

with col4:
    year_list = ingresos_por_anio["anio"].unique().tolist()
    anio = st.pills(
        "Periodos:",
        sorted(year_list, reverse=True),
        default=str(anio_actual),
        selection_mode="single",
    )
    st.session_state["anio_select_ventas"] = anio
    sellers_anio = ingresos_por_anio[
        ingresos_por_anio["anio"] == st.session_state["anio_select_ventas"]
    ].copy()

with col5:
    sellers_anio["buscador_vendedor"] = (
        sellers_anio["co_ven"] + " | " + sellers_anio["ven_des"]
    )
    list_sellers = sorted(sellers_anio["buscador_vendedor"].unique().tolist())
    list_sellers.append("Todos")
    seller = str.strip(
        st.selectbox(
            "Elije un vendedor:", list_sellers, int(len(list_sellers) - 1)
        ).split("|")[0]
    )

primer_anio = int(min(year_list))
if seller == "Todos":
    filter_year = ingresos_por_anio["anio"] == anio
else:
    filter_year = (ingresos_por_anio["anio"] == anio) & (
        ingresos_por_anio["co_ven"] == seller
    )

format_dict = {
    "monto_base_item": "{:,.2f}",
    "porcentaje": "{:.2%}",
}

col6, col7, col8 = st.columns(3, gap="small")
df_ing = ingresos_por_anio[filter_year]

with col6:
    st.write("#### Por mes")
    df_ing_year = (
        df_ing.groupby(["mes_x"], sort=False)["monto_base_item"].sum().reset_index()
    )
    total_mes = df_ing_year["monto_base_item"].sum()
    if total_mes > 0:
        df_ing_year["porcentaje"] = df_ing_year["monto_base_item"] / total_mes
    else:
        df_ing_year["porcentaje"] = 0
    cmap = plt.colormaps["YlGn"]
    st.dataframe(
        df_ing_year.style.format(format_dict).background_gradient(
            subset=["monto_base_item"], cmap=cmap
        ),
        hide_index=True,
    )

total_ing = df_ing_year["monto_base_item"].sum()
anio_ant = int(anio) - 1

if int(anio) > primer_anio:
    ingresos_anio_anterior = total_ingresos_anio_anterior(
        select_emp, anio=anio_ant, vendedor=seller, usd=conv_usd
    )
else:
    ingresos_anio_anterior = 0.00

neto_anio_ant_menos_anio_act = total_ing - ingresos_anio_anterior

with col7:
    st.write("##### Gráfica ingresos de los últimos 6 meses")
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
    fig_ium.update_layout(
        height=250,
        width=500,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="#f5fafa",
    )
    fig_ium.add_trace(
        go.Scatter(
            x=ingresos_ultimos_meses["anio_mes"],
            y=ingresos_ultimos_meses["monto_base_item"],
            mode="lines+markers+text",
            marker=dict(color="#5D69B1", size=6),
            line=dict(color="#52BCA3", width=1, dash="solid"),
            text=ingresos_ultimos_meses["monto_base_item"].apply("${:,.2f}".format),
            textfont=dict(size=12, color="#000000", family="monospace"),
            textposition="top center",
            name="Ingresos",
        )
    )
    minimo = ingresos_ultimos_meses["monto_base_item"].min()
    maximo = ingresos_ultimos_meses["monto_base_item"].max()
    fig_ium.update_yaxes(
        range=[
            round(minimo - (minimo / 7), 2),
            round(maximo + (maximo / 7), 2),
        ],
    )
    fig_ium.update_xaxes(nticks=20)
    st.plotly_chart(fig_ium, use_container_width=True)

col8.metric(
    label="Total base imponible",
    value=f"{total_ing:,.2f}",
    delta=f"{neto_anio_ant_menos_anio_act:,.2f}",
)

st.write("")
st.write("")

col11, col12 = st.columns(2, gap="small")
with col11:
    st.write("#### Ingresos por vendedor")
    df_ing_x_vend = (
        df_ing.groupby(["ven_des"], sort=True)["monto_base_item"].sum().reset_index()
    )
    df_ing_x_vend_sort = df_ing_x_vend.sort_values(
        by=["monto_base_item"], ascending=[False]
    )
    total_vend = df_ing_x_vend_sort["monto_base_item"].sum()
    if total_vend > 0:
        df_ing_x_vend_sort["porcentaje"] = (
            df_ing_x_vend_sort["monto_base_item"] / total_vend
        )
    else:
        df_ing_x_vend_sort["porcentaje"] = 0
    cmap = plt.colormaps["YlGn"]
    format_dict2 = {
        "monto_base_item": "{:,.2f}",
        "porcentaje": "{:.2%}",
    }
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
    st.write("##### Gráfica de ingresos por vendedor y mes")
    fig = go.Figure()
    fig.update_layout(
        height=250,
        width=500,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="#f5fafa",
    )
    for vendedor in vendedores:
        df_v = df_ing_group[df_ing_group["ven_des"] == vendedor]
        fig.add_trace(
            go.Scatter(
                x=df_v["mes_x"],
                y=df_v["monto_base_item"],
                text="Monto",
                name=vendedor,
            )
        )
    fig.update_traces(textposition="bottom right")
    st.plotly_chart(fig, use_container_width=True)

st.write("#### Ingresos por cliente")

if seller == "Todos":
    datos_ingresos_por_client = (
        datos[datos["anio"] == anio]
        .groupby(["co_cli", "cli_des"], sort=False)["monto_base_item"]
        .sum()
        .reset_index()
    )
else:
    datos_ingresos_por_client = (
        datos[(datos["anio"] == anio) & (datos["co_ven"] == seller)]
        .groupby(["co_cli", "cli_des"], sort=False)["monto_base_item"]
        .sum()
        .reset_index()
    )

total_cliente = datos_ingresos_por_client["monto_base_item"].sum()
if total_cliente > 0:
    datos_ingresos_por_client["porcentaje"] = (
        datos_ingresos_por_client["monto_base_item"] / total_cliente
    )
else:
    datos_ingresos_por_client["porcentaje"] = 0

ingresos_por_client = datos_ingresos_por_client.sort_values(
    by=["monto_base_item"], ascending=[False]
)
st.dataframe(
    ingresos_por_client.style.format(format_dict).background_gradient(
        subset=["monto_base_item"], cmap=cmap
    ),
    hide_index=True,
)

st.write("##### Por cliente y mes")
month_list = df_ing_year["mes_x"].unique().tolist()
clientes_list = ingresos_por_client["cli_des"].unique().tolist()
client_list_select = st.multiselect("Elije uno o varios clientes:", clientes_list)
mes_list_select = st.multiselect("Elije uno o varios meses:", month_list)

if seller == "Todos":
    ingresos_por_client = (
        datos[datos["anio"] == anio]
        .groupby(["mes_x", "co_cli", "cli_des"], sort=False)["monto_base_item"]
        .sum()
        .reset_index()
    )
else:
    ingresos_por_client = (
        datos[(datos["anio"] == anio) & (datos["co_ven"] == seller)]
        .groupby(["mes_x", "co_cli", "cli_des"], sort=False)["monto_base_item"]
        .sum()
        .reset_index()
    )

filter_mes = ingresos_por_client["mes_x"].isin(mes_list_select)
filter_cliente = ingresos_por_client["cli_des"].isin(client_list_select)

# Optimización: solo selecciona columnas si existen y hay datos
cols = [
    col
    for col in ["mes_x", "co_cli", "cli_des", "monto_base_item"]
    if col in ingresos_por_client.columns
]
if len(mes_list_select) != 0:
    ingresos_por_client_filter = ingresos_por_client[filter_mes & filter_cliente][cols]
else:
    ingresos_por_client_filter = ingresos_por_client[filter_cliente][cols]

if ingresos_por_client_filter.empty:
    st.info("No hay datos para los filtros seleccionados.")
else:
    st.dataframe(
        ingresos_por_client_filter.style.format(format_dict).background_gradient(
            subset=["monto_base_item"], cmap=cmap
        ),
        hide_index=True,
        width=1200,
    )
