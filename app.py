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
# Garante que a pasta de upload existe no ambiente de produção
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


#@app.route('/painel')
#def painel():
#    if not session.get('admin'):
 #       return redirect(url_for('login'))
#    return render_template('painel.html')


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
        cur.execute("INSERT INTO produtos (nome, preco, imagem) VALUES (%s, %s, %s)",
                    (nome, preco, imagem_url))
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

@app.before_request
def registrar_acesso():
    if request.endpoint not in ['static', 'registrar_clique']:
        ip = request.remote_addr
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO acessos (ip) VALUES (%s)", (ip,))
        con.commit()
        con.close()

@app.route('/registrar-clique/<int:id>')
def registrar_clique(id):
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT INTO cliques (produto_id) VALUES (%s)", (id,))
    con.commit()
    con.close()
    return redirect("https://wa.me/5515998366823")

@app.route('/painel')
def painel():
    if not session.get('admin'):
        return redirect(url_for('login'))

    con = conectar()
    cur = con.cursor()

    # Acessos
    cur.execute("SELECT COUNT(*) FROM acessos WHERE DATE(data) = CURRENT_DATE")
    acessos_dia = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM acessos WHERE data >= NOW() - INTERVAL '7 days'")
    acessos_semana = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM acessos WHERE data >= NOW() - INTERVAL '30 days'")
    acessos_mes = cur.fetchone()[0]

    # Produto mais clicado
    cur.execute("""
        SELECT produtos.nome, COUNT(cliques.id) AS total
        FROM cliques
        JOIN produtos ON cliques.produto_id = produtos.id
        GROUP BY produtos.nome
        ORDER BY total DESC
        LIMIT 1
    """)
    produto_mais_clicado = cur.fetchone()

    con.close()

    return render_template(
        'painel.html',
        acessos_dia=acessos_dia,
        acessos_semana=acessos_semana,
        acessos_mes=acessos_mes,
        produto_mais_clicado=produto_mais_clicado
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
