import requests
import json
import time

datainicial = "20261225"
datafinal = "20261225"
uf = "SP"
codModalidade = 6
pagina = 1
tamanhopagina = 50
url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

todas_compras = []
while True:

    parametros = {"dataInicial": datainicial, "dataFinal" : datafinal,"uf" : uf, "codigoModalidadeContratacao" : codModalidade, "pagina" : pagina, "tamanhoPagina" : tamanhopagina}
    r = requests.get(url, timeout=30, params=parametros) 
    print(r.status_code)

    if r.status_code == 204:
        break

    response_dict = r.json()
    print("Página ",parametros["pagina"]," de ",response_dict["totalPaginas"])
    compras_da_pagina = response_dict["data"]
    todas_compras.extend(compras_da_pagina)

    if pagina >= response_dict["totalPaginas"]:
        break

    time.sleep(1)
    pagina += 1
print(len(todas_compras))