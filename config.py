"""
Sistema I9 - Configurações da Aplicação
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações base."""
    
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://i9_user:I9SecurePass2024!@localhost:5432/sistema_i9_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Infosimples API
    INFOSIMPLES_API_KEY = os.getenv('INFOSIMPLES_API_KEY', '')
    
    # Upload de certificados
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificados')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento."""
    DEBUG = True


class ProductionConfig(Config):
    """Configurações de produção."""
    DEBUG = False
    
    # Em produção, exige variáveis de ambiente
    @classmethod
    def init_app(cls, app):
        assert os.getenv('FLASK_SECRET_KEY'), 'FLASK_SECRET_KEY não configurado!'
        assert os.getenv('DATABASE_URL'), 'DATABASE_URL não configurado!'


class TestingConfig(Config):
    """Configurações de teste."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
