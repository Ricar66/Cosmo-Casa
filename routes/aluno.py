"""Blueprint de rotas de aluno: login, entrada e respostas.

Foco em usabilidade e clareza para estudantes:
- `aluno_login`: valida nome exato na lista da sala (feedback claro);
- `aluno_entrar`: fluxo por código + nome com normalização (acentos/espaços);
- `modulo_underscore_espaco`: página pós-login com informações da sala;
- `api/registrar-resposta`: registro simplificado das respostas dos desafios.

Mantém a mesma API pública, separando responsabilidades de app.py.
"""

import sqlite3
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.db import db_manager
from functools import wraps


aluno_bp = Blueprint('aluno', __name__)


def verificar_autenticacao_aluno(f):
    """Decorator para verificar se o aluno está autenticado e a sessão é válida."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se as informações básicas estão na sessão
        if not all(key in session for key in ['aluno_id', 'nome_aluno', 'sala_id']):
            logging.warning(f"[SECURITY] Tentativa de acesso sem autenticação - IP: {request.remote_addr}")
            session.clear()
            return redirect(url_for('aluno.aluno_entrar'))
        
        # Verificar se o aluno ainda existe no banco de dados
        try:
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.id, a.nome, s.ativa 
                    FROM alunos a 
                    JOIN salas_virtuais s ON a.sala_id = s.id 
                    WHERE a.id = ? AND a.sala_id = ?
                ''', (session['aluno_id'], session['sala_id']))
                
                resultado = cursor.fetchone()
                
                if not resultado:
                    logging.warning(f"[SECURITY] Aluno ou sala não encontrados - Aluno ID: {session.get('aluno_id')} | Sala ID: {session.get('sala_id')} - IP: {request.remote_addr}")
                    session.clear()
                    return redirect(url_for('aluno.aluno_entrar'))
                
                aluno_id, nome_aluno, sala_ativa = resultado
                
                # Verificar se a sala ainda está ativa
                if not sala_ativa:
                    logging.warning(f"[SECURITY] Tentativa de acesso a sala inativa - Aluno: {nome_aluno} | Sala ID: {session['sala_id']} - IP: {request.remote_addr}")
                    session.clear()
                    return redirect(url_for('aluno.aluno_entrar'))
                
                # Verificar se o nome na sessão confere com o banco
                if session['nome_aluno'] != nome_aluno:
                    logging.warning(f"[SECURITY] Inconsistência de nome na sessão - Sessão: '{session['nome_aluno']}' | Banco: '{nome_aluno}' - IP: {request.remote_addr}")
                    session.clear()
                    return redirect(url_for('aluno.aluno_entrar'))
                
        except Exception as e:
            logging.exception(f"[SECURITY] Erro na verificação de autenticação - IP: {request.remote_addr}")
            session.clear()
            return redirect(url_for('aluno.aluno_entrar'))
        
        return f(*args, **kwargs)
    return decorated_function


# Impedir voltar às páginas de login/entrada quando já autenticado como aluno
@aluno_bp.before_request
def _aluno_block_back_to_login():
    """Controla acesso às páginas de login/entrada quando já autenticado.

    Objetivo: permitir que o botão "Iniciar Missão" abra `aluno_entrar.html`
    mesmo quando o aluno já tem sessão, porém impedir reenvio de formulário.

    Regras:
    - Bloqueia qualquer acesso (GET/POST) a `aluno_login` quando autenticado.
    - Permite GET em `aluno_entrar` mesmo autenticado (renderiza a página).
    - Bloqueia POST em `aluno_entrar` quando autenticado (evita re-login).
    """
    try:
        ep = request.endpoint
        if session.get('aluno_id'):
            # Nunca voltar para a rota de login se já autenticado
            if ep == 'aluno.aluno_login':
                return redirect(url_for('missao.retry_modulos'))
            # Permite visualizar a página de entrar, mas bloqueia reenvio de POST
            if ep == 'aluno.aluno_entrar' and request.method == 'POST':
                return redirect(url_for('missao.retry_modulos'))
    except Exception:
        pass
    return None


@aluno_bp.after_request
def _aluno_no_cache_login_pages(response):
    """Evita cache do navegador nas páginas de login/entrada do aluno.

    Isso previne que o botão Voltar exiba o formulário a partir do cache.
    """
    try:
        if request.endpoint in {'aluno.aluno_login', 'aluno.aluno_entrar', 'aluno.modulo_underscore_espaco'}:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    except Exception:
        pass
    return response


@aluno_bp.route('/aluno/login/<codigo_sala>', methods=['GET', 'POST'])
def aluno_login(codigo_sala):
    """Login do aluno: valida se nome corresponde exatamente à lista.

    Mostra mensagem de erro amigável em casos comuns:
    - Sala inexistente ou inativa
    - Campo de nome vazio
    - Nome não encontrado (sugere verificar acentos e espaços)
    """
    sala = db_manager.buscar_sala_por_codigo(codigo_sala)
    if not sala:
        return "Sala não encontrada", 404

    erro = None
    if request.method == 'POST':
        nome_digitado = request.form.get('nome_aluno', '').strip()
        logging.info(f"Tentativa de login para sala {codigo_sala} com nome: '{nome_digitado}'")
        if not nome_digitado:
            erro = 'Digite seu nome completo.'
        else:
            try:
                with sqlite3.connect(db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id, nome FROM alunos WHERE sala_id = ?
                    ''', (sala['id'],))
                    alunos_na_sala = cursor.fetchall()
                    logging.info(f"Alunos registrados na sala {codigo_sala}: {[a[1] for a in alunos_na_sala]}")

                    # Verifica se o nome digitado corresponde exatamente a algum nome na lista
                    row = next((a for a in alunos_na_sala if a[1] == nome_digitado), None)
                    if row:
                        session['aluno_id'] = row[0]
                        session['nome_aluno'] = row[1]
                        session['sala_id'] = sala['id']
                        # Limpar qualquer estado anterior de viagem para garantir ida à seleção
                        try:
                            for k in [
                                'missao_etapa','viagem_diario','viagem_destino','viagem_nave_id','viagem_nave',
                                'viagem_modulos','viagem_chegada_ok','viagem_pontuacao','missao_score','chegada_ok',
                                'missao_feedback','erro_modulos'
                            ]:
                                session.pop(k, None)
                            session['missao_etapa'] = 'selecao'
                            session['missao_destino'] = sala.get('destino')
                            session['missao_nave'] = sala.get('nave_id')
                        except Exception:
                            pass
                        logging.info(f"Login bem-sucedido para aluno {row[1]} na sala {codigo_sala}")
                        return redirect(url_for('missao.selecao_modulos', destino=sala['destino'], nave_id=sala['nave_id']))
                    else:
                        erro = 'Nome não encontrado na lista. Verifique e tente novamente.'
            except Exception:
                logging.exception("Erro ao validar login do aluno")
                erro = 'Ocorreu um erro ao validar seu login.'

    return render_template('aluno_login.html', sala=sala, erro=erro)


@aluno_bp.route('/aluno/entrar', methods=['GET', 'POST'])
def aluno_entrar():
    """Entrada segura do aluno por código da sala e nome.

    Validações de segurança implementadas:
    - Verificação rigorosa de código de sala válido e ativo
    - Validação estrita de nome exatamente como cadastrado
    - Prevenção contra tentativas de login com nomes inexistentes
    - Logs de segurança para auditoria
    """
    erro = None
    sala = None
    
    if request.method == 'POST':
        # Sanitização e validação de entrada
        codigo = request.form.get('codigo_sala', '').strip().upper()
        nome = request.form.get('nome_aluno', '').strip()
        
        # Log de tentativa de acesso para auditoria
        logging.info(f"[SECURITY] Tentativa de login - Sala: '{codigo}' | Nome: '{nome}' | IP: {request.remote_addr}")
        
        # Validação básica de campos obrigatórios
        if not codigo or not nome:
            erro = 'Código da sala e nome são obrigatórios.'
            logging.warning(f"[SECURITY] Tentativa de login com campos vazios - IP: {request.remote_addr}")
            return render_template('aluno_entrar.html', erro=erro)
        
        # Validação de formato do código da sala (deve ter 8 caracteres hexadecimais)
        if len(codigo) != 8 or not all(c in '0123456789ABCDEF' for c in codigo):
            erro = 'Código da sala inválido. Deve conter exatamente 8 caracteres.'
            logging.warning(f"[SECURITY] Código de sala com formato inválido: '{codigo}' - IP: {request.remote_addr}")
            return render_template('aluno_entrar.html', erro=erro)
        
        # Buscar sala ativa
        sala = db_manager.buscar_sala_por_codigo(codigo)
        if not sala:
            # Verificar se existe sala inativa para dar feedback específico
            sala_any = db_manager.buscar_sala_por_codigo_any(codigo)
            if sala_any:
                erro = 'Sala encontrada, mas está inativa. Peça ao professor para reabrir.'
                logging.warning(f"[SECURITY] Tentativa de acesso a sala inativa: '{codigo}' - IP: {request.remote_addr}")
            else:
                erro = 'Sala não encontrada. Verifique o código e tente novamente.'
                logging.warning(f"[SECURITY] Tentativa de acesso a sala inexistente: '{codigo}' - IP: {request.remote_addr}")
            return render_template('aluno_entrar.html', erro=erro)
        
        # Validação rigorosa do nome do aluno
        try:
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar aluno com nome exato na sala específica
                cursor.execute('''
                    SELECT id, nome FROM alunos 
                    WHERE sala_id = ? AND nome = ? 
                    COLLATE BINARY
                ''', (sala['id'], nome))
                
                aluno = cursor.fetchone()
                
                if not aluno:
                    # Verificar se existe nome similar para dar dica de segurança
                    cursor.execute('''
                        SELECT nome FROM alunos 
                        WHERE sala_id = ? AND LOWER(nome) = LOWER(?)
                    ''', (sala['id'], nome))
                    
                    nome_similar = cursor.fetchone()
                    
                    if nome_similar:
                        erro = 'Nome não encontrado. Verifique maiúsculas, minúsculas e acentos. Digite exatamente como cadastrado.'
                        logging.warning(f"[SECURITY] Nome com diferença de case/acentos - Sala: '{codigo}' | Tentativa: '{nome}' | Correto: '{nome_similar[0]}' - IP: {request.remote_addr}")
                    else:
                        erro = 'Nome não encontrado na lista desta sala. Verifique se está cadastrado.'
                        logging.warning(f"[SECURITY] Nome inexistente na sala - Sala: '{codigo}' | Nome: '{nome}' - IP: {request.remote_addr}")
                    
                    return render_template('aluno_entrar.html', erro=erro)
                
                # Login bem-sucedido - configurar sessão
                session.clear()  # Limpar sessão anterior por segurança
                session['aluno_id'] = aluno[0]
                session['nome_aluno'] = aluno[1]
                session['sala_id'] = sala['id']
                session['codigo_sala'] = codigo
                session['missao_etapa'] = 'selecao'
                session['missao_destino'] = sala.get('destino')
                session['missao_nave'] = sala.get('nave_id')
                
                # Log de sucesso
                logging.info(f"[SECURITY] Login bem-sucedido - Aluno: '{aluno[1]}' | Sala: '{codigo}' | ID: {aluno[0]} - IP: {request.remote_addr}")
                
                return redirect(url_for('missao.selecao_modulos', destino=sala['destino'], nave_id=sala['nave_id']))
                
        except Exception as e:
            logging.exception(f"[SECURITY] Erro crítico no login - Sala: '{codigo}' | Nome: '{nome}' - IP: {request.remote_addr}")
            erro = 'Erro interno do sistema. Tente novamente.'
            return render_template('aluno_entrar.html', erro=erro)

    return render_template('aluno_entrar.html', erro=erro)


@aluno_bp.route('/modulo_underscore_espaco/<codigo_sala>')
@verificar_autenticacao_aluno
def modulo_underscore_espaco(codigo_sala):
    """Página pós-login (Módulo_Underscore_Espaço).

    Exibe dados essenciais da sala e oferece retorno à página inicial.
    """
    sala = db_manager.buscar_sala_por_codigo(codigo_sala)
    if not sala:
        return "Sala não encontrada", 404
    
    # Verificar se o aluno pertence a esta sala
    if session.get('codigo_sala') != codigo_sala.upper():
        logging.warning(f"[SECURITY] Tentativa de acesso a sala diferente - Aluno: {session.get('nome_aluno')} | Sala sessão: {session.get('codigo_sala')} | Sala solicitada: {codigo_sala} - IP: {request.remote_addr}")
        return redirect(url_for('aluno.aluno_entrar'))
    
    nome_aluno = session.get('nome_aluno')
    return render_template('Modulo_Underscore_Espaco.html', sala=sala, nome_aluno=nome_aluno)


@aluno_bp.route('/api/registrar-resposta', methods=['POST'])
@verificar_autenticacao_aluno
def api_registrar_resposta():
    """API segura para registrar respostas dos alunos.

    Validações de segurança:
    - Verificação de autenticação do aluno
    - Validação de que o aluno só pode registrar respostas para sua própria sala
    - Logs de auditoria para todas as respostas
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        # Usar apenas dados da sessão por segurança (não confiar no cliente)
        aluno_id = session.get('aluno_id')
        sala_id = session.get('sala_id')
        desafio_id = data.get('desafio_id') or 'resposta_desafio'
        resposta = data.get('resposta')
        
        if not resposta:
            return jsonify({'success': False, 'error': 'Resposta é obrigatória'}), 400

        correta = 1  # contar como concluído
        pontuacao = int(data.get('pontuacao') or 10)
        
        # Validar pontuação
        if pontuacao < 0 or pontuacao > 1000:
            pontuacao = 10  # valor padrão seguro
        
        # Log de auditoria
        logging.info(f"[SECURITY] Resposta registrada - Aluno: {session.get('nome_aluno')} | Sala: {session.get('codigo_sala')} | Desafio: {desafio_id} | Pontos: {pontuacao} - IP: {request.remote_addr}")

        db_manager.registrar_resposta_desafio(
            aluno_id, sala_id, desafio_id, resposta, correta, pontuacao
        )

        return jsonify({'success': True, 'pontuacao': pontuacao})

    except Exception as e:
        logging.exception(f"[SECURITY] Falha ao registrar resposta - Aluno: {session.get('nome_aluno')} - IP: {request.remote_addr}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500