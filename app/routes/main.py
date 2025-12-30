"""
Sistema I9 - Rotas Principais (Dashboard)
"""

from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.models import Filial

main_bp = Blueprint('main', __name__)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Página principal - Dashboard de consulta."""
    # Obtém filiais permitidas para o usuário
    filiais = current_user.get_filiais_permitidas()
    
    # Verifica se há filial conectada na sessão
    filial_conectada = None
    if 'filial_conectada_id' in session:
        filial_id = session['filial_conectada_id']
        # Verifica se ainda tem permissão
        if current_user.pode_acessar_filial(filial_id):
            filial_conectada = Filial.query.get(filial_id)
            if filial_conectada:
                filial_conectada = {
                    'id': filial_conectada.id,
                    'nome': filial_conectada.nome,
                    'uf': filial_conectada.uf,
                    'conectado_em': session.get('filial_conectada_em', '')
                }
        else:
            # Remove da sessão se não tem mais permissão
            session.pop('filial_conectada_id', None)
            session.pop('filial_conectada_em', None)
    
    return render_template(
        'dashboard.html',
        usuario=current_user,
        filiais=filiais,
        filial_conectada=filial_conectada,
        is_admin=current_user.is_admin()
    )
