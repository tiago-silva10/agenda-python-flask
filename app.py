from flask import Flask, render_template, request, redirect, url_for, flash
from db import AgendaDB
import os
from werkzeug.utils import secure_filename
import math

app = Flask(__name__)

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
def index():
    # Pega o número da página atual pela URL (se não passar nada, assume página 1)
    pagina = request.args.get('pagina', 1, type=int)
    
    limite = 10 # 10 contatos por página
    offset = (pagina - 1) * limite # Calcula quantos registros 'pular' no banco

    # Busca apenas os 10 contatos da página atual
    contatos = db.listar_contatos_paginado(limite, offset)
    
    # Calcula o total de páginas
    total_contatos = db.contar_contatos()
    total_paginas = math.ceil(total_contatos / limite) if total_contatos > 0 else 1

    return render_template(
        'index.html', 
        contatos=contatos, 
        pagina_atual=pagina, 
        total_paginas=total_paginas
    )

@app.route('/adicionar', methods=['GET', 'POST'])
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
def excluir(id):
    db.excluir_contato(id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)