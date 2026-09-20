# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE CLASSES
# =========================================================


def classe(emoji, descricao, especialidade):
    return {
        "emoji": emoji,
        "descricao": descricao,
        "especialidade": especialidade
    }


CLASSES = {

    "Espadachim": classe(
        "⚔️",
        "Combatentes especializados no uso de espadas e armas de lâmina.",
        "Permite desenvolver e dominar estilos de luta relacionados à espada."
    ),

    "Lutador": classe(
        "🥊",
        "Combatentes especializados no próprio corpo e no combate corpo a corpo.",
        "Permite desenvolver estilos marciais, golpes físicos e técnicas desarmadas."
    ),

    "Atirador": classe(
        "🎯",
        "Combatentes especializados em armas e técnicas de longa distância.",
        "Permite desenvolver estilos relacionados a armas de fogo, arcos e projéteis."
    ),

    "Guardião": classe(
        "🛡️",
        "Combatentes especializados em defesa, resistência e proteção.",
        "Permite desenvolver estilos defensivos e técnicas voltadas à proteção."
    ),

    "Berserker": classe(
        "💢",
        "Combatentes que priorizam agressividade, força e pressão ofensiva.",
        "Permite desenvolver estilos pesados e técnicas de combate brutal."
    ),

    "Líder de Batalha": classe(
        "👑",
        "Combatentes especializados em liderança, comando e coordenação durante confrontos.",
        "Permite desenvolver habilidades voltadas à organização e liderança em batalha."
    ),

    "Akuma User": classe(
        "🍈",
        "Combatentes que constroem seu estilo principalmente em torno dos poderes de uma Akuma no Mi.",
        "Permite especialização e evolução voltadas ao domínio da Akuma no Mi."
    ),

    "Haki User": classe(
        "🔥",
        "Combatentes especializados no desenvolvimento e utilização de Haki.",
        "Permite especialização e evolução voltadas aos diferentes tipos de Haki."
    ),
}


# =========================================================
# FUNÇÕES DO CATÁLOGO
# =========================================================

def listar_classes():
    return list(CLASSES.keys())


def buscar_classe(nome):
    return CLASSES.get(nome)


def existe_classe(nome):
    return nome in CLASSES


def quantidade_classes():
    return len(CLASSES)
