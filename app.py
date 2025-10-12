"""Aplicação Flask principal do projeto Cosmo-Casa.

Responsabilidades:
- Registrar blueprints de Professor (admin), Aluno e Missão;
- Expor rotas de índice e seleção de missão (landing e seleção);
- Manter dados de contexto (naves, módulos, eventos) para páginas e simulação;
- Fornecer alias de imagens estáticas para compatibilidade com caminhos de front-end.

Fluxo resumido:
- Professores criam/gerenciam salas via `/professor`;
- Alunos entram com código e nome via rotas de aluno;
- Seleção/montagem de módulos e viagem são tratadas pelo blueprint `missao`.

Este arquivo deve permanecer leve em lógica de negócio; operações de CRUD e
simulação residem nos blueprints e em `services.db`.
"""
# app.py
import math
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import random
import json
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import threading
import requests
import logging

# Inicializa a aplicação Flask
app = Flask(__name__)
# Usa SECRET_KEY do ambiente em produção; mantém fallback para desenvolvimento
app.secret_key = os.getenv('SECRET_KEY', 'minha_nasa_minha_vida_secret_key_2024')

from services.db import db_manager  # Gerencia SQLite e operações de persistência
from routes.professor import professor_bp
from routes.aluno import aluno_bp
from routes.missao import missao_bp
from services.data import NAVES_ESPACIAIS, MODULOS_HABITAT, EVENTOS_ALEATORIOS  # Catálogos estáticos para UI/simulações
logging.basicConfig(level=logging.INFO)


# Removido o uso de json_store: sistema unificado em SQLite


# --- DEFINIÇÃO DAS ROTAS ---

# --- CONSTANTES FÍSICAS PARA CÁLCULOS ---
# Mantidas para cálculos auxiliares de nave/trajetória (educacional)
GRAVIDADE_TERRA = 9.81  # m/s²
CONSTANTE_GRAVITACIONAL = 6.67430e-11  # m³/kg/s²
MASA_TERRA = 5.972e24  # kg
RAIO_TERRA = 6371000  # m

# --- BANCO DE DADOS DAS NAVES (com parâmetros de propulsão realistas) ---
NAVES_ESPACIAIS = {
    'falcon9': {
        'nome': 'Falcon 9',
        'operador': 'EUA / SpaceX',
        'imagem': 'Falcon9.png',
        'descricao': 'Foguete de dois estágios reutilizável com excelente relação empuxo-peso. Ideal para cargas pesadas em órbita baixa.',
        'capacidade_carga': 22.8,  # toneladas para LEO
        'perfil_missao': 'Dois Estágios',
        # Parâmetros de propulsão adicionados
        'empuxo_total': 7607,  # kN (1º estágio: 7.607 kN)
        'impulso_especifico': 282,  # segundos (vacuum)
        'massa_seca': 28.2,  # toneladas (dry mass)
        'massa_combustivel': 433.1,  # toneladas (propellant mass)
        'delta_v_total': 9300,  # m/s (total capability)
        'taxa_empuxo_peso': 1.8  # T/W ratio
    },
    'pslv': {
        'nome': 'PSLV',
        'operador': 'Índia / ISRO',
        'imagem': 'PSLV.jpg',
        'descricao': 'Foguete confiável com múltiplos estágios e capacidade de inserção em órbitas polares e sincronizadas com o sol.',
        'capacidade_carga': 3.8,  # toneladas para LEO
        'perfil_missao': 'Múltiplas Queimas',
        'empuxo_total': 4800,  # kN
        'impulso_especifico': 262,  # segundos
        'massa_seca': 18.5,  # toneladas
        'massa_combustivel': 230.0,  # toneladas
        'delta_v_total': 8200,  # m/s
        'taxa_empuxo_peso': 1.4
    },
    'longmarch8a': {
        'nome': 'Long-March8A',
        'operador': 'China',
        'imagem': 'foguete-longa-marcha.png',
        'descricao': 'Foguete de médio porte com capacidade para múltiplas órbitas e fases de coasting estendidas.',
        'capacidade_carga': 9.8,  # toneladas para LEO
        'perfil_missao': 'Coasting Estendido',
        'empuxo_total': 5800,  # kN
        'impulso_especifico': 275,  # segundos
        'massa_seca': 22.1,  # toneladas
        'massa_combustivel': 320.5,  # toneladas
        'delta_v_total': 8800,  # m/s
        'taxa_empuxo_peso': 1.6
    },
    'gslv': {
        'nome': 'GSLV',
        'operador': 'Índia / ISRO',
        'imagem': 'LVM3_M3.png',
        'descricao': 'Foguete com estágio criogênico superior para inserção precisa em órbitas de transferência geossíncronas.',
        'capacidade_carga': 2.5,  # toneladas para GTO
        'perfil_missao': 'Estágio Criogênico',
        'empuxo_total': 4200,  # kN
        'impulso_especifico': 295,  # segundos (estágio criogênico)
        'massa_seca': 16.8,  # toneladas
        'massa_combustivel': 198.7,  # toneladas
        'delta_v_total': 9500,  # m/s
        'taxa_empuxo_peso': 1.3
    }
}

