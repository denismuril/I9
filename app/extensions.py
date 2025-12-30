"""
Sistema I9 - Extensões Flask
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Instâncias das extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configuração do Login Manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'
