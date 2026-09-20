# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE ESTILOS DE LUTA
# =========================================================


def estilo(emoji, categoria, descricao):
    return {
        "emoji": emoji,
        "categoria": categoria,
        "descricao": descricao
    }


ESTILOS = {

    # ==================== ESPADAS ====================

    "Ittoryu": estilo(
        "⚔️", "Espadachim",
        "Estilo de combate utilizando uma única espada."
    ),

    "Nitoryu": estilo(
        "⚔️", "Espadachim",
        "Estilo de combate utilizando duas espadas."
    ),

    "Santoryu": estilo(
        "⚔️", "Espadachim",
        "Estilo de combate utilizando três espadas."
    ),

    "Oden Nitoryu": estilo(
        "⚔️", "Espadachim",
        "Estilo de duas espadas desenvolvido em Wano."
    ),

    "Foxfire Style": estilo(
        "🔥", "Espadachim",
        "Estilo de espada especializado em técnicas relacionadas ao fogo."
    ),

    "Kappa Style": estilo(
        "🐸", "Espadachim",
        "Estilo de espada baseado nas técnicas de Kawamatsu."
    ),

    "Hanauta Style": estilo(
        "🎵", "Espadachim",
        "Estilo de esgrima baseado em movimentos extremamente rápidos."
    ),


    # ==================== ARTES MARCIAIS ====================

    "Fish-Man Karate": estilo(
        "🌊", "Lutador",
        "Arte marcial dos Homens-Peixe que utiliza golpes físicos "
        "e a força da água."
    ),

    "Fish-Man Jujutsu": estilo(
        "💧", "Lutador",
        "Arte marcial especializada na manipulação da água."
    ),

    "Hasshoken": estilo(
        "💥", "Lutador",
        "Arte marcial capaz de transmitir vibrações através dos golpes."
    ),

    "Ryusoken": estilo(
        "🐉", "Lutador",
        "Arte marcial baseada em golpes semelhantes às garras de um dragão."
    ),

    "Okama Kenpo": estilo(
        "🩰", "Lutador",
        "Arte marcial baseada em movimentos corporais rápidos e acrobáticos."
    ),

    "Newkama Kenpo": estilo(
        "🌈", "Lutador",
        "Forma avançada do Okama Kenpo."
    ),

    "Jao Kun Do": estilo(
        "🥋", "Lutador",
        "Estilo de combate corpo a corpo baseado em golpes rápidos "
        "e técnicas marciais."
    ),

    "Black Leg Style": estilo(
        "🦵", "Lutador",
        "Estilo de combate especializado exclusivamente no uso das pernas."
    ),

    "Diable Jambe": estilo(
        "🔥", "Lutador",
        "Evolução do Black Leg Style que utiliza calor intenso nas pernas."
    ),

    "Ifrit Jambe": estilo(
        "🔥", "Lutador",
        "Forma superior do estilo de pernas, combinando enorme calor "
        "e velocidade."
    ),

    "Electro": estilo(
        "⚡", "Lutador",
        "Estilo racial dos Minks que utiliza eletricidade produzida pelo corpo."
    ),


    # ==================== LONGA DISTÂNCIA ====================

    "Sniper Fighting": estilo(
        "🎯", "Atirador",
        "Estilo especializado em disparos precisos a grandes distâncias."
    ),

    "Gun Fighting": estilo(
        "🔫", "Atirador",
        "Estilo especializado no combate com armas de fogo."
    ),

    "Archery": estilo(
        "🏹", "Atirador",
        "Estilo especializado no uso de arco e flecha."
    ),

    "Kabuto Fighting": estilo(
        "🎯", "Atirador",
        "Estilo especializado no uso do Kabuto e disparos de longa distância."
    ),

    "Pop Green Fighting": estilo(
        "🌱", "Atirador",
        "Estilo que utiliza Pop Greens como munição e recurso de combate."
    ),


    # ==================== GOVERNO / ROKUSHIKI ====================

    "Rokushiki": estilo(
        "🐆", "Lutador",
        "Sistema marcial utilizado por agentes do Governo Mundial."
    ),

    "Six Powers": estilo(
        "六", "Lutador",
        "Domínio das seis técnicas fundamentais do Rokushiki."
    ),

    "Cipher Pol Martial Arts": estilo(
        "🕵️", "Lutador",
        "Estilo de combate especializado utilizado por agentes da Cipher Pol."
    ),


    # ==================== TECNOLOGIA ====================

    "Cyborg Combat": estilo(
        "🤖", "Lutador",
        "Estilo baseado no uso de modificações mecânicas e armas "
        "incorporadas ao corpo."
    ),

    "Pacifista Combat": estilo(
        "🔬", "Lutador",
        "Estilo de combate baseado na tecnologia e nas capacidades "
        "dos Pacifistas."
    ),
}


# =========================================================
# FUNÇÕES DO CATÁLOGO
# =========================================================

def listar_estilos():
    return list(ESTILOS.keys())


def buscar_estilo(nome):
    return ESTILOS.get(nome)


def existe_estilo(nome):
    return nome in ESTILOS


def estilos_por_classe(classe):
    return {
        nome: dados
        for nome, dados in ESTILOS.items()
        if dados["categoria"] == classe
    }


def quantidade_estilos():
    return len(ESTILOS)
