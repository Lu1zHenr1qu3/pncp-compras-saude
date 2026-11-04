# API do PNCP — anotações

Tudo o que foi descoberto testando a API de consulta do PNCP (Portal Nacional de Contratações Públicas).

- **Documentação (Swagger):** https://pncp.gov.br/api/consulta/swagger-ui/index.html
- **Atenção:** `https://pncp.gov.br/pncp-consulta/v3/api-docs` devolve a *especificação* da API (o manual em JSON), não dados.

## Nível 1 — Contratações publicadas num período

**Endpoint:** `GET https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`

### Parâmetros

| Parâmetro | Formato | Exemplo | Observação |
|---|---|---|---|
| `dataInicial` | `AAAAMMDD` (texto) | `20260701` | |
| `dataFinal` | `AAAAMMDD` (texto) | `20260701` | Igual à inicial para buscar um dia só |
| `codigoModalidadeContratacao` | número | `6` | 6 = Pregão - Eletrônico |
| `uf` | sigla | `SP` | |
| `pagina` | número | `1` | Começa em 1 |
| `tamanhoPagina` | número | `50` | Padrão **10** se não for informado. Máximo **50** |

> [!warning] Os nomes dos parâmetros diferenciam maiúsculas de minúsculas
> `tamanhopagina` (com p minúsculo) é **ignorado sem erro**: a API usa o padrão de 10 por página. O mesmo vale para `datainicial`, `datafinal` etc. Sempre copiar os nomes do Swagger.

### Estrutura da resposta (status 200)

| Chave | Tipo | O que é |
|---|---|---|
| `data` | lista de dicionários | As compras desta página |
| `totalRegistros` | número | Total de compras no período (todas as páginas) |
| `totalPaginas` | número | Quantas páginas existem |
| `numeroPagina` | número | Página atual |
| `paginasRestantes` | número | Páginas que faltam depois desta |
| `empty` | booleano | Se a página veio vazia |

### Campos importantes de cada compra (`data[i]`)

| Campo | Caminho no JSON | Para quê |
|---|---|---|
| Identificador único | `numeroControlePNCP` | Chave primária. Formato `CNPJ-1-SEQUENCIAL/ANO` |
| CNPJ do órgão | `orgaoEntidade` → `cnpj` | Chegar no nível 2. **Texto**, não número |
| Razão social do órgão | `orgaoEntidade` → `razaoSocial` | Dimensão órgão |
| Ano da compra | `anoCompra` | Chegar no nível 2 (ver alerta abaixo) |
| Sequencial da compra | `sequencialCompra` | Chegar no nível 2 |
| Objeto | `objetoCompra` | Filtro de saúde/odontologia |
| Município | `unidadeOrgao` → `municipioNome` | Dimensão município |
| Código IBGE | `unidadeOrgao` → `codigoIbge` | Chave do município. **Texto** |
| UF | `unidadeOrgao` → `ufSigla` | |
| Nome da unidade | `unidadeOrgao` → `nomeUnidade` | Ex.: hospital, secretaria, faculdade |
| Valor estimado | `valorTotalEstimado` | Pergunta 2 (economia) |
| Valor homologado | `valorTotalHomologado` | Pergunta 2 (economia) |
| Data de publicação | `dataPublicacaoPncp` | Data usada no filtro da consulta |
| Abertura das propostas | `dataAberturaProposta` | Pergunta 4 (prazo) |
| Encerramento das propostas | `dataEncerramentoProposta` | Pergunta 4 (prazo) |
| Situação | `situacaoCompraNome` | Ex.: Divulgada no PNCP, Anulada, Revogada |
| Modalidade | `modalidadeId` / `modalidadeNome` | |
| Registro de preços | `srp` | `True`/`False` |
| Esfera | `orgaoEntidade` → `esferaId` | F = federal, E = estadual, M = municipal |

## Comportamentos descobertos

