"""
Sistema I9 - Configuração de Certificados por Filial
Gerenciamento seguro de certificados digitais para autenticação DETRAN

IMPORTANTE: Nenhuma senha ou caminho sensível fica neste arquivo.
Todos os dados são lidos de variáveis de ambiente (.env)
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================

class Config:
    """Configurações gerais da aplicação."""
    
    # Chave secreta para sessões Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    
    # Banco de dados
    DATABASE = 'sistema_i9.db'
    
    # API Infosimples
    INFOSIMPLES_API_KEY = os.getenv('INFOSIMPLES_API_KEY', '')
    
    # URLs da API
    API_URLS = {
        'detran_restricoes': 'https://api.infosimples.com/api/v2/consultas/detran/restricoes',
        'detran_veiculos': 'https://api.infosimples.com/api/v2/consultas/detran/veiculos',
    }


# ==============================================================================
# MAPEAMENTO DE FILIAIS -> CERTIFICADOS
# ==============================================================================

# Dicionário de filiais disponíveis
# Cada filial tem: nome, ID, variáveis de ambiente para certificado
FILIAIS = {
    'matriz_sp': {
        'id': 'matriz_sp',
        'nome': 'Matriz São Paulo',
        'uf': 'SP',
        'cert_path_env': 'CERT_MATRIZ_SP_PATH',
        'cert_pass_env': 'CERT_MATRIZ_SP_PASS',
    },
    'filial_rj': {
        'id': 'filial_rj',
        'nome': 'Filial Rio de Janeiro',
        'uf': 'RJ',
        'cert_path_env': 'CERT_FILIAL_RJ_PATH',
        'cert_pass_env': 'CERT_FILIAL_RJ_PASS',
    },
    'filial_mg': {
        'id': 'filial_mg',
        'nome': 'Filial Minas Gerais',
        'uf': 'MG',
        'cert_path_env': 'CERT_FILIAL_MG_PATH',
        'cert_pass_env': 'CERT_FILIAL_MG_PASS',
    },
}


@dataclass
class CertificadoInfo:
    """Informações de um certificado digital."""
    filial_id: str
    filial_nome: str
    uf: str
    caminho: str
    senha: str


def obter_certificado_filial(filial_id: str) -> Optional[CertificadoInfo]:
    """
    Obtém as informações do certificado para uma filial específica.
    
    Args:
        filial_id: ID da filial (ex: 'matriz_sp', 'filial_rj')
    
    Returns:
        CertificadoInfo com caminho e senha do certificado, ou None se não encontrado
    """
    if filial_id not in FILIAIS:
        return None
    
    filial = FILIAIS[filial_id]
    
    # Lê caminho e senha das variáveis de ambiente
    caminho = os.getenv(filial['cert_path_env'], '')
    senha = os.getenv(filial['cert_pass_env'], '')
    
    if not caminho or not senha:
        return None
    
    return CertificadoInfo(
        filial_id=filial['id'],
        filial_nome=filial['nome'],
        uf=filial['uf'],
        caminho=caminho,
        senha=senha
    )


def listar_filiais() -> list:
    """
    Lista todas as filiais disponíveis (sem expor dados sensíveis).
    
    Returns:
        Lista de dicionários com id e nome de cada filial
    """
    return [
        {'id': f['id'], 'nome': f['nome'], 'uf': f['uf']}
        for f in FILIAIS.values()
    ]


def simular_autenticacao_certificado(cert_info: CertificadoInfo) -> Dict:
    """
    Simula a leitura de um certificado .pfx e autenticação com o DETRAN.
    
    Em produção, esta função:
    1. Leria o arquivo .pfx usando a biblioteca 'cryptography' ou 'pyOpenSSL'
    2. Extrairia o certificado e chave privada
    3. Faria a autenticação mTLS com a API do DETRAN
    
    Args:
        cert_info: Informações do certificado
    
    Returns:
        Dicionário com status da autenticação
    """
    # Simula verificação do certificado
    # Em produção, aqui seria feita a leitura real do .pfx:
    #
    # from cryptography.hazmat.primitives.serialization import pkcs12
    # with open(cert_info.caminho, 'rb') as f:
    #     private_key, certificate, chain = pkcs12.load_key_and_certificates(
    #         f.read(), 
    #         cert_info.senha.encode()
    #     )
    
    # Simulação de sucesso
    return {
        'sucesso': True,
        'filial': cert_info.filial_nome,
        'uf': cert_info.uf,
        'mensagem': f'Conexão com DETRAN-{cert_info.uf} estabelecida via certificado',
        'validade_sessao': 3600,  # 1 hora em segundos
    }


# ==============================================================================
# CREDENCIAIS DE USUÁRIOS (lidas de variáveis de ambiente)
# ==============================================================================

def obter_usuarios() -> Dict[str, str]:
    """
    Obtém as credenciais de usuários das variáveis de ambiente.
    
    Returns:
        Dicionário usuário -> senha
    """
    return {
        'admin': os.getenv('USER_ADMIN_PASS', ''),
        'vendedor': os.getenv('USER_VENDEDOR_PASS', ''),
    }


def validar_usuario(usuario: str, senha: str) -> bool:
    """
    Valida as credenciais de um usuário.
    
    Args:
        usuario: Nome de usuário
        senha: Senha fornecida
    
    Returns:
        True se válido, False caso contrário
    """
    usuarios = obter_usuarios()
    return usuario in usuarios and usuarios[usuario] == senha and senha != ''
