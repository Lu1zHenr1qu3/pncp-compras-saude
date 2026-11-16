-- Classifica itens materiais (M) relacionados a saúde/odontologia
-- a partir da descrição do item. Serviços (S) ficam de fora.

create or replace view pncp.vw_itens_saude as
with base as (
    select
        i.codigo_pedido,
        i.numero_item,
        i.registro,
        i.extraido_em,
        ' ' || lower(extensions.unaccent(i.registro ->> 'descricao')) as desc_norm
    from pncp.itens i
    where i.registro ->> 'materialOuServico' = 'M'
),
marcada as (
    select
        b.*,

        desc_norm like any (array[
            '%odont%', '%dentari%', '%dentista%', '% dental%', '% dentais%',
            '%guta%percha%', '%fotopolimer%', '%ponta diamantada%',
            '%alta rotacao%', '%enxaguat%', '%periapical%'
        ]) as tem_odonto,

        desc_norm like any (array[
            '%medicament%', '%medicac%', '%farmac%', '%insulin%',
            '%vacina%', '%antibiot%', '%soro fisiolog%', '%fitoterap%',
            '%ampola%', '%comprimido%', '%capsula%',
            '%solucao injetavel%', '%susp oft%', '%injetavel%'
        ]) as tem_medicamento,

        desc_norm like any (array[
            '%hospitalar%', '%cirurg%', '%seringa%', '%agulha%', '%cateter%',
            '%curativo%', '%luva%', '%ortese%', '%protese%', '%opme%',
            '%oxigenio%', '%gases medicinais%', '%reagente%', '%glicem%',
            '%glicosimetr%', '%enteral%', '%fralda%geriatric%',
            '%desfibril%', '%estetoscop%', '%esfigmoman%', '%autoclave%',
            '%esteriliz%', '%teste% rapido%', '%sorolog%', '%imunocromat%',
            '%imunohemat%', '%equipo%', '%sondas%', '%sonda %',
            '%mascara% cirurg%', '%luva%procediment%', '%luva% nitril%',
            '%luva% latex%', '%luva% cirurg%',
            '%marca%passo%', '%traqueostom%', '%especulo%', '%eletrodo%',
            '%termometr%', '%inalacao%', '%bougie%', '%gaze %',
            '% uso medico%', '%uso em saude%', '%filme radiolog%'
        ]) as tem_material,

        desc_norm like any (array['%ambulanc%']) as tem_ambulancia,

        (
            desc_norm like any (array[
                '%saude%', '%medico%', '%medicina%', '%exame%', '%laboratorio%',
                '%ultrasso%', '%tomograf%', '%mamograf%', '%radiolog%',
                '%raio x%', '%raio-x%', '%raios x%', '%fisioterap%',
                '%hemodial%', '%laser%', '%paciente%', '%clinic%', '%enfermag%'
            ])
            or desc_norm ~ '\mmedicas?\M'
        ) as tem_fraco,

        desc_norm like any (array[
            '%merenda%', '%refeic%', '%marmit%', '%lanche%', '%cafe%',
            '%combustiv%', '%pneus%', '% pneu %', '%veiculo%',
            '%limpeza%', '%lavanderia%', '%residuo%', '%lixo%',
            '%informatica%', '%computador%', '%notebook%', '%impressora%',
            '%toner%', '%software%', '%escritorio%', '%expediente%',
            '%mobiliario%', '%moveis%', '%uniforme%', '%eletrodomest%',
            '%brinquedo%', '%papel higien%', '%sabonete%', '%detergente%',
            '%jardinagem%', '%reforma%', '%constru%',
            '%colageno%', '%saude de dentro%', '%pt-co%', '%saneamento%',
            '%balao laboratorio%', '%frasco laboratorio%', '%vidro ambar%'
        ]) as tem_ruido,

        desc_norm like any (array[
            '%veterinar%', '%castrac%', '%canil%', '% caes%', '% gatos%',
            '%zoonos%', '%agropec%', '%bovin%'
        ]) as tem_veto
    from base b
)
select
    codigo_pedido,
    numero_item,
    registro ->> 'descricao'                         as descricao,
    registro ->> 'materialOuServico'                 as material_ou_servico,
    (registro ->> 'quantidade')::numeric             as quantidade,
    registro ->> 'unidadeMedida'                     as unidade_medida,
    (registro ->> 'valorUnitarioEstimado')::numeric  as valor_unitario_estimado,
    (registro ->> 'valorTotal')::numeric             as valor_total_estimado,
    registro ->> 'situacaoCompraItemNome'            as situacao_item,
    (registro ->> 'temResultado')::boolean           as tem_resultado,
    registro ->> 'orcamentoSigiloso'                 as orcamento_sigiloso,
    case
        when tem_odonto      then 'odontologia'
        when tem_medicamento then 'medicamentos'
        when tem_material    then 'material_medico_hospitalar'
        when tem_ambulancia  then 'ambulancias'
        else 'saude_geral'
    end as categoria,
    case
        when tem_odonto or tem_medicamento or tem_material or tem_ambulancia
            then 'forte'
        else 'fraca'
    end as confianca,
    registro,
    extraido_em
from marcada
where not tem_veto
  and (
        tem_odonto or tem_medicamento or tem_material or tem_ambulancia
        or (tem_fraco and not tem_ruido)
  );
