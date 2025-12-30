"""
Sistema I9 - Rotas de Consulta Veicular (API)
"""

import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Filial, Auditoria

consulta_bp = Blueprint('consulta', __name__)


# ==============================================================================
# CONEXÃO COM FILIAL
# ==============================================================================

@consulta_bp.route('/conectar_filial', methods=['POST'])
@login_required
def conectar_filial():
    """Conecta a uma filial usando o certificado digital."""
    filial_id = request.form.get('filial_id', type=int)
    
    if not filial_id:
        return jsonify({'sucesso': False, 'erro': 'Selecione uma filial.'})
    
    # Verifica permissão
    if not current_user.pode_acessar_filial(filial_id):
        return jsonify({'sucesso': False, 'erro': 'Você não tem permissão para esta filial.'})
    
    filial = Filial.query.get(filial_id)
    if not filial or not filial.ativa:
        return jsonify({'sucesso': False, 'erro': 'Filial não encontrada ou inativa.'})
    
    # Simula conexão com DETRAN
    resultado = filial.simular_conexao_detran()
    
    if resultado['sucesso']:
        # Armazena na sessão
        session['filial_conectada_id'] = filial.id
        session['filial_conectada_em'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        return jsonify({
            'sucesso': True,
            'mensagem': resultado['mensagem'],
            'filial': filial.nome,
            'uf': filial.uf
        })
    else:
        return jsonify({'sucesso': False, 'erro': resultado.get('erro', 'Erro na conexão')})


@consulta_bp.route('/desconectar_filial', methods=['POST'])
@login_required
def desconectar_filial():
    """Desconecta da filial atual."""
    session.pop('filial_conectada_id', None)
    session.pop('filial_conectada_em', None)
    return jsonify({'sucesso': True, 'mensagem': 'Desconectado com sucesso.'})


# ==============================================================================
# CONSULTA VEICULAR
# ==============================================================================

@consulta_bp.route('/consultar', methods=['POST'])
@login_required
def consultar():
    """Processa a consulta de veículo."""
    # Verifica conexão com filial
    filial_id = session.get('filial_conectada_id')
    if not filial_id:
        return jsonify({
            'sucesso': False,
            'erro': 'É necessário conectar a uma filial antes de consultar.'
        })
    
    # Verifica permissão
    if not current_user.pode_acessar_filial(filial_id):
        session.pop('filial_conectada_id', None)
        return jsonify({
            'sucesso': False,
            'erro': 'Você não tem mais permissão para esta filial.'
        })
    
    placa_chassi = request.form.get('placa_chassi', '').strip()
    tipo_busca = request.form.get('tipo_busca', 'placa')
    
    if not placa_chassi:
        return jsonify({
            'sucesso': False,
            'erro': 'Por favor, informe a placa ou chassi do veículo.'
        })
    
    # Validação
    if tipo_busca == 'placa' and not validar_placa(placa_chassi):
        return jsonify({
            'sucesso': False,
            'erro': 'Formato de placa inválido. Use: ABC-1234 ou ABC1D23 (Mercosul).'
        })
    elif tipo_busca == 'chassi' and not validar_chassi(placa_chassi):
        return jsonify({
            'sucesso': False,
            'erro': 'Formato de chassi inválido. O chassi deve ter 17 caracteres alfanuméricos.'
        })
    
    # Realiza consulta (simulada)
    try:
        resultado = consultar_veiculo_api(placa_chassi, tipo_busca)
        
        # Registra auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            filial_id=filial_id,
            placa_chassi=placa_chassi,
            tipo_busca=tipo_busca,
            resultado=_resumo_resultado(resultado),
            status='sucesso' if resultado.get('encontrado') else 'nao_encontrado',
            ip_origem=request.remote_addr
        )
        
        return jsonify({
            'sucesso': True,
            'dados': resultado
        })
        
    except Exception as e:
        # Registra erro na auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            filial_id=filial_id,
            placa_chassi=placa_chassi,
            tipo_busca=tipo_busca,
            resultado=str(e),
            status='erro',
            ip_origem=request.remote_addr
        )
        
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao consultar veículo: {str(e)}'
        })