| Situação | O que acontece | Como tratar no código |
|---|---|---|
| Dia **sem** publicações (testado com `20261225`) | Status **204**, corpo **vazio** | Conferir o status **antes** do `.json()`. Com 204, o `.json()` quebra com `JSONDecodeError` |
| Página além da última (`pagina=999`) | Status **204**, corpo vazio | Mesmo tratamento do dia vazio |
| Domingo (testado com `20260705`) | **Teve 1 publicação** em SP | Não pular fins de semana: percorrer todos os dias |
| Sem `tamanhoPagina` | 10 registros por página | Sempre mandar `tamanhoPagina=50` |
| `tamanhoPagina` fora de 10 a 50 | Status **400**. Acima de 50: `"Tamanho de página inválido"`. Abaixo de 10: `"must be greater than or equal to 10"` | Usar 50 |
| Período maior que 365 dias | Status **422**: `"Período inicial e final maior que 365 dias."` | Buscar dia a dia (o projeto já faz isso) |
| Tempo de resposta | De **menos de 1 s** (um dia) até **~8 s** (período de 1 ano) | `timeout` com folga (30 s ou mais). `timeout=3` é pouco |
| **Muitas chamadas seguidas** | Status **429** depois de ~8 chamadas com 1 s de pausa. O corpo é uma **página HTML**, não JSON. Não vem cabeçalho `Retry-After` | Pausa de **3 a 4 s** entre chamadas (com 4 s, 11 chamadas seguidas passaram sem bloqueio) e `Retry` com *backoff* incluindo o 429 |

### Mensagens de erro (para o `raise_for_status` e o log)

| Status | Quando | Mensagem (`r.text`) |
|---|---|---|
| 400 | Falta parâmetro obrigatório (ex.: sem `codigoModalidadeContratacao`) | `Required request parameter 'codigoModalidadeContratacao' ... is not present` |
| 400 | `pagina=0` | `must be greater than or equal to 1` |
| 400 | `tamanhoPagina` inválido | Ver tabela acima |
| 422 | Data fora do formato (ex.: `2026-07-01`) | `Data Inicial inválida, deve estar no formato yyyyMMdd.` |
| 422 | Data inicial depois da final | `Data Inicial deve ser anterior ou igual à Data Final` |
| 422 | Período maior que 365 dias | `Período inicial e final maior que 365 dias.` |
| 429 | Limite de requisições | Página HTML "Limite de requisições excedido" |

> [!note] Erros 400 e 422 são culpa do código, não da API
> Não adianta tentar de novo: o `Retry` deve repetir só 429 e 5xx. Um 400/422 tem que parar o script e mostrar a mensagem.

## Nível 2 — Itens de uma compra

**Endpoint:** `GET https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{anoCompra}/{sequencialCompra}/itens`

- A resposta é **uma lista direto** (não tem `data`, `totalPaginas` etc. como no nível 1).
- **É paginado, e o padrão é 10.** Sem parâmetros, a compra de instrumentais odontológicos devolveu só **10 de 37 itens**. Sem `pagina` e `tamanhoPagina`, **perde item sem dar erro**.
- Parâmetros: `pagina` e `tamanhoPagina`. Testado: `tamanhoPagina=50` e `tamanhoPagina=500` trouxeram os 37 de uma vez.
- Página além do fim: status **200** com lista **vazia** `[]` (diferente do nível 1, que devolve 204).
- **Total de itens:** `GET .../itens/quantidade` devolve só um número (ex.: `37`).

**Como percorrer:** `while` com `pagina` subindo até vir lista vazia, **ou** consultar `/quantidade` antes e calcular quantas páginas pedir.

### Campos importantes de cada item

| Campo | Para quê |
|---|---|
| `numeroItem` | Chega no nível 3. Chave do item junto com o `numeroControlePNCP` da compra |
| `descricao` | Ex.: "Alavanca Odontológica", "Fórceps Odontológico". Melhor que o `objetoCompra` para o filtro |
| `materialOuServico` / `materialOuServicoNome` | M = Material, S = Serviço |
| `quantidade`, `unidadeMedida` | `unidadeMedida` vem com espaços sobrando (`"Unidade  "`) |
| `valorUnitarioEstimado`, `valorTotal` | Valor estimado do item |
| `orcamentoSigiloso` | **Explica o `valorTotalEstimado` 0.0 do nível 1** (ver alerta 2) |
| `temResultado` | `True` = vale chamar o nível 3 |
| `situacaoCompraItemNome` | Ex.: Homologado, Em andamento |
| `tipoBeneficioNome` | Ex.: "Participação exclusiva para ME/EPP" |
| `criterioJulgamentoNome` | Ex.: Menor preço |
| `ncmNbsCodigo` | Código fiscal do produto (pode ajudar a classificar) |

