import requests

URL_CONTRATACOES = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
TAMANHO_PAGINA = 50
TIMEOUT = 30

def buscar_pagina(dia, uf, modalidade, pagina=1):

    parametros = {"dataInicial": dia, "dataFinal" : dia,"uf" : uf, "codigoModalidadeContratacao" : modalidade, "pagina" : pagina, "tamanhoPagina" : TAMANHO_PAGINA}
    r = requests.get(URL_CONTRATACOES, timeout=TIMEOUT, params=parametros) 
    if r.status_code == 204:
        return {"data": [], "totalPaginas": 0}
    r.raise_for_status()
    print(r.status_code)
    return r.json()


if __name__ == "__main__":               
    resultado1 = buscar_pagina("20260701", "SP", 6)
    print("Total de Páginas: ",resultado1["totalPaginas"],"\nTamanho da Lista: ",len(resultado1["data"]))

    resultado2 = buscar_pagina("20261225", "SP", 6)
    print("Total de Páginas: ",resultado2["totalPaginas"],"\nTamanho da Lista: ",len(resultado2["data"]))