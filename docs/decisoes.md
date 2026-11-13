## Etapa 7 – Filtro de saúde (vw_contratacoes_saude)
- Texto normalizado com unaccent + lower; listas sem acento.
- Palavras fortes (medicamento, odonto, material médico-hospitalar, ambulância) sempre entram.
- Palavras fracas (saúde, médico, hospital, exame, laser...) só entram sem termo de ruído
  (alimentação, obras, limpeza, TI, escritório, veículos...).
- Veto absoluto para veterinária/zoonoses.
- Evitado '%medic%' (pega "medição"), '%dental%' sem espaço (pega "acidental"), '%sonda%' (pega "sondagem").