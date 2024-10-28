class ClsUsuariosRoles:
    
    dic_roles = {}
    
    def __init__(self, dict_roles):
        ClsUsuariosRoles.dic_roles = dict_roles
        
    @staticmethod
    def roles(): 
        return ClsUsuariosRoles.dic_roles
    