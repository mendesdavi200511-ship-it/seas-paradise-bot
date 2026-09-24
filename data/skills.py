# =========================================================
# SEA'S PARADISE
# CATÁLOGO OFICIAL DE ESTILOS DE LUTA
# =========================================================


def estilo(emoji, categoria, descricao, skills=None):
    return {
        "emoji": emoji,
        "categoria": categoria,
        "descricao": descricao,
        "skills": skills or []
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
        "Estilo de combate especializado exclusivamente no uso das pernas.",
        [{"pct": 25, "nome": "Fundamentos do Black Leg", "descricao": "Base técnica de chutes e movimentação do estilo."},
         {"pct": 50, "nome": "Diable Jambe", "descricao": "Evolução do Black Leg que utiliza calor intenso nas pernas."},
         {"pct": 100, "nome": "Ifrit Jambe", "descricao": "Evolução máxima cadastrada do Black Leg, combinando enorme calor e velocidade."}]
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


    "Free Style": estilo(
        "🥊", "Lutador",
        "Estilo livre, sem escola formal fixa, moldado pelo próprio personagem.",
        [{"pct": 25, "nome": "Fundamentos Livres", "descricao": "Consolida a base pessoal do combatente."},
         {"pct": 50, "nome": "Adaptação", "descricao": "Aprimora a identidade e adaptação do estilo próprio."},
         {"pct": 75, "nome": "Assinatura Pessoal", "descricao": "Permite consolidar uma técnica autoral coerente com o estilo."},
         {"pct": 100, "nome": "Estilo Próprio", "descricao": "Domínio completo da escola de combate criada pelo personagem."}],
    ),

    "Tontatta Fight": estilo(
        "🧚", "Lutador",
        "Estilo racial dos Tontatta que explora tamanho, força e agilidade incomuns."
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

# Progressões específicas: cada estilo mostra o que ele realmente desenvolve, sem texto genérico.
_SKILLS_ESPECIFICAS = {
"Ittoryu":[("Corte de Uma Lâmina","Postura, saque e cortes precisos com uma espada."),("Corte à Distância","Projeta a força do corte para alcançar alvos além da lâmina."),("Corte de Alta Potência","Concentra força e técnica em golpes capazes de atravessar defesas superiores."),("Maestria Ittoryu","Controle completo de uma única espada, alcance, precisão e potência.")],
"Nitoryu":[("Dupla Lâmina","Coordena duas espadas simultaneamente em ataque e defesa."),("Cortes Cruzados","Combina trajetórias das duas lâminas para pressionar múltiplos ângulos."),("Fluxo Ofensivo Duplo","Mantém sequências rápidas sem perder guarda."),("Maestria Nitoryu","Domínio completo do combate com duas espadas.")],
"Santoryu":[("Três Lâminas","Coordena duas mãos e a terceira espada na boca."),("Oni Giri","Investida de três cortes convergentes."),("Tatsu Maki","Cortes giratórios capazes de gerar forte pressão ao redor."),("Maestria Santoryu","Domínio pleno das três lâminas e técnicas combinadas.")],
"Oden Nitoryu":[("Postura Oden Nitoryu","Base de duas espadas voltada a golpes extremamente pesados."),("Corte Duplo","Executa ataques simultâneos com ambas as lâminas."),("Togen Shirataki","Corte duplo de enorme potência."),("Togen Totsuka","Técnica máxima cadastrada do Oden Nitoryu.")],
"Foxfire Style":[("Corte Flamejante","Executa cortes associados ao fogo."),("Cortar Chamas","Permite cortar e dispersar fogo com a espada."),("Defesa Contra Fogo","Usa a técnica para interceptar ataques flamejantes."),("Maestria Foxfire","Integra corte, fogo e defesa contra chamas em alto nível.")],
"Kappa Style":[("Esgrima Kappa","Base técnica de espada do estilo de Kawamatsu."),("Sumô com Espada","Combina estabilidade corporal e cortes pesados."),("Cortes de Pressão","Amplia alcance e impacto dos golpes."),("Maestria Kappa","Domínio completo da esgrima e força corporal do estilo.")],
"Hanauta Style":[("Passo Musical","Movimentação leve e ritmada para preparar o saque."),("Corte de Passagem","Golpe executado ao ultrapassar o alvo em alta velocidade."),("Saque Fantasma","Aumenta drasticamente a velocidade do corte e dificulta sua leitura."),("Maestria Hanauta","Esgrima de velocidade extrema com execução quase imperceptível.")],
"Fish-Man Karate":[("Golpes Aquáticos","Transmite impacto usando a água presente no ambiente e nos corpos."),("Uchimizu","Arremessa gotas d’água como projéteis de alta força."),("Karakusagawara Seiken","Propaga um impacto poderoso através da umidade do ambiente."),("Maestria do Karatê Tritão","Controle avançado de golpes físicos e ondas de impacto aquáticas.")],
"Fish-Man Jujutsu":[("Manipulação de Água","Agarra e conduz massas de água como extensão do corpo."),("Correntes Aquáticas","Redireciona água para atacar ou controlar movimento."),("Arremesso Oceânico","Usa grandes volumes de água como força de projeção."),("Maestria Jujutsu Tritão","Controle avançado da água disponível para combate e contenção.")],
"Hasshoken":[("Vibração Corporal","Transmite vibrações destrutivas através dos golpes."),("Impacto Vibratório","Atravessa parcialmente defesas físicas com vibração."),("Onda de Choque","Espalha a vibração para uma área maior."),("Maestria Hasshoken","Controle refinado da vibração ofensiva e defensiva.")],
"Ryusoken":[("Garras do Dragão","Fortalece dedos e pegada para esmagar e perfurar."),("Dragon Claw","Golpe de garra concentrado contra pontos resistentes."),("Dragon Breath","Impacto destrutivo transmitido ao alvo/estrutura."),("Maestria Ryusoken","Domínio de esmagamento, perfuração e impacto do estilo.")],
"Okama Kenpo":[("Passos Okama","Movimentação acrobática e imprevisível."),("Chutes Acrobáticos","Combina giros, saltos e chutes em sequência."),("Esquiva Flexível","Usa mobilidade corporal para evitar e reposicionar."),("Maestria Okama Kenpo","Domínio completo da acrobacia ofensiva do estilo.")],
"Newkama Kenpo":[("Newkama Step","Movimentação e aceleração superiores do Newkama."),("Death Wink","Rajada de pressão gerada pelo piscar."),("Hell Wink","Versão muito mais poderosa da rajada de pressão."),("Maestria Newkama","Domínio das técnicas corporais e rajadas de pressão do estilo.")],
"Jao Kun Do":[("Combate de Pernas","Base marcial focada em chutes rápidos e alcance."),("Sequência de Chutes","Encadeia ataques sem perder mobilidade."),("Chute de Impacto","Concentra força em golpes de grande potência."),("Maestria Jao Kun Do","Domínio completo do combate marcial de pernas.")],
"Electro":[("Eletricidade Mink","Canaliza a eletricidade natural do corpo Mink."),("Electro em Golpes","Reveste ataques físicos com descarga elétrica."),("Electro em Armas","Conduz eletricidade por armas/objetos compatíveis."),("Maestria Electro","Controle avançado da descarga elétrica racial.")],
"Tontatta Fight":[("Força Tontatta","Explora a força física desproporcional da raça."),("Mobilidade Minúscula","Usa tamanho e agilidade para atacar pontos difíceis."),("Investida Tontatta","Combina velocidade e força em ataques explosivos."),("Maestria Tontatta","Domínio completo das vantagens físicas raciais em combate.")],
"Sniper Fighting":[("Mira de Longa Distância","Engaja alvos com precisão em grande alcance."),("Leitura de Trajetória","Compensa movimento, distância e queda do projétil."),("Tiro de Precisão","Ataca pontos específicos sob pressão."),("Maestria Sniper","Controle avançado de alcance, trajetória e precisão.")],
"Gun Fighting":[("Manuseio de Armas","Saque, recarga e disparo eficiente."),("Tiro em Movimento","Mantém precisão enquanto se reposiciona."),("Rajada Controlada","Encadeia disparos mantendo controle do alvo."),("Maestria Gun Fighting","Domínio completo de armas de fogo no combate.")],
"Archery":[("Tiro com Arco","Controle de postura, força e trajetória da flecha."),("Tiro Rápido","Dispara em sequência com menor tempo de preparação."),("Tiro de Longo Alcance","Aumenta alcance e precisão em grandes distâncias."),("Maestria do Arco","Domínio completo de cadência, alcance e precisão.")],
"Kabuto Fighting":[("Kabuto","Opera o estilingue Kabuto com munições especiais."),("Disparo de Longo Alcance","Explora a estrutura do Kabuto para tiros distantes."),("Munição Especializada","Alterna munições conforme terreno e alvo."),("Maestria Kabuto","Domínio completo do Kabuto e suas aplicações.")],
"Pop Green Fighting":[("Pop Green","Utiliza sementes Pop Green como munição."),("Plantas de Combate","Invoca plantas ofensivas/defensivas adequadas à semente."),("Controle de Terreno","Usa plantas para restringir rotas e criar oportunidades."),("Maestria Pop Green","Escolhe e combina Pop Greens com eficiência máxima.")],
"Rokushiki":[("Soru/Geppo","Acesso às técnicas de movimentação do Rokushiki."),("Tekkai/Kami-e","Acesso às técnicas corporais defensivas e evasivas."),("Shigan/Rankyaku","Acesso às técnicas ofensivas perfurantes e cortantes."),("Rokuogan","Técnica avançada que libera impacto destrutivo concentrado.")],
"Six Powers":[("Soru e Geppo","Movimentação explosiva e passos no ar."),("Tekkai e Kami-e","Endurecimento corporal e evasão flexível."),("Shigan e Rankyaku","Perfuração com os dedos e lâminas de ar com chutes."),("Rokuogan","Domínio avançado das seis técnicas e golpe de impacto.")],
"Cipher Pol Martial Arts":[("Combate de Agente","Técnicas corporais de infiltração e neutralização."),("Mobilidade Cipher Pol","Movimentação explosiva para aproximação/evasão."),("Neutralização Letal","Golpes precisos voltados a incapacitar rapidamente."),("Agente de Elite","Integra técnicas marciais e operações de combate da Cipher Pol.")],
"Cyborg Combat":[("Armas Incorporadas","Usa mecanismos e armas instaladas no próprio corpo."),("Propulsão Mecânica","Amplia mobilidade usando sistemas mecânicos."),("Arsenal Integrado","Combina múltiplos dispositivos em combate."),("Overdrive Ciborgue","Extrai desempenho máximo das modificações instaladas.")],
"Pacifista Combat":[("Corpo Pacifista","Usa resistência e força do corpo modificado."),("Laser","Dispara energia pelos sistemas Pacifista quando instalados."),("Mira de Combate","Rastreia e prioriza alvos com sistemas incorporados."),("Arsenal Pacifista","Domínio completo das capacidades tecnológicas disponíveis.")],
}
for _nome,_lista in _SKILLS_ESPECIFICAS.items():
    if _nome in ESTILOS:
        ESTILOS[_nome]["skills"]=[{"pct":pct,"nome":n,"descricao":d} for pct,(n,d) in zip((25,50,75,100),_lista)]
