from mikrowisp.model.interfaz_data_source import DataSource

class Database(DataSource):

    def get_clientes(self):
        print('get_clientes')
    
    def get_ventas_con_detalle(self):
        print('ventas_con_detalle')
    
    def get_articulos(self):
        print('get_articulos')



