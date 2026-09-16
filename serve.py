"""
Roda o sistema com um servidor de produção (sem os avisos/limites do
servidor de desenvolvimento do Flask). Use este arquivo no dia a dia
da empresa; use app.py só para testar/desenvolver.

Rodar:  python3 serve.py   (ou  py -3.14 serve.py)
"""
import socket
from waitress import serve
from app import app, init_db

PORTA = 5000

if __name__ == "__main__":
    init_db()
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip_local = "127.0.0.1"

    print("=" * 55)
    print("Sistema de Chamados no ar (modo produção).")
    print(f"Neste computador:         http://localhost:{PORTA}")
    print(f"Outros PCs da mesma rede: http://{ip_local}:{PORTA}")
    print("Deixe este terminal aberto enquanto o sistema estiver em uso.")
    print("=" * 55)

    serve(app, host="0.0.0.0", port=PORTA)
