import sys
# La ruta SYS es una lista de directorios que Python interpreta para buscar cuando se inicia
sys.path.append('..\\bantel') # Agrega el directorio Bantel a la ruta SYS
from accesos.datos_mkwsp import DatosMikrowisp

class ClsData:
    def __init__(self):
        self.odata = DatosMikrowisp()
        
    def clientes(self):
        return self.odata.clientes()
    
    def clientes_aviso_user(self):
        return self.odata.clientes_aviso_user()
    


# # Ejemplo de uso:
# datos = ClsData().clientes()
# print(datos)