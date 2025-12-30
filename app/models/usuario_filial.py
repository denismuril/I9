"""
Sistema I9 - Modelo de Associação Usuário-Filial
"""

from app.extensions import db


class UsuarioFilial(db.Model):
    """Tabela de associação entre usuários e filiais."""
    
    __tablename__ = 'usuario_filial'
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), primary_key=True)
    
    def __repr__(self):
        return f'<UsuarioFilial {self.usuario_id}-{self.filial_id}>'
