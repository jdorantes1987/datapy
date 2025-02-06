from accesos.datos_mkwsp import DatosMikrowisp


class ClsData:
    def __init__(self):
        self.odata = DatosMikrowisp()

    def clientes(self):
        return self.odata.clientes()

    def clientes_aviso_user(self):
        return self.odata.clientes_aviso_user()


if __name__ == "__main__":
    datos = ClsData().clientes()
    print(datos)
