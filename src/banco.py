from pathlib import Path
import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).parent.parent

def criar_engine():
    load_dotenv(RAIZ / ".env")
    url = os.getenv("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("Não achei o SUPABASE_DB_URL no env.")
    return create_engine(url)

def executar_sql(engine, nome_arquivo):
    caminho = RAIZ / "sql" / nome_arquivo
    texto = caminho.read_text(encoding = "utf-8")

    linhas = []
    for linha in texto.splitlines():
        if not linha.strip().startswith("--"):
            linhas.append(linha)
    texto_limpo = "\n".join(linhas)

    comandos = texto_limpo.split(";")

    with engine.begin() as conexao:
        for comando in comandos:
            if comando.strip():
                conexao.execute(text(comando))

if __name__ == "__main__":
    engine = criar_engine()
    executar_sql(engine, "001_criar_tabelas.sql")
    print("SQL executado com sucesso")