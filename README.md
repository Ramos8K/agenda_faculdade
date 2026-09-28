# AgendaFácil

Projeto acadêmico de Engenharia de Software II.

## Objetivo
Aplicação web para gerenciamento de agendamentos de uma barbearia/salão.

## Funcionalidades
- Cadastro de clientes
- Cadastro de profissionais
- Cadastro de serviços
- Criação de agendamentos
- Validação de conflito de horário
- Alteração de status: Agendado, Realizado e Cancelado
- Dashboard com indicadores básicos

## Tecnologias
- Python
- Flask
- SQLite
- HTML5
- CSS3
- Jinja2
- Pytest

## Como executar
1. Instale Python 3.11+
2. No terminal:
   pip install -r requirements.txt
3. Execute:
   python app.py
4. Acesse:
   http://127.0.0.1:5000

## Testes
Execute:
pytest

## Estrutura
- app.py: rotas e regras de negócio
- templates/: camada de visualização
- static/: CSS
- tests/: testes automatizados
- agendafacil.db: criado automaticamente na primeira execução

## Regra de negócio principal
Um profissional não pode possuir dois agendamentos ativos na mesma data e horário.
