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
    """Simula consulta à API (mock para demonstração)."""
    
    veiculos_simulados = {
        'ABC1234': {
            'encontrado': True,
            'dados_veiculo': {
                'placa': 'ABC-1234',
                'chassi': '9BWZZZ377VT004251',
                'renavam': '123456789',
                'modelo': 'Volkswagen Gol 1.0',
                'ano_fabricacao': 2020,
                'ano_modelo': 2021,
                'cor': 'Prata',
                'combustivel': 'Flex',
                'categoria': 'Particular',
                'uf': 'SP'
            },
            'multas': {
                'possui_multas': True,
                'quantidade': 2,
                'valor_total': 293.47,
                'detalhes': [
                    {'data': '15/03/2024', 'descricao': 'Excesso de velocidade até 20%', 'valor': 130.16, 'local': 'Av. Paulista, 1000 - São Paulo/SP'},
                    {'data': '22/08/2024', 'descricao': 'Estacionar em local proibido', 'valor': 163.31, 'local': 'Rua Augusta, 500 - São Paulo/SP'}
                ]
            },
            'ipva': {'situacao': 'PAGO', 'ano_referencia': 2024, 'valor': 1250.00, 'vencimento': '15/01/2024'},
            'restricoes': {'possui_restricoes': False, 'detalhes': []},
            'leilao': {'possui_historico_leilao': False, 'detalhes': None},
            'proprietarios': {'quantidade': 2, 'historico': [
                {'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2020 - 2022'},
                {'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2022 - Atual'}
            ]}
        },
        'XYZ9876': {
            'encontrado': True,
            'dados_veiculo': {
                'placa': 'XYZ-9876', 'chassi': '9BGRD08X04G117974', 'renavam': '987654321',
                'modelo': 'Chevrolet Onix Plus 1.0 Turbo', 'ano_fabricacao': 2022, 'ano_modelo': 2023,
                'cor': 'Preto', 'combustivel': 'Flex', 'categoria': 'Particular', 'uf': 'RJ'
            },
            'multas': {'possui_multas': False, 'quantidade': 0, 'valor_total': 0, 'detalhes': []},
            'ipva': {'situacao': 'PENDENTE', 'ano_referencia': 2024, 'valor': 2100.00, 'vencimento': '20/02/2024'},
            'restricoes': {'possui_restricoes': True, 'detalhes': [
                {'tipo': 'Alienação Fiduciária', 'instituicao': 'Banco Bradesco S.A.', 'data_inclusao': '10/01/2023'}
            ]},
            'leilao': {'possui_historico_leilao': False, 'detalhes': None},
            'proprietarios': {'quantidade': 1, 'historico': [{'tipo': 'Pessoa Física', 'uf': 'RJ', 'periodo': '2023 - Atual'}]}
        },
        'DEF5678': {
            'encontrado': True,
            'dados_veiculo': {
                'placa': 'DEF-5678', 'chassi': '93Y4SRD64EJ123456', 'renavam': '456789123',
                'modelo': 'Toyota Corolla XEi 2.0', 'ano_fabricacao': 2018, 'ano_modelo': 2019,
                'cor': 'Branco Pérola', 'combustivel': 'Flex', 'categoria': 'Particular', 'uf': 'MG'
            },
            'multas': {'possui_multas': True, 'quantidade': 5, 'valor_total': 1520.89, 'detalhes': [
                {'data': '05/01/2024', 'descricao': 'Avançar sinal vermelho', 'valor': 293.47, 'local': 'Av. Afonso Pena - BH/MG'},
                {'data': '12/02/2024', 'descricao': 'Excesso de velocidade acima de 50%', 'valor': 880.41, 'local': 'BR-040, Km 15 - MG'}
            ]},
            'ipva': {'situacao': 'ATRASADO', 'ano_referencia': 2024, 'valor': 3200.00, 'vencimento': '18/03/2024'},
            'restricoes': {'possui_restricoes': True, 'detalhes': [
                {'tipo': 'Roubo/Furto', 'data_inclusao': '25/11/2023', 'boletim_ocorrencia': 'BO 2023/123456'}
            ]},
            'leilao': {'possui_historico_leilao': True, 'detalhes': {
                'leiloeiro': 'Leilões Brasil S.A.', 'data_leilao': '15/06/2020',
                'motivo': 'Recuperado de Sinistro', 'condicao': 'Avarias de Média Monta'
            }},
            'proprietarios': {'quantidade': 4, 'historico': [
                {'tipo': 'Pessoa Jurídica', 'uf': 'SP', 'periodo': '2019 - 2020'},
                {'tipo': 'Leiloeiro Oficial', 'uf': 'SP', 'periodo': '2020 - 2020'},
                {'tipo': 'Pessoa Física', 'uf': 'MG', 'periodo': '2020 - 2022'},
                {'tipo': 'Pessoa Física', 'uf': 'MG', 'periodo': '2022 - Atual'}
            ]}
        }
    }
    
    placa_normalizada = re.sub(r'[^A-Z0-9]', '', placa_chassi.upper())
    
    if placa_normalizada in veiculos_simulados:
        return veiculos_simulados[placa_normalizada]
    
    # Retorno genérico
    return {
        'encontrado': True,
        'dados_veiculo': {
            'placa': placa_chassi.upper(), 'chassi': f'9BWZZZ377VT{hash(placa_chassi) % 999999:06d}',
            'renavam': f'{hash(placa_chassi) % 999999999:09d}', 'modelo': 'Fiat Argo 1.0',
            'ano_fabricacao': 2021, 'ano_modelo': 2022, 'cor': 'Vermelho',
            'combustivel': 'Flex', 'categoria': 'Particular', 'uf': 'SP'
        },
        'multas': {'possui_multas': False, 'quantidade': 0, 'valor_total': 0, 'detalhes': []},
        'ipva': {'situacao': 'PAGO', 'ano_referencia': 2024, 'valor': 980.00, 'vencimento': '10/01/2024'},
        'restricoes': {'possui_restricoes': False, 'detalhes': []},
        'leilao': {'possui_historico_leilao': False, 'detalhes': None},
        'proprietarios': {'quantidade': 1, 'historico': [{'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2022 - Atual'}]}
    }
