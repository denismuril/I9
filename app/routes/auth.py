"""
Sistema I9 - Rotas de Autenticação
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        lembrar = request.form.get('lembrar', False)
        
        if not email or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha):
            if not usuario.ativo:
                flash('Sua conta está desativada. Contate o administrador.', 'error')
                return render_template('login.html')
            
            login_user(usuario, remember=lembrar)
            usuario.registrar_login()
            
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            
            # Redireciona para página solicitada ou dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email ou senha inválidos.', 'error')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Realiza logout do usuário."""
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def index():
    """Redireciona para login ou dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))
