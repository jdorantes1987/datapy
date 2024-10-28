import sys
import locale
from datetime import datetime
from pandas import to_datetime
from pandas import merge
from pandas import DataFrame
from pandas import factorize
# La ruta SYS es una lista de directorios que Python interpreta para buscar cuando se inicia
sys.path.append('..\\bantel') # Agrega el directorio Bantel a la ruta SYS
from varios.utilidades import date_today
from accesos.conexion import ConexionBD
from accesos.transacciones import GestorTransacciones
from accesos.datos import get_monto_tasa_bcv_del_dia
from accesos.datos import get_fecha_tasa_bcv_del_dia
from accesos.datos_profit import datos_profit
from gestion_user.usuarios import ClsUsuarios


locale.setlocale(locale.LC_ALL, 'es_ES')

class FacturacionMasiva:

    def __init__(self, data, host, data_base):
            self.data = data
            self.data_base = data_base
            self.odata = datos_profit(host, data_base, 'TBANTEL_C')
            self.conexion = ConexionBD(base_de_datos=data_base, host=host) #  Crea un objeto conexión
            self.conexion.conectar()  # inicia la conexión
            self.gestor_trasacc = GestorTransacciones(self.conexion)
            self.gestor_trasacc.iniciar_transaccion()
            self.cursor = self.gestor_trasacc.get_cursor()
            self.data_facturacion = None
            
    #  1) ESTABLE LOS DATOS PARA LA FACTURACIÓN MASIVA            
    #  ------------------------------------------------------------------------------------
    def set_data_facturacion(self, data, **kwargs) -> DataFrame:
        # Establece como String-str la columna nro_doc
        modulo = kwargs.get('modulo', 'Derecha')
        a_bolivares = kwargs.get('conv_a_bs', False)
        doc_emit = kwargs.get('num_doc')
        doc_ctrol_emit = kwargs.get('num_doc_ctrol')
        format_fact = kwargs.get('num_fact_format')
        # primero se filtran los documentos que se van a facturar
        data_ = data[data['facturar']].copy()
        data_['nro_doc'] = str(doc_emit).zfill(6) if format_fact == True else int(doc_emit)
        # Rellena una cadena numérica con ceros a la izquierda
        data_['nro_control'] = str(doc_ctrol_emit).zfill(6) if format_fact == True else int(str(doc_ctrol_emit).replace('00-', ''))
        data_['indice_fact'] = data_.apply(lambda x: x['co_cli'] + str(x['enum']), axis=1)
        # asigna una numeracion a cada cliente que luego se usará para asignar el nuevo número de factura
        # factorize sirve para crear correlativo por grupos
        data_['grupo'] = factorize(data_['indice_fact'])[0]
        # genera el nuevo número de factura, se le suma 1 porque el correlativo del grupo comienza en cero
        # tambien evalua si se le aplicará formato al correlativo del documento 
        data_['nro_doc'] = data_.apply(
            lambda x: str(int(x['nro_doc']) + int(x['grupo']) + 1).zfill(6) if format_fact == True 
                                                                            else (int(x['nro_doc']) + int(x['grupo']) + 1), 
                                                                            axis=1) 
        data_['nro_control'] = data_.apply(
            lambda x: str(int(x['nro_control']) + int(x['grupo']) + 1).zfill(6) if format_fact == True 
                                                                                else '00-0' + str(int(x['nro_control']) + int(x['grupo']) + 1), 
                                                                                axis=1) 
        tasa = get_monto_tasa_bcv_del_dia()
        #  Multiplica la 'cantidad' de artículos por el 'monto_base' para obtener el neto por artículo
        #  despues aplica la tasa de cambio correpondiente
        data_['monto_base'] = data_.apply(
            lambda x: round((x['monto_base'] * x['cantidad']) * tasa if a_bolivares == True
                            else x['monto_base'] * x['cantidad'], ndigits=2), axis=1)
        #  se debe combinar el cod. de artículos con la tabla Artículos
        self.data_facturacion = data_


    def data_encab_facturacion_masiva(self, modulo, a_bs, num_doc, num_doc_ctrol, num_fact_format) -> DataFrame:
        #  Agrupa el monto neto por articulo
        data_f = self.data_facturacion.groupby(['co_cli', 'nro_doc', 'nro_control', 'fecha_fact', 'descrip_encab_fact'])[
            'monto_base'].sum().reset_index()
        return data_f

    #  2) EJECUTA LA INSTRUCCIÓN INDIVIDUAL PARA INSERTAR CADA ENCABEZADO DE FACTURA, PROXIMAMENTE SE MANEJARÁN TRANSACCIONES
    #  ------------------------------------------------------------------------------------
    def facturacion_masiva(self, modulo, a_bs, num_doc, num_doc_ctrol, num_fact_format):
        data = self.data
        self.set_data_facturacion(
                                data=data,
                                modulo=modulo, 
                                conv_a_bs=a_bs, 
                                num_doc=num_doc, 
                                num_doc_ctrol=num_doc_ctrol, 
                                num_fact_format=num_fact_format)
        data = self.data_encab_facturacion_masiva(modulo, a_bs, num_doc, num_doc_ctrol, num_fact_format)
        #  Es necesario agrupar los encabezados de factura para totalizar la Base Imponible y el IVA
        #  Estar atento a esta agrupación ya que si el mismo documento tiene diferentes concepto de factura arroja error.
        data_agrupada = data.groupby(['co_cli', 'nro_doc', 'nro_control', 'fecha_fact', 'descrip_encab_fact'])['monto_base'].sum().reset_index()
        date_current = date_today()  # Fecha actual
        tasa_camb = get_monto_tasa_bcv_del_dia()
        tasa_fecha =  format(get_fecha_tasa_bcv_del_dia(), '%d-%m-%Y')  # fecha sin hora, minutos y segundos
        data_iva = self.determinar_impuesto_por_factura(modulo, True, a_bs, num_doc, num_doc_ctrol, num_fact_format)
        data_con_iva = merge(data_agrupada, data_iva, how='left', left_on='nro_doc', right_on='nro_doc')
        data_con_iva['total'] = data_con_iva.apply(lambda x: x['monto_base'] + x['iva'], axis=1)
        suc=''
        if modulo == 'Derecha':
                comentario = f'Tasa BCV {tasa_camb} Fecha {tasa_fecha}'
                suc='01'
        else: 
            comentario = ""
        
        campo5 = to_datetime(date_current).month_name(locale='es_ES')
        campo7 = to_datetime(date_current).year
        # itera la cantidad de documentos a facturar
        for index, row in data_con_iva.iterrows():
            index += 1
            self.exe_sql_insert_encab_facturacion(row["nro_doc"],
                                            row["descrip_encab_fact"],
                                            row["co_cli"],
                                                '0001',
                                            row["fecha_fact"],
                                            date_current,
                                            row["monto_base"],
                                            row["iva"],
                                            row["total"],
                                            row["nro_control"],
                                            comentario,   # 'Corresponde:' + row["descrip_encab_fact"].replace('Servicio', '') + ' / ' +
                                            campo5,
                                            campo7,
                                            suc)
            
            self.procesar_det_facturacion(modulo, row["nro_doc"], a_bs, num_doc, num_doc_ctrol, num_fact_format, suc)

    
    #  Filtra los datos del detalle de cada factura por la columna 'facturar'
    def procesar_det_facturacion(self, modulo, nro_documento, a_bs, num_doc, num_doc_ctrol, num_fact_format, sucursal):
        df = self.data_facturacion
        data_ = df[df['nro_doc'] == nro_documento].copy()
        # ejemplo de cómo usar groupby y cumcount para crear un correlativo numérico dentro de cada grupo de una columna
        data_['correl'] = data_.groupby('nro_doc').cumcount() + 1
        data_iva_temp = self.determinar_impuesto_por_factura(modulo, False, a_bs, num_doc, num_doc_ctrol, num_fact_format)
        data_iva = data_iva_temp[data_iva_temp['nro_doc'] == nro_documento].copy()
        data_iva.rename(columns={'nro_doc': 'nro_doc_iva'}, inplace=True)
        data_con_iva = merge(data_, data_iva, left_on='correl', right_on='correl_iva', how='left')
        date_current = date_today()
        for index, row in data_con_iva.iterrows():
            index += 1
            comentario = "{l1} \n {l2} \n {l3}".format(l1=row["comentario_l1"],
                                                    l2=row["comentario_l2"],
                                                    l3=row["comentario_l3"]).replace('nan', '')
                
            self.exe_sql_insert_det_facturacion(row["correl"],
                                            row["nro_doc"],
                                            row["co_art"],
                                            round(row["monto_base"] / row["cantidad"], ndigits=2),
                                            row["iva"],
                                            date_current,
                                            row["cantidad"],
                                            row["monto_base"],
                                            comentario,
                                            row["tipo_imp"],
                                            row["p_iva"],
                                            sucursal)

    
    def determinar_impuesto_por_factura(self, modulo, agrupado, a_bs, num_doc, num_doc_ctrol, num_fact_format):
        data_ = self.data_facturacion
        # ejemplo de cómo usar groupby y cumcount para crear un correlativo numérico dentro de cada grupo de una columna
        data_['correl_iva'] = data_.groupby('nro_doc').cumcount() + 1
        articulos = self.odata.articulos_profit()[['co_art', 'tipo_imp']]
        merg1 = merge(data_, articulos, how='left', left_on='co_art', right_on='co_art')
        # Crea una columna con el monto del iva para cada artículo
        merg1['iva'] = merg1.apply(lambda x: round(x['monto_base'] * 16 / 100, ndigits=2) if x['tipo_imp'] == '1' else 0,
                                axis=1)
        # Crea una columna con el porcentaje de iva para cada artículo
        merg1['p_iva'] = merg1.apply(lambda x: 16.0 if x['tipo_imp'] == '1' else 0, axis=1)
        if agrupado == True:
            # es necesario agrupar los encabezados de factura para totalizar la Base Imponible y el IVA
            data_agrupada = merg1.groupby(['co_cli', 'nro_doc', 'fecha_fact', 'descrip_encab_fact', 'tipo_imp', 'p_iva'])[
                ['monto_base', 'iva']].sum().reset_index()[['nro_doc', 'iva', 'tipo_imp', 'p_iva']]
        else:
            data_agrupada = merg1[['nro_doc', 'iva', 'tipo_imp', 'p_iva', 'correl_iva']]
        return data_agrupada
        
        
    def exe_sql_insert_encab_facturacion(self, id_doc, descrip, cod_cli, vendedor, fecha_fact, fecha_cur, monto_base, monto_iva,
                                        monto_total, nro_control, comentario, campo5, campo7, sucursal):
        # SQL para insertar el Encabezado de Factura
        strsql = "INSERT INTO [dbo].[saFacturaVenta] ([doc_num] ,[descrip],[co_cli],[co_tran],[co_mone],[co_ven]," \
                "[co_cond] ,[fec_emis] ,[fec_venc] ,[fec_reg] ,[anulado] ,[status] ,[n_control] ,[ven_ter] ," \
                "[tasa] ,[porc_desc_glob] ,[monto_desc_glob] ,[porc_reca] ,[monto_reca] ,[total_bruto] ," \
                "[monto_imp] ,[monto_imp2] ,[monto_imp3] ,[otros1] ,[otros2] ,[otros3] ,[total_neto] ," \
                "[saldo] ,[dir_ent] ,[comentario] ,[dis_cen] ,[feccom] ,[numcom] ,[contrib] ,[impresa] ," \
                "[seriales_s] ,[salestax] ,[impfis] ,[impfisfac] ,[imp_nro_z] ,[campo1] ,[campo2] ,[campo3] ," \
                "[campo4] ,[campo5] ,[campo6] ,[campo7] ,[campo8] ,[co_us_in] ,[co_sucu_in] ,[fe_us_in] ," \
                "[co_us_mo] ,[co_sucu_mo] ,[fe_us_mo])     " \
                "VALUES ('{doc}', '{descr}', '{c_cli}', '01', 'BS', " \
                "'{ven}', '01', '{f_fact}', '{f_fact}', '{f_fact}', 0, '0', " \
                "'{n_contr}', 0, 1, NULL, 0, NULL, 0, {m_base}, {m_iva}, 0, 0, 0, 0, 0, {m_total}, {m_total}, NULL, " \
                "'{coment}', NULL, NULL, NULL, " \
                "1, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '{camp5}', NULL, '{camp7}', NULL, '999', " \
                "'{suc}', '{f_act}', '999', '{suc}', '{f_act}')".format(doc=id_doc,
                                                                    descr=descrip,
                                                                    c_cli=cod_cli,
                                                                    ven=vendedor,
                                                                    f_fact=fecha_fact,
                                                                    f_act=fecha_cur,
                                                                    m_base=monto_base,
                                                                    m_iva=monto_iva,
                                                                    m_total=monto_total,
                                                                    n_contr=nro_control, 
                                                                    coment=comentario,
                                                                    camp5=campo5,
                                                                    camp7=campo7, 
                                                                    suc=sucursal)

        self.cursor.execute(strsql)

        # SQL para insertar el documento, se coloca dentro del insert encabezado de factura ya que usa los mismos datos
        strsql2 = "INSERT INTO [dbo].[saDocumentoVenta] ([co_tipo_doc],[nro_doc],[co_cli],[co_ven],[co_mone]," \
                "[mov_ban],[tasa],[observa],[fec_reg],[fec_emis],[fec_venc],[anulado],[aut],[contrib],[doc_orig]," \
                "[tipo_origen],[nro_orig],[nro_che],[saldo],[total_bruto],[porc_desc_glob],[monto_desc_glob]," \
                "[porc_reca],[monto_reca],[total_neto],[monto_imp],[monto_imp2],[monto_imp3],[tipo_imp],[tipo_imp2]," \
                "[tipo_imp3],[porc_imp],[porc_imp2],[porc_imp3],[num_comprobante],[feccom],[numcom],[n_control]," \
                "[dis_cen],[comis1],[comis2],[comis3],[comis4],[comis5],[comis6],[adicional],[salestax],[ven_ter]," \
                "[impfis],[impfisfac],[imp_nro_z],[otros1],[otros2],[otros3],[campo1],[campo2],[campo3],[campo4]," \
                "[campo5],[campo6],[campo7],[campo8],[co_us_in],[co_sucu_in],[fe_us_in],[co_us_mo],[co_sucu_mo]," \
                "[fe_us_mo],[co_cta_ingr_egr])     " \
                "VALUES('FACT','{doc}','{c_cli}','{ven}','BS', NULL, 1, 'FACT N° {doc} de Cliente {c_cli}', '{f_fact}'," \
                "'{f_fact}','{f_fact}',0,1,0,'FACT',0,'{doc}',NULL,{m_total},{m_base},NULL,0,NULL,0," \
                "{m_total},{m_iva},0,0,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,'{n_contr}',NULL,0,0,0,0,0,0,0,NULL,0,NULL,NULL,NULL," \
                "0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'999','{suc}','{f_act}','999','{suc}'," \
                "'{f_act}',NULL)".format(doc=id_doc,
                                        descr=descrip,
                                        c_cli=cod_cli,
                                        ven=vendedor,
                                        f_fact=fecha_fact,
                                        f_act=fecha_cur,
                                        m_base=monto_base,
                                        m_iva=monto_iva,
                                        m_total=monto_total,
                                        n_contr=nro_control,
                                        suc=sucursal)
                
        self.cursor.execute(strsql2)
        

    def exe_sql_insert_det_facturacion(self, linea, id_doc, co_art, total_item, monto_iva, fecha_cur, cant_art, total_reng,
                                        comentario, tipo_imp, porcent_iva, sucursal):
        strsql = "INSERT INTO [dbo].[saFacturaVentaReng] ([reng_num] ,[doc_num] ,[co_art] ,[des_art] ,[co_alma] ," \
                "[total_art] ,[stotal_art] ,[co_uni] ,[sco_uni] ,[co_precio] ,[prec_vta] ,[prec_vta_om] ,[porc_desc] ," \
                "[monto_desc] ,[tipo_imp] ,[tipo_imp2] ,[tipo_imp3] ,[porc_imp] ,[porc_imp2] ,[porc_imp3] ,[monto_imp] ," \
                "[monto_imp2] ,[monto_imp3] ,[reng_neto] ,[pendiente] ,[pendiente2] ,[tipo_doc] ,[num_doc] ," \
                "[total_dev] ,[monto_dev] ,[otros] ,[comentario] ,[lote_asignado] ,[monto_desc_glob] ," \
                "[monto_reca_glob] ,[otros1_glob] ,[otros2_glob] ,[otros3_glob] ,[monto_imp_afec_glob] ," \
                "[monto_imp2_afec_glob] ,[monto_imp3_afec_glob] ,[dis_cen] ,[co_us_in] ,[co_sucu_in] ," \
                "[fe_us_in] ,[co_us_mo] ,[co_sucu_mo] ,[fe_us_mo])     " \
                "VALUES ({reng}, '{doc}', '{codigo_art}', NULL, " \
                "'NA', {cant_a}, 0, '001', NULL, '01', {t_item}, NULL, NULL, 0, '{tp_imp}', NULL, NULL, {ptj_iva}, 0, 0, {m_iva}, 0, 0, " \
                "{total_r}, {cant_a}, 0, NULL, NULL, 0, 0, 0, '{coment}', 0, 0, 0, 0, 0, 0, 0, 0, 0, NULL, '999', '{suc}', " \
                "'{f_act}', '999', '{suc}', '{f_act}')".format(reng=linea,
                                                            doc=id_doc,
                                                            codigo_art=co_art,
                                                            t_item=total_item,
                                                            m_iva=monto_iva,
                                                            f_act=fecha_cur,
                                                            cant_a=cant_art,
                                                            total_r=total_reng,
                                                            coment=comentario,
                                                            tp_imp=tipo_imp,
                                                            ptj_iva=porcent_iva,
                                                            suc=sucursal)         
        self.cursor.execute(strsql)
        
    def procesar_facturacion_masiva(self, modulo, a_bs, num_fact_format):
        # Convierte el dataframe obtenido a un diccionario
        lista_last_documents = self.odata.get_last__nro_fact_venta().to_dict()
        # asigna a la variable el último número de factura emitida en profit
        num_doc = lista_last_documents['doc_num'][0] if lista_last_documents['doc_num']!={} else 0  
        # asigna a la variable el último número de control de factura en profit
        num_doc_ctrol = lista_last_documents['n_control'][0] if lista_last_documents['n_control']!={} else 0 
        self.facturacion_masiva(modulo, a_bs, num_doc, num_doc_ctrol, num_fact_format)
        self.gestor_trasacc.confirmar_transaccion()
        today = datetime.now()
        print(f'Módulo: {modulo} Fecha: {today} Usuario: {ClsUsuarios.nombre()} running: procesar_facturacion_masiva()')
        print("Transacción confirmada.")
 
 
 
 
## Implementación 
# fac_mas = FacturacionMasiva(host='10.100.104.11', data_base='BANTEL_A')   
# strsql = "INSERT INTO saColor (co_color ,des_color ,co_us_in ,co_sucu_in ,fe_us_in ,co_us_mo ,co_sucu_mo ,fe_us_mo) VALUES ('00002' ,'prueba' ,'999' ,'01' ,'2024-04-22' ,'999' ,'01' ,'2024-04-22')"
# fac_mas.cursor.execute(strsql)
# strsql2 = "INSERT INTO saColor (co_color ,des_color ,co_us_in ,co_sucu_in ,fe_us_in ,co_us_mo ,co_sucu_mo ,fe_us_mo) VALUES ('00003' ,'prueba' ,'999' ,'01' ,'2024-04-22' ,'999' ,'01' ,'2024-04-22')"
# fac_mas.cursor.execute(strsql2)
# fac_mas.gestor.confirmar_transaccion()
# print("Transacción confirmada.")
