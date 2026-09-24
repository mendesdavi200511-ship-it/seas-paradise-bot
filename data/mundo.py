"""Conteúdo dinâmico do mundo do Sea's Paradise.
Balanceamento próprio do RP; não representa power-scaling canônico oficial.
"""
from data.navegacao import LOCAIS

BOSS_RANKS = {
    "E": {"hp": 350, "attr": 120, "berries": (1500,3500), "pontos": (5,12), "pct": (0,1)},
    "D": {"hp": 700, "attr": 300, "berries": (4000,9000), "pontos": (10,25), "pct": (1,2)},
    "C": {"hp": 1400, "attr": 750, "berries": (10000,25000), "pontos": (20,45), "pct": (1,3)},
    "B": {"hp": 2800, "attr": 1800, "berries": (30000,70000), "pontos": (35,75), "pct": (2,4)},
    "A": {"hp": 5500, "attr": 4500, "berries": (80000,180000), "pontos": (60,120), "pct": (2,5)},
    "S": {"hp": 10000, "attr": 10000, "berries": (200000,450000), "pontos": (90,180), "pct": (3,6)},
    "SS": {"hp": 18000, "attr": 22000, "berries": (500000,1000000), "pontos": (140,260), "pct": (4,8)},
    "LENDARIO": {"hp": 30000, "attr": 40000, "berries": (1200000,3000000), "pontos": (220,400), "pct": (5,10)},
}

# Chefes especiais disponíveis para sorteio global. Recompensas finais são sorteadas dentro do rank.
BOSSES_ESPECIAIS = [
    ("Machado Morgan","D","Shells Town","Marinheiro brutal e resistente, perigoso para novatos."),
    ("Buggy, o Palhaço","C","Orange Town","Capitão pirata imprevisível com uma tripulação armada."),
    ("Kuro dos Mil Planos","C","Syrup Village","Assassino extremamente veloz e estrategista."),
    ("Don Krieg","B","Baratie","Comandante de uma força pirata fortemente equipada."),
    ("Arlong","B","Conomi Islands","Homem-Peixe de força brutal e domínio territorial."),
    ("Caçador de Loguetown","B","Loguetown","Criminoso procurado que se esconde no centro comercial do East Blue."),
    ("Agente Baroque","B","Whisky Peak","Agente de elite operando sob identidade desconhecida."),
    ("Guardião Jurássico","A","Little Garden","Predador colossal que domina uma região da ilha."),
    ("Wapol","B","Drum Island","Antigo tirano acompanhado por combatentes leais."),
    ("Crocodile","S","Alabasta","Ameaça de escala nacional com grande poder e influência."),
    ("Bellamy","B","Jaya","Pirata violento conhecido por esmagar adversários despreparados."),
    ("Sacerdote de Skypiea","A","Skypiea","Combatente dos céus com técnicas e terreno incomuns."),
    ("Agente CP9","S","Enies Lobby","Agente do Governo treinado em técnicas de elite."),
    ("General Zumbi","A","Thriller Bark","Criatura reanimada de enorme resistência."),
    ("Supernova Hostil","S","Sabaody Archipelago","Pirata de grande notoriedade em busca de conflito."),
    ("Guardião de Impel Down","SS","Impel Down","Ameaça criada para impedir qualquer fuga da prisão."),
    ("Oficial de Marineford","SS","Marineford","Combatente de alto escalão da Marinha."),
    ("Sea King Ancestral","S","Calm Belt","Criatura marítima gigantesca capaz de destruir embarcações."),
    ("Novo Pirata do Novo Mundo","S","Punk Hazard","Veterano endurecido pelas condições do Novo Mundo."),
    ("Gladiador Invicto","A","Dressrosa","Combatente famoso do Coliseu Corrida."),
    ("Comandante Mink Corrompido","S","Zou","Guerreiro Mink perigoso sob circunstâncias anormais."),
    ("Oficial de Totto Land","SS","Whole Cake Island","Combatente de elite defendendo o território."),
    ("Samurai Renegado","S","Wano Country","Espadachim veterano com domínio excepcional."),
    ("Experimento Seraphim","SS","Egghead","Arma experimental de altíssimo risco."),
    ("Guerreiro Gigante","SS","Elbaf","Guerreiro de Elbaf com força devastadora."),
    ("Capitão de Hachinosu","SS","Hachinosu","Pirata veterano de uma ilha dominada por criminosos."),
]

