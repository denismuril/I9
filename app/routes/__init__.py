"""
Sistema I9 - Routes Package
"""

from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.admin import admin_bp
from app.routes.consulta import consulta_bp

__all__ = ['auth_bp', 'main_bp', 'admin_bp', 'consulta_bp']
