import mysql.connector

class AgendaDB:
    def __init__(self, host, user, password, database):
        #iniciando conexão com o banco de dados mysql
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def contar_contatos(self):
        sql = "SELECT COUNT(*) FROM contatos"
        self.cursor.execute(sql)
        resultado = self.cursor.fetchone()
        return resultado[0] if isinstance(resultado, (list, tuple)) else resultado['COUNT(*)']

    def listar_contatos_paginado(self, limite=10, offset=0):
        sql = "SELECT * FROM contatos LIMIT %s OFFSET %s"
        self.cursor.execute(sql, (limite, offset))
        return self.cursor.fetchall()

    def listar_contatos(self):
        # READ: Retorna todos os contatos
        self.cursor.execute("SELECT * FROM contatos")
        return self.cursor.fetchall()

    def buscar_contato(self, id):
        self.cursor.execute("SELECT * FROM contatos WHERE id = %s", (id,))
        return self.cursor.fetchone()

    def adicionar_contato(self, nome, telefone, email, endereco, foto='default.png'):
        sql = "INSERT INTO contatos (nome, telefone, email, endereco, foto) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(sql, (nome, telefone, email, endereco, foto))
        self.conn.commit()

    def editar_contato(self, id, nome, telefone, email, endereco, foto):
        sql = "UPDATE contatos SET nome = %s, telefone = %s, email = %s, endereco = %s, foto=%s WHERE id = %s"
        self.cursor.execute(sql, (nome, telefone, email, endereco, foto, id))
        self.conn.commit()

    def excluir_contato(self, id):
        sql = "DELETE FROM contatos WHERE id = %s"
        self.cursor.execute(sql, (id,))
        self.conn.commit()

    def fechar(self):
        # Fecha a conexão
        self.cursor.close()
        self.conn.close()