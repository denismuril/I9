"""
Sistema I9 - Consulta de Histórico Veicular
Aplicação Flask para concessionárias de veículos
Autor: Sistema I9
"""

import os
import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

# ==============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==============================================================================

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta para sessões

# Configuração do banco de dados
DATABASE = 'sistema_i9.db'

# Credenciais de teste (ALTERAR EM PRODUÇÃO!)
USUARIOS = {
    'admin': 'admin123',
    'vendedor': 'venda2024'
}


# ==============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ==============================================================================

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa o banco de dados criando as tabelas necessárias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario VARCHAR(100) NOT NULL,
            placa_chassi VARCHAR(50) NOT NULL,
            tipo_busca VARCHAR(20) NOT NULL,
            resultado_resumido TEXT,
            status_consulta VARCHAR(20) DEFAULT 'sucesso'
        )
    ''')
    
    conn.commit()
    conn.close()


# ==============================================================================
# CONFIGURAÇÃO DA API INFOSIMPLES - DETRAN RESTRIÇÕES
# ==============================================================================
# 
# Documentação: https://infosimples.com/consultas/detran-restricoes/
# 
# COMO CONFIGURAR:
# 1. Acesse https://infosimples.com e crie sua conta
# 2. Obtenha sua API Key no painel do usuário
# 3. Substitua "SUA_API_KEY_AQUI" pela sua chave
# 4. Descomente a função consultar_veiculo_api_real() abaixo
#
# ==============================================================================

# Sua API Key da Infosimples (obtenha em https://infosimples.com)
INFOSIMPLES_API_KEY = "_IMLYfOwRzmPbMATaNvO984h-fej5E023JKIyyrO"

# URLs das APIs da Infosimples
API_URLS = {
    'detran_restricoes': 'https://api.infosimples.com/api/v2/consultas/detran/restricoes',
    'detran_veiculos': 'https://api.infosimples.com/api/v2/consultas/detran/veiculos',
}

# ==============================================================================
# OBSERVAÇÕES POR ESTADO - DETRAN RESTRIÇÕES
# ==============================================================================
# 
# Cada estado brasileiro pode ter particularidades na consulta. Abaixo as 
# observações importantes:
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  ESTADO  ║  OBSERVAÇÕES                                                      ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  AC      ║  Consulta por placa e renavam                                     ║
# ║  AL      ║  Consulta por placa. Pode exigir captcha em momentos de pico      ║
# ║  AM      ║  Consulta por placa e renavam                                     ║
# ║  AP      ║  Consulta por placa                                               ║
# ║  BA      ║  Consulta por placa e renavam. Sistema pode ter instabilidades    ║
# ║  CE      ║  Consulta por placa. Retorna restrições detalhadas                ║
# ║  DF      ║  Consulta por placa e renavam. Sistema estável                    ║
# ║  ES      ║  Consulta por placa. Pode ter delays em horários de pico          ║
# ║  GO      ║  Consulta por placa e renavam                                     ║
# ║  MA      ║  Consulta por placa                                               ║
# ║  MG      ║  Consulta por placa. Sistema robusto e estável                    ║
# ║  MS      ║  Consulta por placa e renavam                                     ║
# ║  MT      ║  Consulta por placa                                               ║
# ║  PA      ║  Consulta por placa. Pode ter instabilidades ocasionais           ║
# ║  PB      ║  Consulta por placa                                               ║
# ║  PE      ║  Consulta por placa e chassi. Sistema bem estruturado             ║
# ║  PI      ║  Consulta por placa                                               ║
# ║  PR      ║  Consulta por placa e renavam. Excelente detalhamento             ║
# ║  RJ      ║  Consulta por placa, renavam e chassi. Alta disponibilidade       ║
# ║  RN      ║  Consulta por placa                                               ║
# ║  RO      ║  Consulta por placa                                               ║
# ║  RR      ║  Consulta por placa. Sistema pode ter delays                      ║
# ║  RS      ║  Consulta por placa e renavam. Sistema muito estável              ║
# ║  SC      ║  Consulta por placa. Retorna dados completos                      ║
# ║  SE      ║  Consulta por placa                                               ║
# ║  SP      ║  Consulta por placa, renavam e chassi. Sistema mais robusto       ║
# ║  TO      ║  Consulta por placa                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# ==============================================================================

# ==============================================================================
# FUNÇÃO DE INTEGRAÇÃO REAL COM API INFOSIMPLES (DESCOMENTE PARA USAR)
# ==============================================================================
#
# REQUISITOS POR ESTADO:
# ----------------------
# TODOS OS ESTADOS: uf, placa, renavam, chassi (obrigatórios)
# TO (Tocantins): + cpf_cnpj (CPF/CNPJ do proprietário)
# MG, RS, SC: + login_govbr, senha_govbr (credenciais gov.br)
# SP (São Paulo): + login_detran_sp, senha_detran_sp (credenciais DETRAN-SP)
#
# import requests
#
# def consultar_veiculo_api_real(uf, placa, renavam, chassi, **kwargs):
#     """
#     Consulta real à API da Infosimples - DETRAN Restrições
#     
#     Args:
#         uf: Estado do veículo (sigla, ex: SP, RJ, MG)
#         placa: Placa do veículo (formato: ABC1234 ou ABC1D23)
#         renavam: Número do RENAVAM
#         chassi: Número do chassi (17 caracteres)
#         **kwargs: Campos adicionais por estado:
#             - cpf_cnpj: CPF/CNPJ do proprietário (TO)
#             - login_govbr: Login gov.br (MG, RS, SC)
#             - senha_govbr: Senha gov.br (MG, RS, SC)
#             - login_detran_sp: Login DETRAN-SP (SP)
#             - senha_detran_sp: Senha DETRAN-SP (SP)
#     
#     Returns:
#         dict: Dados retornados pela API
#     """
#     
#     if INFOSIMPLES_API_KEY == "SUA_API_KEY_AQUI":
#         raise ValueError("Configure sua API Key da Infosimples!")
#     
#     # Payload base (obrigatório para todos os estados)
#     payload = {
#         'token': INFOSIMPLES_API_KEY,
#         'uf': uf.upper(),
#         'placa': placa.upper().replace('-', ''),
#         'renavam': renavam,
#         'chassi': chassi.upper(),
#         'timeout': 300
#     }
#     
#     # Campos específicos por estado
#     if uf.upper() == 'TO':
#         # Tocantins: CPF/CNPJ do proprietário
#         if 'cpf_cnpj' in kwargs:
#             payload['cpf'] = kwargs['cpf_cnpj']
#     
#     elif uf.upper() in ['MG', 'RS', 'SC']:
#         # MG, RS, SC: Credenciais gov.br
#         if 'login_govbr' in kwargs:
#             payload['govbr_user'] = kwargs['login_govbr']
#         if 'senha_govbr' in kwargs:
#             payload['govbr_password'] = kwargs['senha_govbr']
#     
#     elif uf.upper() == 'SP':
#         # São Paulo: Credenciais DETRAN-SP
#         if 'login_detran_sp' in kwargs:
#             payload['detran_user'] = kwargs['login_detran_sp']
#         if 'senha_detran_sp' in kwargs:
#             payload['detran_password'] = kwargs['senha_detran_sp']
#     
#     try:
#         response = requests.post(
#             API_URLS['detran_restricoes'],
#             data=payload,
#             timeout=120
#         )
#         response.raise_for_status()
#         
#         dados = response.json()
#         
#         if dados.get('code') == 200:
#             return {
#                 'encontrado': True,
#                 'dados_api': dados.get('data', []),
#                 'site_receipts': dados.get('site_receipts', [])
#             }
#         else:
#             return {
#                 'encontrado': False,
#                 'erro': dados.get('code_message', 'Erro desconhecido'),
#                 'codigo': dados.get('code')
#             }
#             
#     except requests.Timeout:
#         return {'encontrado': False, 'erro': 'Timeout. Tente novamente.'}
#     except requests.RequestException as e:
#         return {'encontrado': False, 'erro': f'Erro: {str(e)}'}

# ==============================================================================
# FUNÇÃO DE INTEGRAÇÃO COM API (SIMULADA PARA TESTES)
# ==============================================================================

def consultar_veiculo_api(placa_chassi, tipo_busca, **kwargs):
    """
    Simula a consulta à API da Infosimples para obter dados do veículo.
    
    Para usar a API REAL da Infosimples:
    1. Configure INFOSIMPLES_API_KEY acima com sua chave
    2. Descomente a função consultar_veiculo_api_real()
    3. Substitua esta função pela função real
    
    Args:
        placa_chassi: Placa ou chassi do veículo
        tipo_busca: 'placa' ou 'chassi'
    
    Returns:
        dict: Dados do veículo (simulados)
    """
    
    # Dados fictícios para demonstração
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
                    {
                        'data': '15/03/2024',
                        'descricao': 'Excesso de velocidade até 20%',
                        'valor': 130.16,
                        'local': 'Av. Paulista, 1000 - São Paulo/SP'
                    },
                    {
                        'data': '22/08/2024',
                        'descricao': 'Estacionar em local proibido',
                        'valor': 163.31,
                        'local': 'Rua Augusta, 500 - São Paulo/SP'
                    }
                ]
            },
            'ipva': {
                'situacao': 'PAGO',
                'ano_referencia': 2024,
                'valor': 1250.00,
                'vencimento': '15/01/2024'
            },
            'restricoes': {
                'possui_restricoes': False,
                'detalhes': []
            },
            'leilao': {
                'possui_historico_leilao': False,
                'detalhes': None
            },
            'proprietarios': {
                'quantidade': 2,
                'historico': [
                    {'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2020 - 2022'},
                    {'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2022 - Atual'}
                ]
            }
        },
        'XYZ9876': {
            'encontrado': True,
            'dados_veiculo': {
                'placa': 'XYZ-9876',
                'chassi': '9BGRD08X04G117974',
                'renavam': '987654321',
                'modelo': 'Chevrolet Onix Plus 1.0 Turbo',
                'ano_fabricacao': 2022,
                'ano_modelo': 2023,
                'cor': 'Preto',
                'combustivel': 'Flex',
                'categoria': 'Particular',
                'uf': 'RJ'
            },
            'multas': {
                'possui_multas': False,
                'quantidade': 0,
                'valor_total': 0,
                'detalhes': []
            },
            'ipva': {
                'situacao': 'PENDENTE',
                'ano_referencia': 2024,
                'valor': 2100.00,
                'vencimento': '20/02/2024',
                'parcelas_pagas': 2,
                'parcelas_totais': 3
            },
            'restricoes': {
                'possui_restricoes': True,
                'detalhes': [
                    {
                        'tipo': 'Alienação Fiduciária',
                        'instituicao': 'Banco Bradesco S.A.',
                        'data_inclusao': '10/01/2023'
                    }
                ]
            },
            'leilao': {
                'possui_historico_leilao': False,
                'detalhes': None
            },
            'proprietarios': {
                'quantidade': 1,
                'historico': [
                    {'tipo': 'Pessoa Física', 'uf': 'RJ', 'periodo': '2023 - Atual'}
                ]
            }
        },
        'DEF5678': {
            'encontrado': True,
            'dados_veiculo': {
                'placa': 'DEF-5678',
                'chassi': '93Y4SRD64EJ123456',
                'renavam': '456789123',
                'modelo': 'Toyota Corolla XEi 2.0',
                'ano_fabricacao': 2018,
                'ano_modelo': 2019,
                'cor': 'Branco Pérola',
                'combustivel': 'Flex',
                'categoria': 'Particular',
                'uf': 'MG'
            },
            'multas': {
                'possui_multas': True,
                'quantidade': 5,
                'valor_total': 1520.89,
                'detalhes': [
                    {
                        'data': '05/01/2024',
                        'descricao': 'Avançar sinal vermelho',
                        'valor': 293.47,
                        'local': 'Av. Afonso Pena - Belo Horizonte/MG'
                    },
                    {
                        'data': '12/02/2024',
                        'descricao': 'Excesso de velocidade acima de 50%',
                        'valor': 880.41,
                        'local': 'BR-040, Km 15 - MG'
                    }
                ]
            },
            'ipva': {
                'situacao': 'ATRASADO',
                'ano_referencia': 2024,
                'valor': 3200.00,
                'vencimento': '18/03/2024',
                'juros_multa': 480.00
            },
            'restricoes': {
                'possui_restricoes': True,
                'detalhes': [
                    {
                        'tipo': 'Roubo/Furto',
                        'data_inclusao': '25/11/2023',
                        'boletim_ocorrencia': 'BO 2023/123456'
                    }
                ]
            },
            'leilao': {
                'possui_historico_leilao': True,
                'detalhes': {
                    'leiloeiro': 'Leilões Brasil S.A.',
                    'data_leilao': '15/06/2020',
                    'motivo': 'Recuperado de Sinistro',
                    'condicao': 'Avarias de Média Monta'
                }
            },
            'proprietarios': {
                'quantidade': 4,
                'historico': [
                    {'tipo': 'Pessoa Jurídica', 'uf': 'SP', 'periodo': '2019 - 2020'},
                    {'tipo': 'Leiloeiro Oficial', 'uf': 'SP', 'periodo': '2020 - 2020'},
                    {'tipo': 'Pessoa Física', 'uf': 'MG', 'periodo': '2020 - 2022'},
                    {'tipo': 'Pessoa Física', 'uf': 'MG', 'periodo': '2022 - Atual'}
                ]
            }
        }
    }
    
    # Normaliza a entrada (remove hífen e espaços)
    placa_normalizada = re.sub(r'[^A-Z0-9]', '', placa_chassi.upper())
    
    # Verifica se o veículo existe nos dados simulados
    if placa_normalizada in veiculos_simulados:
        return veiculos_simulados[placa_normalizada]
    
    # Se não encontrar, retorna dados genéricos para demonstração
    return {
        'encontrado': True,
        'dados_veiculo': {
            'placa': placa_chassi.upper(),
            'chassi': f'9BWZZZ377VT{hash(placa_chassi) % 999999:06d}',
            'renavam': f'{hash(placa_chassi) % 999999999:09d}',
            'modelo': 'Fiat Argo 1.0',
            'ano_fabricacao': 2021,
            'ano_modelo': 2022,
            'cor': 'Vermelho',
            'combustivel': 'Flex',
            'categoria': 'Particular',
            'uf': 'SP'
        },
        'multas': {
            'possui_multas': False,
            'quantidade': 0,
            'valor_total': 0,
            'detalhes': []
        },
        'ipva': {
            'situacao': 'PAGO',
            'ano_referencia': 2024,
            'valor': 980.00,
            'vencimento': '10/01/2024'
        },
        'restricoes': {
            'possui_restricoes': False,
            'detalhes': []
        },
        'leilao': {
            'possui_historico_leilao': False,
            'detalhes': None
        },
        'proprietarios': {
            'quantidade': 1,
            'historico': [
                {'tipo': 'Pessoa Física', 'uf': 'SP', 'periodo': '2022 - Atual'}
            ]
        }
    }


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def validar_placa(placa):
    """
    Valida o formato da placa brasileira (antiga e Mercosul).
    
    Formatos válidos:
    - Padrão antigo: ABC-1234 ou ABC1234
    - Mercosul: ABC1D23
    """
    placa_limpa = re.sub(r'[^A-Z0-9]', '', placa.upper())
    
    # Padrão antigo: 3 letras + 4 números
    padrao_antigo = re.compile(r'^[A-Z]{3}[0-9]{4}$')
    
    # Mercosul: 3 letras + 1 número + 1 letra + 2 números
    padrao_mercosul = re.compile(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
    
    return bool(padrao_antigo.match(placa_limpa) or padrao_mercosul.match(placa_limpa))


def validar_chassi(chassi):
    """
    Valida o formato do chassi (17 caracteres alfanuméricos).
    Não pode conter I, O, Q (conforme padrão internacional).
    """
    chassi_limpo = chassi.upper().strip()
    
    if len(chassi_limpo) != 17:
        return False
    
    # Verifica se contém apenas caracteres válidos
    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', chassi_limpo):
        return False
    
    return True


def login_required(f):
    """Decorator para proteger rotas que requerem autenticação."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def salvar_consulta(usuario, placa_chassi, tipo_busca, resultado):
    """Salva a consulta no histórico do banco de dados."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cria um resumo do resultado
        if resultado.get('encontrado'):
            dados = resultado.get('dados_veiculo', {})
            resumo = f"{dados.get('modelo', 'N/A')} | {dados.get('cor', 'N/A')} | {dados.get('ano_modelo', 'N/A')}"
            status = 'sucesso'
        else:
            resumo = 'Veículo não encontrado'
            status = 'nao_encontrado'
        
        cursor.execute('''
            INSERT INTO historico_consultas 
            (usuario, placa_chassi, tipo_busca, resultado_resumido, status_consulta)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario, placa_chassi.upper(), tipo_busca, resumo, status))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao salvar consulta: {e}")


