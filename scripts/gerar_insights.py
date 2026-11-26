from pathlib import Path
from dotenv import load_dotenv
import os
from urllib.parse import urlparse, unquote
import psycopg

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
u = urlparse(os.getenv("SUPABASE_DB_URL"))
conn = psycopg.connect(
    host=u.hostname,
    port=u.port or 5432,
    dbname=u.path.lstrip("/"),
    user=unquote(u.username or ""),
    password=unquote(u.password or ""),
    connect_timeout=30,
    sslmode="require",
)

sqls = {
    "visao": """
select
  count(*) as linhas,
  count(distinct municipio) as municipios,
  count(distinct cnpj_fornecedor) as fornecedores,
  round(sum(valor_total_homologado)/1e9, 2) as valor_bi,
  round(sum(economia_valor_total) filter (where economia_util)/1e6, 2) as economia_mi,
  round(avg(economia_pct_unitario) filter (where economia_util), 2) as econ_media_pct,
  round(100.0 * count(*) filter (where porte_fornecedor in ('ME','EPP')) / nullif(count(*),0), 2) as pct_linhas_me_epp
from pncp.vw_analitica;
""",
    "por_categoria": """
select categoria,
  count(*) as linhas,
  round(sum(valor_total_homologado)/1e6, 2) as valor_mi,
  round(100.0 * sum(valor_total_homologado) / sum(sum(valor_total_homologado)) over (), 1) as pct_valor,
  round(avg(economia_pct_unitario) filter (where economia_util), 1) as econ_media
from pncp.vw_analitica
group by categoria
order by valor_mi desc;
""",
    "por_porte_valor": """
select coalesce(porte_fornecedor,'Não Informado') as porte,
  count(*) as linhas,
  round(sum(valor_total_homologado)/1e6, 2) as valor_mi,
  round(100.0 * sum(valor_total_homologado) / sum(sum(valor_total_homologado)) over (), 1) as pct_valor,
  round(100.0 * count(*) / sum(count(*)) over (), 1) as pct_linhas
from pncp.vw_analitica
group by 1
order by valor_mi desc;
""",
    "top_fornecedores": """
select fornecedor, round(sum(valor_total_homologado)/1e6, 2) as valor_mi
from pncp.vw_analitica
group by fornecedor
order by sum(valor_total_homologado) desc
limit 5;
""",
    "geo": """
select
  round(sum(valor_total_homologado) filter (where municipio = 'São Paulo')/1e9, 2) as capital_bi,
  round(sum(valor_total_homologado) filter (where municipio is distinct from 'São Paulo')/1e6, 2) as interior_mi,
  round(100.0 * sum(valor_total_homologado) filter (where municipio = 'São Paulo')
        / nullif(sum(valor_total_homologado),0), 1) as pct_capital
from pncp.vw_analitica;
""",
    "top_orgaos": """
select orgao, round(sum(valor_total_homologado)/1e6, 2) as valor_mi
from pncp.vw_analitica
group by orgao
order by sum(valor_total_homologado) desc
limit 5;
""",
    "top_municipios": """
select municipio, round(sum(valor_total_homologado)/1e6, 2) as valor_mi
from pncp.vw_analitica
group by municipio
order by sum(valor_total_homologado) desc
limit 5;
""",
    "medlaser": """
select
  round(sum(valor_total_homologado) filter (where categoria='odontologia')/1e6, 2) as odonto_mi,
  round(sum(valor_total_homologado) filter (where categoria='material_medico_hospitalar')/1e6, 2) as material_mi,
  round(avg(economia_pct_unitario) filter (where economia_util and categoria='odontologia'), 1) as econ_odonto,
  round(avg(economia_pct_unitario) filter (
      where economia_util and categoria in ('odontologia','material_medico_hospitalar')
  ), 1) as econ_recorte,
  count(*) filter (where descricao ilike '%laser%') as itens_laser,
  round(sum(valor_total_homologado) filter (where descricao ilike '%laser%')/1e3, 1) as valor_laser_mil
from pncp.vw_analitica;
""",
    "odonto_fornecedores": """
select fornecedor, round(sum(valor_total_homologado)/1e6, 2) as valor_mi
from pncp.vw_analitica
where categoria = 'odontologia'
group by fornecedor
order by sum(valor_total_homologado) desc
limit 5;
""",
    "por_mes_pub": """
select to_char(date_trunc('month', data_publicacao), 'YYYY-MM') as mes,
  count(*) as linhas,
  round(sum(valor_total_homologado)/1e6, 2) as valor_mi
from pncp.vw_analitica
group by 1
order by 1;
""",
}

with conn.cursor() as cur:
    for name, q in sqls.items():
        print("====", name, "====")
        cur.execute(q)
        cols = [d.name for d in cur.description]
        print("|".join(cols))
        for row in cur.fetchall():
            print("|".join("" if v is None else str(v) for v in row))
        print()

conn.close()
