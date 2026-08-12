from flask import Flask, render_template, request, redirect, url_for, flash, Response
from db import AgendaDB
from werkzeug.utils import secure_filename
import os
import csv
import io
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
    pagina = request.args.get('pagina', 1, type=int)
    busca = request.args.get('busca', '', type=str)

    limite = 10
    offset = (pagina - 1) * limite

    contatos = db.listar_contatos_paginado(limite, offset, busca)
    
    total_contatos = db.contar_contatos(busca)
    if total_contatos is None:
        total_contatos = 0
    else:
        total_paginas = 1
        
    return render_template(
        'index.html', 
        contatos=contatos, 
        pagina_atual=pagina, 
        total_paginas=total_paginas,
        busca=busca
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

@app.route('/exportar')
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

if __name__ == '__main__':
    app.run(debug=True)