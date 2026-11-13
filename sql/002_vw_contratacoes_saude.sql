create extension if not exists unaccent with schema extensions;

create or replace view pncp.vw_contratacoes_saude as
with base as (
    select
        c.*,
        ' ' || lower(extensions.unaccent(c.registro ->> 'objetoCompra')) as obj
    from pncp.contratacoes c
),
marcada as (
    select
        b.*,

        obj like any (array[
            '%odont%', '%dentari%', '%dentista%', '% dental%', '% dentais%'
        ]) as tem_odonto,

        obj like any (array[
            '%medicament%', '%medicac%', '%farmac%', '%insulin%',
            '%vacina%', '%antibiot%', '%soro fisiolog%', '%fitoterap%'
        ]) as tem_medicamento,

        obj like any (array[
            '%medico%hospitalar%', '%material hospitalar%', '%materiais hospitalares%',
            '%equipamento% hospitalar%', '%mobiliario hospitalar%',
            '%equipamento% medico%', '%materia% medico%', '%insumo% medico%', '%insumo% hospitalar%',
            '%material cirurg%', '%materiais cirurg%', '%instrument% cirurg%', '%mascara% cirurg%',
            '%luva%procediment%', '%luva% cirurg%', '%luva% nitril%', '%luva% latex%',
            '%curativo%', '%seringa%', '%agulha%', '%cateter%', '%sondas%', '%sonda %', '%equipo%',
            '%ortese%', '%protese%', '%opme%', '%oxigenio%', '%gases medicinais%',
            '%reagente%', '%glicem%', '%glicosimetr%', '%enteral%', '%fralda%geriatric%',
            '%desfibril%', '%estetoscop%', '%esfigmoman%', '%autoclave%', '%esteriliz%'
        ]) as tem_material,

        obj like any (array['%ambulanc%']) as tem_ambulancia,

        obj like any (array[
            '%saude%', '%medico%', '%medicina%', '%hospita%', '%cirurg%', '%clinic%',
            '%enfermag%', '%laborator%', '%exame%', '%paciente%', '%laser%',
            '%radiolog%', '%ultrasso%', '%tomograf%', '%mamograf%',
            '%raio x%', '%raio-x%', '%raios x%', '%fisioterap%', '%hemodial%'
        ]) as tem_fraco,

        obj like any (array[
            '%merenda%', '%generos aliment%', '%alimentacao escolar%', '%refeic%', '%marmit%',
            '%lanche%', '%coffee%', '%cafe%', '% paes%', '%padaria%', '%hortifrut%', '%carne%',
            '%agua mineral%',
            '%combustiv%', '%pneu%', '%veiculo%', '%pecas automot%', '%oficina%', '%lubrific%',
            '%obras%', '%reforma%', '%constru%', '%pavimenta%', '%ar condicionado%', '%climatiz%',
            '%eletric%', '%hidraulic%', '%serralher%', '%pintura%', '%manutencao predial%',
            '%ferrament%', '%dedetiz%', '%pragas%', '%jardin%', '%rocada%',
            '%limpeza%', '%lavanderia%', '%residuo%', '%lixo%', '%vigilancia patrimonial%',
            '%seguranca patrimonial%', '%portaria%',
            '%informatica%', '%computador%', '%notebook%', '%impressora%', '%impressao%',
            '%toner%', '%software%', '%sistema de gestao%', '%internet%', '%telefon%',
            '%expediente%', '%escritorio%', '%grafic%',
            '%mobiliario%', '%moveis%', '%uniforme%', '%eletrodomest%', '%evento%', '%seguro%',
            '%locacao de imove%', '%transporte%', '%passagens%', '%hospedagem%',
            '%publicidade%', '%brinquedo%', '%esportiv%'
        ]) as tem_ruido,

        obj like any (array[
            '%veterinar%', '%castrac%', '%canil%', '% caes%', '% gatos%',
            '%zoonos%', '%agropec%', '%bovin%'
        ]) as tem_veto
    from base b
)
select
    codigo_pedido,
    data_publicacao,
    uf,
    modalidade,
    cnpj_orgao,
    ano_compra,
    sequencial_compra,
    registro ->> 'objetoCompra'                    as objeto,
    registro -> 'orgaoEntidade' ->> 'razaoSocial'  as orgao,
    registro -> 'unidadeOrgao' ->> 'municipioNome' as municipio,
    (registro ->> 'valorTotalEstimado')::numeric   as valor_estimado,
    case
        when tem_odonto      then 'odontologia'
        when tem_medicamento then 'medicamentos'
        when tem_material    then 'material_medico_hospitalar'
        when tem_ambulancia  then 'ambulancias'
        else 'saude_geral'
    end as categoria,
    case
        when tem_odonto or tem_medicamento or tem_material or tem_ambulancia then 'forte'
        else 'fraca'
    end as confianca
from marcada
where not tem_veto
  and (
        tem_odonto or tem_medicamento or tem_material or tem_ambulancia
        or (tem_fraco and not tem_ruido)
  );