# --- FUNÇÕES DE CÁLCULO DE PERFORMANCE ---
def calcular_delta_v(massa_seca, massa_combustivel, impulso_especifico):
    """
    Calcula o Delta-V usando a Equação de Foguete de Tsiolkovsky
    Δv = Isp * g0 * ln(m0/mf)
    
    Onde:
    - Isp: Impulso específico (segundos)
    - g0: Gravidade padrão na Terra (9.81 m/s²)
    - m0: Massa inicial (seca + combustível)
    - mf: Massa final (apenas seca)
    """
    massa_inicial = massa_seca + massa_combustivel
    massa_final = massa_seca
    
    if massa_final <= 0:
        return 0
    
    return impulso_especifico * GRAVIDADE_TERRA * math.log(massa_inicial / massa_final)

def calcular_distancia_maxima_sem_carga(nave, destino='leo'):
    """
    Calcula a distância máxima que um foguete pode alcançar sem carga útil
    considerando sua performance máxima (Delta-V total).
    
    Para órbitas: 
    - LEO: ~7800 m/s Delta-V necessário
    - GTO: ~10700 m/s Delta-V necessário
    - Lua: ~10800 m/s Delta-V necessário
    - Marte: ~13600 m/s Delta-V necessário
    """
    delta_v_disponivel = nave['delta_v_total']
    
    # Delta-V necessário para diferentes destinos (em m/s)
    requisitos_delta_v = {
        'leo': 7800,    # Órbita Terrestre Baixa
        'gto': 10700,   # Órbita de Transferência Geossíncrona
        'lua': 10800,   # Órbita Lunar/Trajetória Lua
        'marte': 13600  # Trajetória Marte
    }
    
    delta_v_necessario = requisitos_delta_v.get(destino.lower(), 7800)
    
    # Se o foguete tem Delta-V suficiente para o destino
    if delta_v_disponivel >= delta_v_necessario:
        # Calcular distância máxima baseada no Delta-V excedente
        delta_v_excedente = delta_v_disponivel - delta_v_necessario
        
        # Converter Delta-V excedente em distância adicional
        # (aproximação simplificada para órbitas)
        distancia_base = {
            'leo': 400,      # km de altitude
            'gto': 35786,    # km (órbita geoestacionária)
            'lua': 384400,   # km
            'marte': 225e6   # km (média)
        }
        
        distancia_adicional = (delta_v_excedente / 1000) * 10000  # Aproximação
        return distancia_base.get(destino.lower(), 0) + distancia_adicional
    
    # Se não tem Delta-V suficiente, calcular fração alcançável
    fracao_alcancavel = delta_v_disponivel / delta_v_necessario
    
    distancias_maximas = {
        'leo': 400 * fracao_alcancavel,
        'gto': 35786 * fracao_alcancavel,
        'lua': 384400 * fracao_alcancavel,
        'marte': 225e6 * fracao_alcancavel
    }
    
    return distancias_maximas.get(destino.lower(), 0)

def calcular_carga_maxima_para_destino(nave, destino, distancia_destino):
    """
    Calcula a carga máxima possível para um destino específico
    baseado na distância máxima sem carga.
    
    Usa a relação: carga_max = capacidade_nominal * (1 - (distancia_destino / distancia_max_sem_carga))
    """
    distancia_max_sem_carga = calcular_distancia_maxima_sem_carga(nave, destino)
    
    if distancia_max_sem_carga <= 0:
        return 0
    
    # Fator de redução baseado na distância
    fator_reducao = 1 - (distancia_destino / distancia_max_sem_carga)
    
    # Limitar entre 0 e 1
    fator_reducao = max(0, min(1, fator_reducao))
    
    # Capacidade nominal da nave (em kg)
    capacidade_nominal = nave['capacidade_carga'] * 1000  # Convertendo para kg
    
    return capacidade_nominal * fator_reducao