## Nível 3 — Resultados (vencedor) de um item

**Endpoint:** `GET https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{anoCompra}/{sequencialCompra}/itens/{numeroItem}/resultados`

- A resposta é **uma lista** (normalmente com 1 resultado; pode ter mais, ex.: registro de preços com vários fornecedores).
- Item **sem** resultado (`temResultado: False`): status **204**, corpo vazio.

### Campos importantes de cada resultado

| Campo | Para quê |
|---|---|
| `niFornecedor` | CNPJ (ou **CPF**, se pessoa física/MEI) do vencedor. Chave da dimensão fornecedor |
| `tipoPessoa` | PJ / PF |
| `nomeRazaoSocialFornecedor` | Nome do vencedor. **Mascarar CPF** quando aparecer |
| `porteFornecedorId` / `porteFornecedorNome` | Ex.: 1 = ME. Pergunta 3 |
| `naturezaJuridicaNome` | Ex.: Sociedade Empresária Limitada |
| `quantidadeHomologada` | |
| `valorUnitarioHomologado`, `valorTotalHomologado` | Pergunta 2 (economia) |
| `percentualDesconto` | **Não confiável** (ver alerta 7) |
| `dataResultado` | Pergunta 4 (prazo) |
| `situacaoCompraItemResultadoNome` | Ex.: Informado |
| `dataCancelamento`, `motivoCancelamento` | Resultado cancelado |
| `sequencialResultado` | Chave do resultado junto com compra + item |
| `numeroControlePNCPCompra` | Liga o resultado de volta à compra |

### Exemplo seguido pelos três níveis

1. **Compra:** "Instrumentais de Uso Odontológico." — Faculdade de Odontologia de Ribeirão Preto (USP), `63025530000104-1-002342/2026`.
2. **Itens:** 37 (alavanca, fórceps, seringa e pinça odontológicas, cabo de bisturi, porta-agulha, tesoura...), todos `Homologado` e com `temResultado: True`. Participação exclusiva para ME/EPP.
3. **Resultado do item 1** (Alavanca Odontológica): estimado R$ 58,66, homologado **R$ 46,96** (−19,9%), vencedor KENYA CARRILO - MATERIAIS, VESTUARIO, EQUIPAMENTOS E PROMOCAO DE VENDAS LTDA, porte **ME**, resultado em 02/09/2026.

## Volume

- **01/07/2026 (quarta-feira), SP, pregão eletrônico:** 274 compras, 6 páginas de 50.
- **12 meses (01/07/2025 a 30/06/2026), SP, pregão eletrônico:** 78.767 compras.
- **Estimativa para 3 meses:** ~92 dias × ~6 páginas = **~550 chamadas** no nível 1. Com 3 a 4 s de pausa, **~30 a 40 minutos**.

> [!warning] Os níveis 2 e 3 são muito mais pesados
> Cada compra precisa de 1 chamada de itens + 1 chamada de resultados **por item**. A compra odontológica do exemplo sozinha = 1 + 37 = **38 chamadas**. Com 4 s de pausa, ~2,5 minutos para uma compra só.
> Se o filtro de saúde deixar, por exemplo, 3 mil compras com 10 itens em média, são ~33 mil chamadas, ou **~37 horas**. Por isso:
> 1. aplicar o filtro de saúde/odontologia **antes** dos níveis 2 e 3;
> 2. chamar resultados só quando `temResultado` for `True`;
> 3. começar com um período curto (1 mês) ou só odontologia, e medir o tempo real antes de ampliar;
> 4. a carga incremental (poder parar e continuar) é obrigatória.

## Alertas de qualidade dos dados

1. **`anoCompra` pode ser diferente do ano da publicação.**
   - Sorocaba: publicada em 07/2026, `anoCompra` 2025 (`46634044000174-1-000569/2025`).
   - DRS-VII Campinas: publicada em 07/2026, `anoCompra` 2027 (`46374500000194-1-000009/2027`).
   - **Regra:** para montar a URL do nível 2, usar sempre o `anoCompra` do registro, nunca o ano da data.
