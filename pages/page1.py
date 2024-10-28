import os
import time
import altair as alt 
import streamlit as st
from multiprocessing import Process, Queue
from seaborn import heatmap, set_style, lineplot
from matplotlib.pyplot import subplots, title, show, tight_layout, xticks
from datetime import datetime, date
from consulta_data import ClsData
from navigation import make_sidebar
from banco_central.bcv_estadisticas_tasas import actulizar_file_tasas
from accesos.files_excel import datos_estadisticas_tasas

st.set_page_config(page_title='DataPy: Inicio', 
                   layout='wide', 
                   page_icon=':vs:')

st.header("Información")

def archivo_xlsx_bcv_actualizado():
    path = '..\\bantel\\accesos\\excel\\tasas_BCV.xlsx'
    # obtiene la última fecha de modificación.
    modTimesinceEpoc = os.path.getmtime(path)
    hoy = date.today()
    fecha_modificacion = datetime.fromtimestamp(modTimesinceEpoc).date()
    archivo_actualizado = hoy == fecha_modificacion
    return archivo_actualizado

def update_file(tasks_to_accomplish, tasks_that_are_done):
      task = tasks_to_accomplish.get_nowait()
      actulizar_file_tasas()
      tasks_that_are_done.put(task)
      time.sleep(.5)

def actualizar_tasa_bcv():
    tasks_to_accomplish = Queue()
    tasks_that_are_done = Queue()
    tasks_to_accomplish.put("Tasa de cambio actualizada!")
    p = Process(target=update_file,args=(tasks_to_accomplish, tasks_that_are_done))
    p.start()
    p.join()
    st.info(tasks_that_are_done.get())
    time.sleep(1)
    st.rerun()
          

def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


if __name__ == '__main__':
    odata = ClsData(data_base=os.getenv("DB_NAME_IZQUIERDA_PROFIT"))
    new_cod = odata.generar_cod_cliente()
    date = odata.get_fecha_tasa_bcv_dia().date()

    table_scorecard = """
    <div class="ui five small statistics">
      <div class="grey statistic">
        <div class="value">"""+str(odata.get_tasa_bcv_dia())+"""
        </div>
        <div class="grey label">
          Tasa BCV
        </div>
      </div>
      <div class="grey statistic">
        <div class="value">""" +str(date)+  """
        </div>
        <div class="grey label">
          Fecha valor tasa BCV
        </div>
      </div>
        <div class="grey statistic">
            <div class="value">"""+str(new_cod)+"""
            </div>
            <div class="label">
            Nuevo código de cliente
            </div>
        </div>
      """
    st.markdown(table_scorecard, unsafe_allow_html=True)
    local_css("style.css")
    make_sidebar()
    if not archivo_xlsx_bcv_actualizado():
       actualizar_tasa_bcv()

with st.expander("📊  Evolución tasa BCV"):
     var_tasa = datos_estadisticas_tasas()
     df = var_tasa[var_tasa['año'] == 2024]
     chart = alt.Chart(df, title='Histórico').mark_line().encode(
      x='fecha', y=alt.Y('venta_ask2', scale=alt.Scale(domain=[df['venta_ask2'].min() - 1,df['venta_ask2'].max() + 1])), strokeDash='cod_mon'
        ).properties(width=650, height=350)     
     st.altair_chart(chart, use_container_width=True)
     


