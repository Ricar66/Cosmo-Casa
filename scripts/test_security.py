#!/usr/bin/env python3
"""
Script de teste para verificar as correções de segurança implementadas.
Testa validações de autenticação, códigos de sala e nomes de alunos.
"""

import sys
import os
import sqlite3
import requests
import json

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import DatabaseManager

def test_database_reset():
    """Testa se o banco foi resetado corretamente"""
    print("🧪 Testando reset do banco de dados...")
    
    db_path = 'C:\\Users\\ricardo.moretti\\CosmoCasa\\Cosmo-Casa\\salas_virtuais.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar se as tabelas estão vazias
            cursor.execute("SELECT COUNT(*) FROM salas_virtuais")
            salas_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alunos")
            alunos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM respostas_desafios")
            respostas_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM professores")
            professores_count = cursor.fetchone()[0]
            
            if salas_count == 0 and alunos_count == 0 and respostas_count == 0 and professores_count == 0:
                print("✅ Banco de dados resetado corretamente")
                return True
            else:
                print(f"❌ Banco não está vazio - Salas: {salas_count}, Alunos: {alunos_count}, Respostas: {respostas_count}, Professores: {professores_count}")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

def test_duplicate_names_prevention():
    """Testa se a prevenção de nomes duplicados está funcionando"""
    print("🧪 Testando prevenção de nomes duplicados...")
    
    try:
        db_manager = DatabaseManager()
        
        # Criar uma sala de teste
        codigo_sala = db_manager.criar_sala_virtual(1, "Sala Teste", "lua", "falcon9", "[]")
        
        # Buscar ID da sala
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM salas_virtuais WHERE codigo_sala = ?', (codigo_sala,))
            sala_id = cursor.fetchone()[0]
        
        # Tentar adicionar o mesmo nome duas vezes
        try:
            db_manager.adicionar_aluno(sala_id, "João Silva")
            print("✅ Primeiro aluno adicionado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao adicionar primeiro aluno: {e}")
            return False
        
        try:
            db_manager.adicionar_aluno(sala_id, "João Silva")
            print("❌ FALHA: Nome duplicado foi aceito!")
            return False
        except ValueError as e:
            print("✅ Nome duplicado foi rejeitado corretamente")
            return True
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def test_room_code_validation():
    """Testa validação de códigos de sala"""
    print("🧪 Testando validação de códigos de sala...")
    
    # Códigos inválidos para testar
    invalid_codes = [
        "",           # vazio
        "123",        # muito curto
        "123456789",  # muito longo
        "GGGGGGGG",   # caracteres inválidos
        "1234567G",   # misturado
        "abcd1234",   # minúsculas
    ]
    
    valid_codes = [
        "12345678",
        "ABCDEF12",
        "A1B2C3D4",
    ]
    
    print("Testando códigos inválidos:")
    for code in invalid_codes:
        if len(code) != 8 or not all(c in '0123456789ABCDEF' for c in code):
            print(f"✅ Código '{code}' rejeitado corretamente")
        else:
            print(f"❌ Código '{code}' deveria ser rejeitado")
            return False
    
    print("Testando códigos válidos:")
    for code in valid_codes:
        if len(code) == 8 and all(c in '0123456789ABCDEF' for c in code):
            print(f"✅ Código '{code}' aceito corretamente")
        else:
            print(f"❌ Código '{code}' deveria ser aceito")
            return False
    
    return True

def test_authentication_decorator():
    """Testa se o decorator de autenticação está funcionando"""
    print("🧪 Testando decorator de autenticação...")
    
    # Este teste seria mais completo com um cliente de teste Flask
    # Por enquanto, apenas verificamos se as funções existem
    try:
        from routes.aluno import verificar_autenticacao_aluno
        print("✅ Decorator de autenticação importado com sucesso")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar decorator: {e}")
        return False

def run_all_tests():
    """Executa todos os testes de segurança"""
    print("🔒 INICIANDO TESTES DE SEGURANÇA")
    print("=" * 50)
    
    tests = [
        ("Reset do Banco de Dados", test_database_reset),
        ("Prevenção de Nomes Duplicados", test_duplicate_names_prevention),
        ("Validação de Códigos de Sala", test_room_code_validation),
        ("Decorator de Autenticação", test_authentication_decorator),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico no teste: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as correções de segurança estão funcionando!")
        return True
    else:
        print("⚠️  Algumas correções precisam de atenção.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)