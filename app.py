from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime  # Adicione esta linha


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Necessária para sessões e mensagens flash

# BANCO DE DADOS #
############################################################################################################################

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cpf = db.Column(db.String(11), nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo_usuario = db.Column(db.String(10), default='aluno')
    status = db.Column(db.Boolean, default=False)  # Status (True ou False)

class Aluno(Usuario):
    __tablename__ = 'aluno'
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    matricula = db.Column(db.String(20), nullable=False)
    curso = db.Column(db.String(50), nullable=False)

class Externo(Usuario):
    __tablename__ = 'externo'
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)  # Chave estrangeira referenciando Usuario

    
class Livro(db.Model):
    __tablename__ = 'livro'
    
    id = db.Column(db.Integer, primary_key=True)
    autor = db.Column(db.String(100), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.Integer, unique=True, nullable=False)
    editora = db.Column(db.String(100), nullable=False)
    assunto = db.Column(db.String(100), nullable=False)
    edicao = db.Column(db.String(20), nullable=False)
    data_inclusao = db.Column(db.DateTime, default=datetime.utcnow)  # Data de inclusão
    disponivel = db.Column(db.Boolean, default=True)  # Disponibilidade (True ou False)
    reservado = db.Column(db.Boolean, default=False)  # Novo campo para indicar se o livro foi reservado

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.id'))
    livro = db.relationship('Livro', backref='reservas')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', backref='reservas')
    status = db.Column(db.String(20), default='pendente')  # Pode ser 'pendente', 'aceito', ou 'recusado'

    def __init__(self, livro_id, usuario_id):
        self.livro_id = livro_id
        self.usuario_id = usuario_id
        self.status = 'pendente'

    

"""
    # Relacionamento com Exemplares
    exemplares = db.relationship('Exemplar', backref='livro', lazy=True)
"""

"""
# Modelo de Exemplar
class Exemplar(db.Model):
    __tablename__ = 'exemplar'
    
    id = db.Column(db.Integer, primary_key=True)
    data_inclusao = db.Column(db.DateTime, default=datetime.utcnow)  # Data de inclusão
    disponivel = db.Column(db.Boolean, default=True)  # Disponibilidade (True ou False)
    reservado = db.Column(db.Boolean, default=False)  # Novo campo para indicar se o livro foi reservado

    # Relacionamento com Título
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.id'))  # Relacionamento correto com a tabela 'livro'

    def __init__(self, livro_id, disponivel):
        self.livro_id = livro_id
        self.disponivel = disponivel
        self.reservado = False  # Inicialmente, não está reservado
"""

# Criação do banco de dados
with app.app_context():
    db.create_all()

############################################################################################################################

# ENDEREÇAMENTO PARA TELAS

@app.route('/painel-admin')
def painelAdmin():
    return render_template('painel-admin.html')

@app.route('/lib-solicitacoes')
def painelSolicitacoes():
    usuarios = Usuario.query.all()  # Buscando todos os usuários
    return render_template('lib-solicitacoes.html', usuarios=usuarios)

@app.route('/listar-usuarios')
def listarUsuarios():
    usuarios = Usuario.query.all()  # Buscando todos os usuários
    return render_template('lib-usuarios.html', usuarios=usuarios)

@app.route('/painel-lib')
def painelLib():
    livros = Livro.query.all()  # Buscando todos os livros
    return render_template('painel-lib.html', livros=livros)

@app.route('/painel-principal')
def painelPrincipal():
    livros = Livro.query.all()  # Buscando todos os livros
    return render_template('painel-principal.html', livros=livros)

@app.route('/tela-cadastro')
def telaCadastro():
    return render_template('tela-cadastro-aluno.html')

@app.route('/tela-cadastro-livro')
def telaCadastroLivro():
    return render_template('tela-cadastro-livro.html')    

@app.route('/tela-cadastro-usuario')
def telaCadastroUsuario():
    return render_template('tela-cadastro-usuario.html')

@app.route('/',  methods=['GET', 'POST'])
def telaLogin():
    if request.method == 'POST':
        return entrar()  # Chama a função de login
    return render_template('tela-login.html')

'''
@app.route('/solicitacoes-reserva')
def solicitacoes_reserva():
    reservas = Reserva.query.filter_by(status='pendente').all()
    return render_template('solicitacoes-reserva.html', reservas=reservas)
'''

@app.route('/sair')
def sair():
    session.pop('usuario_id', None)
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('telaLogin'))

