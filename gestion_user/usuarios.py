class ClsUsuarios:
    
    var_id_usuario, var_nombre, var_categoria = '', '', ''
    
    def __init__(self, id_usuario, nombre, categoria):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.categoria = categoria
        ClsUsuarios.var_id_usuario = id_usuario
        ClsUsuarios.var_nombre = nombre
        ClsUsuarios.var_categoria = categoria
    
    @staticmethod
    def id_usuario(): 
        return str(ClsUsuarios.var_id_usuario)
    
    @staticmethod
    def nombre(): 
        return ClsUsuarios.var_nombre
    
    @staticmethod
    def categoria(): 
        return ClsUsuarios.var_categoria
        
        