import argparse
import json
import logging
import time

import requests
from sqlalchemy import text

from banco import criar_engine, executar_sql
from pncp_api import buscar_itens

PAUSA_ENTRE_COMPRAS = 1

SQL_COMPRAS_PENDENTES = """
SELECT v.codigo_pedido, v.cnpj_orgao, v.ano_compra, v.sequencial_compra
FROM pncp.vw_contratacoes_saude v
WHERE NOT EXISTS (
    SELECT 1 FROM pncp.controle_itens c
    WHERE c.codigo_pedido = v.codigo_pedido
)
ORDER BY v.data_publicacao, v.codigo_pedido
"""

SQL_UPSERT_ITEM = """
INSERT INTO pncp.itens (codigo_pedido, numero_item, registro)
VALUES (:codigo_pedido, :numero_item, cast(:registro as jsonb))
ON CONFLICT (codigo_pedido, numero_item) DO UPDATE SET
    registro    = EXCLUDED.registro,
    extraido_em = now()
"""

SQL_UPSERT_CONTROLE_ITENS = """
INSERT INTO pncp.controle_itens (codigo_pedido, qtd_itens)
VALUES (:codigo_pedido, :qtd_itens)
ON CONFLICT (codigo_pedido) DO UPDATE SET
    qtd_itens   = EXCLUDED.qtd_itens,
    extraido_em = now()
"""


def compras_pendentes(engine):
    with engine.connect() as conexao:
        return conexao.execute(text(SQL_COMPRAS_PENDENTES)).all()


def montar_linha_item(codigo_pedido, item):
    return{
        "codigo_pedido" : codigo_pedido,
        "numero_item"   : item["numeroItem"],
        "registro" : json.dumps(item, ensure_ascii=False)
    }

def gravar_compra(engine, codigo_pedido, linhas):
    with engine.begin() as conexao:
        if linhas:
            conexao.execute(text(SQL_UPSERT_ITEM), linhas)
        conexao.execute(text(SQL_UPSERT_CONTROLE_ITENS),{
            "codigo_pedido" : codigo_pedido,
            "qtd_itens"     : len(linhas)
        })

def ler_argumentos():
    parser = argparse.ArgumentParser(description="Extrai os itens das compras de saúde do PNCP")
    parser.add_argument("--limite", type=int, help="processa só as N primeiras compras pendentes")
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = ler_argumentos()

    engine = criar_engine()
    executar_sql(engine, "003_criar_tabelas_itens.sql")

    compras = compras_pendentes(engine)
    if args.limite:
        compras = compras[:args.limite]
    total = len(compras)
    logging.info(f"{total} compras pendentes")

    falhas = []
    for i, (codigo_pedido, cnpj, ano, sequencial) in enumerate(compras, start=1):
        try:
            itens = buscar_itens(cnpj, ano, sequencial)

            linhas = []
            for item in itens:
                linhas.append(montar_linha_item(codigo_pedido, item))

            gravar_compra(engine, codigo_pedido, linhas)
            logging.info(f"[{i}/{total}] {codigo_pedido}: {len(linhas)} itens gravados")

        except requests.RequestException as erro:
            logging.error(f"[{i}/{total}] {codigo_pedido}: falhou {erro}")
            falhas.append(codigo_pedido)

        time.sleep(PAUSA_ENTRE_COMPRAS)

    logging.info(f"Fim. Compras com falha: {falhas}")


if __name__ == "__main__":
    main()