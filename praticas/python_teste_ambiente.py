import requests
import json

datainicial = "20260701"
datafinal = "20260701"
uf = "SP"
codModalidade = 6
pagina = 1
tamanhopagina = 50

parametros = {"dataInicial": datainicial, "dataFinal" : datafinal,"uf" : uf, "codigoModalidadeContratacao" : codModalidade, "pagina" : pagina, "tamanhoPagina" : tamanhopagina}

url = f"https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
r = requests.get(url, timeout=30, params=parametros) 

print("Status:",r.status_code)

response_dict = r.json()
print("Total Registros:",response_dict["totalRegistros"])
print("Total de Paginas:",response_dict["totalPaginas"])
print("Dados:",len(response_dict["data"]))
print(response_dict["data"][0])

for compra in response_dict["data"]:
    print("\nCompra:",compra["objetoCompra"])
    print("Municipio:",compra["unidadeOrgao"]["municipioNome"])

