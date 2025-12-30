"""
Sistema I9 - Modelo de Auditoria
"""

from datetime import datetime
from app.extensions import db


class Auditoria(db.Model):
    """Modelo de log de auditoria de consultas."""
    
    __tablename__ = 'auditorias'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    filial_id = db.Column(db.Integer, db.ForeignKey('filiais.id'), nullable=False)
    placa_chassi = db.Column(db.String(50), nullable=False)
    tipo_busca = db.Column(db.String(20), nullable=False)  # placa, chassi
    resultado = db.Column(db.Text)  # JSON com resumo do resultado
    status = db.Column(db.String(20), default='sucesso')  # sucesso, erro, nao_encontrado
    ip_origem = db.Column(db.String(45))  # IPv4 ou IPv6
    data_consulta = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @staticmethod
    def registrar(usuario_id, filial_id, placa_chassi, tipo_busca, resultado, status='sucesso', ip_origem=None):
        """Registra uma nova entrada de auditoria."""
        import json
        
        auditoria = Auditoria(
            usuario_id=usuario_id,
            filial_id=filial_id,
            placa_chassi=placa_chassi.upper(),
            tipo_busca=tipo_busca,
            resultado=json.dumps(resultado, ensure_ascii=False) if isinstance(resultado, dict) else resultado,
            status=status,
            ip_origem=ip_origem
        )
        db.session.add(auditoria)
        db.session.commit()
        return auditoria
    
    def get_resultado_dict(self):
        """Retorna o resultado como dicionário."""
        import json
        try:
            return json.loads(self.resultado) if self.resultado else {}
        except:
            return {}
    
    def __repr__(self):
        return f'<Auditoria {self.id} - {self.placa_chassi}>'
