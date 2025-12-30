"""
Sistema I9 - Modelo de Filial
"""

import os
from datetime import datetime
from app.extensions import db


class Filial(db.Model):
    """Modelo de filial/concessionária."""
    
    __tablename__ = 'filiais'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    endereco = db.Column(db.String(200))
    cert_path = db.Column(db.String(255))  # Caminho do arquivo .pfx
    cert_senha_env = db.Column(db.String(50))  # Nome da var de ambiente
    cert_validade = db.Column(db.Date)  # Data de validade do certificado
    ativa = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com auditorias
    auditorias = db.relationship('Auditoria', backref='filial', lazy='dynamic')
    
    def get_cert_senha(self):
        """Obtém a senha do certificado da variável de ambiente."""
        if self.cert_senha_env:
            return os.getenv(self.cert_senha_env, '')
        # Padrão: CERT_FILIAL_{ID}_PASS
        return os.getenv(f'CERT_FILIAL_{self.id}_PASS', '')
    
    def certificado_configurado(self):
        """Verifica se o certificado está configurado corretamente."""
        if not self.cert_path:
            return False
        if not os.path.exists(self.cert_path):
            return False
        if not self.get_cert_senha():
            return False
        return True
    
    def simular_conexao_detran(self):
        """
        Simula conexão com o DETRAN usando o certificado.
        Em produção, aqui seria feita a autenticação mTLS real.
        """
        # Verificação básica
        senha = self.get_cert_senha()
        if not senha:
            return {
                'sucesso': False,
                'erro': f'Senha do certificado não configurada. Configure {self.cert_senha_env or f"CERT_FILIAL_{self.id}_PASS"} no .env'
            }
        
        # Simulação de sucesso
        return {
            'sucesso': True,
            'mensagem': f'Conexão com DETRAN-{self.uf} estabelecida',
            'filial': self.nome,
            'uf': self.uf
        }
    
    @staticmethod
    def formatar_cnpj(cnpj):
        """Remove formatação do CNPJ."""
        return ''.join(c for c in cnpj if c.isdigit())
    
    def __repr__(self):
        return f'<Filial {self.nome}>'
