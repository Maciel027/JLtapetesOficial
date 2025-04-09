import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from datetime import datetime

# Configuração do Cloudinary com variáveis de ambiente
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET")
)

app = Flask(__name__)
app.secret_key = 'segredo'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def conectar():
    return psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
        port=os.environ.get("PGPORT")
    )

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
        cur.execute("SELECT * FROM admin WHERE usuario=%s AND senha=%s", (usuario, senha))
        admin = cur.fetchone()
        con.close()
        if admin:
            session['admin'] = True
            return redirect(url_for('painel'))
        else:
            return "Login inválido"
    return render_template('login.html')

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

@app.route('/ajustar-tabela-acessos')
def ajustar_tabela():
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("ALTER TABLE acessos ADD COLUMN ip VARCHAR(50);")
        con.commit()
        return "Coluna 'ip' adicionada com sucesso!"
    except Exception as e:
        return f"Erro: {e}"
    finally:
        con.close()

@app.route('/editar-produto/<int:id>', methods=['POST'])
def editar_produto(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    nome = request.form['nome']
    preco = request.form['preco']
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE produtos SET nome=%s, preco=%s WHERE id=%s", (nome, preco, id))
    con.commit()
    con.close()
    return redirect(url_for('editar_loja'))

@app.route('/excluir-produto/<int:id>')
def excluir_produto(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM produtos WHERE id=%s", (id,))
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
        upload_result = cloudinary.uploader.upload(imagem)
        imagem_url = upload_result['secure_url']
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO produtos (nome, preco, imagem) VALUES (%s, %s, %s)", (nome, preco, imagem_url))
        con.commit()
        con.close()
    return redirect(url_for('painel'))

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# DESATIVADO TEMPORARIAMENTE para evitar erro com tabelas inexistentes
# @app.before_request
# def registrar_acesso():
#     if request.endpoint not in ['static', 'registrar_clique']:
#         ip = request.remote_addr
#         con = conectar()
#         cur = con.cursor()
#         cur.execute("INSERT INTO acessos (ip) VALUES (%s)", (ip,))
#         con.commit()
#         con.close()

# @app.route('/registrar-clique/<int:id>')
# def registrar_clique(id):
#     con = conectar()
#     cur = con.cursor()
#     cur.execute("INSERT INTO cliques (produto_id) VALUES (%s)", (id,))
#     con.commit()
#     con.close()
#     return redirect("https://wa.me/5515998366823")

@app.route('/painel')
def painel():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('painel.html')

def apagar_tabela_acessos_uma_vez():
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS cliques")
        con.commit()
        print("✅ Tabela 'acessos' foi apagada automaticamente no startup.")
    except Exception as e:
        print(f"❌ Erro ao apagar a tabela acessos: {e}")
    finally:
        con.close()

# CHAMADA DIRETA (executa assim que o servidor inicia)
#apagar_tabela_acessos_uma_vez()

if __name__ == '__main__':
    apagar_tabela_acessos_uma_vez()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
