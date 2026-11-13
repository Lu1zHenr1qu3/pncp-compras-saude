CREATE TABLE IF NOT EXISTS pncp.itens(
  codigo_pedido TEXT NOT NULL REFERENCES pncp.contratacoes (codigo_pedido),
  numero_item   INT NOT NULL,
  registro      JSONB NOT NULL,
  estraido_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (codigo_pedido, numero_item)
);

CREATE TABLE IF NOT EXISTS pncp.controle_itens(
  codigo_pedido TEXT PRIMARY KEY REFERENCES PNCP.contratacoes (codigo_pedido),
  qtd_itens     INT NOT NULL,
  extraido_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);