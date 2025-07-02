import os
import sys
from datetime import date

from dotenv import load_dotenv

# # Agrega el directorio facturacion_digital a la ruta SYS
sys.path.append("..\\facturacion_digital")
from api_gateway_client import ApiGatewayClient
from api_key_manager import ApiKeyManager
from get_api_invoices import GetInvoices
from token_generator import TokenGenerator

env_path = os.path.join("..\\facturacion_digital", ".env")
load_dotenv(
    dotenv_path=env_path,
    override=True,
)  # Recarga las variables de entorno desde el archivo

path_api_key = os.path.join("..\\facturacion_digital", "api_key.txt")
token_actualizado = TokenGenerator(path_api_key=path_api_key).update_token()

api_url = os.getenv("API_GATEWAY_URL_GET_LIST_INVOICES")
api_key_manager = ApiKeyManager(path_api_key)
client = ApiGatewayClient(api_url, api_key_manager)
invoice_consultas = GetInvoices(client)

hoy = date.today().strftime("%Y-%m-%d")

# Puedes pasar parámetros de consulta si la API los soporta, por ejemplo: {"numeroFactura": "12345"}
params = {
    "fechaInicio": "2025-06-20",  # Fecha de inicio del rango
    "fechaFin": hoy,  # Fecha de fin del rango
}
result = invoice_consultas.get_last_invoice(params)

print("Resultado:", result)
