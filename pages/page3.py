import locale
from io import BytesIO
from pandas import merge
import streamlit as st
import matplotlib.pyplot as plt
from navigation import make_sidebar
from empresa import ClsEmpresa
from consulta_data import ClsData

st.set_page_config(page_title='DataPy: Cuentas por cobrar', layout='wide', page_icon=':vs:')

st.header('Resumen de Cuentas por Cobrar')

@st.cache_data
def cuentas_por_cobrar_agrupadas(empresa, anio, mes, usd, vendedor):
    return ClsData(empresa).cuentas_por_cobrar_agrupadas(anio=anio, mes=mes, usd=usd, vendedor=vendedor)

@st.cache_data
def cuentas_por_cobrar_det(empresa, anio, mes, usd, vendedor):
    return ClsData(empresa).cuentas_por_cobrar_det(anio=anio, mes=mes, usd=usd, vendedor=vendedor)

@st.cache_data
def cuentas_por_cobrar_pivot(empresa, anio, mes, usd, vendedor):
    return ClsData(empresa).cuentas_por_cobrar_pivot(anio=anio, mes=mes, usd=usd, vendedor=vendedor)

@st.cache_data
def data_facturacion(empresa, usd):
    df = ClsData(empresa).ventas_rsm(anio='all', 
                                     mes='all', 
                                     usd=usd)
    locale.setlocale(locale.LC_ALL, 'es_ES')
    df['mes_x'] = df['fec_reg'].dt.month_name(locale='es_ES').str[:3]
    locale.setlocale(locale.LC_ALL, '')
    return df

