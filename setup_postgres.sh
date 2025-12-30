#!/bin/bash
# ==============================================================================
# Sistema I9 - Script de Instalação e Configuração do PostgreSQL
# Execute com: sudo bash setup_postgres.sh
# ==============================================================================

set -e

echo "=============================================="
echo "   Sistema I9 - Setup PostgreSQL"
echo "=============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variáveis (podem ser alteradas)
DB_NAME="sistema_i9_db"
DB_USER="i9_user"
DB_PASSWORD="${POSTGRES_PASSWORD:-I9SecurePass2024!}"

echo -e "${YELLOW}[1/5] Atualizando sistema...${NC}"
apt-get update -qq

echo -e "${YELLOW}[2/5] Instalando PostgreSQL...${NC}"
apt-get install -y postgresql postgresql-contrib libpq-dev

echo -e "${YELLOW}[3/5] Iniciando serviço PostgreSQL...${NC}"
systemctl start postgresql
systemctl enable postgresql

echo -e "${YELLOW}[4/5] Criando banco de dados e usuário...${NC}"

# Executa comandos como usuário postgres
sudo -u postgres psql <<EOF
-- Criar usuário se não existir
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
      CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}';
   END IF;
END
\$\$;

-- Criar banco se não existir
SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

-- Garantir permissões
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
ALTER USER ${DB_USER} CREATEDB;
EOF

echo -e "${YELLOW}[5/5] Configurando acesso local...${NC}"

# Permite conexão local com senha
PG_HBA=$(sudo -u postgres psql -t -P format=unaligned -c "SHOW hba_file;")
if ! grep -q "${DB_USER}" "$PG_HBA" 2>/dev/null; then
    echo "local   ${DB_NAME}   ${DB_USER}   md5" >> "$PG_HBA"
    echo "host    ${DB_NAME}   ${DB_USER}   127.0.0.1/32   md5" >> "$PG_HBA"
    systemctl reload postgresql
fi

echo ""
echo -e "${GREEN}=============================================="
echo "   ✅ PostgreSQL Configurado com Sucesso!"
echo "=============================================="
echo ""
echo "   Banco de Dados: ${DB_NAME}"
echo "   Usuário: ${DB_USER}"
echo "   Senha: ${DB_PASSWORD}"
echo ""
echo "   DATABASE_URL para .env:"
echo -e "   ${YELLOW}postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}${NC}"
echo ""
echo "=============================================="\
echo -e "${NC}"

# Testar conexão
echo -e "${YELLOW}Testando conexão...${NC}"
if PGPASSWORD="${DB_PASSWORD}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Conexão bem sucedida!${NC}"
else
    echo -e "${RED}⚠️  Erro na conexão. Verifique as configurações.${NC}"
fi

echo ""
echo "Próximos passos:"
echo "1. Copie a DATABASE_URL acima para o arquivo .env"
echo "2. Execute: flask db upgrade"
echo "3. Execute: python3 run.py"