# --- HABITAT MODULES DATABASE (with images and tooltips) ---
MODULOS_HABITAT = {
    'suporte_vida': {"nome": "Life Support", "massa": 800, "energia": 15, "agua": 50,
                     "imagem": "suporte_vida.svg", "obs": "Essential. Connects to Housing, Sanitation, and Food Production."},
    'habitacional': {"nome": "Private Quarters", "massa": 200, "energia": 1, "agua": 5,
                     "imagem": "Privado.svg", "obs": "Crew accommodations. Can be integrated with Leisure."},
    'alimentacao': {"nome": "Food and Meals", "massa": 300, "energia": 3, "agua": 20,
                    "imagem": "Cultura.svg", "obs": "Area for food preparation and consumption."},
    'medico': {"nome": "Medical Module", "massa": 250, "energia": 2, "agua": 5,
               "imagem": "Medicina.svg", "obs": "For medical emergencies and crew health monitoring."},
    'exercicios': {"nome": "Exercise", "massa": 400, "energia": 5, "agua": 2,
                   "imagem": "Exercicio.svg", "obs": "Equipment to mitigate muscle and bone loss."},
    'pesquisa': {"nome": "Work and Research", "massa": 350, "energia": 4, "agua": 2,
                 "imagem": "Pesquisa.svg", "obs": "Laboratory for conducting scientific experiments."},
    'armazenamento': {"nome": "Storage", "massa": 150, "energia": 0.5, "agua": 0,
                      "imagem": "Armazenagem.svg", "obs": "Stock of supplies, tools, and samples."},
    'sanitario': {"nome": "Sanitation and Hygiene", "massa": 250, "energia": 2, "agua": 30,
                  "imagem": "Sanitário.svg", "obs": "Bathroom, shower, and water recycling systems."},
    'inflavel': {"nome": "Expandable Inflatable", "massa": 500, "energia": 2, "agua": 5,
                 "imagem": "Inflavel.svg", "obs": "Large-volume module when inflated, highly versatile."},
    'airlock': {"nome": "Airlock", "massa": 300, "energia": 2, "agua": 2,
                "imagem": "AirLock.svg", "obs": "Depressurization chamber for extravehicular activities (EVAs)."},
    'hidroponia': {"nome": "Food Production (Hydroponics)", "massa": 500, "energia": 8, "agua": 40,
                   "imagem": "Hidroponia.svg", "obs": "Growing plants in a controlled environment to supplement the diet."},
    'impressao3d': {"nome": "3D Printing/Manufacturing", "massa": 300, "energia": 5, "agua": 2,
                    "imagem": "Impressora.svg", "obs": "Manufacturing spare parts and tools on demand."}
}

# --- RANDOM EVENTS DATABASE ---
EVENTOS_ALEATORIOS = [
    {
        "nome": "Solar Storm",
        "descricao": "A radiation wave hits the spacecraft. Modules with low shielding may suffer damage.",
        "efeito": "risco_avaria_modulo"
    },
    {
        "nome": "Minor Mechanical Failure",
        "descricao": "A subsystem experiences a minor failure, consuming extra resources for repair and causing a slight delay.",
        "efeito": "atraso_e_consumo_extra"
    },
    {
        "nome": "Micrometeoroid Impact",
        "descricao": "Small space debris collides with the hull. The spacecraft's shielding is tested.",
        "efeito": "risco_perda_carga"
    },
    {
        "nome": "Power Surge",
        "descricao": "A fluctuation in the power systems forces resource diversion for stabilization.",
        "efeito": "consumo_extra"
    },
    {
        "nome": "All Calm",
        "descricao": "The journey proceeds without incidents. The crew uses the calm to check systems.",
        "efeito": "nenhum"
    },
    {
        "nome": "Optimized Navigation",
        "descricao": "The flight team finds a more efficient trajectory, saving propellant and slightly advancing arrival.",
        "efeito": "bonus_economia"
    }
]

# --- DEFINIÇÃO DAS ROTAS ---

# Rota para a página inicial ('/') com endpoint 'index' para compatibilidade
@app.route('/', endpoint='index')
def tela_inicial():
    """Landing page com links para aluno e professor."""
    return render_template('index.html')

# Rota para a página de seleção de missão ('/selecao')
# app.py

