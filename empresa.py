import os
class ClsEmpresa:
    var_st_empresa, var_modulo, convertir_a_usd = '', '', ''
    
    def __init__(self, modulo_empresa, convertir_a_usd):
        empresa_select = os.getenv('DB_NAME_DERECHA_PROFIT') if modulo_empresa == 'Derecha' else os.getenv('DB_NAME_IZQUIERDA_PROFIT')
        self.sel_emp = empresa_select
        self.modulo = modulo_empresa
        self.a_usd = convertir_a_usd
        ClsEmpresa.var_st_empresa = empresa_select
        ClsEmpresa.convertir_a_usd = convertir_a_usd
        ClsEmpresa.var_modulo = modulo_empresa
        
    @staticmethod
    def empresa_seleccionada(): 
        return str(ClsEmpresa.var_st_empresa)
    
    @staticmethod
    def convert_usd(): 
        return ClsEmpresa.convertir_a_usd
    
    @staticmethod
    def modulo(): 
        return str(ClsEmpresa.var_modulo)
