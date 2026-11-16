create table if not exists pncp.resultados (
    codigo_pedido       text not null,
    numero_item         int  not null,
    sequencial_resultado int not null,
    registro            jsonb not null,
    extraido_em         timestamptz not null default now(),
    primary key (codigo_pedido, numero_item, sequencial_resultado),
    foreign key (codigo_pedido, numero_item)
        references pncp.itens (codigo_pedido, numero_item)
);

create table if not exists pncp.controle_resultados (
    codigo_pedido  text not null,
    numero_item    int  not null,
    qtd_resultados int  not null,
    extraido_em    timestamptz not null default now(),
    primary key (codigo_pedido, numero_item),
    foreign key (codigo_pedido, numero_item)
        references pncp.itens (codigo_pedido, numero_item)
);

alter table pncp.resultados enable row level security;
alter table pncp.controle_resultados enable row level security;
