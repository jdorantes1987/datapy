import os

import accesos.data_base as db

import gestion_user.control_roles as croles
import gestion_user.usuarios as u


def data_user(user, pw):
    sql = f"""
          Select * From usuarios where idusuario ='{user}' and PWDCOMPARE('{pw}', passw)= 1
          """
    return db.get_read_sql(
        sql=sql,
        host=os.getenv("HOST_DESARROLLO_PROFIT"),
        base_de_datos=os.getenv("DB_NAME_DERECHA_PROFIT"),
    )


def get_users():
    sql = "Select * From usuarios"
    return db.get_read_sql(
        sql=sql,
        host=os.getenv("HOST_DESARROLLO_PROFIT"),
        base_de_datos=os.getenv("DB_NAME_DERECHA_PROFIT"),
    )


def existe_user(user):
    sql = f"""
          Select * From usuarios where idusuario ='{user}'
          """
    return (
        len(
            db.get_read_sql(
                sql=sql,
                host=os.getenv("HOST_DESARROLLO_PROFIT"),
                base_de_datos=os.getenv("DB_NAME_DERECHA_PROFIT"),
            )
        )
        > 0
    )


def aut_user(user, pw):
    aut = False
    df_users = data_user(user, pw)
    if len(df_users) > 0:
        u.ClsUsuarios(
            df_users["idusuario"][0], df_users["nombre"][0], df_users["categoria"][0]
        )
        croles.set_roles(u.ClsUsuarios.id_usuario())
        aut = True
    return aut


def change_password(user, pw):
    sql = f"""
          UPDATE usuarios SET passw=PWDENCRYPT('{pw}') WHERE idusuario='{user}'
          """
    db.insert_sql(
        sql,
        host=os.getenv("HOST_DESARROLLO_PROFIT"),
        base_de_datos=os.getenv("DB_NAME_DERECHA_PROFIT"),
    )


def insert_user(user, nombre, pw):
    sql = f"""
          insert into usuarios(idusuario, nombre, passw) values('{user}','{nombre}',PWDENCRYPT('{pw}'))
          """
    db.insert_sql(
        sql,
        host=os.getenv("HOST_DESARROLLO_PROFIT"),
        base_de_datos=os.getenv("DB_NAME_DERECHA_PROFIT"),
    )


# aut = aut_user('amonasterios', 'ale')
# print(aut)
# print(u.ClsUsuarios.id_usuario())
# print(u.ClsUsuarios.nombre())
# print(u.ClsUsuarios.categoria())
# croles.set_roles(u.ClsUsuarios.id_usuario())
# print('Modulo derecha habilitado:', r.ClsUsuariosRoles.dic_roles['Derecha'])
# print('Modulo Facturación habilitado:', r.ClsUsuariosRoles.dic_roles['Facturacion'])
