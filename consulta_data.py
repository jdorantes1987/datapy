import os
import sys
from datetime import datetime

from pandas import merge

from empresa import ClsEmpresa
from gestion_user.usuarios import ClsUsuarios

sys.path.append("..\\bantel")
from accesos.datos_profit import datos_profit


class ClsData:
    @staticmethod
    def audit(method):
        def wrapper(self, *args, **kwargs):
            today = datetime.now()
            modulo = ClsEmpresa.modulo()
            print(
                f"Módulo: {modulo} Fecha: {today} Usuario: {ClsUsuarios.nombre()} running: {method.__name__}"
            )
            return method(self, *args, **kwargs)  # Ojo llamada!

        return wrapper

    def __init__(self, data_base):
        self.data_base = data_base
        self.odata = datos_profit(
            host=os.getenv("HOST_PRODUCCION_PROFIT"),
            data_base_admin=data_base,
            data_base_cont="TBANTEL_C",
        )

    def ventas_dt(self, anio, mes, usd):
        return self.odata.ventas_con_detalle(anio=anio, mes=mes, usd=usd)

    def ventas_rsm(self, anio, mes, usd):
        return self.odata.ventas_sin_detalle(anio=anio, mes=mes, usd=usd)

    def ventas_dicc(self, anio, usd):
        return self.odata.dicc_ventas_total_por_anio(anio=anio, usd=usd)

    def ventas_dicc_x_vendedor(self, anio, vendedor, usd):
        return (
            self.ventas_dicc(anio, usd)
            if vendedor == "Todos"
            else self.odata.dicc_ventas_total_por_anio_vendedor(
                anio=anio, vendedor=vendedor, usd=usd
            )
        )

    def cuentas_por_cobrar_agrupadas(self, anio, mes, usd, vendedor):
        return self.odata.cxc_clientes_resum_grouped(
            anio=anio, mes=mes, usd=usd, vendedor=vendedor
        )

    def cuentas_por_cobrar_det(self, anio, mes, usd, vendedor):
        return self.odata.facturacion_saldo_x_clientes_detallado(
            anio=anio, mes=mes, usd=usd, vendedor=vendedor
        )

    @audit
    def cuentas_por_cobrar_pivot(self, anio, mes, usd, vendedor):
        return self.odata.cxc_clientes_resum_pivot(
            anio=anio, mes=mes, usd=usd, vendedor=vendedor
        )

    def generar_cod_cliente(self):
        return self.odata.new_cod_client()

    def articulos(self):
        return self.odata.articulos_profit()

    def clientes(self):
        return self.odata.clientes()

    def clintes_search(self, str_search, resumir_info):
        return self.odata.search_clients(str_search, resumir_datos=resumir_info)

    def get_tasa_bcv_dia(self):
        return self.odata.get_monto_tasa_bcv_del_dia()

    def get_fecha_tasa_bcv_dia(self):
        return self.odata.get_fecha_tasa_bcv_del_dia()

    def facturacion_saldo_x_intervalo_dias(self, usd):
        return self.odata.facturacion_saldo_x_intervalo_dias(usd=usd)

    def saldo_a_favor_clientes(self):
        return self.odata.doc_cxc_clientes_resumido()

    @audit
    def ultimo_plan_facturado(self):
        articulos = self.articulos()[["co_art", "art_des"]]
        df = self.ventas_dt(anio="all", mes="all", usd=True)
        # La propieda 'as_index=False' permite mantener los encabezados en la agrupación o groupby
        ultimas_facturas = df.groupby(["co_cli"], sort=False, as_index=False)[
            ["fec_emis", "doc_num"]
        ].max()
        conjunto_ultimas_facturas = set(ultimas_facturas["doc_num"])
        datos_utimo_plan_facturado = df[df["doc_num"].isin(conjunto_ultimas_facturas)][
            ["doc_num", "fec_emis", "co_cli", "cli_des", "co_art"]
        ]
        ultimo_plan = merge(
            datos_utimo_plan_facturado,
            articulos,
            how="left",
            left_on="co_art",
            right_on="co_art",
        )
        ultimo_plan["fec_emis"] = ultimo_plan["fec_emis"].dt.strftime("%d-%m-%Y")
        return ultimo_plan.sort_values(by="doc_num", ascending=[False])

    @audit
    def ultimo_plan_facturado_implementacion_imprenta(self):
        from datetime import date

        from dotenv import load_dotenv

        sys.path.append("..\\profit")
        from conn.database_connector import DatabaseConnector
        from conn.sql_server_connector import SQLServerConnector
        from data.mod.ventas.facturas_ventas import FacturasVentas

        env_path = os.path.join("..\\profit", ".env")
        load_dotenv(
            env_path, override=True
        )  # Recarga las variables de entorno desde el archivo

        # Para SQL Server
        sqlserver_connector = SQLServerConnector(
            host=os.environ["HOST_PRODUCCION_PROFIT"],
            database=self.data_base,
            user=os.environ["DB_USER_PROFIT"],
            password=os.environ["DB_PASSWORD_PROFIT"],
        )
        db = DatabaseConnector(sqlserver_connector)
        oFacturaVentas = FacturasVentas(db)
        hoy = date.today().strftime("%Y-%m-%d")
        params = {
            "fechaInicio": "2025-06-20",  # Fecha de inicio del rango
            "fechaFin": hoy,  # Fecha de fin del rango
        }
        df = oFacturaVentas.get_facturas(
            fecha_d=params["fechaInicio"], fecha_h=params["fechaFin"]
        )
        # Eliminar filas donde 'co_cli' o 'co_art' son nulos de una forma más eficiente u optimizada
        df["co_cli"] = df["co_cli"].map(str.strip)
        df["co_art"] = df["co_art"].map(str.strip)
        clientes = self.clientes()[["co_cli", "cli_des"]]
        df = merge(
            df,
            clientes,
            how="left",
            left_on="co_cli",
            right_on="co_cli",
        )
        # La propieda 'as_index=False' permite mantener los encabezados en la agrupación o groupby
        ultimas_facturas = df.groupby(["co_cli"], sort=False, as_index=False)[
            ["fec_emis", "doc_num_encab"]
        ].max()
        conjunto_ultimas_facturas = set(ultimas_facturas["doc_num_encab"])
        utimo_plan_facturado = df[df["doc_num_encab"].isin(conjunto_ultimas_facturas)][
            ["doc_num_encab", "fec_emis", "co_cli", "cli_des", "co_art"]
        ]
        utimo_plan_facturado["fec_emis"] = utimo_plan_facturado["fec_emis"].dt.strftime(
            "%d-%m-%Y"
        )
        return utimo_plan_facturado.sort_values(by="doc_num_encab", ascending=[False])


if __name__ == "__main__":
    data = ClsData("BANTEL_A")
    print(data.ultimo_plan_facturado_implementacion_imprenta())
