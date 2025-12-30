"""
Sistema I9 - Application Factory
"""

import os
from flask import Flask
from config import config


def create_app(config_name='development'):
    """Factory function para criar a aplicação Flask."""
    
    app = Flask(__name__)
    
    # Carrega configurações
    app.config.from_object(config.get(config_name, config['default']))
    
    # Inicializa extensões
    from app.extensions import db, login_manager, migrate
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Importa modelos (necessário para migrations)
    from app.models import Usuario, Filial, UsuarioFilial, Auditoria
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Registra Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.consulta import consulta_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(consulta_bp, url_prefix='/api')
    
    # Cria diretório de certificados
    cert_folder = app.config.get('UPLOAD_FOLDER')
    if cert_folder and not os.path.exists(cert_folder):
        os.makedirs(cert_folder)
    
    # Cria tabelas se não existirem (desenvolvimento)
    with app.app_context():
        db.create_all()
        
        # Cria admin padrão se não existir
        _criar_admin_padrao(db, Usuario)
    
    return app


def _criar_admin_padrao(db, Usuario):
    """Cria usuário admin padrão se não existir nenhum."""
    from werkzeug.security import generate_password_hash
    
    if Usuario.query.filter_by(role='admin').first() is None:
        admin = Usuario(
            nome='Administrador',
            email='admin@i9sistema.com',
            senha_hash=generate_password_hash('admin123'),
            role='admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado: admin@i9sistema.com / admin123")
