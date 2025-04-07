import os
import psycopg2

def conectar():
    return psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
        port=os.environ.get("PGPORT")
    )

def apagar_tabela_acessos():
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("DROP TABLE IF EXISTS acessos")
        con.commit()
        print("✅ Tabela 'acessos' apagada com sucesso.")
    except Exception as e:
        print("❌ Erro ao apagar a tabela:", e)
    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    apagar_tabela_acessos()
