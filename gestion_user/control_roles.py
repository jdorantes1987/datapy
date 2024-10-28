import sys
import os
# La ruta SYS es una lista de directorios que Python interpreta para buscar cuando se inicia
sys.path.append('..\\bantel') # Agrega el directorio Bantel a la ruta SYS
from accesos.datos_profit import datos_profit
from accesos.sql_read import get_read_sql
from gestion_user.usuarios_roles import ClsUsuariosRoles

def dict_users_rols(id_user):
    sql = f"""
          select * from usuarios_roles where idusuario ='{id_user}'
          """
    df = get_read_sql(sql=sql, 
                      host=os.getenv('HOST_DESARROLLO_PROFIT'), 
                      base_de_datos=os.getenv('DB_NAME_DERECHA_PROFIT'))
    users = df.set_index('modulo')['habilitado']
    return users.to_dict()

def set_roles(id_user):
    d_roles = dict_users_rols(id_user)
    ClsUsuariosRoles(d_roles)


# set_roles('amonasterios')
# print(ur.ClsUsuariosRoles.roles()['Derecha'])


