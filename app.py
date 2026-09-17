from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import sqlite3
import os

# --- Conexão com o Turso (produção) ou SQLite local (desenvolvimento) ---
try:
    import libsql_client
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "chamados.db")
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

SETORES = ["TI", "Almoxarifado", "RH", "Financeiro", "ADM", "Manutenção"]
STATUS_OPCOES = ["Aberto", "Em andamento", "Concluído"]

CLASSIFICACAO = {
    "Almoxarifado": [
        "mouse", "teclado", "monitor", "cadeira", "mesa", "papel", "caneta",
        "grampeador", "toner", "cartucho", "headset", "fone", "mochila",
        "pasta", "caixa", "material de escritorio", "notebook", "cabo",
    ],
    "TI": [
        "senha", "internet", "rede", "wifi", "sistema", "software", "login",
        "acesso", "impressora", "computador travando", "email", "e-mail",
        "instalar", "formatar", "antivirus", "vpn", "servidor",
    ],
    "Manutenção": [
        "ar condicionado", "lampada", "lâmpada", "tomada", "encanamento",
        "vazamento", "porta", "janela", "eletrica", "elétrica", "infiltração",
    ],
    "RH": [
        "ferias", "férias", "salario", "salário", "holerite", "contracheque",
        "admissao", "admissão", "demissao", "demissão", "rescisao", "rescisão",
        "beneficio", "benefício", "vale transporte", "vale-transporte",
        "vale alimentacao", "vale-alimentacao", "atestado", "plano de saude",
        "plano de saúde", "ponto", "banco de horas", "advertencia", "advertência",
    ],
    "Financeiro": [
        "reembolso", "nota fiscal", "pagamento", "boleto", "fatura",
        "despesa", "adiantamento", "nota de debito", "centro de custo",
    ],
}


def classificar_setor(item_texto):
    texto = item_texto.lower()
    for setor, palavras in CLASSIFICACAO.items():
        if any(p in texto for p in palavras):
            return setor
    return "Não classificado"


# ---------- Classes de adaptação para o Turso ----------
class RowWrapper:
    """Simula o comportamento de sqlite3.Row (acesso por atributo)."""
    def __init__(self, columns, values):
        self._columns = columns
        self._values = values
        for col, val in zip(columns, values):
            setattr(self, col, val)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return getattr(self, key)


class TursoCursor:
    """Adapta o resultado do libsql-client para se parecer com sqlite3.Cursor."""
    def __init__(self, result):
        self._rows = result.rows
        self._columns = result.columns

    def fetchall(self):
        return [RowWrapper(self._columns, row) for row in self._rows]

    def fetchone(self):
        if not self._rows:
            return None
        return RowWrapper(self._columns, self._rows[0])


class TursoConnection:
    """Adapta a API do libsql-client para se parecer com sqlite3.Connection."""
    def __init__(self, client):
        self.client = client

    def execute(self, query, params=None):
        params = params or []
        result = self.client.execute(query, params)
        return TursoCursor(result)

    def commit(self):
        # libsql-client já faz commit automático em cada execute
        pass

    def close(self):
        pass


def get_db():
    """Conecta no Turso (produção) ou no SQLite local (desenvolvimento)."""
    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN and HAS_LIBSQL:
        client = libsql_client.create_client_sync(
            url=TURSO_DATABASE_URL,
            auth_token=TURSO_AUTH_TOKEN,
        )
        return TursoConnection(client)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def agora_utc_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def formatar_data_br(data_iso):
    try:
        dt_utc = datetime.strptime(data_iso, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        dt_br = dt_utc.astimezone(FUSO_BRASIL)
        return dt_br.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return data_iso


app.jinja_env.filters["br_data"] = formatar_data_br


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_solicitacao TEXT NOT NULL,
            setor_solicitante TEXT NOT NULL,
            nome_solicitante TEXT NOT NULL,
            item_solicitado TEXT NOT NULL,
            setor_responsavel TEXT NOT NULL,
            nome_responsavel TEXT,
            status TEXT NOT NULL DEFAULT 'Aberto'
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    filtro_status = request.args.get("status", "")
    filtro_setor = request.args.get("setor_responsavel", "")
    ordem = request.args.get("ordem", "recentes")
    if ordem not in ("recentes", "antigos"):
        ordem = "recentes"

    query = "SELECT * FROM chamados WHERE 1=1"
    params = []
    if filtro_status:
        query += " AND status = ?"
        params.append(filtro_status)
    if filtro_setor:
        query += " AND setor_responsavel = ?"
        params.append(filtro_setor)

    if ordem == "recentes":
        query += " ORDER BY data_solicitacao DESC"
    else:
        query += " ORDER BY data_solicitacao ASC"

    proxima_ordem = "antigos" if ordem == "recentes" else "recentes"

    chamados = conn.execute(query, params).fetchall()
    conn.close()
    return render_template(
        "index.html",
        chamados=chamados,
        setores=SETORES,
        status_opcoes=STATUS_OPCOES,
        filtro_status=filtro_status,
        filtro_setor=filtro_setor,
        ordem=ordem,
        proxima_ordem=proxima_ordem,
    )


@app.route("/novo", methods=["GET", "POST"])
def novo_chamado():
    if request.method == "POST":
        item_solicitado = request.form["item_solicitado"]
        setor_responsavel = classificar_setor(item_solicitado)

        conn = get_db()
        conn.execute(
            """INSERT INTO chamados
               (data_solicitacao, setor_solicitante, nome_solicitante,
                item_solicitado, setor_responsavel, nome_responsavel, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                agora_utc_str(),
                request.form["setor_solicitante"],
                request.form["nome_solicitante"],
                item_solicitado,
                setor_responsavel,
                "",
                "Aberto",
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("novo.html", setores=SETORES)


@app.route("/chamado/<int:chamado_id>/status", methods=["POST"])
def atualizar_status(chamado_id):
    novo_status = request.form["status"]
    nome_responsavel = request.form.get("nome_responsavel", "")
    conn = get_db()
    conn.execute(
        "UPDATE chamados SET status = ?, nome_responsavel = ? WHERE id = ?",
        (novo_status, nome_responsavel, chamado_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    import socket

    init_db()
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip_local = "127.0.0.1"

    print("=" * 50)
    print("Sistema de Chamados rodando.")
    print(f"Neste computador:        http://localhost:5000")
    print(f"Outros PCs da mesma rede: http://{ip_local}:5000")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=True)