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
        self.cursor = self.conn.cursor(dictionary=True, buffered=True)

    def contar_contatos(self, busca=""):
        try:
            if busca:
                sql = "SELECT COUNT(*) FROM contatos WHERE nome LIKE %s OR email LIKE %s OR telefone LIKE %s"
                termo = f"%{busca}%"
                self.cursor.execute(sql, (termo, termo, termo))
            else:
                sql = "SELECT COUNT(*) FROM contatos"
                self.cursor.execute(sql)
                    
            res = self.cursor.fetchone()

            if not res:
                return 0
            
            if isinstance(res, dict):
                return res.get('total') if res.get('total') is not None else list(res.values())[0]
            
            return res[0] if res[0] is not None else 0
        except Exception as e:
            print(f"Erro ao contar contatos: {e}")
            return 0

    def listar_contatos_paginado(self, limite=10, offset=0, busca=""):
        if busca:
            sql = """SELECT * FROM contatos 
                    WHERE nome LIKE %s OR email LIKE %s OR telefone LIKE %s 
                    ORDER BY nome ASC LIMIT %s OFFSET %s"""
            termo = f"%{busca}%"
            self.cursor.execute(sql, (termo, termo, termo, limite, offset))
        else:
            sql = "SELECT * FROM contatos ORDER BY nome ASC LIMIT %s OFFSET %s"
            self.cursor.execute(sql, (limite, offset))
            
        return self.cursor.fetchall()

    def listar_contatos(self):
        # READ: Retorna todos os contatos
        self.cursor.execute("SELECT * FROM contatos")
        return self.cursor.fetchall()

    def buscar_contato(self, id):
        self.cursor.execute("SELECT * FROM contatos WHERE id = %s", (id,))
        return self.cursor.fetchone()

    def buscar_duplicado(self, telefone, email, id_atual=None):
        if id_atual:
            sql = "SELECT * FROM contatos WHERE (telefone = %s OR email = %s) AND id != %s"
            self.cursor.execute(sql, (telefone, email, id_atual))
        else:
            sql = "SELECT * FROM contatos WHERE telefone = %s OR email = %s"
            self.cursor.execute(sql, (telefone, email)) 
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

    def cadastrar_usuario(self, nome, email, senha_hash):
        sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (nome, email, senha_hash))
        self.conn.commit()

    def buscar_usuario_por_email(self, email):
        sql = "SELECT * FROM usuarios WHERE email = %s"
        self.cursor.execute(sql, (email,))
        return self.cursor.fetchone()

    def fechar(self):
        # Fecha a conexão
        self.cursor.close()
        self.conn.close()