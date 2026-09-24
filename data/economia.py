"""Catálogo econômico e mapa navegável inicial do Sea's Paradise.

IDs são estáveis: banco/inventário armazenam o ID, nunca o texto de exibição.
"""

ITENS = {
    "refeicao_simples": dict(nome="Refeição Simples", emoji="🍖", categoria="consumivel", preco=500, vendavel=True, consumivel=True, descricao="Uma refeição comum para a jornada."),
    "refeicao_completa": dict(nome="Refeição Completa", emoji="🍲", categoria="consumivel", preco=1500, vendavel=True, consumivel=True, descricao="Uma refeição farta e de qualidade."),
    "primeiros_socorros": dict(nome="Kit de Primeiros Socorros", emoji="🩹", categoria="consumivel", preco=4000, vendavel=True, consumivel=True, descricao="Material para cuidados básicos. O uso é registrado; efeitos narrativos dependem da situação."),
    "kit_medico": dict(nome="Kit Médico", emoji="🩺", categoria="consumivel", preco=12000, vendavel=True, consumivel=True, descricao="Material médico avançado. Não substitui automaticamente uma ação médica no RP."),
    "kit_reparo": dict(nome="Kit de Reparo Naval", emoji="🔧", categoria="naval", preco=8000, vendavel=True, consumivel=True, descricao="Material para reparos emergenciais. Com Carpinteiro, o rendimento aumenta conforme o domínio.", efeito="reparo_navio", valor_efeito=50),
    "revestimento_navio": dict(nome="Revestimento de Sabaody", emoji="🫧", categoria="naval", preco=50000, vendavel=False, consumivel=True, descricao="Revestimento especial necessário para a descida marítima até a Ilha dos Homens-Peixe."),
    "mantimentos": dict(nome="Caixa de Mantimentos", emoji="📦", categoria="suprimento", preco=5000, vendavel=True, consumivel=False, descricao="Mantimentos para viagens e carga."),
    "espada_comum": dict(nome="Espada Comum", emoji="⚔️", categoria="arma", preco=10000, vendavel=True, consumivel=False, descricao="Uma espada simples e confiável."),
    "katana": dict(nome="Katana", emoji="🗡️", categoria="arma", preco=20000, vendavel=True, consumivel=False, descricao="Katana de boa fabricação."),
    "flintlock": dict(nome="Pistola Flintlock", emoji="🔫", categoria="arma", preco=15000, vendavel=True, consumivel=False, descricao="Arma de fogo de curto alcance."),
    "rifle": dict(nome="Rifle", emoji="🎯", categoria="arma", preco=25000, vendavel=True, consumivel=False, descricao="Arma de fogo voltada para distância."),
    "arco": dict(nome="Arco", emoji="🏹", categoria="arma", preco=10000, vendavel=True, consumivel=False, descricao="Arco para combate à distância."),
    "municao": dict(nome="Munição", emoji="💥", categoria="municao", preco=1000, vendavel=True, consumivel=True, descricao="Pacote de munição para armas de fogo."),
    "flechas": dict(nome="Flechas", emoji="🏹", categoria="municao", preco=800, vendavel=True, consumivel=True, descricao="Conjunto de flechas para arco."),
    "bussola": dict(nome="Bússola", emoji="🧭", categoria="navegacao", preco=2500, vendavel=True, consumivel=False, descricao="Auxilia a navegação em mares comuns."),
    "carta_east_blue": dict(nome="Carta Náutica — East Blue", emoji="🗺️", categoria="navegacao", preco=4000, vendavel=True, consumivel=False, descricao="Carta náutica das rotas conhecidas do East Blue."),
    "log_pose": dict(nome="Log Pose", emoji="🧭", categoria="navegacao", preco=25000, vendavel=True, consumivel=False, descricao="Instrumento fundamental para rotas da Grand Line."),
    "den_den_mushi": dict(nome="Den Den Mushi", emoji="📞", categoria="utilidade", preco=20000, vendavel=True, consumivel=False, descricao="Caracol de comunicação à distância."),
    "binoculo": dict(nome="Binóculo", emoji="🔭", categoria="utilidade", preco=3000, vendavel=True, consumivel=False, descricao="Auxilia observação marítima e terrestre."),
    "kit_aventura": dict(nome="Kit de Aventura", emoji="🎒", categoria="utilidade", preco=3500, vendavel=True, consumivel=False, descricao="Corda e ferramentas simples para exploração."),
}

# Eternal Poses são itens reais e individualizados por destino.
for _id, _nome, _preco in [
    ("eternal_dawn", "Dawn Island", 12000),
    ("eternal_orange", "Orange Town", 12000),
    ("eternal_syrup", "Syrup Village", 12000),
    ("eternal_baratie", "Baratie", 15000),
    ("eternal_conomi", "Conomi Islands", 15000),
    ("eternal_loguetown", "Loguetown", 20000),
]:
    ITENS[_id] = dict(nome=f"Eternal Pose — {_nome}", emoji="🧭", categoria="navegacao", preco=_preco, vendavel=True, consumivel=False, destino=_nome, descricao=f"Aponta permanentemente para {_nome}.")


