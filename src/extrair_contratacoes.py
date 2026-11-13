import argparse
import logging
import requests
from banco import criar_engine, executar_sql
import json
from pncp_api import buscar_dia
from sqlalchemy import text
from banco import criar_engine
from datetime import date, timedelta


SQL_UPSERT_CONTRATACAO = """
INSERT INTO pncp.contratacoes
    (codigo_pedido, data_publicacao, uf, modalidade, cnpj_orgao, ano_compra, sequencial_compra, registro)
VALUES
    (:codigo_pedido, :data_publicacao, :uf, :modalidade, :cnpj_orgao, :ano_compra, :sequencial_compra, cast(:registro as jsonb))
ON CONFLICT (codigo_pedido) DO UPDATE SET
    data_publicacao = EXCLUDED.data_publicacao,
    uf            = EXCLUDED.uf,
    modalidade    = EXCLUDED.modalidade,
    cnpj_orgao    = EXCLUDED.cnpj_orgao,
    ano_compra    = EXCLUDED.ano_compra,
    sequencial_compra = EXCLUDED.sequencial_compra,
    registro      = EXCLUDED.registro,
    extraido_em   = now()
"""

SQL_UPSERT_CONTROLE = """
INSERT INTO pncp.controle_extracao(dia, uf, modalidade, qtd_registros)
VALUES (:dia, :uf, :modalidade, :qtd_registros)
ON CONFLICT (dia, uf, modalidade) DO UPDATE SET
    qtd_registros = EXCLUDED.qtd_registros,
    extraido_em   = NOW()
"""

SQL_DIAS_FEITOS = """
SELECT dia
FROM pncp.controle_extracao
WHERE uf = :uf AND modalidade = :modalidade 
"""

def gerar_dias(inicio, fim):
    dias = []
    dia = inicio
    while dia <= fim:
        dias.append(dia)
        dia += timedelta(days=1)
    return dias

def dias_ja_extraidos(engine, uf, modalidade):
    feitos = set()
    with engine.connect() as conexao:
        resultado = conexao.execute(text(SQL_DIAS_FEITOS), {"uf": uf, "modalidade": modalidade})
        for linha in resultado:
            feitos.add(linha[0])
    return feitos


def montar_linha(registro):
    return{
        "codigo_pedido" : registro["numeroControlePNCP"],
        "data_publicacao" : registro["dataPublicacaoPncp"][:10],
        "uf" : registro["unidadeOrgao"]["ufSigla"],
        "modalidade" : registro["modalidadeId"],
        "cnpj_orgao" : registro["orgaoEntidade"]["cnpj"],
        "ano_compra" : registro["anoCompra"],
        "sequencial_compra" : registro["sequencialCompra"],
        "registro" : json.dumps(registro, ensure_ascii=False),
    }

def gravar_dia(engine, linhas, dia, uf, modalidade):
    with engine.begin() as conexao:
        if linhas:
            conexao.execute(text(SQL_UPSERT_CONTRATACAO),linhas)
        conexao.execute(text(SQL_UPSERT_CONTROLE),{
            "dia": dia,
            "uf": uf,
            "modalidade": modalidade,
            "qtd_registros": len(linhas),
        })


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Extrai contratações do PNCP para o Supabase")
    parser.add_argument("--inicio", required=True, help="data inicial AAA-MM-DD")
    parser.add_argument("--fim", required=True, help= "data final AAAA-MM-DD")
    parser.add_argument("--uf", default="SP")
    parser.add_argument("--modalidade", type=int, default=6)
    parser.add_argument("--refazer", action="store_true")
    return parser.parse_args()

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    args = ler_argumentos()
    inicio = date.fromisoformat(args.inicio)
    fim = date.fromisoformat(args.fim)
    uf = args.uf
    modalidade = args.modalidade
    refazer = args.refazer

    engine = criar_engine()
    executar_sql(engine, "001_criar_tabelas.sql")
    feitos = dias_ja_extraidos(engine, uf, modalidade)
    falhas = []

    for dia in gerar_dias(inicio, fim):
        if dia in feitos and not refazer:
            logging.info(f"{dia}: Já extraídos, pulando")
            continue

        try:
            compras = buscar_dia(dia.strftime("%Y%m%d"), uf,modalidade)

            linhas = []
            for compra in compras:
                linhas.append(montar_linha(compra))

            gravar_dia(engine, linhas, dia, uf, modalidade)
            logging.info(f"{dia}:  {len(linhas)} compra gravadas")

        except requests.RequestException as erro:
            logging.error(f"{dia}: falhou {(erro)}")
            falhas.append(dia)
    logging.info(f"Fim. Dias com falha: {falhas}")

if __name__ == "__main__":
    main()