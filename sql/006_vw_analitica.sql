-- Visão pronta para o Power BI: um resultado por linha,
-- com dimensões da compra/item e métricas de preço.

create or replace view pncp.vw_analitica as
select
    -- chaves
    i.codigo_pedido,
    i.numero_item,
    r.sequencial_resultado,

    -- compra
    c.data_publicacao,
    c.uf,
    c.modalidade,
    c.registro -> 'orgaoEntidade' ->> 'razaoSocial'       as orgao,
    c.registro -> 'orgaoEntidade' ->> 'cnpj'               as cnpj_orgao,
    c.registro -> 'orgaoEntidade' ->> 'esferaId'           as esfera,
    c.registro -> 'unidadeOrgao' ->> 'municipioNome'      as municipio,
    c.registro -> 'unidadeOrgao' ->> 'codigoIbge'         as codigo_ibge,
    c.registro -> 'unidadeOrgao' ->> 'nomeUnidade'        as unidade,
    c.registro ->> 'objetoCompra'                         as objeto_compra,
    c.registro ->> 'situacaoCompraNome'                   as situacao_compra,
    (c.registro ->> 'srp')::boolean                       as registro_precos,

    -- item (classificado)
    i.descricao,
    i.categoria,
    i.confianca,
    i.quantidade,
    nullif(trim(i.unidade_medida), '')                    as unidade_medida,
    i.valor_unitario_estimado,
    i.valor_total_estimado,
    i.situacao_item,
    (i.orcamento_sigiloso)::boolean                       as orcamento_sigiloso,

    -- resultado (vencedor)
    r.registro ->> 'niFornecedor'                         as cnpj_fornecedor,
    r.registro ->> 'nomeRazaoSocialFornecedor'            as fornecedor,
    r.registro ->> 'tipoPessoa'                           as tipo_pessoa,
    r.registro ->> 'porteFornecedorNome'                  as porte_fornecedor,
    r.registro ->> 'naturezaJuridicaNome'                 as natureza_juridica,
    (r.registro ->> 'quantidadeHomologada')::numeric      as quantidade_homologada,
    (r.registro ->> 'valorUnitarioHomologado')::numeric   as valor_unitario_homologado,
    (r.registro ->> 'valorTotalHomologado')::numeric      as valor_total_homologado,
    (r.registro ->> 'dataResultado')::date                 as data_resultado,
    r.registro ->> 'situacaoCompraItemResultadoNome'      as situacao_resultado,

    -- métricas derivadas
    -- Homologado 0 e estimado 0/sigiloso não entram no % (evita "100% economia" falso
    -- e divisão por zero). Outliers extremos (kit vs unidade) ficam em economia_util = false.
    case
        when coalesce(i.valor_unitario_estimado, 0) > 0
             and coalesce((r.registro ->> 'valorUnitarioHomologado')::numeric, 0) > 0
        then round(
            (
                1 - (r.registro ->> 'valorUnitarioHomologado')::numeric
                    / i.valor_unitario_estimado
            ) * 100,
            2
        )
    end as economia_pct_unitario,

    case
        when coalesce(i.valor_total_estimado, 0) > 0
             and coalesce((r.registro ->> 'valorTotalHomologado')::numeric, 0) > 0
        then i.valor_total_estimado
             - (r.registro ->> 'valorTotalHomologado')::numeric
    end as economia_valor_total,

    case
        when coalesce(i.valor_unitario_estimado, 0) > 0
             and coalesce((r.registro ->> 'valorUnitarioHomologado')::numeric, 0) > 0
             and abs(
                 1 - (r.registro ->> 'valorUnitarioHomologado')::numeric
                     / i.valor_unitario_estimado
             ) <= 1  -- entre -100% e +100%
        then true
        else false
    end as economia_util

from pncp.resultados r
join pncp.vw_itens_saude i
  on i.codigo_pedido = r.codigo_pedido
 and i.numero_item = r.numero_item
join pncp.contratacoes c
  on c.codigo_pedido = r.codigo_pedido;