with st.spinner('consultando datos...'):  
    make_sidebar()

    select_emp = ClsEmpresa.empresa_seleccionada()
    conv_usd = ClsEmpresa.convert_usd()
    modulo = ClsEmpresa.modulo()

    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button("Refrescar"):
            st.cache_data.clear()

    col3, col4, col43 = st.columns(3, gap="small")

    with col3: 
        if select_emp == 'BANTEL_A':
            moneda = st.selectbox('Seleccione la moneda:', ['USD', 'Bs'], 0)
            conv_usd = moneda == 'USD'
            emp = ClsEmpresa(modulo, conv_usd).sel_emp

     #  Obtiene los datos de los ingresos para la empresa seleccionada.
    ingresos = data_facturacion(select_emp, usd=conv_usd)
    # Convierte las columnas año y mes a formato String
    ingresos[['anio', 'mes_x']] = ingresos[['anio', 'mes_x']].astype('str')
    #  Agrupa los ingresos por año y mes
    ingresos_agrupados = ingresos.groupby(['anio', 'mes_x',], 
                                        sort=False)\
                                        ['total_item'].sum().reset_index()
                                      
    datos_fact_x_cobrar = cuentas_por_cobrar_agrupadas(
                                                       empresa=select_emp, 
                                                       anio='all', 
                                                       mes='all', 
                                                       usd=conv_usd,
                                                       vendedor='all')
    # Almacena la lista de años 
    year_list = datos_fact_x_cobrar['anio'].unique().tolist()
    sellers_list = datos_fact_x_cobrar['ven_des'].unique().tolist()
    year_list.append('todos')
    sellers_list.append('todos')

    with col4:
        # Crea un selectbox que contenga todos los años 
        anio_select = st.selectbox('Elije un año:', year_list, index=int(len(year_list)-1))

    with col43:
        # Crea un selectbox que contenga todos los años 
        seller_select = st.selectbox('Elije un vendedor:', sellers_list, index=int(len(sellers_list)-1))

    filter_year = ((datos_fact_x_cobrar['anio'] == anio_select))
    if anio_select == 'todos':
        ctas_x_cobrar_por_anio = datos_fact_x_cobrar
    else:
        ctas_x_cobrar_por_anio = datos_fact_x_cobrar[filter_year]

    filter_seller = ((ctas_x_cobrar_por_anio['ven_des'] == seller_select))
    if seller_select == 'todos':
        ctas_x_cobrar_por_anio_y_seller = ctas_x_cobrar_por_anio
    else:
        ctas_x_cobrar_por_anio_y_seller = ctas_x_cobrar_por_anio[filter_seller]

    format_dict = {'Total facturacion': '{:,.2f}', 'Total por cobrar': '{:,.2f}', 'Porcentaje': '{:.2%}'} # ejemplo {'sum':'${0:,.0f}', 'date': '{:%m-%Y}', 'pct_of_total': '{:.2%}'}
    col1, col2 = st.columns(2)

    with col1:
        fact_x_cobrar_group_anio_y_mes = ctas_x_cobrar_por_anio_y_seller.groupby(['anio', 'mes'], 
                                                                                 sort=False) \
                                                                                 [['saldo_total_doc']].sum().reset_index()
                                                                                 
        fact_x_cobrar_group_anio_y_mes[['anio', 'mes']] = fact_x_cobrar_group_anio_y_mes[['anio', 'mes']].astype('str')
                                                                                 
        ctas_x_cobrar_con_ingresos = merge(fact_x_cobrar_group_anio_y_mes, ingresos_agrupados,
                                                how='left', 
                                                left_on=['anio', 'mes'], 
                                                right_on=['anio', 'mes_x'])[['anio', 'mes', 'total_item', 'saldo_total_doc']]
        
        ctas_x_cobrar_con_ingresos['Porcentaje'] = ctas_x_cobrar_con_ingresos.apply(lambda x: 
                                                                                        x['saldo_total_doc'] / x['total_item'], 
                                                                                    axis=1)
        
        ctas_x_cobrar_con_ingresos.rename(columns={'total_item': 'Total facturacion', 'saldo_total_doc': 'Total por cobrar'}, 
                                          inplace=True)
        
        cmap = plt.colormaps['BuGn']
        st.write("""#### Por mes """)
        st.dataframe(ctas_x_cobrar_con_ingresos.style
        .format(format_dict)
        .background_gradient(
                             subset=['Total facturacion', 'Total por cobrar', 'Porcentaje'], 
                             cmap=cmap), 
                             hide_index=True  #  oculta el indice del dataframe
        )

    with col2:
        anio_select = 'all' if anio_select == 'todos' else anio_select
        seller_select = 'all' if seller_select == 'todos' else seller_select
        #  total ingresos incluyendo iva + igtf 
        total_ing = ctas_x_cobrar_con_ingresos['Total facturacion'].sum()
        # total por cobrar 
        total_x_cob = ctas_x_cobrar_con_ingresos['Total por cobrar'].sum()

        porcentaje = - (total_x_cob / total_ing) * 100
        col2.metric(
            label ='Total Facturación', 
            value='{:,.2f}'.format(total_ing)
        )

        col2.metric(
            label='Total por cobrar',
            value='{:,.2f}'.format(total_x_cob),
            delta=str('{:,.2f}'.format(porcentaje) + '%'),
            delta_color='normal',
        )    

    with st.expander("Resumen de cuentas por cobrar clientes"):
        datos = cuentas_por_cobrar_pivot(
                                         empresa=select_emp, 
                                         anio=anio_select, 
                                         mes= 'all', 
                                         usd=conv_usd,
                                         vendedor=seller_select
        )
        saldo_facturas = datos.sort_values(
                                           by=['All'], 
                                           ascending=False)
        cmap = plt.colormaps['BuGn']
        st.dataframe(
                     saldo_facturas.style
                        .format('{:,.2f}')
                        .background_gradient(
                                            subset=['All'], 
                                            cmap=cmap),
                    #  Permite ajustar el ancho al tamaño del contenedor    
                    use_container_width=True
        )

        locale.setlocale(locale.LC_ALL, '')
        saldo_facturas.to_excel(buf := BytesIO())
        st.download_button(
            'Download file',
            buf.getvalue(),
            f'Cobranza {ClsEmpresa.modulo()}.xlsx',
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )