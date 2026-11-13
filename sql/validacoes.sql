/*
-- 1. Quantas compras por mês?
-- Resultado (jul–set/2026): jul 6816 | ago 7115 | set 7267

select date_trunc('month', data_publicacao)::date as mes, count(*) as qtd
from pncp.contratacoes
group by mes
order by mes;
*/

/*
-- 2. O controle bate com as compras?
-- Resultado (jul–set/2026): 21198 = 21198

-- select sum(qtd_registros) from pncp.controle_extracao;
-- select count(*) from pncp.contratacoes;

select
    (select sum(qtd_registros) from pncp.controle_extracao) as total_controle,
    (select count(*) from pncp.contratacoes) as total_compras;
*/

/*
-- 3. Dias com poucas compras (dow: 0 = domingo, 6 = sábado)
-- Resultado (jul–set/2026): só fins de semana, mais 09/07 (feriado SP), 10/07 (ponte) e 07/09 (Independência)

select dia, extract(dow from dia) as dia_semana, qtd_registros
from pncp.controle_extracao
where qtd_registros < 30
order by dia;
*/

/*
-- 4. Existe compra duplicada? (não deveria: codigo_pedido é primary key)
-- Resultado (jul–set/2026): nenhuma linha

select codigo_pedido, count(*)
from pncp.contratacoes
group by codigo_pedido
having count(*) > 1;
*/

/*
-- 5. Amostra de campos extraídos do JSON

select
    codigo_pedido,
    registro ->> 'objetoCompra'                     as objeto,
    registro -> 'unidadeOrgao' ->> 'municipioNome'  as municipio,
    (registro ->> 'valorTotalEstimado')::numeric    as valor_estimado
from pncp.contratacoes
limit 10;
*/

/*
-- 6. As 10 maiores compras
-- Atenção: as 2 primeiras parecem erro de cadastro (R$ 50 bi em próteses odontológicas
-- e R$ 11,9 bi em assistência médica). Ver alertas em docs/api.md.

select
    codigo_pedido,
    registro ->> 'objetoCompra'                     as objeto,
    registro -> 'unidadeOrgao' ->> 'municipioNome'  as municipio,
    (registro ->> 'valorTotalEstimado')::numeric    as valor_estimado
from pncp.contratacoes
order by valor_estimado desc
limit 10;
*/
