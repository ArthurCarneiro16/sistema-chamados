"""
Script para popular o banco com chamados de teste.
Roda: python3 seed.py (ou py -3.14 seed.py)
"""
from app import get_db, init_db, classificar_setor
from datetime import datetime, timedelta

init_db()
conn = get_db()

# limpa chamados existentes pra não duplicar toda vez que rodar
conn.execute("DELETE FROM chamados")

chamados_teste = [
    # (dias_atras, setor_solicitante, nome_solicitante, item, nome_responsavel, status)
    (3, "ADM", "Joao", "1 mouse e 1 monitor", "", "Aberto"),
    (2, "ADM", "Marcos", "1 teclado", "", "Aberto"),  # <- esse é o seu, chegou pro Almoxarifado
    (5, "RH", "Fernanda", "cadeira nova, a atual quebrou", "Carlos", "Em andamento"),
    (1, "Financeiro", "Renata", "esqueci a senha do sistema", "", "Aberto"),
    (7, "TI", "Paulo", "internet caiu no setor todo", "Diego", "Em andamento"),
    (10, "Manutenção", "Simone", "lampada queimada na sala 3", "Zé", "Concluído"),
    (4, "ADM", "Bruno", "cabo de rede", "Carlos", "Concluído"),
    (0, "RH", "Ana", "algo bem estranho que ninguem sabe o que é", "", "Aberto"),
]

for dias_atras, setor_sol, nome_sol, item, nome_resp, status in chamados_teste:
    data = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")
    setor_resp = classificar_setor(item)
    conn.execute(
        """INSERT INTO chamados
           (data_solicitacao, setor_solicitante, nome_solicitante,
            item_solicitado, setor_responsavel, nome_responsavel, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data, setor_sol, nome_sol, item, setor_resp, nome_resp, status),
    )

conn.commit()
conn.close()

print(f"{len(chamados_teste)} chamados de teste criados.")
print("O chamado do 'teclado' (Marcos) está Aberto e caiu pro Almoxarifado — abre o sistema e resolve ele.")