MISSOES_MARINHA = [
    ("Patrulha Costeira","E","Investigue relatos de contrabando e proteja civis."),
    ("Captura de Piratas","D","Localize e prenda um pequeno grupo pirata procurado."),
    ("Escolta Oficial","D","Escolte uma carga ou autoridade até o ponto seguro."),
    ("Desmantelar Contrabando","C","Identifique o depósito e prenda os responsáveis."),
    ("Resgate de Civis","C","Encontre desaparecidos e retire-os de uma área hostil."),
    ("Caçada a Capitão Procurado","B","Localize um capitão perigoso e encerre suas operações."),
    ("Operação de Inteligência","B","Investigue uma rede criminosa sem comprometer a operação."),
    ("Cerco Pirata","A","Retome uma área ocupada por uma tripulação poderosa."),
    ("Ameaça de Grande Escala","S","Neutralize uma ameaça capaz de desestabilizar toda a região."),
]

TESOUROS = [
    ("Baú de Berries","comum",55), ("Caixa de Suprimentos","comum",20),
    ("Equipamento Náutico","incomum",10), ("Eternal Pose Perdido","raro",6),
    ("Mapa de Tesouro","raro",5), ("Arma Rara","epico",3), ("Akuma no Mi","lendario",1),
]

PESCAS = {
    "comum":["Sardinha Azul","Atum do East Blue","Peixe-Lua","Cavala Marinha"],
    "incomum":["Peixe-Tigre","Polvo Rubro","Enguia da Grand Line"],
    "raro":["Peixe-Rei","Tubarão Listrado","Carpa Celeste"],
    "lendario":["Peixe Dourado Ancestral","Filhote de Sea Beast"],
}

ILHAS_ESPECIAIS = {
    "Shells Town":{"inimigos":["Piratas locais","Marinheiros corruptos"],"bosses":["Machado Morgan"],"segredos":[]},
    "Orange Town":{"inimigos":["Piratas","Animais hostis"],"bosses":["Buggy, o Palhaço"],"segredos":["Tesouros escondidos entre as ruínas"]},
    "Syrup Village":{"inimigos":["Piratas invasores"],"bosses":["Kuro dos Mil Planos"],"segredos":[]},
    "Baratie":{"inimigos":["Piratas do mar"],"bosses":["Don Krieg"],"segredos":["Rotas comerciais"]},
    "Conomi Islands":{"inimigos":["Homens-Peixe hostis"],"bosses":["Arlong"],"segredos":["Cartografia regional"]},
    "Alabasta":{"inimigos":["Bandidos do deserto","Agentes criminosos"],"bosses":["Crocodile"],"segredos":["Poneglyph histórico"]},
    "Skypiea":{"inimigos":["Guerreiros celestes","Sacerdotes"],"bosses":["Sacerdote de Skypiea"],"segredos":["Poneglyph","Ruínas de Shandora"]},
    "Enies Lobby":{"inimigos":["Agentes do Governo","Marinha"],"bosses":["Agente CP9"],"segredos":["Instalações governamentais"]},
    "Sabaody Archipelago":{"inimigos":["Traficantes","Caçadores","Piratas"],"bosses":["Supernova Hostil"],"segredos":["Mercado clandestino","Revestimento naval"]},
    "Fish-Man Island":{"inimigos":["Criminosos submarinos"],"bosses":["Ameaça submarina"],"segredos":["Poneglyph"]},
    "Whole Cake Island":{"inimigos":["Forças de Totto Land"],"bosses":["Oficial de Totto Land"],"segredos":["Road Poneglyph"]},
    "Wano Country":{"inimigos":["Samurais hostis","Piratas"],"bosses":["Samurai Renegado"],"segredos":["Road Poneglyph","Ruínas antigas"]},
    "Egghead":{"inimigos":["Armas científicas","Agentes"],"bosses":["Experimento Seraphim"],"segredos":["Tecnologia avançada"]},
    "Elbaf":{"inimigos":["Guerreiros gigantes"],"bosses":["Guerreiro Gigante"],"segredos":["Conhecimento ancestral"]},
    "Laugh Tale":{"inimigos":["???"],"bosses":["???"],"segredos":["O segredo final do mundo"]},
}

def info_ilha(nome):
    reg, perigo = LOCAIS.get(nome,("Desconhecida",2))
    x=ILHAS_ESPECIAIS.get(nome,{"inimigos":["Ameaças locais"],"bosses":[],"segredos":["Tesouros ainda não catalogados"]})
    return {"nome":nome,"regiao":reg,"perigo":perigo,**x}
