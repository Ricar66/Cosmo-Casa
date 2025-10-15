#!/usr/bin/env python3
"""
Script para resetar completamente o banco de dados do Cosmo Casa.
Remove todas as salas, alunos, desafios e respostas.
"""

import sqlite3
import os
import sys

# Adicionar o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import DatabaseManager

def reset_database():
    """Reset completo do banco de dados"""
    db_path = 'C:\\Users\\ricardo.moretti\\CosmoCasa\\Cosmo-Casa\\salas_virtuais.db'
    
    print("🔄 Iniciando reset do banco de dados...")
    
    try:
        # Conectar ao banco
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Deletar todos os dados das tabelas (mantendo a estrutura)
            print("🗑️ Removendo todas as respostas de desafios...")
            cursor.execute("DELETE FROM respostas_desafios")
            
            print("🗑️ Removendo todos os alunos...")
            cursor.execute("DELETE FROM alunos")
            
            print("🗑️ Removendo todas as salas virtuais...")
            cursor.execute("DELETE FROM salas_virtuais")
            
            print("🗑️ Removendo todos os professores...")
            cursor.execute("DELETE FROM professores")
            
            # Reset dos auto-increment IDs
            cursor.execute("DELETE FROM sqlite_sequence")
            
            conn.commit()
            
        print("✅ Banco de dados resetado com sucesso!")
        print("📊 Todas as tabelas foram limpas e os IDs resetados.")
        print("🔐 Você precisará criar um novo professor para acessar o sistema.")
        
    except Exception as e:
        print(f"❌ Erro ao resetar banco de dados: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("⚠️  ATENÇÃO: Este script irá DELETAR TODOS OS DADOS do banco!")
    print("   - Todas as salas virtuais")
    print("   - Todos os alunos")
    print("   - Todos os desafios")
    print("   - Todas as respostas")
    print("   - Todos os professores")
    print()
    
    resposta = input("Tem certeza que deseja continuar? (digite 'CONFIRMAR' para prosseguir): ")
    
    if resposta == "CONFIRMAR":
        reset_database()
    else:
        print("❌ Operação cancelada.")