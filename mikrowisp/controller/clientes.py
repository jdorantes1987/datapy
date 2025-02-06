import os

from accesos.conexion import ConexionBD
from accesos.conexion_mkwsp import ConexionBDMysql
from accesos.transacciones import GestorTransacciones
from accesos.transacciones2 import GestorTransacciones2
from numpy import nan
from pandas import merge

from consulta_data import ClsData as cls_data_bantel
from mikrowisp.model.consulta_data_mkwsp import ClsData as cls_data_mikrowisp


class Gestor:
    def __init__(self, data_base):
        self.data_mikrowisp = cls_data_mikrowisp()
        self.data_bantel = cls_data_bantel(data_base)
        self.conn = None
        self.clientes_agregados = None
        self.gestor_trasacc = None
        self.cursor = None
        self.data_base = data_base

    def clientes_mikrowisp(self):
        return self.data_mikrowisp.clientes()

    def clientes_profit(self):
        df = self.data_bantel.clientes()
        return df[~df["inactivo"]]

    def __cod_clientes_x_registrar_en_mikrowisp(self):
        clientes_mkwps = self.clientes_mikrowisp()[["codigo_cliente"]]
        clientes_bantel = self.clientes_profit()[["co_cli"]]
        cod_clientes_mkwsp = set(clientes_mkwps["codigo_cliente"])
        cod_clientes_bantel = set(clientes_bantel["co_cli"])
        return cod_clientes_bantel - cod_clientes_mkwsp

    def datos_clientes_por_registrar(self):
        cod_clientes_por_agregar = self.__cod_clientes_x_registrar_en_mikrowisp()
        df = self.clientes_profit().replace(nan, "s/data")
        return df[df["co_cli"].isin(cod_clientes_por_agregar)]

    def __exec_script_clientes_mikrowisp(self, datos):
        #  Campos de la tabla clientes en BD Profit
        columnas = [
            "co_cli",
            "cli_des",
            "email",
            "telefonos",
            "rif",
            "direc1",
            "campo3",
        ]
        datos = self.datos_clientes_por_registrar()[columnas]  # .iloc[0:2]
        self.conn = ConexionBDMysql()
        self.conn.conectar()
        self.gestor_trasacc = GestorTransacciones2(self.conn)
        self.gestor_trasacc.iniciar_transaccion()
        self.cursor = self.gestor_trasacc.get_cursor()
        for index, row in datos.iterrows():
            index += 1
            cod = row["co_cli"]
            nombre = row["cli_des"]
            correo = row["email"]
            telefono = row["telefonos"]
            cedula = row["rif"]
            direcc = row["direc1"]

            strsql = f"""
            INSERT INTO usuarios (id, nombre, estado, correo, telefono,
                                movil, cedula, pasarela, codigo,
                                direccion_principal, codigo_cliente)
                        VALUES (0, '{nombre}', 'ACTIVO', '{correo}',
                                '{telefono}', '{telefono}', '{cedula}',
                                's/data', '123', '{direcc}', '{cod}');
                      """
            self.cursor.execute(strsql)

        try:
            self.gestor_trasacc.confirmar_transaccion()
        except Exception:
            self.gestor_trasacc.revertir_transaccion()
        finally:
            self.conn.desconectar()
            self.datos_clientes_agregados = datos

    def add_clientes_en_mikrowisp(self):
        datos = self.datos_clientes_por_registrar()
        self.__exec_script_clientes_mikrowisp(datos)

    def add_notificaciones(self):
        clientes_add = self.datos_clientes_agregados
        clientes_mkwps = self.clientes_mikrowisp()[["id", "codigo_cliente"]]
        data_combinada = merge(
            clientes_add,
            clientes_mkwps,
            left_on="co_cli",
            right_on="codigo_cliente",
            how="left",
        )

        self.conn = ConexionBDMysql()
        self.conn.conectar()
        self.gestor_trasacc = GestorTransacciones2(self.conn)
        self.gestor_trasacc.iniciar_transaccion()
        self.cursor = self.gestor_trasacc.get_cursor()
        otros_impuestos = 'a:3:{i:1;s:0:"";i:2;s:0:"";i:3;s:0:"";}'
        for index, row in data_combinada.iterrows():
            index += 1
            cod = row["id"]
            strsql = f"""
            INSERT INTO tblavisouser (id, cliente, mora, reconexion, impuesto,
                                      avatar_cliente, chat, zona, diapago,
                                      tipopago, tipoaviso, meses, fecha_factura,
                                      diafactura, avisopantalla,
                                      corteautomatico, avisosms, avisosms2,
                                      avisosms3, afip_condicion_iva, afip,
                                      afip_condicion_venta, afip_automatico,
                                      avatar_color, tiporecordatorio,
                                      afip_punto_venta, id_telegram,
                                      router_eliminado, otros_impuestos,
                                      mikrowisp_app_id, isaviable,
                                      invoice_electronic, invoice_data,
                                      fecha_suspendido, limit_velocidad,
                                      mantenimiento, data_retirado,
                                      fecha_retirado, tipo_estrato,
                                      fecha_corte_fija, mensaje_comprobante,
                                      id_moneda, afip_enable_percepcion,
                                      gatewaynoty, fecha_registro, empresa_afip,
                                      code_toku)
                            VALUES   (0, {cod}, '', '', 'NADA', '', 0, 1, 0, 1,
                                      0, 0, null, 0, 0, 0, 0, 0, 0,
                                      'Consumidor Final', '', 'Contado', 0,
                                      '#04CF98', 0	, '', 0, 0,
                                      '{otros_impuestos}', '', 0, 0, '', null,
                                      0, 0, '', '', 1, '', 0, 1, 0, '', now(),
                                      1, '');
            """

            self.cursor.execute(strsql)

        try:
            self.gestor_trasacc.confirmar_transaccion()
        except Exception as e:
            print("Ocurrió un error al confirmar transaccion: ", e)
            self.gestor_trasacc.revertir_transaccion()
        finally:
            self.conn.desconectar()

    def __cod_clientes_profit_mikrowisp_por_sinc(self):
        clientes_profit = self.clientes_profit()[
            ["co_cli", "cli_des", "direc1", "telefonos", "email"]
        ].replace(nan, "s/data")
        clientes_profit_s = clientes_profit.sort_values(by=["co_cli"], ascending=[True])
        clientes_mkwsp = self.clientes_mikrowisp()[
            ["codigo_cliente", "nombre", "direccion_principal", "movil", "correo"]
        ]
        clientes_mkwsp.rename(
            columns={
                "codigo_cliente": "co_cli",
                "nombre": "cli_des",
                "direccion_principal": "direc1",
                "movil": "telefonos",
                "correo": "email",
            },
            inplace=True,
        )
        clientes_mkwsp_s = clientes_mkwsp.sort_values(by=["co_cli"], ascending=[True])
        # Hace una combinación para identificar los datos comunes
        clientes_iguales = clientes_profit_s.merge(
            clientes_mkwsp_s, how="inner", indicator=False
        )
        # Almecena un conjunto con todos los códigos de clientes profit
        conjunto_cod_clientes = set(clientes_profit_s["co_cli"])
        # Almecena un conjunto con todos los códigos que coinciden entre profit y microwisp
        conjunto_cod_clientes_iguales = set(clientes_iguales["co_cli"])
        # Almecena un conjunto con todos los códigos de clientes que presentan diferencias
        return conjunto_cod_clientes - conjunto_cod_clientes_iguales

    def datos_clientes_por_sinc_profit_mikrowisp(self):
        cod_clientes_profit_mikrowisp_por_sinc = (
            self.__cod_clientes_profit_mikrowisp_por_sinc()
        )
        clientes = self.clientes_profit()
        return clientes[
            clientes["co_cli"].isin(cod_clientes_profit_mikrowisp_por_sinc)
        ][["co_cli", "cli_des", "direc1", "telefonos", "email"]]

    def sinc_datos_clientes_profit_mikrowisp(self):
        data = self.datos_clientes_por_sinc_profit_mikrowisp().replace(nan, "s/data")
        self.conn = ConexionBDMysql()
        self.conn.conectar()
        self.gestor_trasacc = GestorTransacciones2(self.conn)
        self.gestor_trasacc.iniciar_transaccion()
        self.cursor = self.gestor_trasacc.get_cursor()
        for index, row in data.iterrows():
            index += 1
            cod_client, descrip, direc = row["co_cli"], row["cli_des"], row["direc1"]
            telf, email = row["telefonos"], row["email"]
            strsql = f"""
                        UPDATE usuarios
                        SET nombre = '{descrip}', direccion_principal = '{direc}',  movil = '{telf}', correo = '{email}'
                        WHERE codigo_cliente = '{cod_client}'
                      """
            self.cursor.execute(strsql)

        try:
            self.gestor_trasacc.confirmar_transaccion()
        except Exception as e:
            self.gestor_trasacc.revertir_transaccion()
            print("Ocurrió un error al confirmar transaccion: ", e)
        finally:
            self.conn.desconectar()

    def __clientes_mikrowisp_aviso_user(self):
        data_aviso_user = self.data_mikrowisp.clientes_aviso_user()[
            ["codigo_cliente", "zona"]
        ]
        data_aviso_user.rename(
            columns={"codigo_cliente": "co_cli", "zona": "campo3"}, inplace=True
        )
        data_aviso_user_s = data_aviso_user.sort_values(by=["co_cli"], ascending=[True])
        clientes_profit = self.clientes_profit()[["co_cli", "campo3"]]
        clientes_profit_s = clientes_profit.sort_values(by=["co_cli"], ascending=[True])

        # Hace una combinación para identificar los datos comunes
        clientes_iguales = data_aviso_user_s.merge(
            clientes_profit_s, how="inner", indicator=False
        )
        conjunto_cod_clientes_profit = set(clientes_profit_s["co_cli"])
        # Almecena un conjunto con todos los códigos de clientes Mikrowisp
        conjunto_cod_clientes = set(data_aviso_user_s["co_cli"])
        # Almecena un conjunto con todos los códigos que coinciden entre profit y microwisp
        conjunto_cod_clientes_iguales = set(clientes_iguales["co_cli"])
        # Almecena un conjunto con todos los códigos de clientes que presentan diferencias
        conjunto_por_actualizar = conjunto_cod_clientes - conjunto_cod_clientes_iguales
        return conjunto_por_actualizar & conjunto_cod_clientes_profit

    def datos_clientes_nodo_por_sinc_mikrowisp_profit(self):
        cod_clientes_mikrowisp_profit_por_sinc = self.__clientes_mikrowisp_aviso_user()
        clientes = self.data_mikrowisp.clientes_aviso_user()[
            ["codigo_cliente", "nombre", "zona"]
        ]
        return clientes[
            clientes["codigo_cliente"].isin(cod_clientes_mikrowisp_profit_por_sinc)
        ][["codigo_cliente", "nombre", "zona"]]

    def sinc_datos_clientes_nodos(self):
        data = self.datos_clientes_nodo_por_sinc_mikrowisp_profit()
        conexion = ConexionBD(
            base_de_datos=self.data_base, host=os.getenv("HOST_PRODUCCION_PROFIT")
        )  # Crea un objeto conexión
        conexion.conectar()  # inicia la conexión
        gestor_trasacc = GestorTransacciones(conexion)
        gestor_trasacc.iniciar_transaccion()
        cursor = gestor_trasacc.get_cursor()
        for index, row in data.iterrows():
            index += 1
            cod_client, zona = row["codigo_cliente"], row["zona"]
            strsql = f"""
                        UPDATE saCliente
                        SET campo3 = '{zona}'
                        WHERE co_cli = '{cod_client}'
                      """
            cursor.execute(strsql)

        try:
            gestor_trasacc.confirmar_transaccion()
        except Exception as e:
            gestor_trasacc.revertir_transaccion()
            print("Ocurrió un error al confirmar transaccion: ", e)
        finally:
            conexion.desconectar()


if __name__ == "__main__":
    g = Gestor("BANTEL_A")
    # print(g.datos_clientes_nodo_por_sinc_mikrowisp_profit())
    # print(g.datos_clientes_por_sinc_profit_mikrowisp())
    datos_mkwps = g.clientes_mikrowisp()
    print(datos_mkwps)
