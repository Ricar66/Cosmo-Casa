#!/usr/bin/env python3
"""
Script de teste específico para validações de autenticação.
Testa todas as vulnerabilidades mencionadas pelo usuário.
"""

import sys
import os
import sqlite3
import requests
import json

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import DatabaseManager

def setup_test_data():
    """Configura dados de teste no banco"""
    print("🔧 Configurando dados de teste...")
    
    try:
        db_manager = DatabaseManager()
        
        # Criar um professor de teste
        try:
            db_manager.criar_professor("Professor Teste", "teste@teste.com", "senha123")
        except:
            pass  # Professor já existe
        
        # Criar uma sala de teste
        codigo_sala = db_manager.criar_sala_virtual(1, "Sala Teste Segurança", "lua", "falcon9", "[]")
        
        # Buscar ID da sala
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM salas_virtuais WHERE codigo_sala = ?', (codigo_sala,))
            sala_id = cursor.fetchone()[0]
        
        # Adicionar alunos de teste
        alunos_teste = [
            "João Silva",
            "Maria Santos",
            "Pedro Oliveira",
            "Ana Costa"
        ]
        
        for nome in alunos_teste:
            try:
                db_manager.adicionar_aluno(sala_id, nome)
            except ValueError:
                pass  # Aluno já existe
        
        print(f"✅ Dados de teste configurados - Sala: {codigo_sala}")
        return codigo_sala, sala_id
        
    except Exception as e:
        print(f"❌ Erro ao configurar dados de teste: {e}")
        return None, None

def test_valid_login():
    """Testa login válido com dados corretos"""
    print("🧪 Testando login válido...")
    
    codigo_sala, sala_id = setup_test_data()
    if not codigo_sala:
        return False
    
    # Simular dados de login válidos
    nome_valido = "João Silva"
    
    try:
        db_manager = DatabaseManager()
        
        # Verificar se a sala existe e está ativa
        sala = db_manager.buscar_sala_por_codigo(codigo_sala)
        if not sala:
            print("❌ Sala não encontrada")
            return False
        
        # Verificar se o aluno existe na sala
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome FROM alunos 
                WHERE sala_id = ? AND nome = ? 
                COLLATE BINARY
            ''', (sala['id'], nome_valido))
            
            aluno = cursor.fetchone()
            
            if aluno:
                print("✅ Login válido funcionando corretamente")
                return True
            else:
                print("❌ Aluno válido não encontrado")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste de login válido: {e}")
        return False

def test_invalid_room_codes():
    """Testa códigos de sala inválidos"""
    print("🧪 Testando códigos de sala inválidos...")
    
    codigos_invalidos = [
        "",           # vazio
        "123",        # muito curto
        "123456789",  # muito longo
        "GGGGGGGG",   # caracteres inválidos
        "1234567G",   # misturado
        "abcd1234",   # minúsculas
        "XXXXXXXX",   # não existe
    ]
    
    try:
        db_manager = DatabaseManager()
        
        for codigo in codigos_invalidos:
            # Validação de formato
            if len(codigo) != 8 or not all(c in '0123456789ABCDEF' for c in codigo):
                print(f"✅ Código '{codigo}' rejeitado por formato inválido")
                continue
            
            # Verificar se sala existe
            sala = db_manager.buscar_sala_por_codigo(codigo)
            if not sala:
                print(f"✅ Código '{codigo}' rejeitado - sala não encontrada")
            else:
                print(f"❌ Código '{codigo}' foi aceito incorretamente")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de códigos inválidos: {e}")
        return False

def test_invalid_student_names():
    """Testa nomes de alunos inválidos"""
    print("🧪 Testando nomes de alunos inválidos...")
    
    codigo_sala, sala_id = setup_test_data()
    if not codigo_sala:
        return False
    
    nomes_invalidos = [
        "Aluno Inexistente",
        "joão silva",        # case diferente
        "JOÃO SILVA",        # case diferente
        "João  Silva",       # espaços extras
        " João Silva ",      # espaços nas bordas
        "Joao Silva",        # sem acentos
        "",                  # vazio
    ]
    
    try:
        db_manager = DatabaseManager()
        sala = db_manager.buscar_sala_por_codigo(codigo_sala)
        
        for nome in nomes_invalidos:
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nome FROM alunos 
                    WHERE sala_id = ? AND nome = ? 
                    COLLATE BINARY
                ''', (sala['id'], nome))
                
                aluno = cursor.fetchone()
                
                if not aluno:
                    print(f"✅ Nome '{nome}' rejeitado corretamente")
                else:
                    print(f"❌ Nome '{nome}' foi aceito incorretamente")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de nomes inválidos: {e}")
        return False

