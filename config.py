ambiente = 'producao'

if ambiente == 'teste':
#CONFIG BANCO DE DADOS
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = 'senai'
    DB_NAME = 'blog'

if ambiente == 'producao':
#CONFIG BANCO DE DADOS
    DB_HOST = 'LiihCosta.mysql.pythonanywhere-services.com'
    DB_USER = 'LiihCosta'
    DB_PASSWORD = 'LihPhe03'
    DB_NAME = 'LiihCosta$Blog'

#CONFIG CHAVE SECRETA DE SESSÃO
SECRET_KEY = 'blog'

#SENHA DO ADM
MASTER_EMAIL = "ligia.costa.senai@gmail.com"
MASTER_PASSWORD = "Liginha22*"