@consulta_bp.route('/historico')
@login_required
def historico():
    """Retorna o histórico de consultas do usuário."""
    auditorias = Auditoria.query\
        .filter_by(usuario_id=current_user.id)\
        .order_by(Auditoria.data_consulta.desc())\
        .limit(50)\
        .all()
    
    return jsonify({
        'sucesso': True,
        'consultas': [
            {
                'id': a.id,
                'data_consulta': a.data_consulta.strftime('%d/%m/%Y %H:%M'),
                'placa_chassi': a.placa_chassi,
                'tipo_busca': a.tipo_busca,
                'resultado_resumido': a.resultado[:100] if a.resultado else '',
                'status_consulta': a.status,
                'filial': a.filial.nome if a.filial else 'N/A'
            }
            for a in auditorias
        ]
    })


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def validar_placa(placa):
    """Valida o formato da placa brasileira."""
    placa_limpa = re.sub(r'[^A-Z0-9]', '', placa.upper())
    padrao_antigo = re.compile(r'^[A-Z]{3}[0-9]{4}$')
    padrao_mercosul = re.compile(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
    return bool(padrao_antigo.match(placa_limpa) or padrao_mercosul.match(placa_limpa))


def validar_chassi(chassi):
    """Valida o formato do chassi."""
    chassi_limpo = chassi.upper().strip()
    if len(chassi_limpo) != 17:
        return False
    return bool(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', chassi_limpo))


def _resumo_resultado(resultado):
    """Cria um resumo do resultado para auditoria."""
    if not resultado.get('encontrado'):
        return 'Veículo não encontrado'
    
    dados = resultado.get('dados_veiculo', {})
    return f"{dados.get('modelo', 'N/A')} | {dados.get('cor', 'N/A')} | {dados.get('ano_modelo', 'N/A')}"


def consultar_veiculo_api(placa_chassi, tipo_busca):
    """Consulta veículo via API Infosimples."""
    import requests
    from flask import current_app
    
    api_key = current_app.config.get('INFOSIMPLES_API_KEY')
    if not api_key:
        raise Exception('API Key Infosimples não configurada')
    
    placa_normalizada = re.sub(r'[^A-Z0-9]', '', placa_chassi.upper())
    
    # Endpoint Infosimples
    url = 'https://api.infosimples.com/api/v2/consultas/detran/sp/veiculo'
    
    params = {
        'placa': placa_normalizada,
        'token': api_key,
        'timeout': 300
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        data = response.json()
        
        # Verifica sucesso da API
        if data.get('code') != 200:
            error_msg = data.get('message', 'Erro na consulta')
            if 'not_found' in str(data.get('code_message', '')).lower():
                return {'encontrado': False, 'erro': 'Veículo não encontrado'}
            raise Exception(error_msg)
        
        # Extrai dados da resposta
        veiculo = data.get('data', [{}])[0] if data.get('data') else {}
        
        # Formata resposta no padrão do sistema
        resultado = {
            'encontrado': True,
            'dados_veiculo': {
                'placa': veiculo.get('placa', placa_normalizada),
                'chassi': veiculo.get('chassi', 'N/A'),
                'renavam': veiculo.get('renavam', 'N/A'),
                'modelo': veiculo.get('modelo', veiculo.get('marca_modelo', 'N/A')),
                'ano_fabricacao': veiculo.get('ano_fabricacao', 'N/A'),
                'ano_modelo': veiculo.get('ano_modelo', 'N/A'),
                'cor': veiculo.get('cor', 'N/A'),
                'combustivel': veiculo.get('combustivel', 'N/A'),
                'categoria': veiculo.get('categoria', veiculo.get('tipo', 'N/A')),
                'uf': veiculo.get('uf', 'SP')
            },
            'multas': {
                'possui_multas': bool(veiculo.get('debitos_multas')),
                'quantidade': len(veiculo.get('multas', [])) if veiculo.get('multas') else 0,
                'valor_total': float(veiculo.get('debitos_multas', 0) or 0),
                'detalhes': veiculo.get('multas', [])
            },
            'ipva': {
                'situacao': veiculo.get('situacao_ipva', 'N/A'),
                'ano_referencia': veiculo.get('ano_ipva', 2024),
                'valor': float(veiculo.get('debitos_ipva', 0) or 0),
                'vencimento': 'N/A'
            },
            'restricoes': {
                'possui_restricoes': bool(veiculo.get('restricoes')),
                'detalhes': veiculo.get('restricoes', []) if isinstance(veiculo.get('restricoes'), list) else []
            },
            'leilao': {
                'possui_historico_leilao': bool(veiculo.get('leilao')),
                'detalhes': veiculo.get('leilao')
            },
            'proprietarios': {
                'quantidade': 1,
                'historico': [{'tipo': 'Atual', 'uf': veiculo.get('uf', 'SP'), 'periodo': 'Atual'}]
            }
        }
        
        return resultado
        
    except requests.exceptions.Timeout:
        raise Exception('Timeout na consulta. Tente novamente.')
    except requests.exceptions.RequestException as e:
        raise Exception(f'Erro de conexão: {str(e)}')

