# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE PROFISSÕES
# =========================================================


def estagio(pct, emoji, nome, descricao):
    return {
        "porcentagem": pct,
        "emoji": emoji,
        "nome": nome,
        "descricao": descricao
    }


PROFISSOES = {

    "Arqueólogo": {
        "emoji": "📜",
        "descricao": (
            "Especialistas em ruínas, artefatos, inscrições e civilizações "
            "antigas. Seu maior diferencial é compreender registros históricos "
            "e decifrar Poneglyphs."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🔎", "Análise Histórica",
                "Identifica ruínas, artefatos e inscrições antigas. "
                "Reconhece a estrutura de um Poneglyph, mas não decifra "
                "seu conteúdo."
            ),
            estagio(
                80, "📖", "Decifração Antiga",
                "Interpreta inscrições históricas comuns e compreende "
                "parcialmente mensagens simples em Poneglyphs."
            ),
            estagio(
                120, "🗿", "Leitura dos Poneglyphs",
                "Decifra completamente Poneglyphs históricos comuns."
            ),
            estagio(
                160, "📜", "Conhecimento dos Registros Antigos",
                "Lê Poneglyphs Históricos e Road Poneglyphs; identifica "
                "locais, nomes e acontecimentos."
            ),
            estagio(
                200, "🔴", "Domínio da Escrita Antiga",
                "Lê e interpreta completamente qualquer Poneglyph conhecido, "
                "incluindo Road Poneglyphs."
            ),
        ]
    },

    "Navegador": {
        "emoji": "🧭",
        "descricao": (
            "Responsáveis por traçar rotas, interpretar mapas, administrar "
            "recursos de viagem e conduzir embarcações."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🗺️", "Navegação Básica",
                "Registra mentalmente rotas percorridas e reduz em 10% "
                "o consumo de recursos de viagem."
            ),
            estagio(
                80, "📍", "Mapeamento Mental",
                "Memoriza permanentemente locais, rotas e pontos visitados; "
                "custo de navegação -20%."
            ),
            estagio(
                120, "💰", "Rota Econômica",
                "Viagens planejadas recebem -30% no consumo de suprimentos."
            ),
            estagio(
                160, "🌊", "Leitura da Grand Line",
                "Identifica rotas alternativas e atalhos; duração -20% e "
                "registra novas rotas sem instrumentos convencionais."
            ),
            estagio(
                200, "🧭", "Navegador Excepcional",
                "Custos de navegação -50%, encontra rotas alternativas e "
                "tempo de condução -50%."
            ),
        ]
    },

    "Carpinteiro": {
        "emoji": "🔨",
        "descricao": (
            "Responsáveis pela construção, manutenção e aprimoramento "
            "das embarcações."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🪵", "Reparos Básicos",
                "Repara casco, mastros e estruturas; reparos comuns usam "
                "-20% de materiais."
            ),
            estagio(
                80, "⚙️", "Reparo Rápido",
                "Reduz em 30% o tempo de reparos moderados."
            ),
            estagio(
                120, "🔧", "Manutenção Perfeita",
                "Reduz em 40% o desgaste natural da embarcação e melhora reparos."
            ),
            estagio(
                160, "🚢", "Engenharia Naval",
                "Modifica resistência, velocidade ou carga usando "
                "-30% de materiais."
            ),
            estagio(
                200, "⚒️", "Mestre Carpinteiro",
                "Reconstrói partes severamente danificadas e reparos "
                "emergenciais recuperam até 50% da integridade perdida."
            ),
        ]
    },

    "Médico": {
        "emoji": "⚕️",
        "descricao": (
            "Especialistas em tratamentos, cirurgias, medicamentos "
            "e recuperação de ferimentos."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🩹", "Primeiros Socorros",
                "Trata ferimentos leves e estabiliza aliados; "
                "recuperações básicas +20% eficiência."
            ),
            estagio(
                80, "💊", "Farmacologia",
                "Produz medicamentos simples e antídotos; tratamentos "
                "reduzem 30% do tempo de recuperação."
            ),
            estagio(
                120, "🩺", "Cirurgia de Campo",
                "Trata ferimentos graves sem hospital; cirurgias +40% eficiência."
            ),
            estagio(
                160, "🧪", "Medicina Avançada",
                "Cria tratamentos para doenças, venenos e condições complexas; "
                "medicamentos +50% eficiência."
            ),
            estagio(
                200, "❤️‍🩹", "Médico Excepcional",
                "Procedimentos complexos e estabilização à beira da morte; "
                "tratamentos recuperam até 70% da condição física perdida."
            ),
        ]
    },

    "Cozinheiro": {
        "emoji": "🍳",
        "descricao": (
            "Responsáveis por preparar refeições capazes de recuperar, "
            "fortalecer e manter uma tripulação."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🥩", "Refeições Energéticas",
                "+10% em Força, Resistência ou Velocidade/Agilidade por "
                "2 turnos. ฿5.000 + 1 suplemento; 1 refeição."
            ),
            estagio(
                80, "🍲", "Culinária Revigorante",
                "Recupera 15% da condição física e +15% em um atributo por "
                "3 turnos. ฿10.000 + 2 suplementos; 2 refeições."
            ),
            estagio(
                120, "🌶️", "Pratos Especiais",
                "+25% em um atributo ou Foco, Adrenalina ou Recuperação por "
                "3 turnos. ฿20.000 + 3 suplementos; 2 refeições."
            ),
            estagio(
                160, "🍖", "Culinária de Combate",
                "+35% em um atributo e um estado adicional por 4 turnos. "
                "฿40.000 + 4 suplementos; 3 refeições."
            ),
            estagio(
                200, "👨‍🍳", "Mestre Cozinheiro",
                "Até +50% em um atributo, recupera 30% da condição e aplica "
                "estado especial por 5 turnos. ฿75.000 + 5 suplementos; "
                "3 refeições."
            ),
        ]
    },

    "Cientista": {
        "emoji": "🧪",
        "descricao": (
            "Especialistas em ciência, tecnologia, genética, química "
            "e engenharia."
        ),
        "requisitos": "Sorteio.",
        "maximo": 400,
        "estagios": [
            estagio(
                50, "🔬", "Pesquisa Básica",
                "Analisa materiais, substâncias e organismos; produz "
                "medicamentos simples, reagentes e pequenos equipamentos."
            ),
            estagio(
                100, "⚙️", "Engenharia Experimental",
                "Cria máquinas, armas tecnológicas simples e aprimora "
                "equipamentos; projetos comuns usam -20% de materiais."
            ),
            estagio(
                150, "🧬", "Biotecnologia",
                "Estuda genética, realiza modificações biológicas básicas "
                "e produz aprimoramentos corporais simples."
            ),
            estagio(
                200, "💉", "Modificação Genética",
                "Altera características físicas e cria seres geneticamente "
                "modificados de baixa complexidade."
            ),
            estagio(
                250, "🧪", "Frutas do Diabo Artificiais",
                "Cria versões artificiais de Akuma no Mi com efeitos "
                "limitados e requisitos específicos."
            ),
            estagio(
                300, "🤖", "Tecnologia Cibernética",
                "Cria armas, próteses, robôs e modificações corporais avançadas."
            ),
            estagio(
                350, "🧬", "Clonagem Avançada",
                "Cria clones e organismos modificados, reproduzindo "
                "características físicas de linhagens."
            ),
            estagio(
                400, "☀️", "Tecnologia de Linhagem",
                "Usa fatores genéticos de raças especiais e desenvolve "
                "protótipos semelhantes aos Seraphins, com altos custos e tempo."
            ),
        ]
    },

    "Mercador": {
        "emoji": "💰",
        "descricao": (
            "Especialistas em comércio, negociação e circulação de mercadorias."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🪙", "Negociação Básica",
                "Compra por até -10% e vende por até +10% do valor comum."
            ),
            estagio(
                80, "📦", "Avaliação Comercial",
                "Identifica valor aproximado e evita golpes; compras "
                "e vendas +15% eficiência."
            ),
            estagio(
                120, "💰", "Comércio Regional",
                "Encontra compradores e fornecedores; até +20% de lucro "
                "em negociações bem-sucedidas."
            ),
            estagio(
                160, "🚢", "Rotas Comerciais",
                "Estabelece relações entre ilhas; transporte de mercadorias -30%."
            ),
            estagio(
                200, "👑", "Grande Mercador",
                "Negocia produtos raros e contratos de alto valor; "
                "até +40% de lucro."
            ),
        ]
    },

    "Ferreiro": {
        "emoji": "⚒️",
        "descricao": (
            "Especialistas na criação, reparo e aprimoramento de armas e lâminas."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🔨", "Forja Básica",
                "Armas comuns e reparos. ฿10.000 por arma; sem rank."
            ),
            estagio(
                80, "⚙️", "Forja Especializada",
                "Cria Wazamono. ฿50.000 + 5 metais refinados."
            ),
            estagio(
                120, "🔥", "Metalurgia Avançada",
                "Cria/repara Ryō Wazamono. ฿150.000 + 10 materiais raros."
            ),
            estagio(
                160, "⚔️", "Forja Superior",
                "Cria Ō Wazamono. ฿500.000 + 20 materiais raros "
                "e forja especializada."
            ),
            estagio(
                200, "👑", "Mestre Ferreiro",
                "Cria Saijō Ō Wazamono. ฿2.000.000 + 50 materiais lendários, "
                "forja de alto nível e projeto aprovado pela staff."
            ),
        ]
    },

    "Pescador": {
        "emoji": "🎣",
        "descricao": (
            "Especialistas na vida marítima, captura de criaturas "
            "e sobrevivência no oceano."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🐟", "Pesca Básica",
                "Captura peixes comuns; ฿2.000 em equipamentos/iscas "
                "e até 5 unidades de alimento."
            ),
            estagio(
                80, "🪝", "Pesca de Profundidade",
                "Captura espécies maiores em águas profundas; "
                "até 10 unidades de alimento."
            ),
            estagio(
                120, "🌊", "Caça de Sea Beasts",
                "Localiza e captura Sea Beasts menores; "
                "฿15.000 por expedição."
            ),
            estagio(
                160, "🐋", "Caça de Grandes Sea Beasts",
                "Participa da captura de criaturas gigantes e extrai "
                "materiais; ฿50.000 por expedição."
            ),
            estagio(
                200, "🫧", "Conhecimento do Revestimento",
                "Participa de revestimento de Kairoseki/materiais adequados "
                "e conduz expedições em águas extremamente profundas."
            ),
        ]
    },

    "Caçador": {
        "emoji": "🏹",
        "descricao": (
            "Especialistas em rastreamento, captura e sobrevivência."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "👣", "Rastreamento",
                "Identifica pegadas, marcas, odores e vestígios; localiza "
                "animais e alvos em área definida pelo narrador."
            ),
            estagio(
                80, "🎯", "Mira de Caçador",
                "Aumenta precisão com armas de longo alcance, atinge pontos "
                "específicos e usa armadilhas simples."
            ),
            estagio(
                120, "🪤", "Armadilhas Avançadas",
                "Prepara mecanismos de imobilização/retardo; "
                "฿10.000 em materiais por expedição."
            ),
            estagio(
                160, "🐾", "Caça de Criaturas",
                "Rastreia e enfrenta animais/monstros grandes, identifica "
                "vulnerabilidades e extrai materiais."
            ),
            estagio(
                200, "☠️", "Mestre Caçador",
                "Rastreia por grandes distâncias e caça Reis dos Mares/"
                "criaturas gigantes com equipamento e condições adequadas."
            ),
        ]
    },

    "Músico": {
        "emoji": "🎵",
        "descricao": (
            "Utilizam ritmo, melodia e presença para influenciar "
            "aliados e adversários."
        ),
        "requisitos": "Escolha inicial, sorteio ou eventos/lore.",
        "maximo": 200,
        "estagios": [
            estagio(
                40, "🎶", "Melodia Motivadora",
                "+10% de Resistência ou Velocidade/Agilidade aos aliados "
                "por 2 turnos."
            ),
            estagio(
                80, "🎸", "Ritmo de Batalha",
                "+15% em um atributo por 3 turnos e reduz medo/intimidação."
            ),
            estagio(
                120, "🎼", "Harmonia Revigorante",
                "Remove estados negativos leves como medo, desorientação "
                "e hesitação."
            ),
            estagio(
                160, "🔥", "Concerto de Guerra",
                "+25% em Força, Resistência ou Velocidade/Agilidade e "
                "maior resistência mental por 4 turnos."
            ),
            estagio(
                200, "🎤", "Mestre Músico",
                "+35% em um atributo, resistência a medo/efeitos mentais "
                "e sem penalidade de moral por 5 turnos."
            ),
        ]
    },
}


