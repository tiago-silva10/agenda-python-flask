from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from db import AgendaDB
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import csv
import io
import math

app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Por favor, faça o login para acessar a agenda.", "erro")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app.secret_key = 'sua_chave_secreta_super_segura'
# Configura o caminho absoluto dinâmico para a pasta de uploads (evita erro de FileNotFoundError)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria a pasta 'static/uploads' automaticamente se ela não existir no sistema
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Instanciando o objeto do banco de dados
db = AgendaDB(host="127.0.0.1", user="root", password="root", database="agenda_db")

@app.route('/')
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busca = request.args.get('busca', '', type=str)

    limite = 10
    offset = (pagina - 1) * limite

    contatos = db.listar_contatos_paginado(limite, offset, busca)
    
    total_contatos = db.contar_contatos(busca) or 0
    
    total_paginas = math.ceil(total_contatos / limite) if total_contatos > 0 else 1
        
    return render_template(
        'index.html', 
        contatos=contatos, 
        pagina_atual=pagina, 
        total_paginas=total_paginas,
        busca=busca
    )

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        endereco = request.form['endereco']

        if telefone or email:
            duplicado = db.buscar_duplicado(telefone, email)
            if duplicado:
                flash("Atenção: Já existe um contato com este telefone ou e-mail!", "erro")
                return render_template('adicionar.html', acao="Adicionar", contato=None)
        
        foto = request.files.get('foto')
        nome_arquivo = 'default.png'
        
        if foto and foto.filename != '':
            nome_arquivo = secure_filename(foto.filename)
            caminho_salvar = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            foto.save(caminho_salvar)
            
        db.adicionar_contato(nome, telefone, email, endereco, nome_arquivo)
        return redirect(url_for('index'))
        
    return render_template('adicionar.html', acao="Adicionar", contato=None)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    contato = db.buscar_contato(id)
    
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        endereco = request.form['endereco']

        if telefone or email:
            duplicado = db.buscar_duplicado(telefone, email, id_atual=id)
            if duplicado:
                flash("Atenção: Este telefone ou e-mail já pertence a outro contato!", "erro")
                return render_template('editar.html', acao="Editar", contato=contato)
            
        nome_arquivo = contato[5] if isinstance(contato, (list, tuple)) else contato.get('foto', 'default.png')
        
        foto = request.files.get('foto')
        if foto and foto.filename != '':
            nome_arquivo = secure_filename(foto.filename)
            caminho_salvar = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            foto.save(caminho_salvar)

        # Atualiza no banco de dados
        db.editar_contato(id, nome, telefone, email, endereco, nome_arquivo)
        return redirect(url_for('index'))
        
    return render_template('editar.html', acao="Editar", contato=contato)

@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    db.excluir_contato(id)
    return redirect(url_for('index'))

@app.route('/exportar')
@login_required
def exportar_csv():
    # 1. Busca todos os contatos do banco de dados (sem paginar, queremos todos)
    contatos = db.listar_contatos_paginado(limite=1000, offset=0)

    # 2. Cria um arquivo CSV na memória RAM
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=';') # Ponto e vírgula é o padrão perfeito para o Excel no Brasil

    # 3. Escreve o cabeçalho das colunas
    writer.writerow(['ID', 'Nome', 'Telefone', 'Email', 'Endereço'])

    # 4. Escreve as linhas com os dados de cada contato
    for contato in contatos:
        # Garante suporte tanto para Dicionário quanto para Tupla
        c_id = contato.get('id') if isinstance(contato, dict) else contato[0]
        c_nome = contato.get('nome') if isinstance(contato, dict) else contato[1]
        c_tel = contato.get('telefone') if isinstance(contato, dict) else contato[2]
        c_email = contato.get('email') if isinstance(contato, dict) else contato[3]
        c_end = contato.get('endereco') if isinstance(contato, dict) else contato[4]

        writer.writerow([c_id, c_nome, c_tel, c_email, c_end])

    # 5. Prepara a resposta do Flask para fazer o download do arquivo no navegador
    output = stream.getvalue()
    
    # O 'utf-8-sig' é o segredo para o Excel abrir com todos os acentos e 'ç' perfeitos!
    return Response(
        output.encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=contatos_agenda.csv"}
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = db.buscar_usuario_por_email(email)

        if usuario:
            # Suporta dicionário ou tupla
            senha_hash = usuario.get('senha') if isinstance(usuario, dict) else usuario[3]
            user_id = usuario.get('id') if isinstance(usuario, dict) else usuario[0]
            user_nome = usuario.get('nome') if isinstance(usuario, dict) else usuario[1]

            # Valida a senha digitada com o hash salvo no banco
            if check_password_hash(senha_hash, senha):
                session['usuario_id'] = user_id
                session['usuario_nome'] = user_nome
                flash(f"Bem-vindo(a), {user_nome}!", "sucesso")
                return redirect(url_for('index'))

        flash("E-mail ou senha incorretos!", "erro")

    return render_template('login.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if db.buscar_usuario_por_email(email):
            flash("Este e-mail já está cadastrado!", "erro")
            return render_template('registrar.html')

        # Criptografa a senha antes de salvar
        senha_hash = generate_password_hash(senha)
        db.cadastrar_usuario(nome, email, senha_hash)
        
        flash("Conta criada com sucesso! Faça seu login.", "sucesso")
        return redirect(url_for('login'))

    return render_template('registrar.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)