
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3, os

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

if __name__ == '__main__':
    app.run(debug=True)
