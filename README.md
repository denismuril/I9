# Sistema I9 - Enterprise Edition

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Sistema de **Consulta de Histórico Veicular** para concessionárias, com integração ao DETRAN via certificados digitais.

## 🚀 Funcionalidades

- 🔐 **Autenticação RBAC** - Admin e Consultor
- 🏢 **Multi-Filial** - Cada filial com seu certificado digital
- 📋 **Auditoria Completa** - Registro de todas as consultas
- 🔒 **Segurança Enterprise** - Senhas e certificados via variáveis de ambiente
- 🗄️ **PostgreSQL** - Banco de dados profissional

## 📦 Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Backend | Flask 3.0 + SQLAlchemy |
| Banco de Dados | PostgreSQL |
| Autenticação | Flask-Login |
| Migrations | Flask-Migrate |
| Frontend | TailwindCSS |

## 🛠️ Instalação

### 1. Clonar Repositório

```bash
git clone https://github.com/denismuril/I9.git
cd I9
```

### 2. Instalar PostgreSQL (Ubuntu/AWS)

```bash
sudo bash setup_postgres.sh
```

### 3. Configurar Ambiente

```bash
cp .env.example .env
nano .env  # Configure DATABASE_URL e demais variáveis
```

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5. Iniciar Aplicação

```bash
python3 run.py
```

Acesse: `http://localhost:5000`

**Login padrão:** `admin@i9sistema.com` / `admin123`

## 📁 Estrutura do Projeto

```
I9/
├── run.py                  # Entry point
├── config.py               # Configurações
├── setup_postgres.sh       # Script instalação DB
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py         # Factory pattern
│   ├── extensions.py       # SQLAlchemy, Login
│   ├── models/             # Modelos de dados
│   │   ├── usuario.py
│   │   ├── filial.py
│   │   └── auditoria.py
│   ├── routes/             # Blueprints
│   │   ├── auth.py
│   │   ├── main.py
│   │   ├── admin.py
│   │   └── consulta.py
│   └── templates/          # HTML
```

## 🔐 Configuração de Certificados

1. Cadastre a filial no painel Admin
2. Adicione ao `.env`:

```env
CERT_FILIAL_1_PASS=senha_do_certificado
```

3. Configure o caminho do `.pfx` na filial

## 📊 API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/conectar_filial` | Conectar a uma filial |
| POST | `/api/consultar` | Consultar veículo |
| GET | `/api/historico` | Histórico do usuário |
| GET | `/admin/auditoria/json` | Exportar auditoria |

## 🚀 Deploy AWS

```bash
cd /home/ubuntu/I9 && git pull origin main && pip install -r requirements.txt && pkill -f "python3 run.py"; nohup python3 run.py > ~/I9/app.log 2>&1 &
```

## 📝 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

**Sistema I9 v2.0** - Enterprise Edition
