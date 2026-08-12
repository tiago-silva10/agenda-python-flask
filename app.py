from flask import Flask, render_template, request, redirect, url_for
from db import AgendaDB
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
    contatos = db.listar_contatos()
    return render_template('index.html', contatos=contatos)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        endereco = request.form['endereco']
        
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
        
        # Mantém a foto antiga por padrão caso nenhuma nova seja enviada
        # (Assumindo que no dicionário/tupla do contato a foto seja o último item ou contato['foto'])
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