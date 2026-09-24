import os
import asyncio
import json
import re
import discord
from discord.ext import commands
from openai import AsyncOpenAI

from cogs.npc_profiles import NPC_PROFILES, get_profile, profile_for_narrator, format_profile_for_narrator

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
    buscar_perfil_npc,
    salvar_perfil_npc,
    atualizar_estado_npc,
    registrar_evento_mundo,
    buscar_eventos_mundo,
    buscar_notoriedade_personagem,
    buscar_reputacao_mundo,
    aplicar_impacto_reputacao,
    registrar_noticia_mundo,
    buscar_noticias_mundo,
    atualizar_estado_jogador,
    definir_estado_jogador,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODELO_NARRADOR = "gpt-5.6-luna"
LIMITE_HISTORICO = 12
CANAL_CRIACAO_ID = 1551379201939218502
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


# Perfis mecânicos/canônicos ficam em npc_profiles.py para não transformar o Narrador em um catálogo gigante.

ALIASES_NPC = {
    "zoro": "roronoa zoro",
    "mihawk": "dracule mihawk",
    "dragon": "monkey d. dragon",
    "borsalino": "kizaru",
    "sakazuki": "akainu",
    "kuzan": "aokiji",
    "law": "trafalgar law",
    "bartholomeu": "bartholomew kuma",
    "bartolomeu": "bartholomew kuma",
    "kuma": "bartholomew kuma",
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
- Quando a cena CONSUMAR uma mudança real de localização do player (viagem concluída, transporte, prisão transferida etc.), acrescente ao final: [LOCAL_PLAYER:Localização|Área]. Não use por intenção de viajar.
- Quando o estado persistente do player mudar de fato, acrescente ao final: [ESTADO_PLAYER:estado|custodia|restricoes|combate]. Use vazio para nenhum; combate deve ser sim ou nao.
- Estados úteis: livre, preso, detido, inconsciente, incapacitado, navegando, em_combate. Esses marcadores são internos e nunca devem aparecer na prosa.

FIDELIDADE CANÔNICA DOS NPCS:
- Quando o sistema fornecer um PERFIL CANÔNICO, ele é contexto obrigatório do personagem e deve ser aplicado junto dos atributos e do estado persistente.
- Não transforme personagem canônico em NPC genérico. Use de forma natural Akuma no Mi, Haki, estilo de luta, armas, inteligência, mobilidade e recursos que o PERFIL CANÔNICO confirmar.
- Não invente poder futuro, técnica inexistente, veículo errado, comportamento incompatível ou fala artificial só para a cena funcionar.
- Nomes de armas/técnicas só devem ser falados pelo NPC quando isso for coerente com a obra; saber o nome de uma arma não significa que o personagem grite esse nome ao usá-la.
- Se faltarem números do NPC, o PERFIL CANÔNICO pode estabelecer uma diferença QUALITATIVA inequívoca de poder. Isso permite impedir resultados absurdos (por exemplo, um iniciante acertar repetidamente um Supernova) sem inventar pontos numéricos.
- Atributos numéricos cadastrados continuam tendo prioridade quando existirem.

MUNDO VIVO E INICIATIVA DOS NPCS:
- NPCs têm vontade própria. Eles podem atacar, contra-atacar, perseguir, fugir, cercar, chamar reforços, mentir, negociar, interromper, proteger alguém ou aproveitar uma abertura SEM esperar outra ação do jogador.
- FUGA NÃO É SUCESSO AUTOMÁTICO: se o jogador disser que correu, saltou, escapou, atravessou uma barreira ou foi atrás de alguém, trate isso como tentativa e compare posição, obstáculos e velocidade. Inimigos presentes podem perseguir, interceptar, cortar rota, usar poderes ou atacar durante a fuga.
- Hostilidade escala de forma natural. Depois de tentativas repetidas de homicídio, tiros na cabeça ou ataques letais, um NPC perigoso não deve agir como guarda de tutorial; salvo motivo de personalidade/objetivo em contrário, pode responder com força suficiente para incapacitar ou matar.
- Não crie obstáculos infinitos para salvar nenhum lado. Resolva a troca e mude concretamente o estado da cena.
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

    async def validar_localizacao_do_canal(self, ctx):
        """O canal indica onde a ação QUER ocorrer; não teleporta o personagem."""
        local_canal = self.localizacao_do_canal(ctx)
        if not local_canal:
            return True, None, None

        atual = await buscar_localizacao_jogador(ctx.author.id)

        # Primeira cena do personagem: o canal pode estabelecer o ponto inicial.
        if not atual or not atual["localizacao"]:
            await definir_localizacao_jogador(ctx.author.id, local_canal)
            atual = await buscar_localizacao_jogador(ctx.author.id)
            print(f"🧭 Local inicial de {ctx.author.id}: {local_canal}.")
            return True, local_canal, atual

        local_real = atual["localizacao"]
        if local_real.casefold() != local_canal.casefold():
            return False, local_canal, atual

        return True, local_canal, atual

    def entidade_coletiva_ou_nao_individual(self, nome):
        """Bloqueia grupos/facções/locais antes de qualquer criação de perfil individual."""
        chave = " ".join(str(nome).casefold().strip().split())
        if not chave:
            return True

        # Nomes conhecidos de organizações/grupos e padrões plurais comuns do universo.
        exatos = {
            "marinha", "governo mundial", "exército revolucionário", "exercito revolucionario",
            "cross guild", "cipher pol", "cp0", "cp9", "germa 66",
            "piratas heart", "heart pirates", "piratas do chapéu de palha",
            "piratas do chapeu de palha", "straw hat pirates",
        }
        if chave in exatos:
            return True

        prefixos = (
            "piratas ", "tripulação ", "tripulacao ", "marinheiros ",
            "soldados ", "guardas ", "revolucionários ", "revolucionarios ",
            "agentes ", "caçadores ", "cacadores ", "civis ",
        )
        sufixos = (
            " pirates", " crew", " marines", " tripulação", " tripulacao",
        )
        if chave.startswith(prefixos) or chave.endswith(sufixos):
            return True

        # Descrições coletivas que às vezes escapam do extrator.
        marcadores = (
            "tripulação de ", "tripulacao de ", "tripulação do ", "tripulacao do ",
            "membros dos piratas ", "membros da marinha", "grupo de piratas",
            "grupo de marinheiros",
        )
        return any(m in chave for m in marcadores)

    async def gerar_perfil_npc_automatico(self, nome, contexto=""):
        """Gera UMA VEZ o status mecânico de NPC desconhecido e persiste no PostgreSQL."""
        canonico = self.nome_canonico(nome)

        if self.entidade_coletiva_ou_nao_individual(canonico):
            return None

        # Catálogo manual continua sendo a autoridade para NPCs já calibrados.
        fixo = get_profile(canonico)
        if fixo:
            npc = await registrar_npc(fixo["nome"], faccao=fixo["faccao"])
            if npc["forca"] is None or npc["resistencia"] is None or npc["velocidade"] is None:
                await definir_atributos_npc(fixo["nome"], fixo["forca"], fixo["resistencia"], fixo["velocidade"])
            return fixo

        salvo = await buscar_perfil_npc(canonico)
        if salvo:
            return salvo

        entrada = f"""
NPC: {nome}
CONTEXTO/Fase do RP: {contexto or 'Use somente a fase coerente com o estado atual do Sea\'s Paradise.'}

Crie o perfil mecânico persistente deste NPC para um RP de One Piece.
Se for personagem CANÔNICO, use somente capacidades confirmadas e coerentes com a fase indicada.
NÃO dê poderes futuros, despertar futuro, Haki futuro, arma errada, veículo errado ou técnica inventada.
Se alguma capacidade canônica for desconhecida/não confirmada, escreva isso em vez de inventar.
Se for NPC ORIGINAL, crie um kit coerente com sua função e contexto.

ESCALA DO RP: 0 a 50.000 para Força, Resistência e Velocidade/Agilidade.
Calibre por hierarquia real de ameaça; não iguale iniciantes a oficiais, Supernovas, comandantes, almirantes ou lendas.
Referências internas de escala: civil comum dezenas; combatentes fracos centenas; East Blue relevante milhares; elite da Grand Line dezenas de milhares; topo mundial perto de 50.000.

Responda APENAS JSON válido, sem markdown, exatamente com estas chaves:
{{"nome":"", "titulo":"", "classificacao":"", "raca":"", "faccao":"", "forca":0, "resistencia":0, "velocidade":0, "akuma":"", "haki":"", "estilo":"", "arma":"", "publico":"", "combate":""}}
""".strip()
        obrigatorias = ("nome", "titulo", "classificacao", "raca", "faccao", "forca", "resistencia", "velocidade", "akuma", "haki", "estilo", "arma", "publico", "combate")
        perfil = None
        ultimo_erro = None

        # A saída de modelo pode ocasionalmente vir cercada de texto/markdown.
        # Tentamos até 3 vezes e aceitamos o primeiro objeto JSON completo e válido.
        for tentativa in range(3):
            try:
                resposta = await self.client.responses.create(
                    model=MODELO_NARRADOR,
                    instructions=(
                        "Você cria perfis mecânicos consistentes para Sea's Paradise. "
                        "Priorize cânone e cronologia. Nunca invente habilidade canônica não confirmada. "
                        "Sua resposta DEVE ser um único objeto JSON válido, começando com { e terminando com }. "
                        "Não use markdown, comentários nem texto antes/depois do JSON."
                    ),
                    input=entrada + (
                        "\n\nIMPORTANTE: esta é uma tentativa de correção. "
                        "Retorne SOMENTE o JSON completo solicitado."
                        if tentativa else ""
                    ),
                    max_output_tokens=900,
                )
                bruto = (resposta.output_text or "").strip()
                candidatos = [bruto]
                achado = re.search(r"\{.*\}", bruto, re.S)
                if achado and achado.group(0) != bruto:
                    candidatos.append(achado.group(0))

                for candidato in candidatos:
                    try:
                        p = json.loads(candidato)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if not isinstance(p, dict) or any(k not in p for k in obrigatorias):
                        continue
                    try:
                        for campo in ("forca", "resistencia", "velocidade"):
                            p[campo] = max(0, min(50000, int(p[campo])))
                    except (TypeError, ValueError):
                        continue
                    # Nunca salva resposta vazia/provisória.
                    if not str(p.get("nome") or "").strip():
                        continue
                    perfil = p
                    break
                if perfil:
                    break
                ultimo_erro = f"saída sem JSON completo: {bruto[:180]!r}"
            except Exception as erro:
                ultimo_erro = f"{type(erro).__name__}: {erro}"

        if not perfil:
            raise RuntimeError(
                f"Não foi possível validar o perfil de {nome} após 3 tentativas. "
                f"Último erro: {ultimo_erro}"
            )

        # Persiste primeiro; em corrida entre players, o primeiro perfil salvo vence.
        perfil = await salvar_perfil_npc(canonico, perfil)
        npc = await registrar_npc(perfil["nome"], faccao=perfil["faccao"])
        await definir_atributos_npc(npc["nome"], perfil["forca"], perfil["resistencia"], perfil["velocidade"])
        return perfil

    async def obter_perfil_npc(self, nome, contexto="", criar=True):
        if self.entidade_coletiva_ou_nao_individual(nome):
            return None
        fixo = get_profile(nome)
        if fixo:
            return fixo
        salvo = await buscar_perfil_npc(nome)
        if salvo:
            return salvo
        if not criar:
            return None
        return await self.gerar_perfil_npc_automatico(nome, contexto)

    async def sincronizar_catalogo_npcs(self):
        for nome, (local, area, acesso, aleatorio, faccao) in NPCS_MUNDO_BASE.items():
            # aliases não devem virar cópias se o nome principal já existir; só registra o nome citado quando necessário.
            npc = await buscar_npc(nome)
            if npc:
                await definir_acesso_npc(nome, local, area, acesso, aleatorio, faccao)
                perfil = get_profile(nome)
                if perfil:
                    await definir_atributos_npc(nome, perfil["forca"], perfil["resistencia"], perfil["velocidade"])

    def nome_canonico(self, nome):
        chave = nome.casefold().strip()
        return ALIASES_NPC.get(chave, chave)

    def dados_catalogo(self, nome):
        return NPCS_MUNDO_BASE.get(self.nome_canonico(nome))

    async def garantir_npc_catalogado(self, nome):
        canonico = self.nome_canonico(nome)
        dados = NPCS_MUNDO_BASE.get(canonico)
        if not dados:
            npc = await buscar_npc(canonico)
            if not npc:
                npc = await registrar_npc(nome)
            try:
                perfil = await self.obter_perfil_npc(npc["nome"], criar=True)
            except Exception as erro_perfil:
                print(
                    f"⚠️ Falha não fatal ao gerar perfil de {npc['nome']}: "
                    f"{type(erro_perfil).__name__}: {erro_perfil}"
                )
                perfil = None
            if perfil and (npc["forca"] is None or npc["resistencia"] is None or npc["velocidade"] is None):
                npc = await definir_atributos_npc(npc["nome"], perfil["forca"], perfil["resistencia"], perfil["velocidade"])
            return npc
        local, area, acesso, aleatorio, faccao = dados
        npc = await definir_acesso_npc(canonico, local, area, acesso, aleatorio, faccao)
        perfil = get_profile(canonico)
        if perfil and (npc["forca"] is None or npc["resistencia"] is None or npc["velocidade"] is None):
            npc = await definir_atributos_npc(canonico, perfil["forca"], perfil["resistencia"], perfil["velocidade"])
        return npc

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
            "ESTADO DO JOGADOR: " + ((local_player["estado"] if "estado" in local_player else None) or "livre"),
            "CUSTÓDIA: " + ((local_player["custodia"] if "custodia" in local_player else None) or "nenhuma"),
            "RESTRIÇÕES: " + ((local_player["restricoes"] if "restricoes" in local_player else None) or "nenhuma"),
            "COMBATE ATIVO: " + ("sim" if (local_player and "combate_ativo" in local_player and local_player["combate_ativo"]) else "não"),
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
        if not citados:
            partes.append("NPCS CITADOS: nenhum NPC persistente/catalogado reconhecido.")

        # O mundo lembra acontecimentos mesmo quando o personagem que os causou morreu.
        eventos = await buscar_eventos_mundo(local_nome, limite=20)
        if eventos:
            linhas_eventos = ["CONSEQUÊNCIAS PERSISTENTES RELEVANTES DO MUNDO:"]
            for ev in eventos:
                conhecimento = []
                if ev["marinha_sabe"]: conhecimento.append("Marinha")
                if ev["governo_sabe"]: conhecimento.append("Governo")
                if ev["piratas_sabem"]: conhecimento.append("Piratas")
                if ev["publico_sabe"]: conhecimento.append("Público")
                linhas_eventos.append(
                    f"- [{ev['alcance']} | gravidade {ev['gravidade']}/10] "
                    f"{ev['personagem_nome']}: {ev['resumo']} "
                    f"| conhecimento: {', '.join(conhecimento) if conhecimento else 'não difundido'}"
                )
            partes.append("\n".join(linhas_eventos))

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
            if self.entidade_coletiva_ou_nao_individual(nome):
                print(f"ℹ️ Entidade coletiva ignorada como NPC individual: {nome}")
                continue
            npc = await registrar_npc(nome)
            if npc:
                try:
                    await self.obter_perfil_npc(
                        npc["nome"],
                        contexto=f"NPC confirmado fisicamente na cena. Narração: {narracao[:1200]}",
                        criar=True
                    )
                    npc = await buscar_npc(npc["nome"])
                except Exception as erro_perfil:
                    print(f"⚠️ Não foi possível gerar perfil automático de {nome}: {erro_perfil}")
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

    async def contexto_canonico(self, ctx, acao):
        """Ativa perfis fixos e perfis automáticos persistentes relevantes à cena."""
        universo_original = acao + "\n" + montar_historico(chave_cena(ctx))
        universo = universo_original.casefold()
        encontrados = []
        vistos = set()

        nomes_busca = list(NPC_PROFILES.keys()) + list(ALIASES_NPC.keys())
        for nome in sorted(nomes_busca, key=len, reverse=True):
            if nome not in universo:
                continue
            canonico = self.nome_canonico(nome)
            if canonico in vistos:
                continue
            perfil = get_profile(canonico)
            if perfil:
                vistos.add(canonico)
                encontrados.append(format_profile_for_narrator(perfil))

        # NPCs que já nasceram automaticamente também entram no cérebro do narrador.
        for npc in await listar_npcs_mundo():
            nome_npc_cf = npc["nome"].casefold()
            if nome_npc_cf not in universo or nome_npc_cf in vistos:
                continue
            if self.entidade_coletiva_ou_nao_individual(npc["nome"]):
                continue
            try:
                perfil = await self.obter_perfil_npc(
                    npc["nome"],
                    contexto=f"Canal #{getattr(ctx.channel, 'name', 'desconhecido')}; histórico atual do RP.",
                    criar=True,
                )
            except Exception as erro_perfil:
                # Perfil secundário nunca pode impedir a cena principal de acontecer.
                print(
                    f"⚠️ Perfil secundário ignorado sem interromper narração — "
                    f"{npc['nome']}: {type(erro_perfil).__name__}: {erro_perfil}"
                )
                continue
            if perfil:
                vistos.add(nome_npc_cf)
                encontrados.append(format_profile_for_narrator(perfil))

        return "\n\n".join(encontrados[:8]) if encontrados else "Nenhum perfil canônico específico ativado."

    async def registrar_consequencia_mundial(self, ctx, acao, narracao, ficha):
        """Extrai apenas acontecimentos realmente consumados e dignos de persistência global."""
        local = await buscar_localizacao_jogador(ctx.author.id)
        localizacao = local["localizacao"] if local else None
        area = local["area"] if local else None
        entrada = f"""
PERSONAGEM: {ficha['nome']}
FACÇÃO: {ficha['faccao']}
LOCAL: {localizacao or 'desconhecido'} / {area or 'desconhecida'}
AÇÃO DECLARADA: {acao}
RESULTADO CONFIRMADO PELO NARRADOR: {narracao}

Decida se ocorreu um acontecimento que deve alterar persistentemente o mundo compartilhado.
Registre SOMENTE fatos consumados: crimes relevantes, mortes, destruição, derrota de figura importante,
confronto público, ajuda marcante, fuga notória, invasão, traição, aliança, humilhação pública ou outro fato
que NPCs/locais/facções poderiam lembrar. Tentativas fracassadas triviais não viram evento.

Conhecimento NÃO é onisciente. Marinha/Governo/Piratas/Público só sabem se havia testemunhas,
comunicação, relatório, sobreviventes, Den Den Mushi, jornal ou outra rota plausível na cena.
O Governo não recebe automaticamente tudo que a Marinha local sabe.

Responda SOMENTE JSON válido, sem markdown, neste formato:
{{"registrar":true/false,"tipo":"...","resumo":"...","gravidade":1,
"alcance":"local|regional|faccao|mundial","testemunhas":false,
"marinha_sabe":false,"governo_sabe":false,"piratas_sabem":false,"publico_sabe":false,
"hostil_marinha":false,"hostil_governo":false,"hostil_piratas":false,"ajuda_publica":false,
"virou_noticia":false,"manchete":""}}
""".strip()
        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions="Você é o registrador objetivo do mundo persistente de um RPG de One Piece. Não invente fatos nem conhecimento impossível.",
            input=entrada,
            max_output_tokens=300,
        )
        bruto = resposta.output_text.strip()
        try:
            dados = json.loads(bruto)
        except json.JSONDecodeError:
            achado = re.search(r"\{.*\}", bruto, re.S)
            if not achado:
                return None
            dados = json.loads(achado.group(0))
        if not dados.get("registrar"):
            return None
        resumo = str(dados.get("resumo") or "").strip()
        if not resumo:
            return None
        evento = await registrar_evento_mundo(
            personagem_nome=ficha["nome"], user_id=ctx.author.id,
            localizacao=localizacao, area=area,
            tipo=str(dados.get("tipo") or "acontecimento")[:80], resumo=resumo[:1200],
            gravidade=dados.get("gravidade", 1), alcance=dados.get("alcance", "local"),
            testemunhas=dados.get("testemunhas", False), marinha_sabe=dados.get("marinha_sabe", False),
            governo_sabe=dados.get("governo_sabe", False), piratas_sabem=dados.get("piratas_sabem", False),
            publico_sabe=dados.get("publico_sabe", False),
        )

        # O mesmo evento confirmado alimenta reputação e procura.
        await aplicar_impacto_reputacao(
            personagem_nome=ficha["nome"],
            gravidade=dados.get("gravidade", 1),
            localizacao=localizacao,
            marinha_sabe=dados.get("marinha_sabe", False),
            governo_sabe=dados.get("governo_sabe", False),
            piratas_sabem=dados.get("piratas_sabem", False),
            publico_sabe=dados.get("publico_sabe", False),
            hostil_marinha=dados.get("hostil_marinha", False),
            hostil_governo=dados.get("hostil_governo", False),
            hostil_piratas=dados.get("hostil_piratas", False),
            ajuda_publica=dados.get("ajuda_publica", False),
        )

        # Só fatos que realmente circulariam viram notícia.
        if dados.get("virou_noticia") and str(dados.get("manchete") or "").strip():
            await registrar_noticia_mundo(
                evento["id"], ficha["nome"],
                str(dados["manchete"]).strip(),
                resumo,
                dados.get("alcance", "regional"),
            )
        return evento

    async def apagar_central_personagem(self, guild, user_id):
        """Apaga SOMENTE a thread central sp-USER_ID; nunca a thread/canal da aventura."""
        if guild is None:
            return False
        marcador = f"sp-{user_id}"
        canal = guild.get_channel(CANAL_CRIACAO_ID)
        if canal is None:
            try:
                canal = await guild.fetch_channel(CANAL_CRIACAO_ID)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                canal = None
        candidatos = list(getattr(guild, "threads", []))
        if canal is not None:
            candidatos.extend(getattr(canal, "threads", []))
        for thread in candidatos:
            if thread.parent_id == CANAL_CRIACAO_ID and marcador in thread.name:
                try:
                    await thread.delete(reason="Sea's Paradise — personagem morreu; central antiga removida.")
                    return True
                except discord.NotFound:
                    return True
                except (discord.Forbidden, discord.HTTPException):
                    return False
        if canal is not None:
            for kwargs in ({"limit": None}, {"limit": None, "private": True, "joined": False}):
                try:
                    async for thread in canal.archived_threads(**kwargs):
                        if marcador in thread.name:
                            await thread.delete(reason="Sea's Paradise — personagem morreu; central antiga removida.")
                            return True
                except (discord.Forbidden, discord.NotFound, discord.HTTPException, TypeError, AttributeError):
                    pass
        return False

    async def gerar_narracao(self, ctx, acao, ficha, especializacoes):
        mundo = await self.contexto_mundo(acao, ctx.author.id)
        canon = await self.contexto_canonico(ctx, acao)
        notoriedade = await buscar_notoriedade_personagem(ficha["nome"])
        notoriedade_txt = (
            f"Impacto={notoriedade['impacto_total']}; Marinha={notoriedade['atencao_marinha']}; "
            f"Governo={notoriedade['atencao_governo']}; Piratas={notoriedade['notoriedade_pirata']}; "
            f"Público={notoriedade['fama_publica']}"
        ) if notoriedade else "Sem histórico conhecido."
        entrada = f"""
{formatar_ficha(ficha, especializacoes)}

PERFIL CANÔNICO ATIVO DOS NPCS
{canon}

CANAL/LOCAL DA CENA NO DISCORD
{getattr(ctx.channel, "name", "desconhecido")}

ESTADO PERSISTENTE DO MUNDO
{mundo}

NOTORIEDADE HISTÓRICA DESTE PERSONAGEM
{notoriedade_txt}
REGRA: esses números medem acúmulo de acontecimentos, não autorizam conhecimento onisciente.
NPCs só reconhecem o personagem quando a informação plausivelmente chegou até eles.

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
O ESTADO DO JOGADOR é autoritativo: preso continua preso, inconsciente continua inconsciente,
restrições continuam valendo e armas apreendidas não reaparecem por declaração do jogador.
Mudança de ilha/local só ocorre quando a própria cena realmente conclui deslocamento/viagem.

Narre apenas a continuação desta cena.

DIREÇÃO DESTA RESPOSTA
- Primeiro identifique literalmente o último ato físico que o jogador declarou. Resolva somente esse ato. Não invente movimento, ataque, defesa, fala ou decisão posterior do player.
- Se a ação do jogador for apenas preparação, fala, ameaça ou postura, a consequência concreta deve vir do ambiente/NPCs; o personagem do jogador permanece exatamente no ponto em que sua declaração terminou.
- NPCs presentes possuem iniciativa própria e podem agir/contra-atacar nesta mesma resposta.
- Não use esquiva automática para preservar NPC. Não repita o mesmo bloqueio do turno anterior.
- Consulte o HISTÓRICO: se a cena estiver estagnada, faça-a avançar agora de maneira coerente.
- Use os atributos reais do jogador e os atributos registrados do NPC para resolver combate: Força do atacante contra Resistência do alvo; Velocidade contra Velocidade.
- Não transforme diferença enorme de poder em uma sequência infinita de esquivas. O lado superior deve conseguir impor pressão, contra-atacar e encerrar a troca quando isso for coerente.
- Não invente atributos numéricos ausentes. Se faltarem pontos do NPC, não fabrique números; porém use o PERFIL CANÔNICO para reconhecer diferenças qualitativas óbvias de poder.
- Um player iniciante não recebe "chance dramática" gratuita contra um NPC de elite. Se velocidade, experiência, poderes e contexto tornam o ataque claramente inviável, resolva isso com naturalidade e dê ao NPC uma reação coerente — inclusive ofensiva.
- Antes de narrar um personagem canônico, cheque mentalmente: poderes, estilo de luta, arma, veículo, personalidade, objetivo atual e recursos confirmados no PERFIL CANÔNICO. Não substitua esses elementos por genéricos.
- Se os fatos mecânicos e a situação tornarem um golpe realmente letal, morte é uma consequência permitida tanto para player quanto para NPC; ninguém tem plot armor.
- NPC hostil pode iniciar força letal e tentar matar o player quando isso combina com sua intenção, personalidade e situação. Não o faça lutar eternamente de modo defensivo ou misericordioso sem razão.
- Se um NPC for esmagadoramente superior e tiver intenção letal, não prolongue artificialmente a luta: uma abertura pode resultar em ferimento crítico, incapacitação ou morte conforme os fatos da cena.
- Se a morte do PLAYER for efetivamente consumada nesta resposta, termine com [MORTE_PLAYER]. Não use o marcador para mera tentativa, ameaça, ferimento ou possibilidade.
- Se uma viagem/deslocamento for CONCLUÍDO nesta resposta, emita [LOCAL_PLAYER:Localização|Área].
- Se prisão, libertação, inconsciência, incapacitação, início/fim de combate ou restrições mudarem de fato, emita [ESTADO_PLAYER:estado|custodia|restricoes|sim/nao].
- Recompensas e alterações numéricas de ficha continuam dependendo do sistema apropriado.
- Se o objetivo for encontrar NPC difícil, progresso acumulado deve aproximar o jogador dele; dificuldade não é invisibilidade infinita.
- A resposta deve terminar completa. NUNCA termine no meio de uma frase, oração, diálogo ou ação. Se estiver ficando longa, conclua o acontecimento atual em menos parágrafos em vez de cortar a prosa.
""".strip()

        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=PROMPT_NARRADOR,
            input=entrada,
            max_output_tokens=1800,
        )
        narracao = resposta.output_text.strip()
        if not narracao:
            raise RuntimeError("A OpenAI retornou uma narração vazia.")

        morte_player = "[MORTE_PLAYER]" in narracao

        mudanca_local = None
        match_local = re.search(r"\[LOCAL_PLAYER:([^\]|]+)(?:\|([^\]]*))?\]", narracao)
        if match_local:
            mudanca_local = (
                match_local.group(1).strip(),
                (match_local.group(2) or "").strip() or None
            )

        mudanca_estado = None
        match_estado = re.search(
            r"\[ESTADO_PLAYER:([^\]|]*)(?:\|([^\]]*))?(?:\|([^\]]*))?(?:\|([^\]]*))?\]",
            narracao
        )
        if match_estado:
            combate_txt = (match_estado.group(4) or "").strip().casefold()
            mudanca_estado = {
                "estado": (match_estado.group(1) or "").strip() or "livre",
                "custodia": (match_estado.group(2) or "").strip() or None,
                "restricoes": (match_estado.group(3) or "").strip() or None,
                "combate_ativo": combate_txt in {"sim", "true", "1", "yes"}
            }

        narracao = re.sub(r"\[MORTE_PLAYER\]", "", narracao)
        narracao = re.sub(r"\[LOCAL_PLAYER:[^\]]+\]", "", narracao)
        narracao = re.sub(r"\[ESTADO_PLAYER:[^\]]+\]", "", narracao).strip()
        return narracao, morte_player, mudanca_local, mudanca_estado

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
            permitido, local_canal, estado_atual = await self.validar_localizacao_do_canal(ctx)
            if not permitido:
                area = f" — {estado_atual['area']}" if estado_atual and estado_atual["area"] else ""
                estado = (
                    estado_atual["estado"]
                    if estado_atual and "estado" in estado_atual and estado_atual["estado"]
                    else "livre"
                )
                await ctx.send(
                    "❌ **Você não está neste local.**\n"
                    f"📍 Localização atual: **{estado_atual['localizacao']}**{area}\n"
                    f"🔒 Estado: **{estado}**\n"
                    f"O canal **#{ctx.channel.name}** representa **{local_canal}**. "
                    "Conclua o deslocamento dentro da cena atual antes de agir aqui."
                )
                return

            especializacoes = list(await buscar_especializacoes(ctx.author.id))
            try:
                async with ctx.typing():
                    narracao, morte_player, mudanca_local, mudanca_estado = await self.gerar_narracao(
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

            # O texto da IA não altera o mundo sozinho: somente marcadores internos
            # validados nesta resposta podem atualizar localização/estado.
            if not morte_player:
                if mudanca_local:
                    await definir_localizacao_jogador(
                        ctx.author.id, mudanca_local[0], mudanca_local[1]
                    )
                    print(
                        f"🧭 {ficha['nome']} mudou persistentemente para "
                        f"{mudanca_local[0]} / {mudanca_local[1] or 'sem área'}."
                    )
                if mudanca_estado:
                    await definir_estado_jogador(
                        ctx.author.id,
                        estado=mudanca_estado["estado"],
                        custodia=mudanca_estado["custodia"],
                        restricoes=mudanca_estado["restricoes"],
                        combate_ativo=mudanca_estado["combate_ativo"],
                    )
                    print(
                        f"🔒 Estado persistente de {ficha['nome']}: "
                        f"{mudanca_estado['estado']}."
                    )

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

            try:
                evento = await self.registrar_consequencia_mundial(ctx, texto, narracao, ficha)
                if evento:
                    print(f"🌍 Consequência mundial persistida: {ficha['nome']} — {evento['tipo']}")
            except Exception as erro_mundo:
                # Falha no registro secundário não deve apagar a cena já narrada.
                print(f"⚠️ ERRO AO REGISTRAR CONSEQUÊNCIA DO MUNDO — {type(erro_mundo).__name__}: {erro_mundo}")

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

            # Nunca corte a narração: cada parte vira seu próprio embed.
            # Usamos margem abaixo do limite de 4096 caracteres da descrição
            # para preservar parágrafos e evitar truncamentos.
            partes = dividir_mensagem(narracao, limite=3800)
            total_partes = len(partes)

            for indice, parte in enumerate(partes, start=1):
                titulo = "📖 NARRADOR — SEA'S PARADISE"
                if indice > 1:
                    titulo += f" — CONTINUAÇÃO {indice}/{total_partes}"

                embed = discord.Embed(
                    title=titulo,
                    description=parte,
                    color=discord.Color.blue()
                )
                embed.set_footer(
                    text=f"Ação de {ficha['nome']} • Narração automática"
                )
                await ctx.send(embed=embed)

            if morte_player:
                await ctx.send(
                    f"💀 **{ficha['nome']} morreu.** A ficha foi resetada. "
                    "Você precisará criar um novo personagem para continuar."
                )
                central_apagada = await self.apagar_central_personagem(ctx.guild, ctx.author.id)
                if central_apagada:
                    print(f"🧹 Central antiga de {ctx.author.id} apagada após a morte.")
                else:
                    print(f"⚠️ Central antiga de {ctx.author.id} não foi encontrada ou não pôde ser apagada.")

    @commands.command(name="ondeestou")
    async def ondeestou(self, ctx):
        local = await buscar_localizacao_jogador(ctx.author.id)
        if not local or not local['localizacao']:
            await ctx.send("🧭 Sua localização persistente ainda não foi estabelecida pelo mundo.")
            return
        area = f" • {local['area']}" if local['area'] else ""
        estado = local["estado"] if "estado" in local and local["estado"] else "livre"
        custodia = local["custodia"] if "custodia" in local else None
        restricoes = local["restricoes"] if "restricoes" in local else None
        extras = [f"Estado: **{estado}**"]
        if custodia:
            extras.append(f"Custódia: **{custodia}**")
        if restricoes:
            extras.append(f"Restrições: **{restricoes}**")
        await ctx.send(
            f"🧭 **{local['localizacao']}**{area}\n" + " • ".join(extras)
        )

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

    @commands.command(name="npcstatus", aliases=["statusnpc", "status"])
    async def npcstatus(self, ctx, *, nome_npc: str):
        canonico = self.nome_canonico(nome_npc)
        if self.entidade_coletiva_ou_nao_individual(canonico):
            await ctx.send("❌ Esse nome representa um grupo/facção, não um NPC individual.")
            return
        try:
            perfil = await self.obter_perfil_npc(
                canonico,
                contexto=f"Consulta de status no canal #{getattr(ctx.channel, 'name', 'desconhecido')}.",
                criar=True,
            )
        except Exception as erro:
            await ctx.send(f"❌ Não consegui gerar o perfil mecânico desse NPC: {erro}")
            return

        npc = await self.garantir_npc_catalogado(canonico)
        if not npc:
            await ctx.send("❌ Não foi possível carregar esse NPC no mundo persistente.")
            return

        # Os números são de balanceamento do RP; dados secretos de combate ficam fora do comando.
        embed = discord.Embed(
            title=f"⚔️ STATUS — {perfil['nome'].upper()}",
            description=f"**{perfil['titulo']}** • {perfil['classificacao']}",
            color=discord.Color.dark_gold()
        )
        embed.add_field(name="🌊 Afiliação", value=perfil["faccao"], inline=True)
        embed.add_field(name="🧬 Raça", value=perfil["raca"], inline=True)
        embed.add_field(name="📍 Local conhecido", value=npc["localizacao"] or "Desconhecido", inline=True)
        embed.add_field(
            name="📊 Atributos do RP",
            value=(f"💪 Força: **{npc['forca']}**\n"
                   f"🛡️ Resistência: **{npc['resistencia']}**\n"
                   f"⚡ Velocidade/Agilidade: **{npc['velocidade']}**"),
            inline=False
        )
        embed.add_field(name="🍎 Akuma no Mi", value=perfil["akuma"], inline=True)
        embed.add_field(name="👁️ Haki", value=perfil["haki"], inline=True)
        embed.add_field(name="🥋 Estilo", value=perfil["estilo"], inline=True)
        embed.add_field(name="🗡️ Arma/Recurso", value=perfil["arma"], inline=True)
        embed.add_field(name="📖 Informações conhecidas", value=perfil["publico"], inline=False)
        embed.set_footer(text="Atributos são valores de balanceamento do Sea's Paradise (máx. 50.000).")
        await ctx.send(embed=embed)

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


    @commands.command(name="reputacao", aliases=["procurado", "reputação"])
    async def reputacao(self, ctx):
        ficha = await buscar_ficha(ctx.author.id)
        if not ficha:
            await ctx.send("❌ Você ainda não possui uma ficha ativa.")
            return
        rep = await buscar_reputacao_mundo(ficha["nome"])
        if not rep:
            await ctx.send(f"🌊 **{ficha['nome']}** ainda não possui reputação relevante registrada no mundo.")
            return
        embed = discord.Embed(title=f"🌍 REPUTAÇÃO — {ficha['nome'].upper()}", color=discord.Color.dark_gold())
        embed.add_field(name="☠️ Procurado", value="Sim" if rep["procurado"] else "Não", inline=True)
        embed.add_field(name="💰 Recompensa", value=f"฿ {int(rep['recompensa']):,}", inline=True)
        embed.add_field(name="⚠️ Ameaça", value=f"{rep['nivel_ameaca']}/5", inline=True)
        embed.add_field(name="⚓ Marinha", value=str(rep["marinha"]), inline=True)
        embed.add_field(name="🏛️ Governo", value=str(rep["governo"]), inline=True)
        embed.add_field(name="🏴‍☠️ Piratas", value=str(rep["piratas"]), inline=True)
        embed.add_field(name="👥 Civis", value=str(rep["civis"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="jornal", aliases=["noticias", "notícias"])
    async def jornal(self, ctx):
        noticias = await buscar_noticias_mundo(8)
        if not noticias:
            await ctx.send("📰 Ainda não há notícias relevantes circulando pelo mundo.")
            return
        texto = "\n\n".join(f"**{x['manchete']}**\n{x['corpo']}" for x in noticias)
        for parte in dividir_mensagem(texto, limite=3800):
            await ctx.send(embed=discord.Embed(
                title="📰 JORNAL ECONÔMICO MUNDIAL",
                description=parte,
                color=discord.Color.gold()
            ))

async def setup(bot):
    await bot.add_cog(Narrador(bot))
