
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3, os
import os


app = Flask(__name__)
app.secret_key = 'segredo'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def conectar():
    return sqlite3.connect('loja.db')

@app.route('/')
def index():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT * FROM produtos")
    produtos = cur.fetchall()
    con.close()
    return render_template('index.html', produtos=produtos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT * FROM admin WHERE usuario=? AND senha=?", (usuario, senha))
        admin = cur.fetchone()
        con.close()
        if admin:
            session['admin'] = True
            return redirect(url_for('painel'))
        else:
            return "Login inválido"
    return render_template('login.html')

@app.route('/painel')
def painel():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('painel.html')

@app.route('/editar')
def editar_loja():
    if not session.get('admin'):
        return redirect(url_for('login'))
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT * FROM produtos")
    produtos = cur.fetchall()
    con.close()
    return render_template('editar.html', produtos=produtos)

@app.route('/editar-produto/<int:id>', methods=['POST'])
def editar_produto(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    nome = request.form['nome']
    preco = request.form['preco']
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE produtos SET nome=?, preco=? WHERE id=?", (nome, preco, id))
    con.commit()
    con.close()
    return redirect(url_for('editar_loja'))

@app.route('/excluir-produto/<int:id>')
def excluir_produto(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM produtos WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect(url_for('editar_loja'))


@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if not session.get('admin'):
        return redirect(url_for('login'))

    nome = request.form['nome']
    preco = request.form['preco']
    imagem = request.files['imagem']
    if imagem:
        nome_arquivo = secure_filename(imagem.filename)
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
        imagem.save(caminho)
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO produtos (nome, preco, imagem) VALUES (?, ?, ?)",
                    (nome, preco, caminho))
        con.commit()
        con.close()
    return redirect(url_for('painel'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


def migrar_sqlite_para_postgres():
    import sqlite3
    import psycopg2

    # Conectar ao SQLite local
    sqlite_conn = sqlite3.connect('loja.db')
    sqlite_cur = sqlite_conn.cursor()

    # Ler produtos
    sqlite_cur.execute("SELECT nome, preco, imagem FROM produtos")
    produtos = sqlite_cur.fetchall()
    sqlite_conn.close()

    # Conectar ao PostgreSQL do Railway
    pg_conn = conectar()
    pg_cur = pg_conn.cursor()

    inseridos = 0
    for p in produtos:
        nome, preco, imagem = p
        # Evita duplicados (você pode mudar isso)
        pg_cur.execute("SELECT * FROM produtos WHERE nome = %s AND preco = %s AND imagem = %s", (nome, preco, imagem))
        if not pg_cur.fetchone():
            pg_cur.execute("INSERT INTO produtos (nome, preco, imagem) VALUES (%s, %s, %s)", (nome, preco, imagem))
            inseridos += 1

    pg_conn.commit()
    pg_conn.close()

    print(f"{inseridos} produtos migrados com sucesso do SQLite para PostgreSQL.")


if __name__ == '__main__':
    migrar_sqlite_para_postgres()  # ← Executa a migração!
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
