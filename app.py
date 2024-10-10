from flask import Flask, render_template, request, redirect, session
import mysql.connector
from config import *

def conectar_db():
    #estabelece conexão com o Banco de dados
    conexao = mysql.connector.connect (
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_NAME
    )
    return conexao

def encerrar_db(cursor, conexao):
    #fechar cursor e conexão com o banco de dados
    cursor.close()
    conexao.close()

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route('/')
def index():
    comandoSQL = '''
    SELECT post.*, usuario.nome
    FROM post
    JOIN usuario ON post.id_usuario = usuario.id_usuario
    ORDER BY post.data_post DESC;
    '''

    conexaodb = conectar_db()
    cursordb = conexaodb.cursor()
    cursordb.execute(comandoSQL)
    posts = cursordb.fetchall()
    encerrar_db(cursordb, conexaodb)

    #Formatar a data antes de enviar para o template
    posts_formatados = []
    for post in posts:
        posts_formatados.append ({
            'id_post': post[0],
            'id_usuario': post[1],
            'conteudo': post[2],
            'data': post[3].strftime("%d/%m/%Y  %H:%M"),
            'autor': post[4]
        })
    if 'id_usuario' in session:
        login = True
        id_usuario = session['id_usuario']
    else:
        login = False
        id_usuario = ""

    return render_template('index.html', posts=posts_formatados, login=login, id_usuario=id_usuario)

@app.route('/login')
def login():
    return render_template('login.html')

#Rota para verificar o acesso do admin
@app.route("/acesso", methods=['GET', 'POST'])
def acesso():
    if request.method == 'GET':
        return redirect('/login')
    
    session.clear() #Apagar todas as sessões

    email_informado = request.form["email"]
    senha_informada = request.form["senha"]

    if email_informado == MASTER_EMAIL and senha_informada == MASTER_PASSWORD:
        session["adm"] = True
        return redirect('/adm')

    comandoSQL = 'SELECT * FROM usuario WHERE email = %s AND senha = %s'
    conexaodb= conectar_db()
    cursordb =  conexaodb.cursor()
    cursordb.execute(comandoSQL, (email_informado, senha_informada))
    usuario_encontrado = cursordb.fetchone()
    encerrar_db(cursordb, conexaodb)

    if usuario_encontrado:
        session["id_usuario"] = usuario_encontrado[0]
        return redirect('/')
    else:
        return render_template("login.html", mensagem="Usuário/Senha estão incorretos!")
    
#Rota para logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')

#Rota para abrir a página novo post
@app.route('/novopost')
def novopost():
    if 'id_usuario' in session:
        id_usuario = session['id_usuario']
        comandoSQL = 'SELECT * FROM usuario WHERE id_usuario = %s'
        conexaodb= conectar_db()
        cursordb =  conexaodb.cursor()
        cursordb.execute(comandoSQL, (id_usuario,))
        usuario_encontrado = cursordb.fetchone()
        encerrar_db(cursordb, conexaodb)
        return render_template('novopost.html', usuario=usuario_encontrado)
    else:
        return redirect('/login')
    
#Rota para receber os dados de postagem do formulário
@app.route("/cadastro_post", methods=['GET', 'POST'])
def cadastro_post():
    if request.method == 'GET':
        return redirect('/novopost')

    id_usuario = request.form['id_usuario']
    conteudo = request.form['conteudo']
    if conteudo:
        conexaodb = conectar_db()
        cursordb = conexaodb.cursor()
        cursordb.execute("SET time_zone = '-3:00';")
        comandoSQL = 'INSERT INTO post (id_usuario, conteudo) VALUES (%s,%s)'
        cursordb.execute(comandoSQL, (id_usuario, conteudo))
        conexaodb.commit()
        encerrar_db(cursordb, conexaodb)
        return redirect('/')
    
#Rota trata o erro 404 - Página não encontrada
@app.errorhandler(404)
def not_found(error):
    return render_template('erro404.html'), 404
    
#ROTA PARA ACESSO DO ADM
@app.route("/adm")
def adm():
    if 'adm' not in session:
        return redirect('/login')
    
    conexaodb = conectar_db()
    cursordb = conexaodb.cursor()

    comandoSQL = 'SELECT * FROM usuario;'
    cursordb.execute(comandoSQL)
    usuarios = cursordb.fetchall()

    comandoSQL = '''
        SELECT post.*, usuario.nome
        FROM post
        JOIN usuario ON post.id_usuario = usuario.id_usuario
        ORDER BY post.data_post DESC;
'''
    cursordb.execute(comandoSQL)
    posts = cursordb.fetchall()

    encerrar_db(cursordb, conexaodb)

    return render_template('adm.html', lista_usuarios=usuarios, lista_posts=posts)

#ROTA PARA ABRIR O TEMPLATE PARA NOVO USUÁRIO
@app.route("/novousuario")
def novousuario():
    if 'adm' not in session:
        return redirect('/login')
    
    return render_template('novousuario.html')