# Capturas de pesca — entram no inventário e podem ser vendidas/usar em sistemas futuros.
ITENS.update({
    "peixe_comum": dict(nome="Pescado Comum",emoji="🐟",categoria="pesca",preco=500,vendavel=True,consumivel=False,descricao="Peixes comuns capturados no mar."),
    "peixe_incomum": dict(nome="Pescado Incomum",emoji="🐠",categoria="pesca",preco=1800,vendavel=True,consumivel=False,descricao="Captura incomum, valorizada em mercados e cozinhas."),
    "peixe_raro": dict(nome="Pescado Raro",emoji="🦈",categoria="pesca",preco=6500,vendavel=True,consumivel=False,descricao="Captura rara de alto valor."),
    "peixe_lendario": dict(nome="Pescado Lendário",emoji="🐉",categoria="pesca",preco=25000,vendavel=True,consumivel=False,descricao="Uma captura excepcional e extremamente rara."),
    "akuma_misteriosa": dict(nome="Akuma no Mi Misteriosa",emoji="🍈",categoria="especial",preco=0,vendavel=False,consumivel=False,descricao="Uma Akuma no Mi ainda não identificada. Deve ser identificada/consumida pelo sistema de Akuma antes de conceder poder."),
    "mapa_tesouro": dict(nome="Mapa de Tesouro",emoji="🗺️",categoria="especial",preco=0,vendavel=False,consumivel=False,descricao="Um mapa que aponta para um tesouro especial. Pode alimentar futuras explorações/eventos."),
})

EMBARCACOES = {
    "barco_pequeno": dict(nome="Barco Pequeno", emoji="🛶", preco=25000, capacidade=2, carga=5, integridade=100),
    "veleiro_pequeno": dict(nome="Veleiro Pequeno", emoji="⛵", preco=80000, capacidade=4, carga=15, integridade=200),
    "veleiro": dict(nome="Veleiro", emoji="⛵", preco=200000, capacidade=8, carga=30, integridade=350),
    "caravela": dict(nome="Caravela", emoji="🏴‍☠️", preco=500000, capacidade=15, carga=60, integridade=600),
    "galeao": dict(nome="Galeão", emoji="🚢", preco=1500000, capacidade=30, carga=120, integridade=1000),
}

LOJAS = {
    "Dawn Island": {"itens": ["refeicao_simples","primeiros_socorros","bussola","carta_east_blue","kit_aventura"], "barcos": ["barco_pequeno"]},
    "Orange Town": {"itens": ["refeicao_simples","mantimentos","espada_comum","flintlock","municao","bussola","binoculo","kit_aventura","eternal_orange"], "barcos": ["barco_pequeno","veleiro_pequeno"]},
    "Syrup Village": {"itens": ["refeicao_simples","primeiros_socorros","kit_medico","kit_reparo","mantimentos","bussola","carta_east_blue","eternal_syrup"], "barcos": ["barco_pequeno","veleiro_pequeno"]},
    "Baratie": {"itens": ["refeicao_simples","refeicao_completa","mantimentos","kit_reparo","carta_east_blue","eternal_baratie"], "barcos": []},
    "Conomi Islands": {"itens": ["refeicao_simples","mantimentos","bussola","carta_east_blue","binoculo","kit_reparo","eternal_conomi"], "barcos": ["barco_pequeno","veleiro_pequeno"]},
    "Loguetown": {"itens": list(ITENS.keys()), "barcos": list(EMBARCACOES.keys())},
    "Sabaody Archipelago": {"itens": ["refeicao_completa","kit_medico","kit_reparo","mantimentos","log_pose","den_den_mushi","binoculo","revestimento_navio"], "barcos": ["veleiro","caravela"]},
    "Water 7": {"itens": ["refeicao_completa","kit_medico","kit_reparo","mantimentos","log_pose","den_den_mushi"], "barcos": ["veleiro","caravela","galeao"]},
    "Alabasta": {"itens": ["refeicao_simples","kit_medico","mantimentos","log_pose","den_den_mushi"], "barcos": []},
    "Dressrosa": {"itens": ["refeicao_completa","kit_medico","kit_reparo","mantimentos","log_pose","den_den_mushi"], "barcos": ["veleiro","caravela"]},
    "Whole Cake Island": {"itens": ["refeicao_completa","kit_medico","mantimentos","log_pose","den_den_mushi"], "barcos": []},
    "Wano Country": {"itens": ["refeicao_completa","kit_medico","kit_reparo","mantimentos"], "barcos": []},
    "Egghead": {"itens": ["kit_medico","kit_reparo","log_pose","den_den_mushi","binoculo"], "barcos": []},
    "Elbaf": {"itens": ["refeicao_completa","kit_medico","kit_reparo","mantimentos","log_pose"], "barcos": []},
}

ROTAS = {
    "Dawn Island": ["Orange Town"],
    "Orange Town": ["Dawn Island", "Syrup Village"],
    "Syrup Village": ["Orange Town", "Baratie"],
    "Baratie": ["Syrup Village", "Conomi Islands"],
    "Conomi Islands": ["Baratie", "Loguetown"],
    "Loguetown": ["Conomi Islands"],
}

ALIASES_LOCAL = {
    "sabaody": "Sabaody Archipelago", "sabaody park": "Sabaody Archipelago", "shabondy": "Sabaody Archipelago",
    "water 7": "Water 7", "alabasta": "Alabasta", "arabasta": "Alabasta", "dressrosa": "Dressrosa",
    "whole cake": "Whole Cake Island", "wano": "Wano Country", "egghead": "Egghead", "elbaf": "Elbaf",
    "dawn": "Dawn Island", "dawn island": "Dawn Island", "ilha dawn": "Dawn Island", "foosha": "Dawn Island", "vila foosha": "Dawn Island",
    "orange": "Orange Town", "orange town": "Orange Town",
    "syrup": "Syrup Village", "syrup village": "Syrup Village", "vila syrup": "Syrup Village",
    "baratie": "Baratie",
    "conomi": "Conomi Islands", "conomi islands": "Conomi Islands", "ilhas conomi": "Conomi Islands",
    "loguetown": "Loguetown", "logue town": "Loguetown",
}

def normalizar_local(nome):
    if not nome:
        return None
    chave = str(nome).strip().casefold()
    return ALIASES_LOCAL.get(chave, next((x for x in LOJAS if x.casefold() == chave), str(nome).strip()))
