from abc import ABC, abstractmethod

class IDataSource(ABC):
    @abstractmethod
    def get_clientes(self):
        pass
    
    @abstractmethod
    def get_ventas_con_detalle(self):
        pass
    
    @abstractmethod
    def get_articulos(self):
        pass

    


    
    
    