@app.route('/selecao')
def tela_selecao():
    """Tela de seleção com imagens da NASA e fallback local garantido."""
    missoes = {
        'lua': {
            'nome': 'Moon',
            # Tenta buscar na NASA, se falhar, o valor será None
            'imagem_nasa': buscar_imagem_nasa('apollo moon landing'),
            # URL local garantida
            'imagem_local': url_for('static', filename='imagens/Lua.png'),
            'descricao': 'The gateway to space exploration. A familiar environment, ideal for testing new habitats and technologies with lower risk.',
            'stats': {'Distance': '384,400 km', 'Estimated Duration': 'Short (15 turns)', 'Risks': 'Low'}
        },
        'marte': {
            'nome': 'Mars',
            # 'imagem_nasa': buscar_imagem_nasa('planet mars'),
            'imagem_local': url_for('static', filename='imagens/Marte.png'),
            'descricao': 'The next big leap for humanity. Face dust storms and a hostile environment in a long-duration mission.',
            'stats': {'Distance': '225 million km', 'Estimated Duration': 'Long (60 turns)', 'Risks': 'High'}
        },
        'exoplaneta': {
            'nome': 'Exoplanet',
            'imagem_nasa': buscar_imagem_nasa('Kepler telescope exoplanet concept'),
            'imagem_local': url_for('static', filename='imagens/Exoplaneta.png'),
            'descricao': 'A journey to the stars in search of a new home. Unknown and extreme challenges await in the first interstellar habitat.',
            'stats': {'Distance': '500 light-years', 'Estimated Duration': 'Extreme (250 turns)', 'Risks': 'Unknown'}
        }
    }
    return render_template('selecao.html', missoes=missoes, codigo_sala=request.args.get('codigo_sala'))
# NOVA ROTA: Tela para montar o transporte
# Rota de montagem de transporte movida para blueprint missao

# NOVA ROTA: Tela para selecionar os módulos do habitat
# Rota de seleção de módulos movida para blueprint missao
    
# NOVA ROTA: Simula a viagem em turnos
# Rota de viagem movida para blueprint missao

# --- EXECUÇÃO DO SERVIDOR ---
app.register_blueprint(professor_bp, url_prefix='/professor')
app.register_blueprint(aluno_bp)
app.register_blueprint(missao_bp)

# Proteção global redundante para rotas da missão
# Garante bloqueio mesmo que alguma configuração de blueprint/before_request não seja aplicada.
@app.before_request
def _global_guard_missao():
    try:
        ep = (request.endpoint or '')
        # Apenas protege rotas do blueprint `missao`, excetuando páginas públicas
        if ep.startswith('missao.') and ep not in {'missao.ranking_rodada', 'missao.game_over'}:
            # Permitir acesso de professor/admin à montagem de transporte
            if ep == 'missao.montagem_transporte' and (session.get('user_role') in {'professor', 'admin'} or session.get('professor_id')):
                return None
            # Exigir sessão de aluno para demais páginas da missão
            if not session.get('aluno_id'):
                return redirect(url_for('aluno.aluno_entrar'))
        return None
    except Exception:
        # Em qualquer falha, não bloquear demais rotas
        return None

# Alias estático: atender /static/images/* usando arquivos de static/imagens/*
IMAGENS_ALIAS_MAP = {
    # módulos principais
    'suporte_vida.png': 'suporte_vida.svg',
    'habitacional.png': 'Privado.svg',
    'alimentacao.png': 'Cultura.svg',
    'medico.png': 'Medicina.svg',
    'exercicios.png': 'Exercicio.svg',
    'pesquisa.png': 'Pesquisa.svg',
    'armazenamento.png': 'Armazenagem.svg',
    'sanitario.png': 'Sanitário.svg',
    'inflavel.png': 'Inflavel.svg',
    'airlock.png': 'AirLock.svg',
    'hidroponia.png': 'Hidroponia.svg',
    'impressao3d.png': 'Impressora.svg',
    # naves e destinos (caso algum front use images/)
    'falcon9.png': 'Falcon9.png',
    'gslv.png': 'LVM3_M3.png',
    'longmarch8a.png': 'foguete-longa-marcha.png',
    'lua.png': 'Lua.png',
    'marte.png': 'Marte.png',
    'exoplaneta.png': 'Exoplaneta.png'
}

@app.route('/static/images/<path:filename>')
def static_images_alias(filename):
    """Alias `/static/images/*` para arquivos em `static/imagens/*`.

    Traduz nomes conhecidos `.png` para os `.svg` reais quando aplicável.
    """
    alvo = IMAGENS_ALIAS_MAP.get(filename, filename)
    return send_from_directory(os.path.join(app.root_path, 'static', 'imagens'), alvo)