@app.route('/lib/solicitacoes', methods=['GET'])
def lib_solicitacoes():
    # Obter todas as reservas pendentes
    reservas_pendentes = Reserva.query.filter_by(status='pendente').all()
    
    return render_template('lib-solicitacoes.html', reservas=reservas_pendentes)


############################################################################################################################

# FUNCIONALIDADES

@app.route('/cadastrar-aluno', methods=['GET', 'POST'])
def cadastrarAluno():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        matricula = request.form['matricula']
        curso = request.form['curso']
        email = request.form['email']
        senha = request.form['senha']
        
        if Usuario.query.filter_by(email=email).first():
            flash('Esse email já está cadastrado. Por favor, utilize outro.', 'error')
            return redirect(url_for('telaCadastro'))

        if email.endswith('@aluno-faeterj.com'):
            novo_aluno = Aluno(nome=nome, cpf=cpf, matricula=matricula, curso=curso, email=email, senha=senha)
            db.session.add(novo_aluno)
            db.session.commit()
            flash('Cadastrado com sucesso!', 'success')
            return redirect(url_for('telaLogin'))
        else:
            flash('O email deve ter o domínio @aluno-faeterj.com', 'error')

    return render_template('tela-cadastro-aluno.html')

@app.route('/cadastrar-usuario', methods=['GET', 'POST'])
def cadastrarUsuario():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']
        tipo_usuario = request.form['tipo_usuario']

        usuario = Usuario(nome=nome, cpf=cpf, email=email, senha=senha, tipo_usuario=tipo_usuario)
        db.session.add(usuario)
        db.session.commit()

        return redirect(url_for('painelAdmin'))

    return render_template('tela-cadastro-usuario.html')

@app.route('/cadastrar-livro', methods=['GET', 'POST'])
def cadastrarLivro():
    if request.method == 'POST':
        autor = request.form['autor']
        titulo = request.form['titulo']
        isbn = request.form['isbn']
        editora = request.form['editora']
        assunto = request.form['assunto']
        edicao = request.form['edicao']

        livro = Livro(autor=autor, titulo=titulo, isbn=isbn, editora=editora, assunto=assunto, edicao=edicao)
        db.session.add(livro)
        db.session.commit()

        return redirect(url_for('painelLib'))

    return render_template('tela-cadastro-livro.html')
'''
@app.route('/entrar', methods=['POST'])
def entrar():
    email = request.form['email']
    senha = request.form['senha']

    if (email.endswith('@aluno-faeterj.com') or 
        email.endswith('@prof-faeterj.com')):

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.senha == senha:
            session['usuario_id'] = usuario.id
            flash(f'Bem-vindo, {usuario.email}!', 'success')
            return redirect(url_for('painelPrincipal'))
        else:
            flash('email ou senha incorretos.', 'error')
            return redirect(url_for('telaLogin'))

    elif (email.endswith('@admin-faeterj.com')):
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.senha == senha:
            session['usuario_id'] = usuario.id
            flash(f'Bem-vindo, {usuario.email}!', 'success')
            return redirect(url_for('painelAdmin'))
        else:
            flash('email ou senha incorretos.', 'error')
            return redirect(url_for('telaLogin'))

    elif (email.endswith('@lib-faeterj.com')):
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.senha == senha:
            session['usuario_id'] = usuario.id
            flash(f'Bem-vindo, {usuario.email}!', 'success')
            return redirect(url_for('painelLib'))
        else:
            flash('email ou senha incorretos.', 'error')
            return redirect(url_for('telaLogin'))

    else:
        flash('Email inválido.', 'error')
        return redirect(url_for('telaLogin'))
'''

@app.route('/entrar', methods=['POST'])
def entrar():
    email = request.form['email']
    senha = request.form['senha']

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario:
        if usuario.status:  # Verifica se o usuário está bloqueado
            flash('Seu acesso está bloqueado. Entre em contato com o administrador.', 'error')
            return redirect(url_for('telaLogin'))
        if usuario.senha == senha:
            session['usuario_id'] = usuario.id
            flash(f'Bem-vindo, {usuario.email}!', 'success')

            # Redireciona com base no tipo de usuário
            if email.endswith('@aluno-faeterj.com') or email.endswith('@prof-faeterj.com'):
                return redirect(url_for('painelPrincipal'))
            elif email.endswith('@admin-faeterj.com'):
                return redirect(url_for('painelAdmin'))
            elif email.endswith('@lib-faeterj.com'):
                return redirect(url_for('painelLib'))
        else:
            flash('Email ou senha incorretos.', 'error')
    else:
        flash('Email não encontrado.', 'error')
    return redirect(url_for('telaLogin'))


