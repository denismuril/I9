"""
Sistema I9 - Rotas de Administração
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Usuario, Filial, UsuarioFilial, Auditoria

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator para restringir acesso apenas a admins."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# GESTÃO DE USUÁRIOS
# ==============================================================================

@admin_bp.route('/usuarios')
@admin_required
def listar_usuarios():
    """Lista todos os usuários."""
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    filiais = Filial.query.filter_by(ativa=True).order_by(Filial.nome).all()
    return render_template('admin/usuarios.html', usuarios=usuarios, filiais=filiais)


@admin_bp.route('/usuarios/criar', methods=['POST'])
@admin_required
def criar_usuario():
    """Cria um novo usuário."""
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    senha = request.form.get('senha', '')
    role = request.form.get('role', 'consultor')
    filiais_ids = request.form.getlist('filiais')
    
    if not nome or not email or not senha:
        flash('Preencha todos os campos obrigatórios.', 'error')
        return redirect(url_for('admin.listar_usuarios'))
    
    if Usuario.query.filter_by(email=email).first():
        flash('Já existe um usuário com este email.', 'error')
        return redirect(url_for('admin.listar_usuarios'))
    
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash(senha),
        role=role,
        ativo=True
    )
    
    # Vincula filiais (se consultor)
    if role == 'consultor' and filiais_ids:
        for filial_id in filiais_ids:
            filial = Filial.query.get(int(filial_id))
            if filial:
                usuario.filiais.append(filial)
    
    db.session.add(usuario)
    db.session.commit()
    
    flash(f'Usuário {nome} criado com sucesso!', 'success')
    return redirect(url_for('admin.listar_usuarios'))


@admin_bp.route('/usuarios/<int:id>/editar', methods=['POST'])
@admin_required
def editar_usuario(id):
    """Edita um usuário existente."""
    usuario = Usuario.query.get_or_404(id)
    
    usuario.nome = request.form.get('nome', usuario.nome).strip()
    usuario.email = request.form.get('email', usuario.email).strip().lower()
    usuario.role = request.form.get('role', usuario.role)
    usuario.ativo = request.form.get('ativo') == 'on'
    
    # Atualiza senha se fornecida
    nova_senha = request.form.get('senha', '').strip()
    if nova_senha:
        usuario.set_senha(nova_senha)
    
    # Atualiza filiais
    filiais_ids = request.form.getlist('filiais')
    usuario.filiais = []
    if usuario.role == 'consultor':
        for filial_id in filiais_ids:
            filial = Filial.query.get(int(filial_id))
            if filial:
                usuario.filiais.append(filial)
    
    db.session.commit()
    flash(f'Usuário {usuario.nome} atualizado!', 'success')
    return redirect(url_for('admin.listar_usuarios'))


@admin_bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
@admin_required
def excluir_usuario(id):
    """Exclui (desativa) um usuário."""
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'error')
        return redirect(url_for('admin.listar_usuarios'))
    
    usuario.ativo = False
    db.session.commit()
    flash(f'Usuário {usuario.nome} desativado.', 'info')
    return redirect(url_for('admin.listar_usuarios'))


# ==============================================================================
# GESTÃO DE FILIAIS
# ==============================================================================

@admin_bp.route('/filiais')
@admin_required
def listar_filiais():
    """Lista todas as filiais."""
    from datetime import date
    filiais = Filial.query.order_by(Filial.nome).all()
    return render_template('admin/filiais.html', filiais=filiais, now=date.today())


@admin_bp.route('/filiais/criar', methods=['POST'])
@admin_required
def criar_filial():
    """Cria uma nova filial."""
    nome = request.form.get('nome', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    uf = request.form.get('uf', '').strip().upper()
    endereco = request.form.get('endereco', '').strip()
    cert_path = request.form.get('cert_path', '').strip()
    
    if not nome or not cnpj or not uf:
        flash('Preencha todos os campos obrigatórios.', 'error')
        return redirect(url_for('admin.listar_filiais'))
    
    # Remove formatação do CNPJ
    cnpj_limpo = Filial.formatar_cnpj(cnpj)
    
    if Filial.query.filter_by(cnpj=cnpj_limpo).first():
        flash('Já existe uma filial com este CNPJ.', 'error')
        return redirect(url_for('admin.listar_filiais'))
    
    filial = Filial(
        nome=nome,
        cnpj=cnpj_limpo,
        uf=uf,
        endereco=endereco,
        cert_path=cert_path,
        ativa=True
    )
    
    db.session.add(filial)
    db.session.commit()
    
    flash(f'Filial {nome} criada! Configure CERT_FILIAL_{filial.id}_PASS no .env', 'success')
    return redirect(url_for('admin.listar_filiais'))


@admin_bp.route('/filiais/<int:id>/editar', methods=['POST'])
@admin_required
def editar_filial(id):
    """Edita uma filial existente."""
    from datetime import datetime

    filial = Filial.query.get_or_404(id)

    filial.nome = request.form.get('nome', filial.nome).strip()
    filial.uf = request.form.get('uf', filial.uf).strip().upper()
    filial.endereco = request.form.get('endereco', filial.endereco or '').strip()
    filial.cert_path = request.form.get('cert_path', filial.cert_path or '').strip()
    filial.ativa = request.form.get('ativa') == 'on'

    # Validade do certificado
    cert_validade = request.form.get('cert_validade', '')
    if cert_validade:
        try:
            filial.cert_validade = datetime.strptime(cert_validade, '%Y-%m-%d').date()
        except ValueError:
            pass

    db.session.commit()
    flash(f'Filial {filial.nome} atualizada!', 'success')
    return redirect(url_for('admin.listar_filiais'))


# ==============================================================================
# AUDITORIA
# ==============================================================================

@admin_bp.route('/auditoria')
@admin_required
def listar_auditoria():
    """Lista o log de auditoria."""
    from datetime import datetime, timedelta

    page = request.args.get('page', 1, type=int)
    busca = request.args.get('busca', '').strip()
    usuario_id = request.args.get('usuario_id', type=int)
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    per_page = 50

    query = Auditoria.query

    # Filtro de busca por placa
    if busca:
        query = query.filter(Auditoria.placa_chassi.ilike(f'%{busca}%'))

    # Filtro por usuário
    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)

    # Filtro por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Auditoria.data_consulta >= dt_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Auditoria.data_consulta < dt_fim)
        except ValueError:
            pass

    auditorias = query\
        .order_by(Auditoria.data_consulta.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()

    return render_template('admin/auditoria.html',
                           auditorias=auditorias,
                           usuarios=usuarios)


@admin_bp.route('/auditoria/json')
@admin_required
def auditoria_json():
    """Retorna auditoria em JSON (para relatórios)."""
    limit = request.args.get('limit', 100, type=int)
    
    auditorias = Auditoria.query\
        .order_by(Auditoria.data_consulta.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'sucesso': True,
        'total': len(auditorias),
        'auditorias': [
            {
                'id': a.id,
                'usuario': a.usuario.nome if a.usuario else 'N/A',
                'filial': a.filial.nome if a.filial else 'N/A',
                'placa_chassi': a.placa_chassi,
                'tipo_busca': a.tipo_busca,
                'status': a.status,
                'data': a.data_consulta.isoformat()
            }
            for a in auditorias
        ]
    })


@admin_bp.route('/auditoria/excel')
@admin_required
def auditoria_excel():
    """Exporta auditoria em Excel (CSV)."""
    from flask import Response
    import csv
    from io import StringIO

    auditorias = Auditoria.query\
        .order_by(Auditoria.data_consulta.desc())\
        .limit(1000)\
        .all()

    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    # Header
    writer.writerow([
        'Data/Hora', 'Usuario', 'Filial', 'Placa/Chassi',
        'Tipo', 'Status', 'IP', 'Resultado'
    ])

    # Dados
    for a in auditorias:
        writer.writerow([
            a.data_consulta.strftime('%d/%m/%Y %H:%M:%S'),
            a.usuario.nome if a.usuario else 'N/A',
            a.filial.nome if a.filial else 'N/A',
            a.placa_chassi,
            a.tipo_busca,
            a.status,
            a.ip_origem or '',
            a.resultado or ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=auditoria_i9.csv'
        }
    )