# Alias de acesso direto à sala para compatibilidade
@app.route('/sala/<codigo_sala>', endpoint='sala_detalhes_alias')
def sala_detalhes_alias(codigo_sala):
    # Redireciona para a rota do blueprint de professor
    return redirect(url_for('professor.professor_sala_detalhes', codigo_sala=codigo_sala))


# Rota de aluno_login movida para blueprint aluno

# Rota de aluno_entrar movida para blueprint aluno

# Rota de modulo_underscore_espaco movida para blueprint aluno


# Rota de API para respostas movida para blueprint aluno

def criar_desafios_padrao(destino):
    """Cria desafios padrão baseados no destino"""
    if destino == 'lua':
        return [
            {
                'id': 'desafio_1',
                'titulo': 'Seleção de Módulos Essenciais',
                'descricao': 'Quais módulos são absolutamente necessários para uma missão lunar de 15 dias?',
                'tipo': 'multipla_escolha',
                'opcoes': ['Suporte à Vida', 'Habitacional', 'Exercícios', 'Todos os anteriores'],
                'resposta_correta': 3
            },
            {
                'id': 'desafio_2', 
                'titulo': 'Cálculo de Massa',
                'descricao': 'Se você adicionar 3 módulos de 200kg cada, qual será a massa total?',
                'tipo': 'numerico',
                'resposta_correta': 600
            }
        ]
    elif destino == 'marte':
        return [
            {
                'id': 'desafio_1',
                'titulo': 'Desafios de Longa Duração',
                'descricao': 'Quais são os principais desafios de uma missão a Marte comparada à Lua?',
                'tipo': 'texto',
                'dica': 'Considere duração, radiação e comunicação.'
            }
        ]
    else:
        return [
            {
                'id': 'desafio_1',
                'titulo': 'Tecnologias do Futuro',
                'descricao': 'Que tecnologias seriam necessárias para uma missão interestelar?',
                'tipo': 'texto'
            }
        ]

# Sua chave da API da NASA aqui
NASA_API_KEY = 'IdakpPAlUh3A0M2Qc8RXPgjDlICN9Yi5OwndZgWM'

def buscar_imagem_nasa(query):
    """
    Busca uma imagem na NASA de forma robusta, com diagnóstico no terminal.
    """
    search_url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
    logging.info(f"[API] Etapa 1: Buscando na NASA com a URL: {search_url}")
    
    try:
        # Etapa 1: Fazer a busca inicial
        search_response = requests.get(search_url, timeout=10)
        search_response.raise_for_status() # Verifica se houve erro na requisição (4xx ou 5xx)
        search_data = search_response.json()

        if not search_data.get("collection", {}).get("items"):
            logging.warning(f"[API] Nenhum resultado encontrado na NASA para a busca '{query}'.")
            return None

        # Pega o primeiro item da busca
        first_item = search_data["collection"]["items"][0]
        asset_manifest_url = first_item.get("href")

        if not asset_manifest_url:
            logging.warning("[API] O item da busca não continha um link para os detalhes (href).")
            return None

        # Etapa 2: Buscar os detalhes do item para pegar um link de imagem válido
        logging.info(f"[API] Etapa 2: Buscando detalhes do item em: {asset_manifest_url}")
        manifest_response = requests.get(asset_manifest_url, timeout=10)
        manifest_response.raise_for_status()
        manifest_data = manifest_response.json()

        # Procura por um link de imagem de tamanho médio ou original
        for image_url in manifest_data:
            if "medium.jpg" in image_url or "orig.jpg" in image_url:
                logging.info(f"[API] SUCESSO! Imagem encontrada para '{query}': {image_url}")
                return image_url
        
        # Se não achar um link ideal, pega o primeiro que encontrar
        if manifest_data:
            fallback_url = manifest_data[0]
            logging.info(f"[API] Usando primeira imagem disponível como fallback: {fallback_url}")
            return fallback_url

    except requests.exceptions.RequestException as e:
        logging.error(f"!!! [API] ERRO CRÍTICO ao se comunicar com a NASA para '{query}': {e}")
        return None
    
    logging.error(f"[API] Falha inesperada ao processar a busca por '{query}'.")
    return None


# --- EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
# --- CONTROLE DE CACHE PARA EVITAR BFCACHE (reforça bloqueio do Voltar) ---