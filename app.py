from flask import Flask, render_template, request, redirect, url_for
from db import AgendaDB

app = Flask(__name__)

#instanciando o objeto do banco de dados
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
        db.adicionar_contato(nome, telefone, email, endereco)
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
        db.editar_contato(id, nome, telefone, email, endereco)
        return redirect(url_for('index'))
    return render_template('editar.html', acao="Editar", contato=contato)

@app.route('/excluir/<int:id>')
def excluir(id):
    db.excluir_contato(id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)