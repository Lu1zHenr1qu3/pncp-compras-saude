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

---

## Etapa 9 – Classificação dos itens (`pncp.vw_itens_saude`)

Arquivo: `sql/004_vw_itens_saude.sql`.

### Contagem de palavras nos materiais (descrição do item)
Top: `odont` 5257, `cirurg` 4571, `agulha` 4304, `farmac` 3839, `saude` 2759,
`seringa` 2518, `luva` 1844, `cateter` 1833, `hospitalar` 1447, `exame` 1340.
Cauda útil: insulina, medicamento, reagente, oxigênio, prótese, dental, ultrassom,
laboratório, soro fisiológico, glicemia, laser, órtese, vacina, ambulância.

### Decisões
- Só `materialOuServico = 'M'`. Serviços ficam de fora neste recorte de produto.
- Mesma lógica forte/fraca/veto da view de contratações, aplicada em `descricao`.
- Coluna `tem_resultado` exposta para a extração do nível 3 chamar só quem já tem vencedor.
- Contagens do `unnest` não são exclusivas (um item entra em várias palavras); a view
  deduplica naturalmente porque cada item aparece uma vez.

### Validação (antes do ajuste fino de apresentação)
| categoria | confiança | itens | com resultado |
|---|---|---|---|
| ambulâncias | forte | 37 | 13 |
| material médico-hospitalar | forte | 24.207 | 11.864 |
| medicamentos | forte | 18.745 | 9.121 |
| odontologia | forte | 8.427 | 4.500 |
| saúde geral | fraca | 3.152 | 1.411 |
| **total** | | **54.568** | **26.909** |

Amostra das fracas: maioria produto/exame de saúde. Lixo pontual (colágeno cosmético,
kit Pt-Co de saneamento, vidraria genérica). Remédios citados só pelo nome (ex.: dexametasona)
e alguns itens odontológicos sem a raiz `odont` caíam na faixa fraca → promovidos no ajuste
(`ampola`, `comprimido`, `guta-percha`, `marca-passo`, `gaze`, etc.).

Teto da Etapa 9 (nível 3): ~27 mil chamadas se buscar todos com `tem_resultado`.
Com 1 s de pausa ≈ 7–8 h; script incremental com `--limite` para teste.

### Resultado da carga de resultados
- Extração concluída. Falha transitória `46179941000135-1-000430/2026` item `329` recuperada na retentativa.
- Totais finais: **26.916** itens no controle, **29.080** resultados gravados
  (itens com mais de um resultado, típico de registro de preços).

---

## Etapa 10 – View analítica (`pncp.vw_analitica`)

Arquivo: `sql/006_vw_analitica.sql`.

- Uma linha = um resultado (vencedor) de um item de saúde.
- Junta `resultados` + `vw_itens_saude` + `contratacoes`.
- Expõe órgão, município, categoria, fornecedor/porte e preços.
- `economia_pct_unitario` e `economia_valor_total` calculados no SQL
  (não usar `percentualDesconto` da API — é pouco confiável).
- Economia só quando **estimado > 0 e homologado > 0** (sigiloso e homologado 0 ficam `null`).
- `economia_util`: true só se o % unitário estiver entre −100% e +100%. Fora disso
  costuma ser erro de unidade (preço do kit vs da unidade) ou outlier; no Power BI
  filtrar `economia_util = true` antes de média/mediana.
- Validação inicial sem esse filtro: médias absurdas (−12k% em material, −333k% em
  saúde geral). Odontologia (~37%) e ambulâncias (~19%) já pareciam plausíveis.
