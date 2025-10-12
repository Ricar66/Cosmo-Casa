"""Static application data (spacecraft, habitat modules and events).

Keeps responsibilities separated, avoiding bloating app.py.
"""

# --- BANCO DE DADOS DAS NAVES ESPACIAIS ---
NAVES_ESPACIAIS = {
    'falcon9': {
        'nome': 'Falcon 9',
        'operador': 'USA / SpaceX',
        'imagem': 'Falcon9.png',
        'descricao': 'Reusable two-stage rocket with excellent thrust-to-weight ratio. Ideal for heavy payloads to low Earth orbit.',
        'capacidade_carga': 22.8,
        'perfil_missao': 'Two-Stage',
        'empuxo_total': 7607,
        'impulso_especifico': 282,
        'massa_seca': 28.2,
        'massa_combustivel': 433.1,
        'delta_v_total': 9300,
        'taxa_empuxo_peso': 1.8
    },
    'pslv': {
        'nome': 'PSLV',
        'operador': 'India / ISRO',
        'imagem': 'PSLV.jpg',
        'descricao': 'Reliable multi-stage rocket capable of inserting payloads into polar and sun-synchronous orbits.',
        'capacidade_carga': 3.8,
        'perfil_missao': 'Multiple Burns',
        'empuxo_total': 4800,
        'impulso_especifico': 262,
        'massa_seca': 18.5,
        'massa_combustivel': 230.0,
        'delta_v_total': 8200,
        'taxa_empuxo_peso': 1.4
    },
    'longmarch8a': {
        'nome': 'Long-March8A',
        'operador': 'China / CASC',
        'imagem': 'foguete-longa-marcha.png',
        'descricao': 'Medium-lift launcher with capability for multiple orbits and extended coasting phases.',
        'capacidade_carga': 9.8,
        'perfil_missao': 'Extended Coasting',
        'empuxo_total': 5800,
        'impulso_especifico': 275,
        'massa_seca': 22.1,
        'massa_combustivel': 320.5,
        'delta_v_total': 8800,
        'taxa_empuxo_peso': 1.6
    },
    'gslv': {
        'nome': 'GSLV',
        'operador': 'India / ISRO',
        'imagem': 'LVM3_M3.png',
        'descricao': 'Rocket with an upper cryogenic stage for precise insertion into geosynchronous transfer orbits.',
        'capacidade_carga': 2.5,
        'perfil_missao': 'Cryogenic Upper Stage',
        'empuxo_total': 4200,
        'impulso_especifico': 295,
        'massa_seca': 16.8,
        'massa_combustivel': 198.7,
        'delta_v_total': 9500,
        'taxa_empuxo_peso': 1.3
    }
}

# --- BANCO DE DADOS DOS MÓDULOS (com imagens e observações para tooltips) ---
MODULOS_HABITAT = {
    'suporte_vida': {"nome": "Life Support", "massa": 800, "energia": 15, "agua": 50,
                     "imagem": "suporte_vida.svg", "obs": "Essential. Connects to Housing, Sanitation, and Food Production."},
    'habitacional': {"nome": "Private Quarters", "massa": 200, "energia": 1, "agua": 5,
                     "imagem": "Privado.svg", "obs": "Crew accommodations. Can be integrated with Leisure."},
    'alimentacao': {"nome": "Food and Meals", "massa": 300, "energia": 3, "agua": 20,
                    "imagem": "refeicao.svg", "obs": "Area for food preparation and consumption."},
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
    'blindagem': {"nome": "Shielding/Protection", "massa": 600, "energia": 0, "agua": 0,
                  "imagem": "Blindagem.svg", "obs": "Integrated with inflatable or structural modules."},
    'estrutural': {"nome": "Modular Structural (TESSERAE)", "massa": 400, "energia": 1, "agua": 0,
                   "imagem": "Tesserea.svg", "obs": "Base for other modules, easy reconfiguration."},
    'lazer': {"nome": "Culture and Leisure", "massa": 150, "energia": 1, "agua": 0,
              "imagem": "Cultura.svg", "obs": "Integrates with Housing, Inflatable, or Research."},
    'robotico': {"nome": "Construction/Maintenance Robotics", "massa": 350, "energia": 6, "agua": 0,
                 "imagem": "Robotica.svg", "obs": "Connects to: Modular Structural, Storage."},
    'hidroponia': {"nome": "Food Production (Hydroponics)", "massa": 500, "energia": 8, "agua": 40,
                   "imagem": "Hidroponia.svg", "obs": "Growing plants in a controlled environment to supplement the diet."},
    'controle': {"nome": "Control and Communications", "massa": 200, "energia": 3, "agua": 0,
                 "imagem": "Controle.svg", "obs": "Overlap: Research/Operations."},
    'multifuncional': {"nome": "Multifunctional Module", "massa": 600, "energia": 4, "agua": 10,
                       "imagem": "Multifuncional.svg", "obs": "Dormitory, meals, leisure, work."},
    'impressao3d': {"nome": "3D Printing/Manufacturing", "massa": 300, "energia": 5, "agua": 2,
                    "imagem": "Impressora.svg", "obs": "Manufacturing spare parts and tools on demand."}
}

# --- BANCO DE DADOS DE EVENTOS ALEATÓRIOS ---
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
"""Static data used by Cosmo-Casa's UI and simulation.

- `NAVES_ESPACIAIS`: catalog with name, image, and educational notes;
- `MODULOS_HABITAT`: habitat modules with descriptions and attributes;
- `EVENTOS_ALEATORIOS`: turn-based simulation events with effects.

Keeps educational content separate from logic, allowing independent evolution
and future internationalization.
"""