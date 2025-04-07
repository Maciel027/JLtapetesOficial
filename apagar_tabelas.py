import psycopg2
import os

# conexao com o banco de daods do raiway
conn = psycopg2.connect(
    host=os.environ.get("PGHOST"),
    database=os.environ.get("PGDATABASE"),
    user=os.environ.get("PGUSER"),
    password=os.environ.get("PGPASSWORD"),
    port=os.environ.get("PGPORT")
)

tabelas_para_apagar = ['cliques', 'acessos']

try:
    cur = conn.cursor()
    for tabela in tabelas_para_apagar:
        cur.execute(f"DROP TABLE IF EXISTS {tabela} CASCADE;")
        print(f"Tabela {tabela} apagada com sucesso.")
    conn.commit()
except Exception as e:
    print(f"Erro ao apagar tabelas: {e}")
finally:
    cur.close()
    conn.close()