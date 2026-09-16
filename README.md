# Sistema de Chamados

Sistema web simples para abertura e acompanhamento de chamados internos
(solicitação de objetos, manutenção, etc). O setor responsável por atender
é identificado automaticamente pelo sistema com base no item descrito.

## Tecnologias
- Python + Flask
- SQLite

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

Acesse http://localhost:5000

## Popular com dados de teste (opcional)

```bash
python seed.py
```

## Funcionalidades
- Abertura de chamado (setor solicitante, nome, item)
- Classificação automática do setor responsável (TI, Almoxarifado, Manutenção)
- Listagem com filtro por status e setor
- Atualização de status e responsável pelo atendimento
