#!/usr/bin/env python3
"""Migration tool: move data from data.json to salas_virtuais.db

This script is idempotent: it will skip salas already present by codigo_sala.
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_JSON = os.path.join(BASE, 'data.json')
DB_PATH = os.path.join(BASE, 'salas_virtuais.db')

parser = argparse.ArgumentParser(description='Migrate data.json -> salas_virtuais.db')
parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without writing')
parser.add_argument('--migrate-professores', action='store_true', help='Also migrate professores from data.json into the professores table')
parser.add_argument('--force', action='store_true', help='Force overwrite existing salas with same codigo_sala')
args = parser.parse_args()

if not os.path.exists(DATA_JSON):
    print('No data.json found, nothing to migrate.')
    raise SystemExit(0)

with open(DATA_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)

salas = data.get('salas', [])
professores = data.get('professores', [])

if args.dry_run:
    print('DRY RUN:');
    print(f"Found {len(professores)} professores and {len(salas)} salas in data.json")
    if professores:
        print('Sample professor:', professores[0])
    if salas:
        print('Sample sala:', salas[0])
    print('No changes will be made.')
    raise SystemExit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

migrated = 0
for s in salas:
    codigo = s.get('codigo')
    if not codigo:
        print('Skipping sala with no codigo')
        continue
    # check existing
    cur.execute('SELECT id FROM salas_virtuais WHERE UPPER(codigo_sala)=UPPER(?)', (codigo,))
    existing = cur.fetchone()
    if existing and not args.force:
        print(f"Sala {codigo} already exists in DB, skipping (use --force to overwrite).")
        continue
    if existing and args.force:
        print(f"Sala {codigo} exists: deleting and re-creating due to --force")
        cur.execute('DELETE FROM alunos WHERE sala_id = ?', (existing[0],))
        cur.execute('DELETE FROM salas_virtuais WHERE id = ?', (existing[0],))

    nome_sala = s.get('nome_sala') or s.get('nome') or 'Sala'
    destino = s.get('destino') or 'lua'
    nave_id = s.get('nave_id') or 'falcon9'
    desafios = json.dumps(s.get('desafios', []), ensure_ascii=False)
    data_criacao = s.get('data_criacao') or datetime.now().isoformat()[:19]
    professor_id = 1
    ativa = 1 if s.get('ativa', True) else 0
    data_expiracao = None

    cur.execute('''
        INSERT INTO salas_virtuais (codigo_sala, professor_id, nome_sala, destino, nave_id, desafios_json, ativa, data_criacao, data_expiracao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo, professor_id, nome_sala, destino, nave_id, desafios, ativa, data_criacao, data_expiracao))
    sala_id = cur.lastrowid

    # migrate alunos
    for aluno in s.get('alunos', []):
        nome = aluno.get('nome')
        if not nome:
            continue
        cur.execute('INSERT INTO alunos (sala_id, nome, email, progresso_json) VALUES (?, ?, ?, ?)', (sala_id, nome, aluno.get('email'), json.dumps(aluno.get('progresso', {}), ensure_ascii=False)))

    migrated += 1

prof_migrated = 0
if args.migrate_professores or args.migrate_professores is None:
    # If flag set, migrate professors
    if args.migrate_professores:
        for p in professores:
            nome = p.get('nome') or f"Professor{p.get('id', '')}"
            email = p.get('email') or f"{nome.replace(' ', '').lower()}@local"
            senha_hash = p.get('senha_hash', '')
            # check existing by email
            cur.execute('SELECT id FROM professores WHERE UPPER(email)=UPPER(?)', (email,))
            if cur.fetchone():
                print(f"Professor {email} already exists, skipping.")
                continue
            cur.execute('INSERT INTO professores (nome, email, senha_hash) VALUES (?, ?, ?)', (nome, email, senha_hash))
            prof_migrated += 1

conn.commit()
conn.close()
print(f"Migration complete. Migrated {migrated} salas and {prof_migrated} professores.")
