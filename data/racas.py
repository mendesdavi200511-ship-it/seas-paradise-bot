# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE RAÇAS
# =========================================================


def perk(emoji, nome, descricao):
    return {
        "emoji": emoji,
        "nome": nome,
        "descricao": descricao
    }


RACAS = {

    # =====================================================
    # HUMANO
    # =====================================================

    "Humano": {
        "emoji": "👤",
        "descricao": (
            "Humanos são a raça mais comum dos mares, conhecidos por sua "
            "versatilidade e capacidade de adaptação. Apesar de não possuírem "
            "características especiais, podem alcançar níveis extraordinários "
            "através de treinamento."
        ),
        "perks": [
            perk(
                "🌎",
                "Adaptabilidade",
                "Podem viver e se desenvolver em praticamente qualquer região."
            ),
            perk(
                "🧠",
                "Versatilidade",
                "Podem aprender diferentes estilos de luta e técnicas sem "
                "restrições raciais. Aumentando pra +2 o limite de estilo "
                "de luta e +1 para profissão."
            ),
            perk(
                "💪",
                "Potencial Físico",
                "Possuem grande capacidade de evolução através de treinamento. "
                "Cortando pela metade a quantia de caracteres necessária para "
                "treinamentos físicos."
            ),
            perk(
                "🔥",
                "Vontade",
                "Possuem alto potencial para desenvolver Haki através de "
                "treinamento e experiência. Conseguindo ter mais facilidade "
                "de despertar o Haki do Conquistador através de fortes emoções."
            ),
        ]
    },

    # =====================================================
    # HOMEM-PEIXE
    # =====================================================

    "Homem-Peixe": {
        "emoji": "🐟",
        "descricao": (
            "Homens-Peixe são uma raça humanoide de origem marinha, conhecidos "
            "por sua força física superior e enorme afinidade com o oceano. "
            "Possuem características inspiradas em diferentes espécies "
            "aquáticas e podem utilizar técnicas de combate próprias da raça."
        ),
        "perks": [
            perk(
                "🌊",
                "Nadador Nato",
                "Possuem grande domínio dentro da água, podendo nadar e se "
                "movimentar com extrema facilidade. Aumentando a velocidade "
                "enquanto estão no mar em +150%."
            ),
            perk(
                "💪",
                "Força Aquática",
                "Possuem força física naturalmente superior à de humanos. "
                "Seus atributos são 30% aumentados passivamente. Dentro do mar, "
                "seus atributos aumentam em 100%."
            ),
            perk(
                "🥋",
                "Karatê Homem-Peixe",
                "Possuem aptidão natural para aprender e utilizar o Karatê "
                "Homem-Peixe. Conseguem como adicional o estilo Fish-Man Karate."
            ),
            perk(
                "💧",
                "Manipulação da Água",
                "Podem utilizar a água presente no ambiente como parte de suas "
                "técnicas. Conseguem como adicional o estilo Fish-Man Jujutsu."
            ),
        ]
    },

    # =====================================================
    # SEREIANO
    # =====================================================

    "Sereiano": {
        "emoji": "🧜",
        "descricao": (
            "Sereianos são uma raça aquática de aparência humanoide, "
            "caracterizada por sua cauda de peixe e grande ligação com o "
            "oceano. São conhecidos por sua velocidade na água e por "
            "habilidades naturais únicas."
        ),
        "perks": [
            perk(
                "🌊",
                "Nadador Nato",
                "Possuem enorme velocidade e mobilidade dentro da água. "
                "Passivamente a velocidade e agilidade na água é de +60%."
            ),
            perk(
                "🧜",
                "Cauda Aquática",
                "Sua cauda proporciona grande impulso e permite movimentos "
                "extremamente eficientes debaixo d'água. Aumentando a "
                "velocidade do nado em +50%."
            ),
            perk(
                "🎶",
                "Voz Encantadora",
                "Possuem uma voz naturalmente bela, podendo desenvolver "
                "habilidades relacionadas ao canto e à música. Ganham "
                "automaticamente a profissão vinculada a este perk."
            ),
            perk(
                "🐟",
                "Comunicação Marinha",
                "Podem aprender a se comunicar com criaturas marinhas, "
                "possuindo afinidade natural com a vida oceânica."
            ),
        ]
    },

    # =====================================================
    # MINK
    # =====================================================

    "Mink": {
        "emoji": "🐾",
        "descricao": (
            "Minks são uma raça de humanoides animais originária de Zou. "
            "Possuem características de mamíferos e são conhecidos por sua "
            "força, agilidade e domínio natural da eletricidade."
        ),
        "perks": [
            perk(
                "🐾",
                "Instinto Animal",
                "Possuem sentidos aguçados, facilitando a percepção de "
                "movimentos, sons e cheiros."
            ),
            perk(
                "⚡",
                "Electro",
                "Podem produzir e canalizar eletricidade naturalmente através "
                "do próprio corpo. Adquirem naturalmente o estilo Electro."
            ),
            perk(
                "🌕",
                "Sulong",
                "Sob a luz da lua cheia, podem assumir sua forma Sulong. "
                "Adquirem a transformação automaticamente quando possuem "
                "sangue Mink puro, e não misto."
            ),
            perk(
                "🥊",
                "Predador Nato",
                "Possuem aptidão natural para combate. Aumentando +15% a "
                "velocidade de ataques."
            ),
        ]
    },

    # =====================================================
    # GIGANTE
    # =====================================================

    "Gigante": {
        "emoji": "🗿",
        "descricao": (
            "Gigantes são uma das maiores raças humanoides do mundo, conhecidos "
            "por seu tamanho colossal, força física absurda e grande resistência. "
            "Sua cultura possui forte tradição guerreira, especialmente "
            "associada a Elbaf."
        ),
        "perks": [
            perk(
                "💪",
                "Força Colossal",
                "Seus ataques físicos aumentam +25% passivamente."
            ),
            perk(
                "🛡️",
                "Corpo Gigantesco",
                "Sua resistência aumenta em +35% passivamente."
            ),
            perk(
                "⚔️",
                "Guerreiro de Elbaf",
                "Aumenta sua força de ataque com armas brancas em +15%."
            ),
            perk(
                "🏔️",
                "Constituição Titânica",
                "Consegue carregar coisas até 3x mais pesadas que sua força suporta."
            ),
        ]
    },

    # =====================================================
    # TONTATTA
    # =====================================================

    "Tontatta": {
        "emoji": "🧚",
        "descricao": (
            "Tontattas são uma pequena raça humanoide conhecida por seu tamanho "
            "minúsculo, força surpreendente e enorme agilidade. Vivem "
            "principalmente em Green Bit e possuem forte ligação com a natureza."
        ),
        "perks": [
            perk(
                "💪",
                "Força Surpreendente",
                "Ganham naturalmente o estilo Tontatta Fight."
            ),
            perk(
                "⚡",
                "Pequeno e Veloz",
                "Possuem aumento passivo de +15% em velocidade/agilidade."
            ),
            perk(
                "🌿",
                "Afinidade Natural",
                "Possuem facilidade para interagir com animais e se adaptar "
                "a ambientes naturais."
            ),
            perk(
                "👀",
                "Furtividade",
                "Seu pequeno tamanho facilita a movimentação silenciosa e a "
                "passagem por espaços extremamente reduzidos."
            ),
        ]
    },

    # =====================================================
    # SKYPIEAN
    # =====================================================

    "Skypiean": {
        "emoji": "🪽",
        "descricao": (
            "Skypieans são habitantes das ilhas do céu, conhecidos pelas "
            "pequenas asas presentes em suas costas. Possuem uma cultura "
            "própria e desenvolveram técnicas adaptadas ao ambiente celestial."
        ),
        "perks": [
            perk(
                "🪽",
                "Asas Celestiais",
                "Auxiliam no equilíbrio, movimentação e manobras no ar. "
                "Apenas flutuam e pulam alto; não conseguem voar de fato."
            ),
            perk(
                "☁️",
                "Habitante do Céu",
                "Possuem facilidade para se adaptar às condições das ilhas "
                "celestiais e ambientes elevados."
            ),
            perk(
                "🔧",
                "Tecnologia Celestial",
                "Possuem familiaridade com tecnologias e recursos encontrados "
                "nas ilhas do céu."
            ),
            perk(
                "👁️",
                "Percepção Aérea",
                "Possuem maior facilidade para perceber movimentos e ameaças "
                "enquanto estiverem em posições elevadas."
            ),
        ]
    },

    # =====================================================
    # BIRKAN
    # =====================================================

    "Birkan": {
        "emoji": "🪽",
        "descricao": (
            "Birkans são uma antiga raça alada originária de Birka, uma ilha "
            "do céu. Possuem asas nas costas e ligação histórica com outras "
            "raças celestiais."
        ),
        "perks": [
            perk(
                "🪽",
                "Asas de Birka",
                "Auxiliam no equilíbrio e permitem maior controle durante "
                "movimentos aéreos."
            ),
            perk(
                "⚡",
                "Afinidade Elétrica",
                "Possuem maior facilidade para utilizar tecnologias e armas "
                "baseadas em eletricidade."
            ),
            perk(
                "☁️",
                "Nascido no Céu",
                "Possuem adaptação natural a grandes altitudes e ambientes "
                "das ilhas celestiais."
            ),
            perk(
                "🔧",
                "Conhecimento Celestial",
                "Possuem facilidade para compreender e utilizar tecnologias "
                "e recursos originários das ilhas do céu."
            ),
        ]
    },

    # =====================================================
    # SHANDIAN
    # =====================================================

    "Shandian": {
        "emoji": "🏹",
        "descricao": (
            "Shandians são um antigo povo guerreiro originário de Jaya, "
            "conhecido por sua forte tradição de combate e pela ligação "
            "com sua terra ancestral."
        ),
        "perks": [
            perk(
                "🏹",
                "Guerreiro Shandian",
                "Possuem facilidade natural para desenvolver técnicas de "
                "combate e utilizar armas tradicionais."
            ),
            perk(
                "🌿",
                "Espírito Guerreiro",
                "Possuem grande determinação para continuar lutando mesmo "
                "diante de situações adversas."
            ),
            perk(
                "☁️",
                "Habitante Celestial",
                "Possuem adaptação natural às condições das ilhas do céu."
            ),
            perk(
                "🪶",
                "Herança de Jaya",
                "Mantêm conhecimentos e tradições transmitidos por gerações, "
                "facilitando o aprendizado de técnicas e costumes ancestrais."
            ),
        ]
    },

    # =====================================================
    # LUNARIAN
    # =====================================================

    "Lunarian": {
        "emoji": "🔥",
        "descricao": (
            "Lunarians são uma raça extremamente rara, conhecida por suas asas "
            "negras, cabelos claros e capacidade de produzir chamas naturalmente. "
            "Antigamente habitavam o topo da Red Line."
        ),
        "perks": [
            perk(
                "🔥",
                "Chama da Raça",
                "Podem produzir e manter chamas em suas costas, utilizando-as "
                "para potencializar seus ataques."
            ),
            perk(
                "🛡️",
                "Resistência Divina",
                "Com a chama acesa, resistência +75% passivamente; com a "
                "chama apagada, velocidade +75%."
            ),
            perk(
                "⚡",
                "Mobilidade Aérea",
                "Possuem asas negras que permitem voar e realizar manobras "
                "aéreas durante o combate."
            ),
            perk(
                "🌋",
                "Corpo Incandescente",
                "Suportam ambientes e temperaturas extremas muito melhor "
                "que outras raças."
            ),
        ]
    },

    # =====================================================
    # KUJA
    # =====================================================

    "Kuja": {
        "emoji": "🐍",
        "descricao": (
            "Kujas são um povo guerreiro originário de Amazon Lily, conhecido "
            "por sua habilidade com arco, combate físico e domínio do Haki."
        ),
        "perks": [
            perk(
                "🏹",
                "Arqueira Nato",
                "Possuem facilidade natural com arcos e armas de longo alcance, "
                "possuindo naturalmente o estilo associado a arco."
            ),
            perk(
                "🐍",
                "Guerreira Kuja",
                "Iniciam com 1 atributo de cada categoria acima do inicial."
            ),
            perk(
                "👁️",
                "Haki Guerreiro",
                "Possuem maior facilidade para aprender e desenvolver Haki. "
                "Já nascem com conhecimento em Busoshoku Haki."
            ),
            perk(
                "⚔️",
                "Amazon",
                "Possuem grande familiaridade com combates individuais e "
                "técnicas de caça, além da profissão associada a este perk."
            ),
        ]
    },

    # =====================================================
    # BUCANEIRO
    # =====================================================

    "Bucaneiro": {
        "emoji": "⚒️",
        "descricao": (
            "Bucaneiros são uma raça rara, conhecida por seu enorme porte "
            "físico e força muito acima da média. Sua história está envolta "
            "em mistérios."
        ),
        "perks": [
            perk(
                "💪",
                "Força Colossal",
                "Sua força aumenta em +25% passivamente."
            ),
            perk(
                "🛡️",
                "Corpo Resistente",
                "Sua resistência aumenta em +40% passivamente."
            ),
            perk(
                "🔥",
                "Sangue Guerreiro",
                "Cortam pela metade os requisitos necessários para "
                "aprimoramentos físicos."
            ),
            perk(
                "🩸",
                "Herança Misteriosa",
                "Sua linhagem está ligada a segredos importantes do mundo, "
                "podendo proporcionar vantagens narrativas relacionadas "
                "à sua origem."
            ),
        ]
    },

    # =====================================================
    # ONI
    # =====================================================

    "Oni": {
        "emoji": "👹",
        "descricao": (
            "Onis são uma raça rara de aparência humanoide, conhecida por "
            "seus chifres, enorme força física e resistência. Sua origem "
            "é cercada de mistérios."
        ),
        "perks": [
            perk(
                "👹",
                "Força Oni",
                "Sua força aumenta em +80% passivamente."
            ),
            perk(
                "🛡️",
                "Constituição Oni",
                "Sua resistência aumenta em +120% passivamente."
            ),
            perk(
                "🩸",
                "Instinto Selvagem",
                "Ataques aumentam +35% em força."
            ),
            perk(
                "⚔️",
                "Herança Demoníaca",
                "Naturalmente possuem 2 atributos acima do inicial, "
                "em todas as categorias."
            ),
        ]
    },

    # =====================================================
    # LONG-LEG
    # =====================================================

    "Long-Leg": {
        "emoji": "🦵",
        "descricao": (
            "Long-Legs são uma raça humanoide conhecida por suas pernas "
            "extremamente longas e musculosas. Sua estrutura corporal "
            "proporciona grande alcance e potência nos golpes."
        ),
        "perks": [
            perk(
                "🦵",
                "Pernas Longas",
                "Possuem pernas excepcionalmente longas, proporcionando "
                "maior alcance."
            ),
            perk(
                "💥",
                "Chutes Potentes",
                "Golpes com pernas possuem +20% em aumento de força."
            ),
            perk(
                "⚡",
                "Passos Largos",
                "Sua velocidade aumenta em +20% passivamente."
            ),
            perk(
                "🥋",
                "Especialista em Chutes",
                "Diminuem pela metade o requisito para aprender estilos "
                "focados em técnicas com as pernas."
            ),
        ]
    },

    # =====================================================
    # LONG-ARM
    # =====================================================

    "Long-Arm": {
        "emoji": "💪",
        "descricao": (
            "Long-Arms são uma raça humanoide caracterizada por braços "
            "extremamente longos e uma segunda articulação nos membros."
        ),
        "perks": [
            perk(
                "💪",
                "Braços Alongados",
                "Aumentam significativamente o alcance de seus golpes."
            ),
            perk(
                "🥊",
                "Punhos de Impacto",
                "Ataques com braços possuem +15% de aumento em força."
            ),
            perk(
                "📏",
                "Alcance Superior",
                "Conseguem atacar adversários mantendo uma distância maior."
            ),
            perk(
                "⚔️",
                "Combate Adaptado",
                "Possuem facilidade para desenvolver estilos que utilizem "
                "seus braços e aproveitem seu alcance natural."
            ),
        ]
    },

    # =====================================================
    # LONG-NECK
    # =====================================================

    "Long-Neck": {
        "emoji": "🦒",
        "descricao": (
            "Long-Necks são uma raça humanoide caracterizada por seus "
            "pescoços excepcionalmente longos. Essa estrutura proporciona "
            "maior alcance e visão privilegiada."
        ),
        "perks": [
            perk(
                "🦒",
                "Pescoço Alongado",
                "Aumenta seu alcance em ataques e interações."
            ),
            perk(
                "👁️",
                "Visão Elevada",
                "Sua altura proporciona campo de visão superior."
            ),
            perk(
                "⚖️",
                "Equilíbrio Natural",
                "Possuem controle corporal adaptado à sua estrutura."
            ),
            perk(
                "🥋",
                "Alcance Incomum",
                "Podem desenvolver técnicas de combate que utilizem o "
                "pescoço e a distância a seu favor."
            ),
        ]
    },

    # =====================================================
    # CORPO MODIFICADO
    # =====================================================

    "Corpo Modificado": {
        "emoji": "🧬",
        "descricao": (
            "Corpos Modificados são indivíduos cujo corpo foi alterado "
            "geneticamente através de experimentos científicos avançados. "
            "Sua fisiologia ultrapassa os limites humanos comuns."
        ),
        "perks": [
            perk(
                "🦾",
                "Exoesqueleto",
                "Sua resistência aumenta em +150% naturalmente."
            ),
            perk(
                "💪",
                "Força Aprimorada",
                "Sua força aumenta em +60% naturalmente."
            ),
            perk(
                "⚡",
                "Sistema Nervoso",
                "Possuem reflexos e velocidade de reação aprimorados, "
                "facilitando esquivas e respostas durante o combate."
            ),
            perk(
                "🧬",
                "Modificação Genética",
                "Podem manifestar características especiais de sua linhagem "
                "modificada, como alterações corporais e habilidades físicas "
                "extraordinárias."
            ),
        ]
    },
}


# =========================================================
# FUNÇÕES DO CATÁLOGO
# =========================================================

def listar_racas():
    return list(RACAS.keys())


def buscar_raca(nome):
    return RACAS.get(nome)


def existe_raca(nome):
    return nome in RACAS


def obter_perks(nome):
    raca = buscar_raca(nome)

    if not raca:
        return []

    return raca["perks"]


def quantidade_racas():
    return len(RACAS)