# ==============================================================================
# ROTAS DA APLICAÇÃO
# ==============================================================================

@app.route('/')
def index():
    """Redireciona para o login ou dashboard."""
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')
        
        if not usuario or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session['usuario'] = usuario
            session['login_time'] = datetime.now().strftime('%d/%m/%Y %H:%M')
            flash(f'Bem-vindo(a), {usuario}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Realiza o logout do usuário."""
    session.clear()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Página principal de consulta."""
    return render_template('dashboard.html', usuario=session.get('usuario'))


@app.route('/consultar', methods=['POST'])
@login_required
def consultar():
    """Processa a consulta de veículo."""
    placa_chassi = request.form.get('placa_chassi', '').strip()
    tipo_busca = request.form.get('tipo_busca', 'placa')
    
    # Validações
    if not placa_chassi:
        return jsonify({
            'sucesso': False,
            'erro': 'Por favor, informe a placa ou chassi do veículo.'
        })
    
    # Valida formato de acordo com o tipo de busca
    if tipo_busca == 'placa':
        if not validar_placa(placa_chassi):
            return jsonify({
                'sucesso': False,
                'erro': 'Formato de placa inválido. Use: ABC-1234 ou ABC1D23 (Mercosul).'
            })
    elif tipo_busca == 'chassi':
        if not validar_chassi(placa_chassi):
            return jsonify({
                'sucesso': False,
                'erro': 'Formato de chassi inválido. O chassi deve ter 17 caracteres alfanuméricos.'
            })
    
    # Realiza a consulta (simulada)
    try:
        resultado = consultar_veiculo_api(placa_chassi, tipo_busca)
        
        # Salva no histórico
        salvar_consulta(session.get('usuario'), placa_chassi, tipo_busca, resultado)
        
        return jsonify({
            'sucesso': True,
            'dados': resultado
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao consultar veículo: {str(e)}'
        })


@app.route('/historico')
@login_required
def historico():
    """Retorna o histórico de consultas do usuário."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Busca as últimas 50 consultas do usuário
        cursor.execute('''
            SELECT id, data_consulta, placa_chassi, tipo_busca, 
                   resultado_resumido, status_consulta
            FROM historico_consultas
            WHERE usuario = ?
            ORDER BY data_consulta DESC
            LIMIT 50
        ''', (session.get('usuario'),))
        
        consultas = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'sucesso': True,
            'consultas': [dict(c) for c in consultas]
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })


# ==============================================================================
# INICIALIZAÇÃO
# ==============================================================================

if __name__ == '__main__':
    # Inicializa o banco de dados
    init_db()
    
    # Inicia o servidor Flask
    print("\n" + "="*60)
    print("   SISTEMA I9 - Consulta Veicular")
    print("="*60)
    print("\n🚀 Servidor iniciado em: http://localhost:5000")
    print("\n📋 Credenciais de teste:")
    print("   Usuário: admin    | Senha: admin123")
    print("   Usuário: vendedor | Senha: venda2024")
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
