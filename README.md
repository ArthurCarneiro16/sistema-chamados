# Sistema de Chamados

🔗 **Demo ao vivo:** https://sistema-chamados-y8r6.onrender.com
*(hospedado no plano gratuito do Render — se estiver inativo, a primeira requisição pode levar ~50s pra "acordar" o serviço)*

Sistema web simples para abertura e acompanhamento de chamados internos
(solicitação de objetos, manutenção, etc). O setor responsável por atender
é identificado automaticamente pelo sistema com base no item descrito.

## Tecnologias
- Python + Flask
- SQLite
- Waitress (servidor WSGI de produção)
- Deploy: Render

## Como rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

Acesse http://localhost:5000

Para rodar com o servidor de produção (recomendado fora de ambiente de desenvolvimento):

```bash
python serve.py
```

## Popular com dados de teste (opcional)

```bash
python seed.py
```

## Funcionalidades
- Abertura de chamado (setor solicitante, nome, item)
- Classificação automática do setor responsável (TI, Almoxarifado, Manutenção)
- Listagem com filtro por status e setor, e ordenação por data
- Atualização automática de status e responsável pelo atendimento

