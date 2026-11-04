create schema if not exists pncp;

CREATE TABLE IF NOT EXISTS pncp.contratacoes(
    codigo_pedido       TEXT PRIMARY KEY,
    data_publicacao     DATE NOT NULL,
    uf                  TEXT NOT NULL,
    modalidade          INT NOT NULL,
    cnpj_orgao          TEXT NOT NULL,
    ano_compra          INT NOT NULL,
    sequencial_compra   INT NOT NULL,
    registro            JSONB NOT NULL, 
    extraido_em         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pncp.controle_extracao(
    dia                 DATE NOT NULL,
    uf                  TEXT NOT NULL,
    modalidade          INT NOT NULL,
    qtd_registros       INT NOT NULL,
    extraido_em         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (dia, uf, modalidade)
);

create index if not exists idx_contratacoes_data_publicacao 
    on pncp.contratacoes (data_publicacao);