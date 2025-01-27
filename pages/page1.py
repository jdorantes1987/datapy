import os
import time
from datetime import date, datetime
from io import BytesIO
from multiprocessing import Process, Queue

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st
from accesos.files_excel import datos_estadisticas_tasas
from banco_central.bcv_estadisticas_tasas import (
    actulizar_file_tasas,
    actulizar_file_tasas_manual,
)

from consulta_data import ClsData
from navigation import make_sidebar

st.set_page_config(page_title="DataPy: Inicio", layout="wide", page_icon=":vs:")

st.header("Información")


def archivo_xlsx_bcv_actualizado():
    path = "..\\bantel\\accesos\\excel\\tasas_BCV.xlsx"
    # obtiene la última fecha de modificación.
    modTimesinceEpoc = os.path.getmtime(path)
    hoy = date.today()
    fecha_modificacion = datetime.fromtimestamp(modTimesinceEpoc).date()
    archivo_actualizado = hoy == fecha_modificacion
    return archivo_actualizado


def update_file(tasks_to_accomplish, tasks_that_are_done):
    update_f = actulizar_file_tasas()
    if update_f:
        tasks_that_are_done.put(True)
    else:
        tasks_that_are_done.put(False)


def update_tasa_bcv():
    tasks_to_accomplish = Queue()
    tasks_that_are_done = Queue()
    p = Process(target=update_file, args=(tasks_to_accomplish, tasks_that_are_done))
    p.start()
    p.join()
    return tasks_that_are_done.get()


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def tasa_manual(fecha, valor):
    actulizar_file_tasas_manual(fecha=fecha, valor_tasa=valor)


if __name__ == "__main__":
    odata = ClsData(data_base=os.getenv("DB_NAME_IZQUIERDA_PROFIT"))
    new_cod = odata.generar_cod_cliente()
    date_t = datetime.strptime(str(odata.get_fecha_tasa_bcv_dia().date()), "%Y-%m-%d")
    table_scorecard = (
        """
    <div class="ui five small statistics">
      <div class="grey statistic">
        <div class="value">"""
        + str(odata.get_tasa_bcv_dia())
        + """
        </div>
        <div class="grey label">
          Tasa BCV
        </div>
      </div>
      <div class="grey statistic">
        <div class="value">"""
        + date_t.strftime("%d-%m-%Y")
        + """
        </div>
        <div class="grey label">
          Fecha valor tasa BCV
        </div>
      </div>
        <div class="grey statistic">
            <div class="value">"""
        + str(new_cod)
        + """
            </div>
            <div class="label">
            Nuevo código de cliente
            </div>
        </div>
      """
    )
    st.markdown(table_scorecard, unsafe_allow_html=True)
    local_css("style.css")
    make_sidebar()
    if not archivo_xlsx_bcv_actualizado():
        if update_tasa_bcv():
            st.info("Tasa BCV actualizada!")
            time.sleep(0.5)
        else:
            st.warning("No se pudo actualizar el archivo de histórico de tasas BCV")
            fecha = st.date_input("fecha de la tasa", disabled=True).strftime(
                "%Y%m%d"
            )  # Convierte la fecha a YYYYMMDD
            valor = st.number_input("Ingrese el valor de la tasa", format="%.5f")
            if st.button(
                "Deseas actualizar la tasa de forma manual?",
                on_click=tasa_manual,
                args=(fecha, valor),
            ):
                st.info("Tasa BCV actualizada!")
        st.rerun()


with st.expander("📊  Evolución tasa BCV"):
    historico_tasa = datos_estadisticas_tasas()
    df = historico_tasa[historico_tasa["año"] == date.today().year]
    fig = go.Figure()
    fig = fig.add_trace(
        go.Scatter(
            x=df["fecha"].dt.normalize(),
            y=df["venta_ask2"],
            mode="lines+markers",  # marcadores puntos
            marker=dict(  # configura tamaño y color del marcador
                size=3,
                color="rgba(255, 217, 102, .9)",
                line=dict(
                    color="rgba(191, 70, 0, .8)",  # configura color y tamaño de la linea
                    width=1,
                ),
            ),
            text="Tasa",
            name="Tasas",
        )
    )
    fig.update_traces(textposition="bottom right")
    fig.update_layout(
        title="Histórico de tasas BCV",
        plot_bgcolor="#f5fafa",
    )
    fig.update_xaxes(nticks=13)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Histórico de tasas"):
    cmap = plt.colormaps["YlOrRd"]
    st.dataframe(
        historico_tasa[
            ["cod_mon", "fecha", "compra_bid2", "venta_ask2", "var_tasas"]
        ].style.background_gradient(
            subset=["var_tasas"], cmap=cmap, low=0, vmin=-2, vmax=2, high=1, axis=0
        ),
        column_config={
            "cod_mon": st.column_config.TextColumn(
                "moneda",
            ),
            "compra_bid2": st.column_config.NumberColumn(
                "compra",
                format="%.4f",
            ),
            "venta_ask2": st.column_config.NumberColumn(
                "venta",
                format="%.4f",
            ),
            "var_tasas": st.column_config.NumberColumn(
                "variación",
                format="%.4f",
            ),
            "fecha": st.column_config.DateColumn("fecha", format="DD-MM-YYYY"),
        },
        use_container_width=False,
        hide_index=True,
    )
    historico_tasa.to_excel(buf := BytesIO())
    st.download_button(
        "Descargar histórico de tasas",
        buf.getvalue(),
        "Histórico de tasas BCV.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