# =========================================================
# FUNÇÕES DO CATÁLOGO
# =========================================================

def listar_profissoes():
    return list(PROFISSOES.keys())


def buscar_profissao(nome):
    return PROFISSOES.get(nome)


def existe_profissao(nome):
    return nome in PROFISSOES


def obter_estagios(nome):
    profissao = buscar_profissao(nome)

    if not profissao:
        return []

    return profissao["estagios"]


def obter_estagio_atual(nome, porcentagem):
    """
    Retorna o estágio mais alto já desbloqueado pelo jogador.
    """

    profissao = buscar_profissao(nome)

    if not profissao:
        return None

    atual = None

    for nivel in profissao["estagios"]:
        if porcentagem >= nivel["porcentagem"]:
            atual = nivel
        else:
            break

    return atual


def obter_proximo_estagio(nome, porcentagem):
    """
    Retorna o próximo estágio que ainda não foi desbloqueado.
    """

    profissao = buscar_profissao(nome)

    if not profissao:
        return None

    for nivel in profissao["estagios"]:
        if porcentagem < nivel["porcentagem"]:
            return nivel

    return None


def porcentagem_maxima(nome):
    profissao = buscar_profissao(nome)

    if not profissao:
        return 0

    return profissao["maximo"]


def quantidade_profissoes():
    return len(PROFISSOES)
