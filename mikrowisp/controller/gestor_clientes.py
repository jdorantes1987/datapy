from datetime import datetime
from mikrowisp.controller.clientes import Gestor
from gestion_user.usuarios import ClsUsuarios
from empresa import ClsEmpresa

class GestionarClientes(Gestor):
    @staticmethod
    def audit(method):
        def wrapper(self, *args, **kwargs):
            today = datetime.now()
            modulo = ClsEmpresa.modulo()
            print(f'Módulo: {modulo} Fecha: {today} Usuario: {ClsUsuarios.nombre()} running: {method.__name__}')
            return method(self, *args, **kwargs)  # Ojo llamada!
        return wrapper
    
    def __init__(self, data_base):
            super().__init__(data_base)

    def clientes_mikrowisp(self):
          return super().clientes_mikrowisp()
    
    def clientes_mikrowisp_aviso_user(self):
          return super().clientes_mikrowisp_aviso_user()
      
    def clientes_profit(self):
          return super().clientes_profit()
    
    @audit
    def add_clientes_en_mikrowisp(self):
          return super().add_clientes_en_mikrowisp()

    @audit  
    def add_notificaciones(self):
          return super().add_notificaciones()
      
    def datos_clientes_por_sinc_profit_mikrowisp(self):
          return super().datos_clientes_por_sinc_profit_mikrowisp()
    
    @audit  
    def sinc_datos_clientes_profit_mikrowisp(self):
          return super().sinc_datos_clientes_profit_mikrowisp()
    
    def datos_clientes_nodo_por_sinc_mikrowisp_profit(self):
          return super().datos_clientes_nodo_por_sinc_mikrowisp_profit()
    
    @audit
    def sinc_datos_clientes_nodos(self):
          return super().sinc_datos_clientes_nodos()
    
    @audit
    def ultimo_plan_facturado(self):
          return super().ultimo_plan_facturado()