2. **`valorTotalEstimado` igual a `0.0` = orçamento sigiloso (confirmado).** No microcateter do IAMSPE (`60747318000162-1-000862/2026`), o item tem `orcamentoSigiloso: true` e `valorUnitarioEstimado: 0`. A lei permite esconder o valor estimado até o fim da disputa. **Consequência:** essas compras **não entram** no cálculo de economia (estimado vs homologado), senão dá divisão por zero ou desconto falso. Contar quantas são e citar como limitação.
3. **`valorTotalHomologado` igual a `None`:** a compra ainda não tem resultado, ou ele não foi informado.
4. **Valores unitários no lugar do total:** combustível do SEMAE Piracicaba com estimado **R$ 5,70** e homologado **R$ 1,89** (preço por litro). Outlier que distorce somas e médias.
5. **Compras anuladas e revogadas** vêm na mesma consulta (`situacaoCompraNome`). Decidir se entram na análise de gasto.
6. **Textos com quebra de linha (`\n`)** e espaços sobrando no `objetoCompra`, na `informacaoComplementar` e na `unidadeMedida` dos itens. Limpar com `strip` antes de filtrar.
7. **`percentualDesconto` do resultado não é confiável.** No item 1 da compra odontológica, o estimado foi R$ 58,66 e o homologado R$ 46,96 (19,9% menor), mas o campo veio `0.0`. **Calcular o desconto a partir dos valores**, não usar o campo.
8. **Viés na pergunta 3 (fatia de ME/EPP):** há compras com `tipoBeneficioNome` "Participação exclusiva para ME/EPP". Nelas, só ME/EPP podem vencer. Separar compras exclusivas das de ampla concorrência antes de concluir que "ME/EPP vencem mais".

## Pistas para o filtro de saúde/odontologia (Etapa 7)

**Exemplos que devem entrar** (todos de 01/07/2026):
- "Instrumentais de Uso Odontológico." — Faculdade de Odontologia de Ribeirão Preto (USP)
- "Microcateter p/ angiografia...", "Cateter para cpre...", "Próteses endovascular..." — IAMSPE
- "Curativos / esponja e reservatórios", "Kit pinças para curativos"
- "REGISTRO DE PRECOS DE MEDICAMENTOS...", "MEDICAMENTOS JUDICIAL AMPLA COTA", "Etilefrina cloridrato... ampola"
- "Aquisição de material permanente de saúde" — EsPCEx
- "Cadeiras de rodas... pacientes assistidos pela rede municipal de saúde"
- "Insumos CME... lavadora termodesinfectora"
- "Câmara fria... medicamentos termolábeis"

**Falsos positivos já vistos:**
- "Aquisição de gêneros alimentícios para... Secretaria de Saúde" (Adamantina) — contém "saúde", mas é comida.
- "Aquisição de Materiais de escritório e copo descartável" — publicada pela Secretaria de Estado da **Saúde**. Filtrar pelo **órgão** traria compras que não são de saúde.

**Palavras candidatas:** odonto, medicamento, cateter, curativo, prótese, hospitalar, cirúrgico, ampola, insumo, material de saúde.

**Dica do nível 2:** a `descricao` de cada item é bem mais específica que o `objetoCompra` (ex.: "Fórceps Odontológico", "Seringa Odontológica"). Dá para filtrar no nível 1 de forma mais larga e refinar pelos itens depois.

## Pendente

- [x] `tamanhoPagina` acima de 50 → 400 (ver Comportamentos)
- [x] Mensagens de erro 400, 422 e 429 → ver tabela de mensagens
- [x] Período máximo → 365 dias
- [x] Nível 2: paginado (padrão 10), lista direto, campo `temResultado`
- [x] Nível 3: campos do fornecedor, porte e valores homologados
- [x] Seguir uma compra pelos três níveis (instrumentais odontológicos da USP de Ribeirão Preto)
- [ ] Erro 500 (servidor): não deu para provocar. Tratar junto com o 429 no `Retry`
- [ ] Encontrar um resultado com fornecedor **pessoa física/MEI** (`tipoPessoa` PF) para ver o formato do CPF no nome e no `niFornecedor`
- [ ] Ver um item com **mais de um resultado** (registro de preços) para definir a chave do resultado