#ROTA PARA RECEBER OS DADOS E CADASTRAR UM NOVO USUÁRIO
@app.route("/cadastro_usuario", methods= ['POST'])
def cadastro_usuario():
    #verifica se o acesso a essa rota é do ADM
    if 'adm' not in session:
        return redirect('/login')
    
    #Verifica se o acesso foi via formulário
    if request.method == 'POST':
        nome_usuario = request.form['nome']
        email_usuario = request.form['email']
        senha_usuario = request.form['senha']
        #verifica se os campos estão preenchidos
        if nome_usuario and email_usuario and senha_usuario:
            try:
                conexaodb = conectar_db()
                cursordb = conexaodb.cursor()
                comandoSQL = 'INSERT INTO usuario (nome, email, senha) VALUES (%s, %s, %s)'
                cursordb.execute(comandoSQL, (nome_usuario, email_usuario, senha_usuario))
                conexaodb.commit()
            except mysql.connector.IntegrityError:
                return render_template("novousuario.html", msgerro=f"O e-mail {email_usuario} já está em uso!")
            finally:
                encerrar_db(cursordb, conexaodb)

    return redirect("/adm")

#ROTA PARA RECEBER OS DADOS E CADASTRAR UM NOVO USUÁRIO
@app.route("/editar-user/<int:id>")
def editar_usuario(id):
    #verifica se o acesso a essa rota é do ADM
    if 'adm' not in session:
        return redirect('/login')
    
    session['user_id'] = id #Salvndo o ID do usuário na sessão
    conexaodb = conectar_db()
    cursordb = conexaodb.cursor()
    comandoSQL = 'SELECT * FROM usuario WHERE id_usuario = %s'
    cursordb.execute(comandoSQL, (id,))
    usuario_encontrado = cursordb.fetchone()
    encerrar_db(cursordb, conexaodb)

    return render_template('editarusuario.html', usuario=usuario_encontrado)

#ROTA PARA ATUALIZAR O USUÁRIO
@app.route("/atualizar_usuario", methods=['POST'])
def atualizar_usuario():
    #Verifica se o acesso a essa rota é do ADM
    if 'adm' not in session:
        return redirect('/login')
    
    #verifica se o acesso foi via formulário
    if request.method == 'POST':
        user_id = session.get('user_id') #Recuperando o ID do usuário da sessão
        nome_usuario = request.form['nome']
        email_usuario = request.form['email']
        senha_usuario = request.form['senha']
        #verifica se os campos estão preenchidos
        if nome_usuario and email_usuario and senha_usuario:
            conexaodb = conectar_db()
            cursordb = conexaodb.cursor()
            comandoSQL = 'UPDATE usuario SET nome = %s, email = %s, senha = %s WHERE id_usuario = %s'
            cursordb.execute(comandoSQL, (nome_usuario, email_usuario, senha_usuario, user_id))
            conexaodb.commit()
            encerrar_db(cursordb, conexaodb)

    return redirect("/adm")

#ROTA EXCLUINDO USUÁRIO
@app.route("/excluir-user/<int:id>")
def excluir_usuario(id):
    #Verifica se o acesso a essa rota é do ADM
    if 'adm' not in session:
        return redirect('/login')
    
    #Excluirá os posts do usuário a ser excluído
    conexaodb = conectar_db()
    cursordb = conexaodb.cursor()
    comandoSQL = 'DELETE FROM post WHERE id_usuario = %s'
    cursordb.execute(comandoSQL, (id,))
    conexaodb.commit()

    #Excluirá o usuário do ID informado
    comandoSQL = 'DELETE FROM usuario WHERE id_usuario = %s'
    cursordb.execute(comandoSQL, (id,))
    conexaodb.commit()
    encerrar_db(cursordb, conexaodb)

    return redirect("/adm")

#ROTA PARA EXCLUIR POSTS 
@app.route("/excluir-post/<int:id>")
def excluir_post(id):
    #Verifica se tem usuário logado no sistema
    if not session:
        return redirect('/login')
    
    #Conecta com o BD
    conexaodb = conectar_db()
    cursordb = conexaodb.cursor()
    usuario_autor = ()

    #Armazena o id do usuário logado
    if not 'adm' in session:
        id_usuario = session['id_usuario']
        comandoSQL = 'SELECT * FROM post WHERE id_post = %s AND id_usuario = %s'
        cursordb.execute(comandoSQL, (id, id_usuario))
        usuario_autor =cursordb.fetchone ()

    if usuario_autor or 'adm' in session:
        comandoSQL = 'DELETE FROM post WHERE id_post = %s'
        cursordb.execute(comandoSQL, (id,))
        conexaodb.commit()
        encerrar_db(cursordb, conexaodb)
    else:
        return redirect('/')
    
    if 'adm' in session:
        return redirect("/adm")
    else:
        return redirect("/")

#Final do código
#Final do arquivo
if __name__ == '__main__':
    app.run(debug=True)