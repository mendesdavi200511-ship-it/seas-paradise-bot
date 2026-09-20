# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE FAMÍLIAS
# =========================================================


def perk(nome, descricao):
    return {
        "nome": nome,
        "descricao": descricao
    }


FAMILIAS = {

    "Monkey": {
        "personagem": "Monkey D. Luffy",
        "raridade": "Lendária",
        "descricao": (
            "Uma linhagem conhecida por enorme determinação e força de vontade, "
            "com membros ligados à Marinha e à pirataria."
        ),
        "perks": [
            perk("🔥 Vontade Herdada",
                 "Grande determinação para superar limites em situações extremas."),
            perk("💪 Sangue Monstruoso",
                 "Reduz pela metade os caracteres necessários para subir atributos físicos."),
            perk("⚔️ Espírito Livre",
                 "Obtém automaticamente a qualidade de rei indicada pelo sistema."),
            perk("👑 Vontade do D.",
                 "Obtém automaticamente a Vontade do D."),
        ]
    },

    "Nefertari": {
        "personagem": "Nefertari Vivi",
        "raridade": "Rara",
        "descricao": (
            "Linhagem real fundadora do Governo Mundial que permaneceu em "
            "Alabasta, preservando sua soberania."
        ),
        "perks": [
            perk("👑 Sangue Real",
                 "Prestígio e reconhecimento dentro de Alabasta."),
            perk("🏜️ Herança de Alabasta",
                 "Conhecimento da cultura, território e história de Alabasta."),
            perk("📜 Legado Antigo",
                 "Linhagem com mais de 800 anos ligada à fundação do Governo Mundial."),
            perk("🕊️ Vontade de Nefertari",
                 "Forte determinação para proteger seu povo e seus ideais."),
        ]
    },

    "Kozuki": {
        "personagem": "Kozuki Oden",
        "raridade": "Lendária",
        "descricao": (
            "Antiga linhagem de Wano ligada à liderança, à história do país "
            "e à criação dos Poneglyphs."
        ),
        "perks": [
            perk("⚒️ Mestre dos Poneglyphs",
                 "Adquire automaticamente a profissão de Arqueólogo e conhecimento ancestral dos Poneglyphs."),
            perk("👑 Sangue de Wano",
                 "Prestígio e reconhecimento entre habitantes de Wano."),
            perk("⚔️ Herança Samurai",
                 "Facilidade com espada e começa com o estilo de luta herdado de Wano."),
            perk("📜 Legado Ancestral",
                 "Conhecimentos transmitidos por gerações ligados à história perdida."),
        ]
    },

    "Shimotsuki": {
        "personagem": "Shimotsuki Ryuma",
        "raridade": "Lendária",
        "descricao": (
            "Antiga linhagem de Wano conhecida por lendários espadachins "
            "e tradição de lâminas."
        ),
        "perks": [
            perk("⚔️ Sangue Samurai",
                 "Requisitos de skills de espadachim reduzidos pela metade."),
            perk("🗡️ Forja de Lâminas",
                 "Obtém automaticamente conhecimento/profissão ligada à forja."),
            perk("🎯 Disciplina do Dojo",
                 "Limite de treinos de skills +1."),
            perk("🔥 Espírito Shimotsuki",
                 "Grande determinação em combate."),
        ]
    },

    "Vinsmoke": {
        "personagem": "Vinsmoke Sanji",
        "raridade": "Rara",
        "descricao": (
            "Poderosa linhagem do North Blue, líder de Germa, associada à "
            "ciência, engenharia genética e poder militar."
        ),
        "perks": [
            perk("🧬 Engenharia Genética",
                 "Acesso à tecnologia genética da família."),
            perk("🦾 Corpo Aprimorado",
                 "Adquire automaticamente a raça Corpo Modificado."),
            perk("⚙️ Tecnologia Germa",
                 "Acesso e conhecimento de tecnologia militar avançada."),
            perk("⚔️ Linhagem de Combate",
                 "Treinamento precoce para combate e estratégia militar."),
        ]
    },

    "Donquixote": {
        "personagem": "Donquixote Doflamingo",
        "raridade": "Rara",
        "descricao": (
            "Linhagem descendente dos Vinte Reis, marcada por nobreza, "
            "poder e influência em Dressrosa."
        ),
        "perks": [
            perk("👑 Sangue Celestial",
                 "Origem ligada aos antigos Dragões Celestiais."),
            perk("💰 Herança Nobre",
                 "Acesso a recursos e contatos; pode gastar em nome do Governo enquanto não for criminoso."),
            perk("⚔️ Tradição de Combate",
                 "Histórico de indivíduos habilidosos favorece desenvolvimento marcial."),
            perk("🕸️ Legado Donquixote",
                 "Conexões e consequências narrativas ligadas à antiga família."),
        ]
    },

    "Figarland": {
        "personagem": "Figarland Garling",
        "raridade": "Mítica",
        "descricao": (
            "Antiga linhagem associada aos Dragões Celestiais e ao alto "
            "escalão do poder mundial, ligada a God Valley."
        ),
        "perks": [
            perk("👑 Sangue Celestial",
                 "Grande prestígio dentro da nobreza mundial."),
            perk("⚔️ Linhagem Guerreira",
                 "Conhecimento dos três tipos de Haki."),
            perk("🏛️ Influência Mundial",
                 "Facilidade para contatos entre autoridades e elite."),
            perk("🔥 Legado de God Valley",
                 "Conexões narrativas com os mistérios de God Valley."),
        ]
    },

    "Charlotte": {
        "personagem": "Charlotte Linlin",
        "raridade": "Lendária",
        "descricao": (
            "Enorme linhagem pirata ligada à Big Mom e centrada em Whole Cake."
        ),
        "perks": [
            perk("👨‍👩‍👧 Família Numerosa",
                 "Grande rede de parentes e alianças centradas em Whole Cake."),
            perk("💪 Sangue da Big Mom",
                 "Pode iniciar um nível de atributo acima em todas as categorias."),
            perk("🍬 Talento Natural",
                 "Pode obter obrigatoriamente uma Akuma no Mi Paramecia, rolando até sair a tipagem."),
            perk("🏴‍☠️ Herança Pirata",
                 "Facilidade de relações com piratas e submundo."),
        ]
    },

    "Rocks": {
        "personagem": "Rocks D. Xebec",
        "raridade": "Mítica",
        "descricao": (
            "Linhagem cercada por mistérios e associada a Rocks D. Xebec."
        ),
        "perks": [
            perk("☠️ Legado de Xebec",
                 "Obtém automaticamente a Vontade do D."),
            perk("🔥 Ambição Desmedida",
                 "Qualidades de rei e conhecimento dos três tipos de Haki."),
            perk("⚔️ Sangue de Monstros",
                 "Treinos físicos pela metade e talento/prodígio herdado."),
            perk("🌑 Herança Proibida",
                 "Conexões com segredos da história perdida."),
        ]
    },

    "Gol": {
        "personagem": "Gol D. Roger",
        "raridade": "Mítica",
        "descricao": (
            "Linhagem marcada por grandes feitos e pela determinação "
            "do Rei dos Piratas."
        ),
        "perks": [
            perk("🔥 Vontade do D.",
                 "Obtém automaticamente a Vontade do D."),
            perk("👑 Espírito do Rei",
                 "Qualidade de rei, treinos relacionados pela metade e conhecimento dos três Hakis."),
            perk("⚔️ Legado do Rei",
                 "Tradição de enfrentar os maiores nomes do mundo."),
            perk("🌊 Herdeiro da Liberdade",
                 "Forte inclinação a buscar liberdade e seguir seus ideais."),
        ]
    },

    "Neptune": {
        "personagem": "Neptune",
        "raridade": "Rara",
        "descricao": (
            "Linhagem real do Reino Ryugu, profundamente ligada ao povo do mar."
        ),
        "perks": [
            perk("👑 Sangue Real",
                 "Autoridade e prestígio na Ilha dos Homens-Peixe."),
            perk("🌊 Herdeiro do Mar",
                 "Familiaridade com ambiente marítimo e cultura local."),
            perk("🏰 Nobreza Ryugu",
                 "Acesso a recursos, informações e contatos do reino."),
            perk("🤝 Protetor do Povo",
                 "Maior influência em negociações entre povos."),
        ]
    },

    "Rosward": {
        "personagem": "Saint Rosward",
        "raridade": "Rara",
        "descricao": (
            "Linhagem de Dragões Celestiais pertencente à nobreza mundial."
        ),
        "perks": [
            perk("👑 Sangue Celestial",
                 "Status e privilégios de Dragão Celestial."),
            perk("🏛️ Nobreza Mundial",
                 "Acesso à elite do Governo Mundial."),
            perk("💰 Riqueza Abundante",
                 "Pode ser custeado pelo Governo."),
            perk("🛡️ Proteção Mundial",
                 "Proteção especial das forças subordinadas ao Governo."),
        ]
    },

    "Saint": {
        "personagem": "Dragões Celestiais",
        "raridade": "Rara",
        "descricao": (
            "Uma das linhagens dos Dragões Celestiais descendentes dos Vinte Reis."
        ),
        "perks": [
            perk("👑 Sangue Celestial",
                 "Privilégios exclusivos perante o Governo."),
            perk("🏛️ Nobreza Mundial",
                 "Influência em Mary Geoise."),
            perk("💰 Riqueza Ancestral",
                 "Pode ser custeado totalmente pelo Governo."),
            perk("🛡️ Autoridade Celestial",
                 "Pode exigir proteção e assistência das forças subordinadas."),
        ]
    },

    "Manmayer": {
        "personagem": "Saint Manmayer",
        "raridade": "Rara",
        "descricao": (
            "Linhagem dos Dragões Celestiais com grande prestígio e privilégios."
        ),
        "perks": [
            perk("👑 Sangue Celestial",
                 "Privilégios exclusivos perante o Governo."),
            perk("🏛️ Nobreza Mundial",
                 "Acesso à elite de Mary Geoise."),
            perk("💰 Riqueza Ancestral",
                 "Pode ser custeado totalmente pelo Governo."),
            perk("🛡️ Proteção Celestial",
                 "Proteção especial das forças subordinadas."),
        ]
    },

    "Riku": {
        "personagem": "Riku Doldo III",
        "raridade": "Rara",
        "descricao": (
            "Antiga linhagem real de Dressrosa, ligada à proteção "
            "e ao bem-estar do povo."
        ),
        "perks": [
            perk("👑 Sangue Real",
                 "Prestígio e autoridade em Dressrosa."),
            perk("🕊️ Rei do Povo",
                 "Facilidade para conquistar confiança e apoio."),
            perk("⚔️ Tradição Guerreira",
                 "Aprendizado de técnicas físicas pela metade."),
            perk("❤️ Vontade de Proteger",
                 "Grande determinação ao proteger aliados, família ou povo."),
        ]
    },

    "Nerona": {
        "personagem": "Imu",
        "raridade": "Mítica",
        "descricao": (
            "Linhagem extremamente misteriosa ligada à fundação "
            "do Governo Mundial e a Imu."
        ),
        "perks": [
            perk("👑 Sangue dos Fundadores",
                 "Acesso excepcional ao Governo, suas áreas e embarcações; autoridade ampla conforme as regras do RP."),
            perk("🌑 Legado Oculto",
                 "Conhecimento sobre técnicas, armas ancestrais, Akuma no Mi e Haki."),
            perk("🏛️ Autoridade Absoluta",
                 "Conexões com os níveis mais altos do poder mundial."),
            perk("👁️ Herança de Imu",
                 "Conexão excepcional com os maiores mistérios do mundo."),
        ]
    },

    "Kaido": {
        "personagem": "Kaido",
        "raridade": "Lendária",
        "descricao": (
            "Linhagem marcada por constituição física extraordinária "
            "e domínio do combate."
        ),
        "perks": [
            perk("💪 Sangue Monstruoso",
                 "Treinos envolvendo físico pela metade."),
            perk("🛡️ Constituição Anormal",
                 "Balas e lâminas convencionais não cortam; exige 2 níveis de Força acima, salvo uso de Haki do Armamento."),
            perk("⚔️ Instinto de Combate",
                 "Pode evoluir 2x o domínio de estilos de luta."),
            perk("🔥 Vontade Indomável",
                 "Grande determinação em situações extremas."),
        ]
    },

    "Crocodile": {
        "personagem": "Crocodile",
        "raridade": "Rara",
        "descricao": (
            "Linhagem associada ao submundo e à pirataria, "
            "marcada por ambição e estratégia."
        ),
        "perks": [
            perk("🐊 Instinto Predador",
                 "A cada duas ações do oponente, pode prever a terceira conforme a regra do RP."),
            perk("💰 Influência no Submundo",
                 "Facilidade para contatos clandestinos."),
            perk("♟️ Mente Estratégica",
                 "Maior capacidade de manipular NPCs sem transmitir maldade automaticamente."),
            perk("🏜️ Sobrevivente",
                 "Derrotas ou capturas não apagam seu nome nem seu respeito automaticamente."),
        ]
    },

    "Enel": {
        "personagem": "Enel",
        "raridade": "Rara",
        "descricao": (
            "Linhagem associada a Birka e às tradições das ilhas do céu."
        ),
        "perks": [
            perk("⚡ Herança de Birka",
                 "Possui automaticamente a raça Birkan."),
            perk("☁️ Sangue Celestial",
                 "Facilidade de adaptação às ilhas do céu."),
            perk("👁️ Mantra",
                 "Conhecimento inicial do Haki da Observação."),
            perk("👑 Complexo Divino",
                 "Grande confiança e crença de ser uma divindade."),
        ]
    },

    "Sengoku": {
        "personagem": "Sengoku",
        "raridade": "Lendária",
        "descricao": (
            "Linhagem associada à Marinha, disciplina, estratégia "
            "e dedicação à justiça."
        ),
        "perks": [
            perk("⚓ Tradição Naval",
                 "Como marinheiro, recebe 2x mais Honra de qualquer fonte."),
            perk("🧠 Mente Estratégica",
                 "Obtém automaticamente o talento/prodígio indicado pelo sistema."),
            perk("⚔️ Treinamento Militar",
                 "Treinos físicos pela metade enquanto treina na estrutura naval indicada."),
            perk("🛡️ Vontade da Justiça",
                 "Determinação para proteger aliados e cumprir objetivos."),
        ]
    },

    "Sakazuki": {
        "personagem": "Sakazuki",
        "raridade": "Lendária",
        "descricao": (
            "Linhagem da Marinha marcada por disciplina, autoridade "
            "e Justiça Absoluta."
        ),
        "perks": [
            perk("⚓ Disciplina Naval",
                 "Facilidade com hierarquia e treinamento militar."),
            perk("🔥 Justiça Absoluta",
                 "Grande determinação para cumprir objetivos."),
            perk("💪 Força de Vontade",
                 "Resistência mental diante de pressão e dor."),
            perk("🌋 Temperamento Intenso",
                 "Favorece estilos agressivos e ofensivos."),
        ]
    },

    "Borsalino": {
        "personagem": "Borsalino (Kizaru)",
        "raridade": "Lendária",
        "descricao": (
            "Linhagem da Marinha marcada por postura tranquila, "
            "experiência e eficiência em alto risco."
        ),
        "perks": [
            perk("⚓ Experiência Naval",
                 "Facilidade com operações e hierarquia da Marinha."),
            perk("🧠 Calma Absoluta",
                 "Mantém concentração sob pressão."),
            perk("⚡ Reflexos Apurados",
                 "Potencial para velocidade e reação."),
            perk("☀️ Luz Intocável",
                 "Ataques que usam velocidade recebem +30%."),
        ]
    },

    "Smoker": {
        "personagem": "Smoker",
        "raridade": "Rara",
        "descricao": (
            "Linhagem associada à Marinha, determinação e perseguição "
            "implacável de criminosos."
        ),
        "perks": [
            perk("⚓ Tradição Naval",
                 "Facilidade com treinamentos e operações militares."),
            perk("🔥 Justiça Inflexível",
                 "Determinação para perseguir objetivos."),
            perk("🥊 Combate de Campo",
                 "Adquire automaticamente a classe indicada pelo sistema."),
            perk("🚬 Espírito Independente",
                 "Facilidade para agir por conta própria seguindo seus princípios."),
        ]
    },
}


# =========================================================
# FUNÇÕES DO CATÁLOGO
# =========================================================

def listar_familias():
    return list(FAMILIAS.keys())


def buscar_familia(nome):
    return FAMILIAS.get(nome)


def existe_familia(nome):
    return nome in FAMILIAS


def obter_perks(nome):
    familia = buscar_familia(nome)

    if not familia:
        return []

    return familia["perks"]


def obter_raridade(nome):
    familia = buscar_familia(nome)

    if not familia:
        return None

    return familia["raridade"]


def familias_por_raridade(raridade):
    return [
        nome
        for nome, dados in FAMILIAS.items()
        if dados["raridade"] == raridade
    ]


def quantidade_familias():
    return len(FAMILIAS)
