# Decisões do projeto

## Etapa 7 – Filtro de saúde (`pncp.vw_contratacoes_saude`)

Arquivo: `sql/002_vw_contratacoes_saude.sql`.

### Regra geral
- Texto normalizado com `unaccent` + `lower`; listas escritas sem acento.
- Prefixo `' '` no texto normalizado para padrões com espaço no começo (ex.: `'% dental%'`) funcionarem no início da frase.
- Duas faixas de confiança:
  - **Forte**: medicamento, odonto, material médico-hospitalar, ambulância → sempre entram.
  - **Fraca**: saúde, médico, hospital, exame, laser etc. → só entram se **não** houver termo de ruído.
- Veto absoluto para veterinária/zoonoses (`veterinar`, `castrac`, `canil`...).
- Serviços de saúde (consultas, enfermagem, exames por imagem) podem ficar na faixa fraca; a separação produto × serviço fica para o nível de itens (`materialOuServico`).

### Armadilhas de substring
| Padrão ruim | Por quê | Correção |
|---|---|---|
| `%medic%` | Pega "medição" | Usar `%medicament%`, `%medicac%`, `%farmac%` |
| `%dental%` sem espaço | Pega "acidental"/"ocidental" | `'% dental%'`, `'% dentais%'` |
| `%sonda%` | Pega "sondagem" de solo | `'%sondas%'`, `'%sonda %'` |
| `%jardin%` | Pega "Jardinópolis" | `%jardinagem%` |
| `%grafic%` | Pega "cromatográfico" | `'% grafic%'` (com espaço) |
| `%pneu%` | Pega "pneumologia" | `%pneus%`, `% pneu %` |
| `%portaria%` | Pega "Portaria GM/MS" | `%servicos de portaria%` |
| `%lubrific%` | Pega "gel lubrificante" de ultrassom | `%oleo%lubrific%` |
| `%medica%` / `%médic%` soltos | Ambíguo demais | Regex de palavra inteira: `obj ~ '\mmedicas?\M'` |

### Validação (amostra)
- Contagem inicial por categoria (antes do ajuste fino): odontologia 380, medicamentos 1720, material 1423, ambulâncias 65, saúde_geral/fraca 1619.
- Amostra das fracas misturava produto bom (BIPAP, ultrassom, testes lab) com ruído (bebedouro, vidraçaria, calhas, vigilância patrimonial, software).
- Compras excluídas com razão na amostra de "fora": pneus, marmitex, eletrodomésticos, combustível, medicamentos veterinários.
- Aceitável perder compra mista tipo "equipamentos e mobiliários para o PA" por causa de `%mobiliario%`: na Etapa 8 o item recupera o que for produto de saúde.

---

## Etapa 8 – Extração de itens

Arquivos: `sql/003_criar_tabelas_itens.sql`, `src/pncp_api.py` (`buscar_itens`), `src/extrair_itens.py`.

### Decisões de modelagem
- Tabelas `pncp.itens` e `pncp.controle_itens`.
- Controle é obrigatório: compra com 0 itens não deixa linha em `itens`; sem controle o script repetiria a chamada para sempre.
- RLS ligado nas tabelas do schema `pncp` (clientes `anon`/`authenticated` não leem; o Python usa a connection string direta).
- Upsert por `(codigo_pedido, numero_item)`.
- `--limite` no script para teste; pausa de 1 s entre compras; retomada automática pelas pendentes da view.

### API (nível 2)
- Base diferente do nível 1: `https://pncp.gov.br/api/pncp/v1/...` (não `/api/consulta/v1/`).
- Resposta é **lista direta**, sem `data` / `totalPaginas`.
- Parada: página com menos itens que `tamanhoPagina` (usamos 500) ou 204.
- Não existe endpoint de resultados por compra (`.../resultados` → 404; `.../itens/resultados` → 400). Resultados só item a item → Etapa 9.

### Resultado da carga
- Extração das compras da `vw_contratacoes_saude` concluída.
- Diagnóstico na tabela `pncp.itens` (após carga completa):

| total  | materiais (M) | serviços (S) | materiais com `temResultado` |
| ------ | ------------- | ------------ | ---------------------------- |
| 131711 | 125037        | 6674         | 58197                        |

- ~95% dos itens são material. Serviços ficam de fora na classificação de produto.
- 58.197 materiais com resultado são o teto bruto antes do filtro por descrição do item.

### Exceção registrada
- Compra `46634176000104-1-000022/2026`: API de itens retorna **404** (compra/itens indisponíveis). Marcada em `controle_itens` com `qtd_itens = 0` para não voltar como pendente. Não insistir.

### Próximo (Etapa 9)
1. Classificar itens pela `descricao` + `materialOuServico = 'M'` → view `pncp.vw_itens_saude`.
2. Buscar resultados só dos itens de saúde com `temResultado = true`, para cortar volume de chamadas.
