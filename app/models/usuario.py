"""
Sistema I9 - Modelo de Usuário
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Usuario(UserMixin, db.Model):
    """Modelo de usuário do sistema."""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='consultor')  # admin, consultor
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    
    # Relacionamentos
    filiais = db.relationship('Filial', secondary='usuario_filial', 
                              backref=db.backref('usuarios', lazy='dynamic'))
    auditorias = db.relationship('Auditoria', backref='usuario', lazy='dynamic')
    
    def set_senha(self, senha):
        """Define a senha do usuário."""
        self.senha_hash = generate_password_hash(senha)
    
    def verificar_senha(self, senha):
        """Verifica se a senha está correta."""
        return check_password_hash(self.senha_hash, senha)
    
    def is_admin(self):
        """Verifica se o usuário é administrador."""
        return self.role == 'admin'
    
    def pode_acessar_filial(self, filial_id):
        """Verifica se o usuário pode acessar uma filial específica."""
        if self.is_admin():
            return True
        return any(f.id == filial_id for f in self.filiais)
    
    def get_filiais_permitidas(self):
        """Retorna as filiais que o usuário pode acessar."""
        if self.is_admin():
            from app.models.filial import Filial
            return Filial.query.filter_by(ativa=True).all()
        return [f for f in self.filiais if f.ativa]
    
    def registrar_login(self):
        """Registra o horário do último login."""
        self.ultimo_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
