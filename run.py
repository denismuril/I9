"""
Sistema I9 - Entry Point
"""

import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("   SISTEMA I9 - Enterprise Edition")
    print("=" * 60)
    print("\n🚀 Servidor iniciado em: http://localhost:5000")
    print("🔐 Autenticação: Flask-Login")
    print("🗄️  Banco: PostgreSQL")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))
