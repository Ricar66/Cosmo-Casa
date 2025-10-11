import sqlite3
import sys
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/reset_admin_password.py <nova_senha>")
        sys.exit(1)

    nova = sys.argv[1]
    if len(nova) < 6:
        print("Erro: a senha deve ter pelo menos 6 caracteres.")
        sys.exit(1)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'salas_virtuais.db')
    print('Banco:', db_path)

    os.makedirs(project_root, exist_ok=True)

    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            # Garante tabela admins
            cur.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    must_change INTEGER DEFAULT 1,
                    created_at TEXT
                )
            ''')

            # Se não há admin, cria
            cur.execute('SELECT COUNT(*) FROM admins')
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute(
                    'INSERT INTO admins (username, password_hash, must_change, created_at) VALUES (?, ?, ?, ?)',
                    ('admin', generate_password_hash('admin'), 1, datetime.utcnow().isoformat())
                )

            # Atualiza senha do admin
            cur.execute(
                'UPDATE admins SET password_hash = ?, must_change = 0 WHERE username = ?',
                (generate_password_hash(nova), 'admin')
            )
            conn.commit()

        print('Senha do admin atualizada com sucesso.')
        print('Usuário: admin')
        print('Nova senha:', '*' * len(nova))
    except Exception as e:
        print('Falha ao atualizar senha:', e)
        sys.exit(1)

if __name__ == '__main__':
    main()