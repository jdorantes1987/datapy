import os

import streamlit as st


class ClsEmpresa:
    # Diccionario con clave=usuario y valor={empresa, modulo, moneda}
    _usuarios: dict = {}

    def __init__(self, username: str, modulo_empresa: str, convertir_a_usd: bool):
        empresa_select = (
            os.getenv("DB_NAME_DERECHA_PROFIT")
            if modulo_empresa == "Derecha"
            else os.getenv("DB_NAME_IZQUIERDA_PROFIT")
        )
        self.sel_emp = empresa_select
        self.a_usd = convertir_a_usd
        ClsEmpresa._usuarios[username] = {
            "empresa": empresa_select,
            "modulo": modulo_empresa,
            "convertir_a_usd": convertir_a_usd,
        }

    @staticmethod
    def _get_username() -> str:
        return st.session_state.get("usuario", "")

    @staticmethod
    def empresa_seleccionada() -> str:
        username = ClsEmpresa._get_username()
        return str(ClsEmpresa._usuarios.get(username, {}).get("empresa", ""))

    @staticmethod
    def convert_usd() -> bool:
        username = ClsEmpresa._get_username()
        return ClsEmpresa._usuarios.get(username, {}).get("convertir_a_usd", False)

    @staticmethod
    def modulo() -> str:
        username = ClsEmpresa._get_username()
        return str(ClsEmpresa._usuarios.get(username, {}).get("modulo", ""))

    @staticmethod
    def limpiar_usuario(username: str) -> None:
        ClsEmpresa._usuarios.pop(username, None)