@app.route('/disponibilizar-livro/<int:livro_id>', methods=['POST'])
def disponibilizarLivro(livro_id):
    livro = Livro.query.get(livro_id)
    if livro:
        livro.disponivel = True
        db.session.commit()
        flash(f'O livro "{livro.titulo}" foi marcado como disponível.', 'success')
    else:
        flash('Livro não encontrado.', 'error')
    return redirect(url_for('painelLib'))

@app.route('/indisponibilizar-livro/<int:livro_id>', methods=['POST'])
def indisponibilizarLivro(livro_id):
    livro = Livro.query.get(livro_id)
    if livro:
        livro.disponivel = False
        db.session.commit()
        flash(f'O livro "{livro.titulo}" foi marcado como indisponível.', 'success')
    else:
        flash('Livro não encontrado.', 'error')
    return redirect(url_for('painelLib'))

'''
@app.route('/bloquear-usuario/<int:usuario_id>', methods=['POST'])
def bloquearUsuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.status = True  # Marcando como bloqueado
        db.session.commit()
        flash(f'O usuário "{usuario.nome}" foi marcado como bloqueado.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')
    return redirect(url_for('listarUsuarios'))

@app.route('/desbloquear-usuario/<int:usuario_id>', methods=['POST'])
def desbloquearUsuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.status = False  # Marcando como desbloqueado
        db.session.commit()
        flash(f'O usuário "{usuario.nome}" foi marcado como desbloqueado.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')
    return redirect(url_for('listarUsuarios'))
'''

@app.route('/bloquear-usuario/<int:usuario_id>', methods=['POST'])
def bloquearUsuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.status = True  # Marcando como bloqueado
        db.session.commit()
        flash(f'O usuário "{usuario.nome}" foi bloqueado com sucesso.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')
    return redirect(url_for('listarUsuarios'))

@app.route('/desbloquear-usuario/<int:usuario_id>', methods=['POST'])
def desbloquearUsuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.status = False  # Marcando como desbloqueado
        db.session.commit()
        flash(f'O usuário "{usuario.nome}" foi desbloqueado com sucesso.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')
    return redirect(url_for('listarUsuarios'))


@app.route('/solicitar-reserva/<int:livro_id>', methods=['POST'])
def solicitar_reserva(livro_id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para reservar um livro.', 'error')
        return redirect(url_for('telaLogin'))

    usuario_id = session['usuario_id']
    livro = Livro.query.get_or_404(livro_id)

    if not livro.disponivel:
        flash('O livro não está disponível para reserva.', 'error')
        return redirect(url_for('painelPrincipal'))

    # Criar solicitação de reserva
    reserva = Reserva(livro_id=livro.id, usuario_id=usuario_id)
    db.session.add(reserva)
    db.session.commit()

    flash('Solicitação de reserva enviada com sucesso!', 'success')
    return redirect(url_for('painelPrincipal'))

'''

@app.route('/gerenciar-reserva/<int:reserva_id>/<string:acao>', methods=['POST'])
def gerenciar_reserva(reserva_id, acao):
    reserva = Reserva.query.get_or_404(reserva_id)

    if acao == 'aceitar':
        reserva.status = 'aceito'
        reserva.livro.disponivel = False  # O livro não está mais disponível
    elif acao == 'recusar':
        reserva.status = 'recusado'
        reserva.livro.disponivel = True  # O livro volta a estar disponível

    db.session.commit()

    flash(f'Solicitação {acao} com sucesso!', 'success')
    return redirect(url_for('lib_solicitacoes'))  # Redireciona para a página de solicitações



@app.route('/reservar_livro/<int:livro_id>', methods=['POST'])
def reservar_livro(livro_id):
    livro = Livro.query.get_or_404(livro_id)
    usuario = current_user  # Assume que você está usando um sistema de autenticação com `current_user`

    if livro.disponivel:  # Verifica se o livro está disponível
        nova_reserva = Reserva(livro_id=livro.id, usuario_id=usuario.id)
        db.session.add(nova_reserva)
        livro.disponivel = False  # Marca o livro como não disponível
        db.session.commit()

        flash('Solicitação de reserva enviada com sucesso!', 'success')
    else:
        flash('Este livro não está disponível para reserva no momento.', 'danger')

    return redirect(url_for('painel_livros'))  # Redireciona de volta para a tela de livros

'''



############################################################################################################################

# EXCECUTA O PROJETO

if __name__ == '__main__':
    app.run(debug=True)
