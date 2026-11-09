import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_CONTRATACOES = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
TAMANHO_PAGINA = 50
TIMEOUT = 30
PAUSA = 3

def criar_sessao():
    regra = Retry(
        total= 5,
        backoff_factor= 2,
        status_forcelist=[429,500,502,503,504],
        allowed_methods=["GET"],
    )
    adaptador = HTTPAdapter(max_retries = regra)
    sessao = requests.Session()
    sessao.mount("https://", adaptador)
    sessao.headers.update({"User-Agent": "pncp-compras-saude/1.0"})
    return sessao

SESSAO = criar_sessao()

def buscar_pagina(dia, uf, modalidade, pagina=1):
    parametros = {"dataInicial": dia, "dataFinal" : dia,"uf" : uf, "codigoModalidadeContratacao" : modalidade, "pagina" : pagina, "tamanhoPagina" : TAMANHO_PAGINA}
    r = SESSAO.get(URL_CONTRATACOES, timeout=TIMEOUT, params=parametros) 

    if r.status_code == 204:
        return {"data": [], "totalPaginas": 0}
    
    r.raise_for_status()
    return r.json()

def buscar_dia(dia, uf, modalidade):
    todas_compras = []
    pagina = 1

    while True:
        resposta = buscar_pagina(dia, uf, modalidade, pagina=pagina)
        todas_compras.extend(resposta["data"])

        if pagina >= resposta["totalPaginas"]:
            break

        time.sleep(PAUSA)
        pagina += 1 

    return todas_compras

if __name__ == "__main__":   

    # resultado1 = buscar_pagina("20260701", "SP", 6)
    # print("Total de Páginas: ",resultado1["totalPaginas"],"\nTamanho da Lista: ",len(resultado1["data"]))

    # resultado2 = buscar_pagina("20261225", "SP", 6)
    # print("Total de Páginas: ",resultado2["totalPaginas"],"\nTamanho da Lista: ",len(resultado2["data"]))

    compras = buscar_dia("20260701", "SP", 6)
    print("Compras no Dia: ", len(compras))

    compras_natal = buscar_dia("20261225", "SP", 6)
    print("Compras no Natal: ", len(compras_natal))

