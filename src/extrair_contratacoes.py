import json
from pncp_api import buscar_dia
from sqlalchemy import text
from banco import criar_engine

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


if __name__ == "__main__":
    engine = criar_engine()
    compras = buscar_dia("20260701", "SP", 6)

    linhas = []

    for compra in compras:
        linhas.append(montar_linha(compra))

    gravar_dia(engine, linhas, "20260701", "SP", 6)
    print("Gravadas:", len(linhas))



