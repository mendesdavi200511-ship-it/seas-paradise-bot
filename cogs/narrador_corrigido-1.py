import os
import asyncio
import discord
from discord.ext import commands
from openai import AsyncOpenAI

from database.database import (
    buscar_ficha,
    buscar_especializacoes,
    buscar_npc,
    buscar_memorias_npc,
    listar_npcs_mundo,
    registrar_npc,
    registrar_memoria_npc,
    recrutar_npc,
    buscar_localizacao_jogador,
    definir_localizacao_jogador,
    definir_acesso_npc,
    definir_atributos_npc,
    resetar_ficha_por_morte,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODELO_NARRADOR = "gpt-5.6-luna"
LIMITE_HISTORICO = 12
historicos = {}
locks = {}

# Catálogo-base do mundo. Não cria cópias: apenas dá posição/regras aos NPCs únicos.
NPCS_MUNDO_BASE = {
    "makino": ("Vila Foosha", "Bar da Makino", "livre", True, "Civil"),
    "woop slap": ("Vila Foosha", "Vila", "livre", True, "Civil"),
    "higuma": ("Vila Foosha", "Arredores", "normal", True, "Bandido"),
    "alvida": ("East Blue", "Navio de Alvida", "normal", False, "Pirata"),
    "koby": ("East Blue", "Marinha", "restrito", False, "Marinha"),
    "helmeppo": ("East Blue", "Marinha", "restrito", False, "Marinha"),
    "morgan": ("Shells Town", "Base da Marinha", "difícil", False, "Marinha"),
    "roronoa zoro": ("Shells Town", "Praça da Base", "normal", False, "Independente"),
    "buggy": ("Orange Town", "Base dos Piratas Buggy", "difícil", False, "Pirata"),
    "cabaji": ("Orange Town", "Base dos Piratas Buggy", "restrito", False, "Pirata"),
    "mohji": ("Orange Town", "Base dos Piratas Buggy", "restrito", False, "Pirata"),
    "richie": ("Orange Town", "Base dos Piratas Buggy", "restrito", False, "Pirata"),
    "kuro": ("Vila Syrup", "Mansão Kaya", "difícil", False, "Pirata"),
    "kaya": ("Vila Syrup", "Mansão Kaya", "restrito", False, "Civil"),
    "usopp": ("Vila Syrup", "Vila", "livre", True, "Civil"),
    "zeff": ("Baratie", "Restaurante Baratie", "livre", True, "Civil"),
    "sanji": ("Baratie", "Restaurante Baratie", "livre", True, "Civil"),
    "don krieg": ("Baratie", "Arredores marítimos", "difícil", False, "Pirata"),
    "gin": ("Baratie", "Arredores", "normal", False, "Pirata"),
    "dracule mihawk": ("Grand Line", "Em viagem", "extremo", False, "Pirata"),
    "arlong": ("Ilhas Conomi", "Arlong Park", "difícil", False, "Pirata"),
    "hatchan": ("Ilhas Conomi", "Arlong Park", "restrito", False, "Pirata"),
    "kuroobi": ("Ilhas Conomi", "Arlong Park", "restrito", False, "Pirata"),
    "chew": ("Ilhas Conomi", "Arlong Park", "restrito", False, "Pirata"),
    "smoker": ("Loguetown", "Base da Marinha", "difícil", False, "Marinha"),
    "tashigi": ("Loguetown", "Base da Marinha", "restrito", False, "Marinha"),
    "monkey d. dragon": ("Desconhecida", "Desconhecida", "extremo", False, "Revolucionário"),
    "kizaru": ("Marineford", "Área de Alto Comando", "extremo", False, "Marinha"),
    "akainu": ("Marineford", "Área de Alto Comando", "extremo", False, "Marinha"),
    "aokiji": ("Marineford", "Em missão / Alto Comando", "extremo", False, "Marinha"),
    "sengoku": ("Marineford", "Alto Comando", "extremo", False, "Marinha"),
    "garp": ("Marineford", "Marinha", "difícil", False, "Marinha"),
    "trafalgar law": ("Sabaody Park", "Arquipélago de Sabaody", "difícil", False, "Pirata"),
}

ALIASES_NPC = {
    "zoro": "roronoa zoro",
    "mihawk": "dracule mihawk",
    "dragon": "monkey d. dragon",
    "borsalino": "kizaru",
    "sakazuki": "akainu",
    "kuzan": "aokiji",
    "law": "trafalgar law",
}

# O nome do canal do Discord é a fonte de localização da cena quando !acao é usado.
# Canais administrativos/comuns são ignorados para não virarem lugares do mundo.
CANAIS_NAO_LOCALIZACAO = {
    "geral", "general", "chat", "bate-papo", "comandos", "commands",
    "fichas", "ficha", "regras", "rules", "off-topic", "offtopic",
    "anuncios", "anúncios", "logs", "log", "staff", "admin", "tickets"
}

ALIASES_LOCALIZACAO_CANAL = {
    "marineford": "Marineford",
    "sabaody": "Sabaody Park",
    "sabaody-park": "Sabaody Park",
    "sabaody-park-rp": "Sabaody Park",
    "loguetown": "Loguetown",
    "orange-town": "Orange Town",
    "shells-town": "Shells Town",
    "vila-foosha": "Vila Foosha",
    "foosha": "Vila Foosha",
    "vila-syrup": "Vila Syrup",
    "baratie": "Baratie",
    "ilhas-conomi": "Ilhas Conomi",
    "arlong-park": "Ilhas Conomi",
}

PROMPT_NARRADOR = """
Você é o Narrador oficial do RPG Sea's Paradise, uma aventura pirata marítima shonen.
Sua função é narrar um MUNDO VIVO, contínuo e imparcial. Você não é um escudo dos NPCs nem um servo do jogador.

REGRAS ABSOLUTAS DO SISTEMA:
- Nunca altere atributos, porcentagens, Berries, reputação ou ficha.
- Nunca conceda itens, Akuma no Mi, Haki, técnicas, estilos ou poderes ausentes do contexto.
- Nunca invente números de dano, HP ou porcentagens.
- Nunca determine recompensas mecânicas.
- Não controle decisões, falas ou pensamentos do personagem do jogador.
- REGRA DE AGÊNCIA DO PLAYER: execute SOMENTE as ações físicas explicitamente declaradas na AÇÃO ATUAL. Nunca complete, prolongue ou deduza uma ação do player por parecer uma continuação natural.
- Se o jogador disser apenas que ergueu/apontou/sacou uma arma, ameaçou, olhou, falou, preparou postura ou demonstrou intenção, isso NÃO autoriza narrar que ele avançou, atacou, disparou, golpeou, esquivou, bloqueou ou se moveu depois.
- Fala de intenção não é execução. Frases como "irei matá-lo", "vou atacar", "prepare-se" ou equivalentes são ameaça/intenção até o jogador declarar a ação física correspondente.
- O Narrador pode descrever consequências imediatas da ação realmente declarada e pode controlar livremente as reações dos NPCs, mas jamais adicionar uma nova ação voluntária ao personagem do jogador.
- Preserve fatos narrados anteriormente e trate o ESTADO DO MUNDO como autoridade.
- NPCs únicos não podem existir em dois lugares nem em duas tripulações ao mesmo tempo.
- Mencionar, chamar ou procurar um NPC NÃO o materializa.
- Só faça um NPC agir fisicamente se ele estiver presente/acessível segundo o estado e a progressão da cena.
- NPC fora do local não é teleportado. NPC morto, recrutado ou indisponível mantém esse estado.
- O jogador não muda de ilha/local importante apenas declarando que chegou.
- Os únicos atributos físicos do sistema são Força, Resistência e Velocidade/Agilidade.
- Em combate, atributos registrados são fatos mecânicos e têm prioridade sobre fama, nome ou conveniência narrativa.
- Compare Força do atacante com Resistência do alvo e Velocidade/Agilidade entre os envolvidos.
- Diferença brutal de atributos deve produzir diferença brutal de resultado. Não crie plot armor.
- Um personagem muito inferior não pode ferir seriamente um alvo cuja Resistência torne o golpe fisicamente irrelevante, salvo poder/técnica explicitamente registrada que justifique isso.
- Um personagem muito mais lento não acompanha, intercepta ou esquiva repetidamente de alguém absurdamente mais veloz sem justificativa registrada.
- Player pode ser ferido, incapacitado, derrotado e morrer. NPC também. Ninguém possui imunidade narrativa.
- NPC hostil não deve poupar o jogador sem motivo coerente. Se a personalidade, objetivo e situação justificarem força letal, ele pode tentar matar de verdade.
- Não faça inimigos perigosos reduzirem artificialmente seus ataques para manter o player vivo. Um adversário muito superior pode encerrar o combate rapidamente quando obtém uma abertura real.
- Morte só deve ocorrer quando a situação for realmente letal e sustentada pelos fatos mecânicos/contexto; não mate arbitrariamente.
- Se, E SOMENTE SE, a narração desta resposta confirmar inequivocamente a morte do personagem do jogador, acrescente ao FINAL da resposta, em linha separada, exatamente: [MORTE_PLAYER]
- [MORTE_PLAYER] é um sinal interno. Nunca use esse marcador para derrota, desmaio, ferimento grave, risco de morte ou ataque potencialmente letal; somente para morte consumada nesta resposta.

MUNDO VIVO E INICIATIVA DOS NPCS:
- NPCs têm vontade própria. Eles podem atacar, contra-atacar, perseguir, fugir, cercar, chamar reforços, mentir, negociar, interromper, proteger alguém ou aproveitar uma abertura SEM esperar outra ação do jogador.
- Quando o jogador inicia hostilidade, os inimigos não ficam passivos. Se for coerente, a mesma resposta deve incluir reação e iniciativa dos NPCs.
- Não transforme combate em 'jogador ataca -> NPC desvia -> jogador ataca -> NPC desvia'. Esquiva perfeita repetida é proibida.
- Não proteja NPCs por serem personagens conhecidos. Um figurante não ganha reflexos absurdos apenas para impedir a ação do jogador.
- Também não favoreça o jogador: inimigos perigosos podem pressionar, ferir narrativamente, encurralar ou obrigar reação quando isso for coerente.
- A declaração do jogador é uma TENTATIVA somente quanto ao resultado daquilo que ele EXPLICITAMENTE executou. Resolva esse ato sem inventar um ato seguinte.
- Diferencie rigorosamente PREPARAÇÃO/INTENÇÃO de EXECUÇÃO: erguer a espada não é atacar; mirar não é disparar; ameaçar não é avançar; assumir postura não é golpear.
- Resultados narrativos possíveis incluem acerto, erro, defesa, acerto parcial, interrupção, vantagem, desvantagem ou mudança concreta da situação. Varie conforme contexto, capacidade aparente, surpresa, posição e histórico.
- Sem resolvedor mecânico, não invente valores nem aplique alterações de ficha. Porém isso NÃO impede consequências narrativas concretas como um tiro atingir um figurante, alguém cair, sangrar, ser desarmado, fugir, contra-atacar ou o cenário ser destruído.
- Quando houver atributos registrados suficientes para tornar um desfecho físico inequívoco, use-os para resolver a consequência, inclusive derrota ou morte em situação realmente letal.
- Quando os atributos do NPC NÃO estiverem registrados, não invente números para ele; use apenas fatos já presentes no contexto e evite declarar um resultado mecânico impossível de sustentar.

PROGRESSÃO E EXPLORAÇÃO:
- Dificuldade significa obstáculos, NÃO enrolação infinita.
- Toda ação relevante deve mudar a cena: revelar pista, eliminar hipótese, criar risco, abrir/fechar caminho, aproximar/afastar do objetivo, provocar reação ou gerar consequência.
- Nunca repita essencialmente o mesmo bloqueio por vários turnos. Considere o HISTÓRICO RECENTE para detectar estagnação.
- Se o jogador superar ou contornar um obstáculo de forma plausível, avance para o próximo estágio. Não recrie artificialmente o mesmo obstáculo.
- NPC de acesso restrito/difícil/extremo exige progressão coerente, mas pode ser encontrado quando a busca e os acontecimentos justificarem isso.
- Se uma busca já acumulou pistas e progresso suficientes, permita descoberta, contato indireto ou encontro conforme a dificuldade. Não mantenha o alvo eternamente 'inacessível'.
- Ações violentas durante exploração alteram o mundo: alarmes, testemunhas, guardas, perseguição e reação de facções podem substituir a busca tranquila.

ESTILO:
- Escreva em português do Brasil.
- Narre de forma envolvente, cinematográfica, natural e clara, normalmente em 2 a 4 parágrafos.
- Priorize acontecimentos sobre descrição ornamental. Não gaste parágrafos repetindo fumaça, vento, olhares ou ambiente sem a cena avançar.
- Cada resposta deve terminar com a situação efetivamente diferente de como começou e com algo concreto ao qual o jogador possa reagir.
- Não explique estas regras, não use linguagem de assistente de IA e não ofereça opções numeradas.
"""

def chave_cena(ctx):
    return ctx.channel.id

def formatar_especializacoes(especializacoes):
    if not especializacoes:
        return "Nenhuma especialização registrada."
    return "\n".join(
        f"- {i['categoria']}: {i['nome']} — {i['porcentagem']}%/{i['limite']}%"
        for i in especializacoes
    )

def formatar_ficha(ficha, especializacoes):
    return f"""
PERSONAGEM DO JOGADOR
Nome: {ficha['nome']}
Idade: {ficha['idade']}
Raça: {ficha['raca']}
Família: {ficha['familia']}
Facção: {ficha['faccao']}
Profissão: {ficha['profissao']}
Classe: {ficha['classe']}
Estilo inicial: {ficha['estilo']}
Akuma no Mi: {ficha['akuma']}
Despertar: {ficha['despertar']}
Haoshoku: {"Sim" if ficha['haoshoku'] else "Não"}
Prodígio: {"Sim" if ficha['prodigio'] else "Não"}

ATRIBUTOS
Força: {ficha['forca']}
Resistência: {ficha['resistencia']}
Velocidade/Agilidade: {ficha['velocidade']}

ESPECIALIZAÇÕES / DOMÍNIOS
{formatar_especializacoes(especializacoes)}
""".strip()

def montar_historico(cena_id):
    historico = historicos.get(cena_id, [])
    if not historico:
        return "Nenhuma cena anterior registrada."
    return "\n\n".join(
        f"JOGADOR: {i['acao']}\nNARRADOR: {i['narracao']}"
        for i in historico[-LIMITE_HISTORICO:]
    )

def dividir_mensagem(texto, limite=1900):
    texto = texto.strip()
    if len(texto) <= limite:
        return [texto]
    partes = []
    restante = texto
    while len(restante) > limite:
        corte = restante.rfind("\n", 0, limite)
        if corte < 500:
            corte = restante.rfind(" ", 0, limite)
        if corte < 500:
            corte = limite
        partes.append(restante[:corte].strip())
        restante = restante[corte:].strip()
    if restante:
        partes.append(restante)
    return partes

class Narrador(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY não foi configurada no ambiente.")
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    def localizacao_do_canal(self, ctx):
        nome = getattr(ctx.channel, "name", None)
        if not nome:
            return None

        chave = nome.casefold().strip().replace("_", "-")
        if chave in CANAIS_NAO_LOCALIZACAO:
            return None

        if chave in ALIASES_LOCALIZACAO_CANAL:
            return ALIASES_LOCALIZACAO_CANAL[chave]

        # Fallback para canais de RP com nomes como "little-garden".
        # O nome é convertido para apresentação, mas continua vindo do próprio canal.
        return " ".join(parte.capitalize() for parte in chave.split("-") if parte)

    async def sincronizar_localizacao_com_canal(self, ctx):
        local = self.localizacao_do_canal(ctx)
        if not local:
            return None

        atual = await buscar_localizacao_jogador(ctx.author.id)
        if not atual or atual["localizacao"] != local:
            await definir_localizacao_jogador(ctx.author.id, local)
            print(f"🧭 {ctx.author.id} entrou em cena em {local} pelo canal #{ctx.channel.name}.")
        return local

    async def sincronizar_catalogo_npcs(self):
        for nome, (local, area, acesso, aleatorio, faccao) in NPCS_MUNDO_BASE.items():
            # aliases não devem virar cópias se o nome principal já existir; só registra o nome citado quando necessário.
            npc = await buscar_npc(nome)
            if npc:
                await definir_acesso_npc(nome, local, area, acesso, aleatorio, faccao)

    def nome_canonico(self, nome):
        chave = nome.casefold().strip()
        return ALIASES_NPC.get(chave, chave)

    def dados_catalogo(self, nome):
        return NPCS_MUNDO_BASE.get(self.nome_canonico(nome))

    async def garantir_npc_catalogado(self, nome):
        canonico = self.nome_canonico(nome)
        dados = NPCS_MUNDO_BASE.get(canonico)
        if not dados:
            return await buscar_npc(nome)
        local, area, acesso, aleatorio, faccao = dados
        return await definir_acesso_npc(canonico, local, area, acesso, aleatorio, faccao)

    async def npcs_catalogados_na_acao(self, acao):
        texto = acao.casefold()
        encontrados = []
        vistos = set()
        # nomes maiores primeiro evita capturar aliases curtos antes do nome completo
        nomes_busca = list(NPCS_MUNDO_BASE.keys()) + list(ALIASES_NPC.keys())
        for nome in sorted(nomes_busca, key=len, reverse=True):
            if nome in texto:
                npc = await self.garantir_npc_catalogado(nome)
                if npc and npc['id'] not in vistos:
                    vistos.add(npc['id'])
                    encontrados.append(npc)
        return encontrados[:8]

    async def contexto_mundo(self, acao, user_id=None):
        npcs = await listar_npcs_mundo()
        texto = acao.casefold()
        citados = [npc for npc in npcs if npc["nome"].casefold() in texto]
        catalogados = await self.npcs_catalogados_na_acao(acao)
        por_id = {npc['id']: npc for npc in citados}
        por_id.update({npc['id']: npc for npc in catalogados})
        citados = list(por_id.values())

        local_player = await buscar_localizacao_jogador(user_id) if user_id else None
        local_nome = local_player['localizacao'] if local_player else None
        area_player = local_player['area'] if local_player else None

        # Migração suave: se ainda não existe localização do jogador, mas ele já possui
        # memória persistente com um único NPC citado e esse NPC tem local conhecido,
        # a cena existente pode estabelecer o ponto inicial sem teleportar ninguém.
        if user_id and not local_nome and len(citados) == 1:
            mems = await buscar_memorias_npc(citados[0]['nome'], 12)
            if any(m['user_id'] == user_id for m in mems) and citados[0]['localizacao']:
                await definir_localizacao_jogador(user_id, citados[0]['localizacao'])
                local_nome = citados[0]['localizacao']

        partes = [
            "LOCALIZAÇÃO DO JOGADOR: " + (local_nome or "desconhecida/não estabelecida"),
            "ÁREA DO JOGADOR: " + (area_player or "não estabelecida"),
            "REGRA: localização declarada pelo jogador não substitui o estado persistente."
        ]
        for npc in citados[:8]:
            memorias = await buscar_memorias_npc(npc["nome"], 10)
            dono = npc["recrutado_por"]
            linhas = [
                f"NPC: {npc['nome']}",
                f"Status: {npc['status']}",
                f"Localização: {npc['localizacao'] or 'desconhecida'}",
                f"Área: {npc['area'] or 'desconhecida'}",
                f"Facção: {npc['faccao'] or 'não definida'}",
                f"Nível de acesso: {npc['nivel_acesso'] or 'normal'}",
                f"Encontrável aleatoriamente: {'sim' if npc['encontravel_aleatoriamente'] else 'não'}",
                f"Disponível: {'sim' if npc['disponivel'] else 'não'}",
                f"Mesmo local do jogador: {'sim' if local_nome and npc['localizacao'] and local_nome.casefold() == npc['localizacao'].casefold() else 'não'}",
                f"Recrutado por user_id: {dono if dono is not None else 'ninguém'}",
                f"Força: {npc['forca'] if npc['forca'] is not None else 'não configurada'}",
                f"Resistência: {npc['resistencia'] if npc['resistencia'] is not None else 'não configurada'}",
                f"Velocidade/Agilidade: {npc['velocidade'] if npc['velocidade'] is not None else 'não configurada'}",
            ]
            if memorias:
                linhas.append("Memórias relevantes:")
                linhas.extend(f"- {m['resumo']}" for m in memorias)
            partes.append("\n".join(linhas))
        if len(partes) == 3:
            partes.append("NPCS CITADOS: nenhum NPC persistente/catalogado reconhecido.")
        return "\n\n".join(partes)

    async def detectar_npcs_automaticamente(self, acao, narracao, ficha):
        entrada = f"""
PERSONAGEM DO JOGADOR:
{ficha['nome']}

AÇÃO DO JOGADOR:
{acao}

NARRAÇÃO GERADA:
{narracao}

Identifique SOMENTE NPCs que a NARRAÇÃO confirmou como fisicamente presentes na cena.
Não inclua NPC citado apenas como nome, rumor, lembrança, destino, busca ou tentativa de encontro.

REGRAS:
- Não inclua o personagem do jogador.
- Não inclua lugares, ilhas, organizações, objetos ou ataques.
- Não invente personagens.
- Preserve o nome do personagem.
- Se não houver NPC, responda exatamente: NENHUM
- Se houver NPCs, escreva apenas os nomes.
- Um NPC por linha.
- Não coloque marcadores, números ou explicações.
""".strip()

        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=(
                "Você é um extrator de entidades de um RPG de One Piece. "
                "Sua única função é identificar NPCs que a narração confirmou como fisicamente presentes. "
                "Mera menção, procura, lembrança ou tentativa de encontro NÃO conta. Não invente nomes."
            ),
            input=entrada,
            max_output_tokens=120,
        )

        resultado = resposta.output_text.strip()
        if not resultado or resultado.upper() == "NENHUM":
            return []

        nomes = []
        for linha in resultado.splitlines():
            nome = linha.strip().strip("-•*0123456789. ")
            if not nome:
                continue
            if nome.casefold() == ficha["nome"].casefold():
                continue
            if len(nome) > 80:
                continue
            if nome.casefold() not in [n.casefold() for n in nomes]:
                nomes.append(nome)

        npcs = []
        for nome in nomes[:8]:
            npc = await registrar_npc(nome)
            if npc:
                npcs.append(npc)
        return npcs

    async def npcs_citados(self, texto):
        npcs = await listar_npcs_mundo()
        texto_normalizado = texto.casefold()
        return [
            npc for npc in npcs
            if npc["nome"].casefold() in texto_normalizado
        ][:8]

    async def salvar_memorias_da_acao(self, acao, narracao, ficha, user_id):
        npcs_existentes = await self.npcs_citados(acao + "\n" + narracao)
        npcs_detectados = await self.detectar_npcs_automaticamente(
            acao, narracao, ficha
        )

        npcs_por_id = {}
        for npc in npcs_existentes:
            npcs_por_id[npc["id"]] = npc
        for npc in npcs_detectados:
            npcs_por_id[npc["id"]] = npc

        npcs = list(npcs_por_id.values())

        for npc in npcs:
            resumo = (
                f"{ficha['nome']} disse/fez: {acao}\n"
                f"Resultado narrado na cena: {narracao}"
            )
            await registrar_memoria_npc(
                npc["nome"],
                resumo,
                user_id=user_id,
                personagem_nome=ficha["nome"],
                importancia=5,
                permanente=True
            )

        return len(npcs)

    async def gerar_narracao(self, ctx, acao, ficha, especializacoes):
        mundo = await self.contexto_mundo(acao, ctx.author.id)
        entrada = f"""
{formatar_ficha(ficha, especializacoes)}

CANAL/LOCAL DA CENA NO DISCORD
{getattr(ctx.channel, "name", "desconhecido")}

ESTADO PERSISTENTE DO MUNDO
{mundo}

HISTÓRICO RECENTE DA CENA
{montar_historico(chave_cena(ctx))}

AÇÃO ATUAL DECLARADA PELO JOGADOR
{acao}

VALIDAÇÃO DE PRESENÇA E DESLOCAMENTO
A ação acima é uma TENTATIVA, não um fato consumado.
Se o jogador disser que chegou, encontrou, entrou, falou com ou está diante de alguém,
compare isso com o ESTADO PERSISTENTE DO MUNDO antes de aceitar.
NPC fora do local do jogador NÃO está na cena.
NPC de acesso restrito/difícil/extremo NÃO fica acessível só porque foi citado.
Não teleporte jogador nem NPC. Não crie cópia de NPC único.

Narre apenas a continuação desta cena.

DIREÇÃO DESTA RESPOSTA
- Primeiro identifique literalmente o último ato físico que o jogador declarou. Resolva somente esse ato. Não invente movimento, ataque, defesa, fala ou decisão posterior do player.
- Se a ação do jogador for apenas preparação, fala, ameaça ou postura, a consequência concreta deve vir do ambiente/NPCs; o personagem do jogador permanece exatamente no ponto em que sua declaração terminou.
- NPCs presentes possuem iniciativa própria e podem agir/contra-atacar nesta mesma resposta.
- Não use esquiva automática para preservar NPC. Não repita o mesmo bloqueio do turno anterior.
- Consulte o HISTÓRICO: se a cena estiver estagnada, faça-a avançar agora de maneira coerente.
- Use os atributos reais do jogador e os atributos registrados do NPC para resolver combate: Força do atacante contra Resistência do alvo; Velocidade contra Velocidade.
- Não transforme diferença enorme de poder em uma sequência infinita de esquivas. O lado superior deve conseguir impor pressão, contra-atacar e encerrar a troca quando isso for coerente.
- Não invente atributos ausentes. Se faltarem atributos do NPC, não fabrique números.
- Se os fatos mecânicos e a situação tornarem um golpe realmente letal, morte é uma consequência permitida tanto para player quanto para NPC; ninguém tem plot armor.
- NPC hostil pode iniciar força letal e tentar matar o player quando isso combina com sua intenção, personalidade e situação. Não o faça lutar eternamente de modo defensivo ou misericordioso sem razão.
- Se um NPC for esmagadoramente superior e tiver intenção letal, não prolongue artificialmente a luta: uma abertura pode resultar em ferimento crítico, incapacitação ou morte conforme os fatos da cena.
- Se a morte do PLAYER for efetivamente consumada nesta resposta, termine com [MORTE_PLAYER]. Não use o marcador para mera tentativa, ameaça, ferimento ou possibilidade.
- Recompensas e alterações numéricas de ficha continuam dependendo do sistema apropriado.
- Se o objetivo for encontrar NPC difícil, progresso acumulado deve aproximar o jogador dele; dificuldade não é invisibilidade infinita.
""".strip()

        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=PROMPT_NARRADOR,
            input=entrada,
            max_output_tokens=600,
        )
        narracao = resposta.output_text.strip()
        if not narracao:
            raise RuntimeError("A OpenAI retornou uma narração vazia.")

        morte_player = "[MORTE_PLAYER]" in narracao
        narracao = narracao.replace("[MORTE_PLAYER]", "").strip()
        return narracao, morte_player

    @commands.command(name="acao", aliases=["ação"])
    async def acao(self, ctx, *, texto: str):
        ficha = await buscar_ficha(ctx.author.id)
        if not ficha:
            await ctx.send("❌ Você ainda não possui uma ficha.")
            return
        texto = texto.strip()
        if len(texto) > 1500:
            await ctx.send("❌ Sua ação ficou muito grande. Use no máximo 1.500 caracteres.")
            return

        cena_id = chave_cena(ctx)
        locks.setdefault(cena_id, asyncio.Lock())
        if locks[cena_id].locked():
            await ctx.send("⏳ O narrador ainda está concluindo a ação anterior.")
            return

        async with locks[cena_id]:
            # A localização física da cena vem do canal/tópico onde !acao foi usado.
            # Isso acontece antes de montar o ESTADO DO MUNDO.
            await self.sincronizar_localizacao_com_canal(ctx)

            especializacoes = list(await buscar_especializacoes(ctx.author.id))
            try:
                async with ctx.typing():
                    narracao, morte_player = await self.gerar_narracao(
                        ctx, texto, ficha, especializacoes
                    )
            except Exception as erro:
                print(f"❌ ERRO NO NARRADOR — {type(erro).__name__}: {erro}")
                await ctx.send(
                    "⚠️ O Narrador não conseguiu gerar a cena agora. "
                    "Tente novamente em instantes."
                )
                return

            historicos.setdefault(cena_id, []).append(
                {"acao": texto, "narracao": narracao}
            )
            historicos[cena_id] = historicos[cena_id][-LIMITE_HISTORICO:]

            try:
                quantidade_memorias = await self.salvar_memorias_da_acao(
                    texto, narracao, ficha, ctx.author.id
                )
                if quantidade_memorias:
                    print(
                        f"🧠 {quantidade_memorias} memória(s) persistente(s) "
                        f"salva(s) para {ficha['nome']}."
                    )
            except Exception as erro_memoria:
                print(
                    f"❌ ERRO AO SALVAR MEMÓRIA PERSISTENTE — "
                    f"{type(erro_memoria).__name__}: {erro_memoria}"
                )

            # A morte é confirmada pelo narrador através de um marcador interno.
            # Só depois de salvar a cena/memórias o personagem é resetado.
            if morte_player:
                try:
                    await resetar_ficha_por_morte(ctx.author.id)
                    historicos.pop(cena_id, None)
                    print(f"💀 {ficha['nome']} morreu. Ficha de {ctx.author.id} resetada.")
                except Exception as erro_morte:
                    print(
                        f"❌ ERRO AO RESETAR FICHA APÓS MORTE — "
                        f"{type(erro_morte).__name__}: {erro_morte}"
                    )
                    await ctx.send(
                        "⚠️ A morte foi narrada, mas houve erro ao resetar a ficha. "
                        "Avise a administração antes de continuar."
                    )
                    return

            partes = dividir_mensagem(narracao)
            embed = discord.Embed(
                title="📖 NARRADOR — SEA'S PARADISE",
                description=partes[0],
                color=discord.Color.blue()
            )
            embed.set_footer(
                text=f"Ação de {ficha['nome']} • Narração automática"
            )
            await ctx.send(embed=embed)
            for parte in partes[1:]:
                await ctx.send(parte)

            if morte_player:
                await ctx.send(
                    f"💀 **{ficha['nome']} morreu.** A ficha foi resetada. "
                    "Você precisará criar um novo personagem para continuar."
                )

    @commands.command(name="ondeestou")
    async def ondeestou(self, ctx):
        local = await buscar_localizacao_jogador(ctx.author.id)
        if not local or not local['localizacao']:
            await ctx.send("🧭 Sua localização persistente ainda não foi estabelecida pelo mundo.")
            return
        area = f" • {local['area']}" if local['area'] else ""
        await ctx.send(f"🧭 **{local['localizacao']}**{area}")

    @commands.command(name="localplayer")
    @commands.has_permissions(administrator=True)
    async def localplayer(self, ctx, membro: discord.Member, *, localizacao: str):
        await definir_localizacao_jogador(membro.id, localizacao)
        await ctx.send(f"🧭 Localização persistente de **{membro.display_name}** definida como **{localizacao}**.")

    @commands.command(name="npclocal")
    @commands.has_permissions(administrator=True)
    async def npclocal(self, ctx, nome_npc: str, *, localizacao: str):
        npc = await self.garantir_npc_catalogado(nome_npc)
        if not npc:
            npc = await registrar_npc(nome_npc)
        from database.database import atualizar_estado_npc
        await atualizar_estado_npc(nome_npc, localizacao=localizacao)
        await ctx.send(f"🌍 **{nome_npc}** agora está persistentemente em **{localizacao}**.")

    @commands.command(name="npcatributos")
    @commands.has_permissions(administrator=True)
    async def npcatributos(self, ctx, nome_npc: str, forca: int, resistencia: int, velocidade: int):
        try:
            npc = await definir_atributos_npc(nome_npc, forca, resistencia, velocidade)
        except ValueError as erro:
            await ctx.send(f"❌ {erro}")
            return
        await ctx.send(
            f"⚔️ **{npc['nome']}** configurado — "
            f"Força **{npc['forca']}** | Resistência **{npc['resistencia']}** | "
            f"Velocidade **{npc['velocidade']}**."
        )

    @commands.command(name="cena")
    async def cena(self, ctx):
        quantidade = len(historicos.get(chave_cena(ctx), []))
        if quantidade == 0:
            await ctx.send("📖 Nenhuma cena automática está ativa neste tópico.")
            return
        await ctx.send(
            f"📖 Este tópico possui **{quantidade}** turno(s) recentes "
            "na memória do Narrador."
        )

    @commands.command(name="limparcena")
    @commands.has_permissions(administrator=True)
    async def limparcena(self, ctx):
        historicos.pop(chave_cena(ctx), None)
        await ctx.send("🧹 Memória narrativa deste tópico limpa.")

    @commands.command(name="npcregistrar")
    @commands.has_permissions(administrator=True)
    async def npcregistrar(self, ctx, *, nome: str):
        npc = await registrar_npc(nome)
        await ctx.send(f"🌍 NPC persistente registrado: **{npc['nome']}**.")

    @commands.command(name="npcmemoria")
    @commands.has_permissions(administrator=True)
    async def npcmemoria(self, ctx, nome_npc: str, *, resumo: str):
        await registrar_memoria_npc(nome_npc, resumo, permanente=True)
        await ctx.send(f"🧠 Memória permanente adicionada a **{nome_npc}**.")

    @commands.command(name="npcrecrutar")
    @commands.has_permissions(administrator=True)
    async def npcrecrutar(self, ctx, membro: discord.Member, *, nome_npc: str):
        ficha = await buscar_ficha(membro.id)
        if not ficha:
            await ctx.send("❌ Esse jogador não possui ficha.")
            return
        ok, motivo = await recrutar_npc(nome_npc, membro.id)
        if not ok:
            await ctx.send(f"❌ **{nome_npc}** não pode ser recrutado: `{motivo}`.")
            return
        await registrar_memoria_npc(
            nome_npc,
            f"{ficha['nome']} recrutou {nome_npc} para sua tripulação.",
            user_id=membro.id,
            personagem_nome=ficha['nome'],
            importancia=10,
            permanente=True
        )
        await ctx.send(
            f"🏴‍☠️ **{nome_npc}** agora pertence à tripulação de **{ficha['nome']}**."
        )

async def setup(bot):
    await bot.add_cog(Narrador(bot))
