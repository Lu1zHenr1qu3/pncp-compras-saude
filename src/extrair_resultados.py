import argparse
import json
import logging
import time

import requests
from sqlalchemy import text

from banco import criar_engine, executar_sql
from pncp_api import buscar_resultados

PAUSA_ENTRE_ITENS = 1

SQL_ITENS_PENDENTES = """
SELECT
    v.codigo_pedido,
    v.numero_item,
    c.cnpj_orgao,
    c.ano_compra,
    c.sequencial_compra
FROM pncp.vw_itens_saude v
JOIN pncp.contratacoes c ON c.codigo_pedido = v.codigo_pedido
WHERE v.tem_resultado = true
  AND NOT EXISTS (
      SELECT 1 FROM pncp.controle_resultados r
      WHERE r.codigo_pedido = v.codigo_pedido
        AND r.numero_item = v.numero_item
  )
ORDER BY v.codigo_pedido, v.numero_item
"""

SQL_UPSERT_RESULTADO = """
INSERT INTO pncp.resultados
    (codigo_pedido, numero_item, sequencial_resultado, registro)
VALUES
    (:codigo_pedido, :numero_item, :sequencial_resultado, cast(:registro as jsonb))
ON CONFLICT (codigo_pedido, numero_item, sequencial_resultado) DO UPDATE SET
    registro    = EXCLUDED.registro,
    extraido_em = now()
"""

SQL_UPSERT_CONTROLE_RESULTADOS = """
INSERT INTO pncp.controle_resultados (codigo_pedido, numero_item, qtd_resultados)
VALUES (:codigo_pedido, :numero_item, :qtd_resultados)
ON CONFLICT (codigo_pedido, numero_item) DO UPDATE SET
    qtd_resultados = EXCLUDED.qtd_resultados,
    extraido_em    = now()
"""


def itens_pendentes(engine):
    with engine.connect() as conexao:
        return conexao.execute(text(SQL_ITENS_PENDENTES)).all()


def montar_linha_resultado(codigo_pedido, numero_item, resultado):
    return{
        "codigo_pedido" : codigo_pedido,
        "numero_item" : numero_item,
        "sequencial_resultado" : resultado["sequencialResultado"],
        "registro" : json.dumps(resultado, ensure_ascii=False),
    }


def gravar_resultado(engine, codigo_pedido, numero_item, linhas):
    with engine.begin() as conexao:
        if linhas:
            conexao.execute(text(SQL_UPSERT_RESULTADO), linhas)
        conexao.execute(
            text(SQL_UPSERT_CONTROLE_RESULTADOS),
            {
                "codigo_pedido" : codigo_pedido,
                "numero_item" : numero_item,
                "qtd_resultados" : len(linhas),
            },
        )


def ler_argumentos():
    parser = argparse.ArgumentParser(
        description="Extrai os resultados (vencedores) dos itens de saúde do PNCP"
    )
    parser.add_argument(
        "--limite", type=int, help="processa só os N primeiros itens pendentes"
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = ler_argumentos()

    engine = criar_engine()
    executar_sql(engine, "005_criar_tabelas_resultados.sql")

    itens = itens_pendentes(engine)
    if args.limite:
        itens = itens[: args.limite]
    total = len(itens)
    logging.info(f"{total} itens pendentes com resultado")

    falhas = []
    for i, (codigo_pedido, numero_item, cnpj, ano, sequencial) in enumerate(
        itens, start=1
    ):
        try:
            resultados = buscar_resultados(cnpj, ano, sequencial, numero_item)

            linhas = []
            for resultado in resultados:
                linhas.append(
                    montar_linha_resultado(codigo_pedido, numero_item, resultado)
                )

            gravar_resultado(engine, codigo_pedido, numero_item, linhas)
            logging.info(
                f"[{i}/{total}] {codigo_pedido} item {numero_item}: "
                f"{len(linhas)} resultado(s)"
            )

        except requests.RequestException as erro:
            logging.error(
                f"[{i}/{total}] {codigo_pedido} item {numero_item}: falhou {erro}"
            )
            falhas.append((codigo_pedido, numero_item))

        time.sleep(PAUSA_ENTRE_ITENS)

    logging.info(f"Fim. Itens com falha: {falhas}")


if __name__ == "__main__":
    main()