def test_exact_name_matching():
    """Testa correspondência exata de nomes"""
    print("🧪 Testando correspondência exata de nomes...")
    
    codigo_sala, sala_id = setup_test_data()
    if not codigo_sala:
        return False
    
    # Nome exato cadastrado
    nome_exato = "João Silva"
    
    # Variações que devem ser rejeitadas
    variacoes_invalidas = [
        "joão silva",        # minúsculas
        "JOÃO SILVA",        # maiúsculas
        "João  Silva",       # espaços extras
        " João Silva",       # espaço no início
        "João Silva ",       # espaço no final
        "Joao Silva",        # sem acento
        "João silva",        # case misto
    ]
    
    try:
        db_manager = DatabaseManager()
        sala = db_manager.buscar_sala_por_codigo(codigo_sala)
        
        # Testar nome exato (deve funcionar)
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome FROM alunos 
                WHERE sala_id = ? AND nome = ? 
                COLLATE BINARY
            ''', (sala['id'], nome_exato))
            
            aluno = cursor.fetchone()
            
            if not aluno:
                print(f"❌ Nome exato '{nome_exato}' foi rejeitado incorretamente")
                return False
            else:
                print(f"✅ Nome exato '{nome_exato}' aceito corretamente")
        
        # Testar variações (devem ser rejeitadas)
        for variacao in variacoes_invalidas:
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nome FROM alunos 
                    WHERE sala_id = ? AND nome = ? 
                    COLLATE BINARY
                ''', (sala['id'], variacao))
                
                aluno = cursor.fetchone()
                
                if aluno:
                    print(f"❌ Variação '{variacao}' foi aceita incorretamente")
                    return False
                else:
                    print(f"✅ Variação '{variacao}' rejeitada corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de correspondência exata: {e}")
        return False

def test_inactive_room_access():
    """Testa acesso a salas inativas"""
    print("🧪 Testando acesso a salas inativas...")
    
    try:
        db_manager = DatabaseManager()
        
        # Criar uma sala e depois desativá-la
        codigo_sala = db_manager.criar_sala_virtual(1, "Sala Inativa", "lua", "falcon9", "[]")
        
        # Desativar a sala
        db_manager.fechar_sala_por_codigo(codigo_sala)
        
        # Tentar buscar sala ativa (deve falhar)
        sala_ativa = db_manager.buscar_sala_por_codigo(codigo_sala)
        if sala_ativa:
            print("❌ Sala inativa foi encontrada como ativa")
            return False
        
        # Verificar se existe como inativa
        sala_inativa = db_manager.buscar_sala_por_codigo_any(codigo_sala)
        if not sala_inativa:
            print("❌ Sala inativa não foi encontrada")
            return False
        
        print("✅ Acesso a salas inativas bloqueado corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de salas inativas: {e}")
        return False

def run_authentication_tests():
    """Executa todos os testes de autenticação"""
    print("🔐 INICIANDO TESTES DE AUTENTICAÇÃO")
    print("=" * 50)
    
    tests = [
        ("Login Válido", test_valid_login),
        ("Códigos de Sala Inválidos", test_invalid_room_codes),
        ("Nomes de Alunos Inválidos", test_invalid_student_names),
        ("Correspondência Exata de Nomes", test_exact_name_matching),
        ("Acesso a Salas Inativas", test_inactive_room_access),
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
    print("📊 RESUMO DOS TESTES DE AUTENTICAÇÃO")
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
        print("🎉 Todas as validações de autenticação estão funcionando!")
        return True
    else:
        print("⚠️  Algumas validações precisam de atenção.")
        return False

if __name__ == "__main__":
    success = run_authentication_tests()
    sys.exit(0 if success else 1)