import os
import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands, tasks
from openai import AsyncOpenAI

from database.database import buscar_viagem_ativa, buscar_treinamento_ativo, listar_subordinados, evento_ativo_usuario, forma_ativa
from cogs.npc_profiles import NPC_PROFILES, get_profile, profile_for_narrator, format_profile_for_narrator
from data.mundo import BOSS_RANKS
from data.navegacao import normalizar_destino
from data.combat_rules import COMBAT_LOGIC_RULES
from database.database import get_pool, adicionar_pontos_atributo, adicionar_pontos_percentuais, adicionar_berries, adicionar_reputacao

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
    atualizar_estado_jogador,
    definir_estado_jogador,
    buscar_sessao_ativa,
    obter_ou_criar_sessao,
    entrar_sessao,
    listar_participantes_sessao, listar_participantes_ciclo, definir_inicio_ciclo_participante,
    marcar_participante_sessao,
    registrar_turno_sessao,
    buscar_turnos_sessao,
    encerrar_sessao_narracao,
    buscar_reputacao_mundo, aplicar_impacto_reputacao, registrar_noticia_mundo, buscar_noticias_mundo, sincronizar_noticias_recentes,
    configurar_sessao_narracao, marcar_sessao_iniciada,
    registrar_acao_cena_sessao, listar_acoes_cena_sessao, avancar_ciclo_cena_sessao, definir_deadline_ciclo, limpar_deadline_ciclo, listar_ciclos_expirados,
    buscar_combate_ativo, iniciar_combate_sessao, entrar_combate, listar_combatentes,
    registrar_acao_combate, listar_acoes_rodada, atualizar_status_combatente,
    avancar_rodada_combate, encerrar_combate_sessao, atualizar_estado_cena_sessao,
    buscar_evento_por_thread, status_participacao_evento, participar_evento_global, buscar_sessao_por_id,
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

# A mesma lei de combate vale em cenas normais, PvP, NPCs, eventos e Boss Rank.
PROMPT_NARRADOR = PROMPT_NARRADOR + "\n\n" + COMBAT_LOGIC_RULES

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
        self.verificar_ciclos_pendentes.start()

    def cog_unload(self):
        self.verificar_ciclos_pendentes.cancel()

    async def cog_before_invoke(self, ctx):
        # No canal de RP, comandos operacionais somem sozinhos; !acao é parte do registro narrativo.
        if ctx.command and ctx.command.name != "acao":
            async def apagar_comando():
                await asyncio.sleep(120)
                try: await ctx.message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException): pass
            asyncio.create_task(apagar_comando())

    async def aviso(self, ctx, conteudo=None, *, embed=None, segundos=120):
        # Avisos operacionais são temporários e, quando destinados a um jogador,
        # sempre o mencionam para gerar notificação no Discord.
        autor = getattr(ctx, "author", None)
        if conteudo and autor is not None and getattr(autor, "mention", None) and autor.mention not in conteudo:
            conteudo = f"{autor.mention} {conteudo}"
        return await ctx.send(conteudo, embed=embed, delete_after=segundos)

    async def _resolver_timeout_sessao(self, sessao, canal=None):
        """Resolve um ciclo vencido e solta a cena de participantes que não responderam."""
        cena_id = int(sessao['channel_id'])
        locks.setdefault(cena_id, asyncio.Lock())
        if locks[cena_id].locked():
            return False
        async with locks[cena_id]:
            atual = await buscar_sessao_por_id(sessao['id'])
            if not atual or atual['status'] != 'ativa' or not atual['ciclo_deadline']:
                return False
            # Reconfirma no PostgreSQL: não resolve antes do prazo por relógio/cache local.
            expirados = {int(x['id']) for x in await listar_ciclos_expirados()}
            if int(atual['id']) not in expirados:
                return False
            ciclo = atual['ciclo_cena']
            acoes = await listar_acoes_cena_sessao(atual['id'], ciclo)
            if not acoes:
                await limpar_deadline_ciclo(atual['id'])
                return False
            participantes = await listar_participantes_ciclo(atual['id'], ciclo)
            ids_acao = {int(a['user_id']) for a in acoes}
            ausentes = [p for p in participantes if int(p['user_id']) not in ids_acao]
            if canal is None:
                canal = self.bot.get_channel(cena_id)
                if canal is None:
                    try: canal = await self.bot.fetch_channel(cena_id)
                    except Exception: canal = None
            if canal is None:
                # Não perde o deadline: tentaremos novamente no próximo watchdog.
                return False
            class CtxTimeout:
                def __init__(self,ch): self.channel=ch; self.guild=getattr(ch,'guild',None); self.bot=None
                async def send(self,*a,**kw): return await self.channel.send(*a,**kw)
                def typing(self): return self.channel.typing()
            await self.resolver_cena_multiplayer(CtxTimeout(canal), atual, acoes, timeout=True)
            # Quem não respondeu em 5 min deixa de bloquear a cena. Não é movido,
            # morto nem controlado pela IA; pode voltar com !entrar.
            for p in ausentes:
                await marcar_participante_sessao(atual['id'], p['user_id'], 'ausente')
            if ausentes:
                mencoes = ' '.join(f"<@{p['user_id']}>" for p in ausentes)
                await canal.send(
                    f"{mencoes} 💤 **Tempo de ação esgotado.** A cena continuou com quem agiu. "
                    "Você saiu da participação ativa para não prender os demais; quando voltar, use `!entrar`.",
                    delete_after=120
                )
            return True

    @tasks.loop(seconds=10, reconnect=True)
    async def verificar_ciclos_pendentes(self):
        # O watchdog nunca deve morrer por uma falha pontual de banco/Discord/IA.
        try:
            expirados = await listar_ciclos_expirados()
            for sessao in expirados:
                try:
                    await self._resolver_timeout_sessao(sessao)
                except Exception as ex:
                    print(f"❌ ERRO TIMEOUT CENA {sessao['id']} — {type(ex).__name__}: {ex}")
        except Exception as ex:
            print(f"❌ ERRO WATCHDOG NARRATIVO — {type(ex).__name__}: {ex}")

    @verificar_ciclos_pendentes.before_loop
    async def antes_timeout_ciclos(self):
        await self.bot.wait_until_ready()

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

    async def contexto_participantes_sessao(self, sessao_id, autor_id):
        """
        Todos os participantes ativos pertencem à mesma realidade.
        Não há limite artificial de jogadores. Mantemos cada ficha compacta para escalar.
        """
        participantes = await listar_participantes_sessao(sessao_id, somente_ativos=True)
        if not participantes:
            return "Nenhum participante ativo registrado."

        linhas = []
        for p in participantes:
            ficha = await buscar_ficha(p["user_id"])
            estado = await buscar_localizacao_jogador(p["user_id"])
            if ficha:
                papel = "JOGADOR DA AÇÃO ATUAL" if p["user_id"] == autor_id else "OUTRO PLAYER PRESENTE"
                forma = await forma_ativa(p["user_id"])
                forma_txt = (f" | Forma ativa={forma['nome']} (+{forma['bonus_forca']}% Força, +{forma['bonus_resistencia']}% Resistência, +{forma['bonus_velocidade']}% Velocidade; {forma['capacidades'] or 'sem capacidade adicional'})" if forma else "")
                linhas.append(
                    f"- {papel}: {ficha['nome']} (user_id={p['user_id']}) | "
                    f"Facção={ficha['faccao']} | Força={ficha['forca']} | "
                    f"Resistência={ficha['resistencia']} | Velocidade={ficha['velocidade']} | "
                    f"Akuma={ficha['akuma']} | Estado={(estado['estado'] if estado and 'estado' in estado else 'livre')} | "
                    f"Local={(estado['localizacao'] if estado else 'desconhecido')}{forma_txt}"
                )
                try:
                    subs = await listar_subordinados(p["user_id"])
                    for sub in subs:
                        linhas.append(f"  - SUBORDINADO NPC AUTÔNOMO de {ficha['nome']}: {sub['nome']} | Função={sub['funcao']} | Rank={sub['rank']} | Lealdade={sub['lealdade']} | Personalidade={sub['personalidade']}. Reaja por conta própria de forma coerente com personalidade, função, perigo e lealdade; não espere ordem para toda reação, mas não controle o player.")
                except Exception:
                    pass
            else:
                linhas.append(
                    f"- PARTICIPANTE SEM FICHA ATIVA: {p['personagem_nome']} (user_id={p['user_id']})"
                )
        return "\n".join(linhas)

    async def historico_compartilhado_sessao(self, sessao_id):
        turnos = await buscar_turnos_sessao(sessao_id, limite=30)
        if not turnos:
            return "Esta é a primeira ação desta sessão."
        return "\n\n".join(
            f"{t['personagem_nome']}: {t['acao']}\nNARRADOR: {t['narracao']}"
            for t in turnos
        )

    async def resumo_encerramento_sessao(self, sessao_id):
        participantes = await listar_participantes_sessao(sessao_id, somente_ativos=False)
        turnos = await buscar_turnos_sessao(sessao_id, limite=100)
        nomes = ", ".join(dict.fromkeys(str(p["personagem_nome"]) for p in participantes)) or "Nenhum"
        historico = "\n\n".join(
            f"{t['personagem_nome']}: {t['acao']}\nNARRADOR: {t['narracao']}"
            for t in turnos
        )
        if len(historico) > 24000:
            historico = historico[-24000:]
        entrada = f"""
PARTICIPANTES: {nomes}

HISTÓRICO DA SESSÃO:
{historico or 'Sem turnos registrados.'}

Produza um resumo factual e curto do encerramento desta sessão de RP.
Inclua apenas fatos que realmente aconteceram: objetivos concluídos, derrotas, mortes,
alianças, prisões, fugas, descobertas e estado final relevante.
Não conceda pontos, porcentagens, itens ou recompensas numéricas aqui.
""".strip()
        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions="Resuma objetivamente uma sessão encerrada do Sea's Paradise. Não invente fatos nem recompensas.",
            input=entrada,
            max_output_tokens=500,
        )
        return resposta.output_text.strip() or "Sessão encerrada."

    async def deve_encerrar_sessao(self, sessao_id, narracao_atual, declaracoes_atuais=""):
        sessao_atual=await buscar_sessao_por_id(sessao_id)
        if sessao_atual and "conflito_ativo" in sessao_atual and sessao_atual["conflito_ativo"]:
            return False
        participantes=await listar_participantes_sessao(sessao_id,True)
        historico=await self.historico_compartilhado_sessao(sessao_id)
        entrada=f"""PARTICIPANTES ATIVOS: {', '.join(p['personagem_nome'] for p in participantes)}
DECLARAÇÕES ATUAIS DOS PLAYERS:
{declaracoes_atuais or 'Não fornecidas.'}
HISTÓRICO:
{historico}
ÚLTIMA NARRAÇÃO:
{narracao_atual}

Decida se ESTA sessão deve terminar agora.
SIM quando o objetivo/conflito acabou OU quando TODOS os participantes ativos declararam claramente
que estão deixando/encerrando o acontecimento atual e não existe impedimento imediato que os prenda
à cena (combate ativo, perseguição, captura, perigo inevitável ou ação obrigatória pendente).
Não mantenha a sessão aberta só porque o texto ainda os descreve caminhando para fora: se todos
abandonaram o acontecimento e a saída é viável, encerre.
NAO se apenas um terminou, outro quer continuar, ou há conflito imediato realmente pendente.
Responda somente SIM ou NAO."""
        r=await self.client.responses.create(model=MODELO_NARRADOR,
            instructions="Seja conservador ao encerrar sessões de RPG. Responda somente SIM ou NAO.",
            input=entrada,max_output_tokens=8)
        return r.output_text.strip().upper().startswith("SIM")

    async def resolver_cena_multiplayer(self,ctx,sessao,acoes,timeout=False):
        blocos=[]; fichas={}
        for a in acoes:
            f=await buscar_ficha(a["user_id"])
            if f:
                fichas[a["user_id"]]=f
                esp=list(await buscar_especializacoes(a["user_id"]))
                blocos.append(f"USER_ID={a['user_id']}\\n{formatar_ficha(f,esp)}")
        declaracoes="\\n".join(f"- {a['personagem_nome']} (USER_ID={a['user_id']}): {a['acao']}" for a in acoes)
        participantes_ciclo_resolucao = await listar_participantes_ciclo(sessao["id"], sessao["ciclo_cena"])
        ids_com_acao = {int(a["user_id"]) for a in acoes}
        ausentes = [p for p in participantes_ciclo_resolucao if int(p["user_id"]) not in ids_com_acao]
        contexto_ausentes = (
            "PARTICIPANTES SEM DECLARAÇÃO NESTE CICLO (NÃO invente ação voluntária para eles):\n" +
            "\n".join(f"- {p['personagem_nome']} (USER_ID={p['user_id']}): preserve a última situação conhecida; apenas consequências inevitáveis do mundo podem afetá-lo." for p in ausentes)
        ) if ausentes else "TODOS OS PARTICIPANTES DO CICLO DECLARARAM AÇÃO."
        hist=await self.historico_compartilhado_sessao(sessao["id"])
        # Todos já passaram pelo portão de localização. Usamos um participante real
        # como âncora do contexto compartilhado em vez de user_id=None.
        ancora_user_id = acoes[0]["user_id"] if acoes else None
        mundo=await self.contexto_mundo(declaracoes,ancora_user_id)
        canon=await self.contexto_canonico(ctx,declaracoes)
        entrada=f"""CENA MULTIPLAYER NORMAL — NÃO É RODADA DE COMBATE
FICHAS:
{chr(10).join(blocos)}
DECLARAÇÕES DESTE CICLO:
{declaracoes}
{contexto_ausentes}
NPCS:
{canon}
MUNDO:
{mundo}
HISTÓRICO:
{hist}
ESTADO TÁTICO PERSISTENTE DA CENA:
{sessao['estado_cena'] if 'estado_cena' in sessao and sessao['estado_cena'] else 'Ainda não consolidado.'}

Resolva TODAS as declarações em UMA continuação compartilhada. Não faça uma narração isolada por player.
REGRA DE COBERTURA: cada declaração RECEBIDA deste ciclo DEVE produzir uma consequência perceptível nesta mesma resposta. Não adie uma ação para o próximo ciclo e não omita nenhum jogador.
Não invente ação voluntária posterior dos players.
NPCs/ambiente possuem iniciativa. Se houver hostilidade imediata, eles DEVEM tomar uma decisão concreta coerente nesta resposta (atacar, defender, fugir, avançar, buscar cobertura, negociar, proteger alguém, chamar reforço etc.); ficar apenas mirando/cercando/reposicionando repetidamente não conta como reação.
Combate é um ESTADO da própria cena, não um modo separado. Continue resolvendo tudo por !acao.
Ao final emita [CONFLITO:SIM] se ainda existe confronto/perseguição/ameaça imediata que exige resolução, ou [CONFLITO:NAO] se não existe.
Emita também [CENA_ESTADO:resumo factual curto] com posições, contenções, ferimentos, armas relevantes, coberturas e ameaças que DEVEM persistir no próximo ciclo.
Use [ENCERRAR_SESSAO] apenas se a sessão inteira acabou E [CONFLITO:NAO]. Também use quando TODOS os participantes deste ciclo
deixarem claramente o acontecimento atual e não houver impedimento imediato que os prenda à cena.
Use [MORTE_PLAYER:USER_ID], [LOCAL_PLAYER:USER_ID|Local|Area] e
[ESTADO_PLAYER:USER_ID|estado|custodia|restricoes|sim/nao] apenas quando consumados.
Seja objetivo: 2 a 6 parágrafos curtos."""
        r=await self.client.responses.create(model=MODELO_NARRADOR,instructions=PROMPT_NARRADOR,input=entrada,max_output_tokens=900)
        bruto=r.output_text.strip()
        if not bruto: raise RuntimeError("Cena multiplayer vazia.")
        auto="[ENCERRAR_SESSAO]" in bruto
        conflito_m = re.search(r"\[CONFLITO:(SIM|NAO)\]", bruto, re.I)
        conflito = (conflito_m.group(1).upper()=="SIM") if conflito_m else bool(sessao.get("conflito_ativo", False))
        estado_m = re.search(r"\[CENA_ESTADO:([^\]]+)\]", bruto, re.I)
        estado_cena = estado_m.group(1).strip() if estado_m else None
        mortos={int(x) for x in re.findall(r"\[MORTE_PLAYER:(\d+)\]",bruto)}
        locais=re.findall(r"\[LOCAL_PLAYER:(\d+)\|([^\]|]+)(?:\|([^\]]*))?\]",bruto)
        estados=re.findall(r"\[ESTADO_PLAYER:(\d+)\|([^\]|]*)\|([^\]|]*)\|([^\]|]*)\|([^\]]*)\]",bruto)
        texto=re.sub(r"\[MORTE_PLAYER:\d+\]","",bruto)
        texto=re.sub(r"\[LOCAL_PLAYER:[^\]]+\]","",texto)
        texto=re.sub(r"\[ESTADO_PLAYER:[^\]]+\]","",texto)
        texto=re.sub(r"\[CONFLITO:(?:SIM|NAO)\]","",texto,flags=re.I)
        texto=re.sub(r"\[CENA_ESTADO:[^\]]+\]","",texto,flags=re.I).replace("[ENCERRAR_SESSAO]","").strip()
        await atualizar_estado_cena_sessao(sessao["id"], conflito, estado_cena)
        for pp in await listar_participantes_sessao(sessao["id"], True):
            loc=await buscar_localizacao_jogador(pp["user_id"])
            await definir_estado_jogador(pp["user_id"], (loc["estado"] if loc and loc["estado"] else "livre"), (loc["custodia"] if loc else None), (loc["restricoes"] if loc else None), conflito)
        if conflito: auto=False
        # Entrega a resposta principal antes de memórias/notoriedade/consequências secundárias.
        # Isso reduz a latência percebida sem sacrificar persistência.
        for parte in dividir_mensagem(texto,3800):
            await ctx.send(embed=discord.Embed(title="📖 NARRADOR — SEA'S PARADISE",description=parte,color=discord.Color.blue()))
        coletiva=" | ".join(f"{a['personagem_nome']}: {a['acao']}" for a in acoes)
        await registrar_turno_sessao(sessao["id"],0,"Cena coletiva",coletiva,texto)
        for a in acoes:
            f=fichas.get(a["user_id"])
            if f:
                try:
                    await self.salvar_memorias_da_acao(a["acao"],texto,f,a["user_id"])
                    await self.registrar_consequencia_mundial(ctx,a["acao"],texto,f,user_id=a["user_id"])
                except Exception as ex: print(f"⚠️ Consequência multiplayer: {ex}")
        for uid,loc,area in locais: await definir_localizacao_jogador(int(uid),loc.strip(),(area or "").strip() or None)
        for uid,est,cus,res,comb in estados:
            await definir_estado_jogador(int(uid),est.strip() or "livre",cus.strip() or None,res.strip() or None,
                                         comb.strip().casefold() in {"sim","true","1","yes"})
        for uid in mortos:
            await marcar_participante_sessao(sessao["id"],uid,"morto"); await resetar_ficha_por_morte(uid)
        await avancar_ciclo_cena_sessao(sessao["id"])
        if not auto:
            try: auto=await self.deve_encerrar_sessao(sessao["id"],texto,declaracoes)
            except Exception as ex: print(f"⚠️ Verificador de encerramento: {ex}")
        if auto:
            resumo=await self.resumo_encerramento_sessao(sessao["id"])
            if await encerrar_sessao_narracao(sessao["id"],resumo):
                e=discord.Embed(title="🏁 FIM DA NARRAÇÃO",description=resumo,color=discord.Color.gold())
                e.set_footer(text="Sessão arquivada • pronta para avaliação de recompensas")
                await ctx.send(embed=e)

    async def detectar_intencao_combate(self, texto):
        resposta=await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=("Responda SOMENTE COMBATE ou NORMAL. COMBATE apenas se o player ataca/tenta ferir, "
                          "defende alguém num confronto explícito ou declara entrar numa luta. "
                          "Ameaça, conversa, observar, viajar e treino casual = NORMAL."),
            input=texto,max_output_tokens=8)
        return resposta.output_text.strip().upper().startswith("COMBATE")

    async def painel_rodada(self, combate):
        ps=await listar_combatentes(combate["id"],True)
        acts=await listar_acoes_rodada(combate["id"],combate["rodada"])
        feitos={a["user_id"] for a in acts}
        linhas=[("✅" if p["user_id"] in feitos else "⏳")+f" **{p['personagem_nome']}**" for p in ps]
        return (f"⚔️ **Rodada {combate['rodada']}**\\n👥 Combatentes: **{len(ps)}**\\n"
                f"📝 Ações: **{len(feitos)}/{len(ps)}**\\n"+("\\n".join(linhas) if linhas else "Nenhum."))

    async def rodada_completa(self, combate):
        ps=await listar_combatentes(combate["id"],True)
        feitos={a["user_id"] for a in await listar_acoes_rodada(combate["id"],combate["rodada"])}
        return bool(ps) and all(p["user_id"] in feitos for p in ps)

    async def resolver_rodada_coletiva(self,ctx,sessao,combate):
        ps=await listar_combatentes(combate["id"],True)
        acts=await listar_acoes_rodada(combate["id"],combate["rodada"])
        if not acts:
            await ctx.send("❌ Nenhuma ação nesta rodada."); return
        blocos=[]; fichas={}
        for p in ps:
            f=await buscar_ficha(p["user_id"]); e=await buscar_localizacao_jogador(p["user_id"])
            if f:
                fichas[p["user_id"]]=f; esp=list(await buscar_especializacoes(p["user_id"]))
                blocos.append(f"USER_ID={p['user_id']}\\n{formatar_ficha(f,esp)}\\nESTADO={(e['estado'] if e and 'estado' in e else 'livre')}")
        declaracoes="\\n".join(f"- USER_ID={a['user_id']} | {a['personagem_nome']}: "+("PASSOU." if a["pulou"] else a["acao"]) for a in acts)
        hist=await self.historico_compartilhado_sessao(sessao["id"])
        mundo=await self.contexto_mundo(declaracoes,None); canon=await self.contexto_canonico(ctx,declaracoes)
        entrada=f"""COMBATE COLETIVO — RODADA {combate['rodada']}
FICHAS:
{chr(10).join(blocos)}
AÇÕES:
{declaracoes}
NPCS:
{canon}
MUNDO:
{mundo}
HISTÓRICO:
{hist}

Resolva todas as declarações como UMA rodada coerente. Compare Força, Resistência e Velocidade,
poderes e contexto. Não invente ação voluntária de player. Quem passou não age. NPCs têm iniciativa.
Sem plot armor.
Use [MORTE_PLAYER:USER_ID] apenas em morte consumada.
Use [ESTADO_PLAYER:USER_ID|estado|custodia|restricoes|sim/nao] para mudança real.
Use [FIM_COMBATE] somente se o confronto terminou.
Use [ENCERRAR_SESSAO] somente se toda a narração também terminou."""
        resp=await self.client.responses.create(model=MODELO_NARRADOR,instructions=PROMPT_NARRADOR,input=entrada,max_output_tokens=2200)
        bruto=resp.output_text.strip()
        mortos={int(x) for x in re.findall(r"\[MORTE_PLAYER:(\d+)\]",bruto)}
        estados=re.findall(r"\[ESTADO_PLAYER:(\d+)\|([^\]|]*)\|([^\]|]*)\|([^\]|]*)\|([^\]]*)\]",bruto)
        fim="[FIM_COMBATE]" in bruto; fim_sess="[ENCERRAR_SESSAO]" in bruto
        texto=re.sub(r"\[MORTE_PLAYER:\d+\]","",bruto)
        texto=re.sub(r"\[ESTADO_PLAYER:[^\]]+\]","",texto).replace("[FIM_COMBATE]","").replace("[ENCERRAR_SESSAO]","").strip()
        coletiva=" | ".join(f"{a['personagem_nome']}: {'PASSOU' if a['pulou'] else a['acao']}" for a in acts)
        await registrar_turno_sessao(sessao["id"],0,f"Rodada {combate['rodada']}",coletiva,texto)
        for a in acts:
            if a["pulou"]: continue
            f=fichas.get(a["user_id"])
            if f:
                try:
                    await self.salvar_memorias_da_acao(a["acao"],texto,f,a["user_id"])
                    await self.registrar_consequencia_mundial(ctx,a["acao"],texto,f,user_id=a["user_id"])
                except Exception as ex: print(f"⚠️ Consequência coletiva: {ex}")
        for uid,est,cus,res,comb in estados:
            await definir_estado_jogador(int(uid),est.strip() or "livre",cus.strip() or None,res.strip() or None,comb.strip().casefold() in {"sim","true","1","yes"})
        for uid in mortos:
            await atualizar_status_combatente(combate["id"],uid,"morto")
            await marcar_participante_sessao(sessao["id"],uid,"morto")
            await resetar_ficha_por_morte(uid)
        for parte in dividir_mensagem(texto,3800):
            await ctx.send(embed=discord.Embed(title=f"⚔️ COMBATE — RODADA {combate['rodada']}",description=parte,color=discord.Color.red()))
        if fim:
            await encerrar_combate_sessao(combate["id"]); await ctx.send("🏁 **Combate encerrado.** A sessão continua.")
        else:
            novo=await avancar_rodada_combate(combate["id"]); await ctx.send(await self.painel_rodada(novo))
        if fim_sess:
            resumo=await self.resumo_encerramento_sessao(sessao["id"])
            if await encerrar_sessao_narracao(sessao["id"],resumo):
                await ctx.send(embed=discord.Embed(title="🏁 FIM DA NARRAÇÃO",description=resumo,color=discord.Color.gold()))

    async def validar_localizacao_do_canal(self, ctx):
        """O canal indica onde a ação QUER ocorrer; não teleporta o personagem."""
        local_canal = self.localizacao_do_canal(ctx)
        if not local_canal:
            return True, None, None

        atual = await buscar_localizacao_jogador(ctx.author.id)

        # Eventos globais/Bosses são instâncias não-canônicas. O tópico ignora somente
        # a trava física do canal, sem alterar a localização persistente do personagem.
        evento = await evento_ativo_usuario(ctx.author.id)
        evento_thread = await buscar_evento_por_thread(getattr(ctx.channel,'id',0))
        if (evento and evento['thread_id'] and int(evento['thread_id']) == int(getattr(ctx.channel,'id',0))) or evento_thread:
            return True, local_canal, atual

        # Durante uma viagem persistente, o personagem está em alto-mar.
        # O Narrador pode continuar cenas sem transformar o canal em teleporte.
        viagem = await buscar_viagem_ativa(ctx.author.id)
        if viagem:
            return True, local_canal, atual

        # Primeira cena do personagem: o canal pode estabelecer o ponto inicial.
        if not atual or not atual["localizacao"]:
            await definir_localizacao_jogador(ctx.author.id, local_canal)
            atual = await buscar_localizacao_jogador(ctx.author.id)
            print(f"🧭 Local inicial de {ctx.author.id}: {local_canal}.")
            return True, local_canal, atual

        local_real = atual["localizacao"]
        # Todos os sistemas usam a mesma normalização de mundo/navegação.
        # Ex.: o legado "Sabaody Park" e "Sabaody Archipelago" representam o mesmo local macro.
        real_norm = normalizar_destino(local_real)
        canal_norm = normalizar_destino(local_canal)
        if str(local_real).casefold() == "sabaody park":
            real_norm = "Sabaody Archipelago"
        if str(local_canal).casefold() == "sabaody park":
            canal_norm = "Sabaody Archipelago"
        if str(real_norm).casefold() != str(canal_norm).casefold():
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

    def _normalizar_perfil_npc_gerado(self, perfil, nome_fallback):
        if not isinstance(perfil,dict): return None
        aliases={"velocidade_agilidade":"velocidade","agilidade":"velocidade","afiliação":"faccao",
                 "afiliacao":"faccao","akuma_no_mi":"akuma","fruta":"akuma","informacoes":"publico",
                 "informações":"publico","descricao_publica":"publico","descrição_publica":"publico",
                 "estilo_de_luta":"estilo","armas":"arma"}
        for origem,destino in aliases.items():
            if destino not in perfil and origem in perfil: perfil[destino]=perfil[origem]
        defaults={"nome":str(nome_fallback).strip().title(),"titulo":"Sem título conhecido",
                  "classificacao":"NPC","raca":"Não confirmada","faccao":"Não confirmada",
                  "akuma":"Nenhuma confirmada","haki":"Não confirmado","estilo":"Não confirmado",
                  "arma":"Nenhuma confirmada","publico":"Sem informações públicas adicionais registradas.",
                  "combate":"Capacidades detalhadas não confirmadas."}
        for campo in ("nome","titulo","classificacao","raca","faccao","akuma","haki","estilo","arma","publico","combate"):
            v=perfil.get(campo); perfil[campo]=str(v).strip() if v not in (None,"") else defaults[campo]
        def numero(v):
            if isinstance(v,(int,float)): return int(v)
            m=re.search(r"-?\d+",str(v).replace(".","").replace(",",""))
            return int(m.group()) if m else None
        for campo in ("forca","resistencia","velocidade"):
            n=numero(perfil.get(campo))
            if n is None: return None
            perfil[campo]=max(0,min(50000,n))
        return {k:perfil[k] for k in ("nome","titulo","classificacao","raca","faccao","forca","resistencia",
            "velocidade","akuma","haki","estilo","arma","publico","combate")}

    def _extrair_json_perfil_npc(self, bruto, nome_fallback):
        if not bruto: return None
        texto=str(bruto).strip()
        texto=re.sub(r"^```(?:json)?\s*|\s*```$","",texto,flags=re.I|re.S).strip()
        candidatos=[texto]
        ini=texto.find("{"); fim=texto.rfind("}")
        if ini!=-1 and fim>ini: candidatos.append(texto[ini:fim+1])
        for candidato in candidatos:
            try:
                perfil=json.loads(candidato)
                normal=self._normalizar_perfil_npc_gerado(perfil,nome_fallback)
                if normal: return normal
            except (json.JSONDecodeError,TypeError,ValueError):
                pass
        return None

    async def gerar_perfil_npc_automatico(self, nome, contexto=""):
        """Gera, valida e persiste NPC desconhecido; nunca grava perfil quebrado."""
        canonico=self.nome_canonico(nome)
        if self.entidade_coletiva_ou_nao_individual(canonico): return None
        fixo=get_profile(canonico)
        if fixo:
            npc=await registrar_npc(fixo["nome"],faccao=fixo["faccao"])
            if npc["forca"] is None or npc["resistencia"] is None or npc["velocidade"] is None:
                await definir_atributos_npc(fixo["nome"],fixo["forca"],fixo["resistencia"],fixo["velocidade"])
            return fixo
        salvo=await buscar_perfil_npc(canonico)
        if salvo: return salvo

        schema='{"nome":"","titulo":"","classificacao":"","raca":"","faccao":"","forca":0,"resistencia":0,"velocidade":0,"akuma":"","haki":"","estilo":"","arma":"","publico":"","combate":""}'
        entrada=f"""NPC individual: {nome}
CONTEXTO/Fase: {contexto or "fase atual do RP"}.
Crie o perfil mecânico persistente para Sea's Paradise.
Se for canônico de One Piece, respeite capacidades confirmadas e cronologia; não invente poder futuro.
Se algo não for confirmado, diga "Não confirmado". Se for original, crie kit coerente.
Atributos Força/Resistência/Velocidade: inteiros de 0 a 50.000.
Escala: civil dezenas; fracos centenas; East Blue relevante milhares; elite Grand Line dezenas de milhares;
topo mundial perto de 50.000.
Retorne SOMENTE JSON com estas chaves:
{schema}"""
        ultimo=""
        for tentativa in range(3):
            r=await self.client.responses.create(
                model=MODELO_NARRADOR,
                instructions=("Retorne exclusivamente um objeto JSON válido, sem markdown nem texto externo. "
                              "Todos os campos pedidos devem existir e os três atributos devem ser inteiros."),
                input=entrada,max_output_tokens=900)
            ultimo=(r.output_text or "").strip()
            perfil=self._extrair_json_perfil_npc(ultimo,nome)
            if perfil:
                perfil=await salvar_perfil_npc(canonico,perfil)
                npc=await registrar_npc(perfil["nome"],faccao=perfil["faccao"])
                await definir_atributos_npc(npc["nome"],perfil["forca"],perfil["resistencia"],perfil["velocidade"])
                return perfil
            print(f"⚠️ Perfil NPC inválido ({nome}) tentativa {tentativa+1}: {ultimo[:300]!r}")
        raise RuntimeError(f"respostas inválidas após 3 tentativas para {nome}; nenhum perfil incompleto foi salvo.")

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
            "ESTADO DO JOGADOR: " + ((local_player["estado"] if local_player and "estado" in local_player else None) or "livre"),
            "CUSTÓDIA: " + ((local_player["custodia"] if local_player and "custodia" in local_player else None) or "nenhuma"),
            "RESTRIÇÕES: " + ((local_player["restricoes"] if local_player and "restricoes" in local_player else None) or "nenhuma"),
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

    async def registrar_consequencia_mundial(self, ctx, acao, narracao, ficha, user_id=None):
        """Extrai apenas acontecimentos realmente consumados e dignos de persistência global."""
        uid = int(user_id if user_id is not None else ctx.author.id)
        local = await buscar_localizacao_jogador(uid)
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

REPUTAÇÃO DE FACÇÃO:
- Se um personagem da Marinha cumpre serviço útil confirmado para marinheiros/Marinha (captura, perseguição,
  proteção, apoio operacional, informação útil, combate a criminoso etc.), marque ajuda_marinha=true quando
  a Marinha presente souber do feito. Isso NÃO exige virar jornal nem ajudar civis.
- Use ajuda_governo/ajuda_piratas da mesma forma para ajuda relevante e confirmada às respectivas facções.
- Tentativa sem resultado útil não conta como ajuda só porque a intenção era boa.

Responda SOMENTE JSON válido, sem markdown, neste formato:
{{"registrar":true/false,"tipo":"...","resumo":"...","gravidade":1,
"alcance":"local|regional|faccao|mundial","testemunhas":false,
"marinha_sabe":false,"governo_sabe":false,"piratas_sabem":false,"publico_sabe":false,
"hostil_marinha":false,"hostil_governo":false,"hostil_piratas":false,
"ajuda_marinha":false,"ajuda_governo":false,"ajuda_piratas":false,"ajuda_publica":false,
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
            personagem_nome=ficha["nome"], user_id=uid,
            localizacao=localizacao, area=area,
            tipo=str(dados.get("tipo") or "acontecimento")[:80], resumo=resumo[:1200],
            gravidade=dados.get("gravidade", 1), alcance=dados.get("alcance", "local"),
            testemunhas=dados.get("testemunhas", False), marinha_sabe=dados.get("marinha_sabe", False),
            governo_sabe=dados.get("governo_sabe", False), piratas_sabem=dados.get("piratas_sabem", False),
            publico_sabe=dados.get("publico_sabe", False),
        )

        # O mesmo fato alimenta as relações do mundo. Não cria uma segunda "verdade":
        # deriva somente do evento que acabou de ser confirmado.
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
            ajuda_marinha=dados.get("ajuda_marinha", False),
            ajuda_governo=dados.get("ajuda_governo", False),
            ajuda_piratas=dados.get("ajuda_piratas", False),
        )

        # Jornal é consequência, não exposição automática de todo evento.
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

    async def gerar_narracao(self, ctx, acao, ficha, especializacoes, sessao_id):
        mundo = await self.contexto_mundo(acao, ctx.author.id)
        canon = await self.contexto_canonico(ctx, acao)
        participantes_txt = await self.contexto_participantes_sessao(sessao_id, ctx.author.id)
        historico_sessao = await self.historico_compartilhado_sessao(sessao_id)
        sessao_atual = await buscar_sessao_por_id(sessao_id)
        estado_cena_atual = (sessao_atual["estado_cena"] if sessao_atual and "estado_cena" in sessao_atual and sessao_atual["estado_cena"] else "Ainda não consolidado.")
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

SESSÃO MULTIPLAYER — PARTICIPANTES PRESENTES
{participantes_txt}

HISTÓRICO COMPARTILHADO DA SESSÃO
{historico_sessao}

ESTADO TÁTICO PERSISTENTE DA CENA
{estado_cena_atual}
REGRA: fatos deste estado continuam verdadeiros até uma ação resolvida alterá-los.

AÇÃO ATUAL — SOMENTE {ficha['nome']} DECLAROU ESTA AÇÃO
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
REGRA DE TAMANHO DA RESPOSTA
- Resolva SOMENTE o ato atual e as reações/consequências imediatas necessárias.
- Narração normal: normalmente 2 a 5 parágrafos curtos.
- NÃO continue sozinho para uma nova etapa, perseguição inteira, conversa inteira ou segundo ato do jogador.
- Assim que o resultado do ato estiver claro, PARE e devolva a iniciativa ao jogador.

- Esta é uma sessão MULTIPLAYER. Todos os players listados compartilham a mesma realidade e o mesmo histórico.
- SOMENTE o jogador identificado como JOGADOR DA AÇÃO ATUAL pode ter novas ações, falas, ataques, movimentos ou decisões inventariadas a partir do comando atual.
- NUNCA controle outro player presente. Outros players permanecem exatamente no último estado confirmado até que eles próprios usem !acao.
- A ação de um player pode afetar fisicamente outro player quando isso for consequência inevitável e coerente, mas não invente a reação/decisão voluntária do alvo.
- NPCs continuam tendo iniciativa própria e podem agir contra qualquer participante coerentemente presente.
- Não existe limite de tripulação/participantes imposto pelo Narrador; use a lista persistente da sessão.
- Primeiro identifique literalmente o último ato físico que o jogador declarou. Resolva somente esse ato. Não invente movimento, ataque, defesa, fala ou decisão posterior do player.
- Se a ação do jogador for apenas preparação, fala, ameaça ou postura, a consequência concreta deve vir do ambiente/NPCs; o personagem do jogador permanece exatamente no ponto em que sua declaração terminou.
- NPCs presentes possuem iniciativa própria e, diante de hostilidade imediata, DEVEM tomar uma decisão concreta nesta mesma resposta. Não repita apenas mirar, cercar ou reposicionar sem consequência.
- Toda ação física declarada pelo jogador deve receber resultado perceptível NESTA resposta; nunca empurre a resolução dela para o turno seguinte.
- Combate é um estado orgânico da cena; não peça ao jogador para ativar outro sistema ou usar !pronto/!resolver.
- Ao final emita [CONFLITO:SIM] se ainda houver combate, perseguição ou ameaça imediata pendente; caso contrário [CONFLITO:NAO].
- Emita [CENA_ESTADO:resumo factual curto] com posições, ferimentos, contenções, armas, coberturas e ameaças que precisam persistir.
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
- Se e SOMENTE SE um NPC marcante for definitivamente derrotado/incapacitado nesta resposta, emita [NPC_DERROTADO:Nome Exato]. Não use para fuga, empate, ferimento ou ameaça.
- Se a SESSÃO inteira tiver terminado de forma inequívoca (objetivo/conflito encerrado e não há continuação imediata PARA NENHUM participante), termine com [ENCERRAR_SESSAO]. Não use por pausa, silêncio, fim de um único ataque ou porque apenas um jogador terminou sua parte.
- Se o objetivo for encontrar NPC difícil, progresso acumulado deve aproximar o jogador dele; dificuldade não é invisibilidade infinita.
- A resposta deve terminar completa. NUNCA termine no meio de uma frase, oração, diálogo ou ação. Se estiver ficando longa, conclua o acontecimento atual em menos parágrafos em vez de cortar a prosa.
""".strip()

        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=PROMPT_NARRADOR,
            input=entrada,
            max_output_tokens=750,
        )
        narracao = resposta.output_text.strip()
        if not narracao:
            raise RuntimeError("A OpenAI retornou uma narração vazia.")

        morte_player = "[MORTE_PLAYER]" in narracao
        npcs_derrotados = [x.strip() for x in re.findall(r"\[NPC_DERROTADO:([^\]]+)\]", narracao) if x.strip()]
        encerrar_sessao = "[ENCERRAR_SESSAO]" in narracao
        conflito_m = re.search(r"\[CONFLITO:(SIM|NAO)\]", narracao, re.I)
        conflito = (conflito_m.group(1).upper()=="SIM") if conflito_m else None
        estado_m = re.search(r"\[CENA_ESTADO:([^\]]+)\]", narracao, re.I)
        estado_cena = estado_m.group(1).strip() if estado_m else None
        if conflito: encerrar_sessao = False

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
        narracao = re.sub(r"\[ENCERRAR_SESSAO\]", "", narracao)
        narracao = re.sub(r"\[LOCAL_PLAYER:[^\]]+\]", "", narracao)
        narracao = re.sub(r"\[ESTADO_PLAYER:[^\]]+\]", "", narracao)
        narracao = re.sub(r"\[NPC_DERROTADO:[^\]]+\]", "", narracao)
        narracao = re.sub(r"\[CONFLITO:(?:SIM|NAO)\]", "", narracao, flags=re.I)
        narracao = re.sub(r"\[CENA_ESTADO:[^\]]+\]", "", narracao, flags=re.I).strip()
        return narracao, morte_player, mudanca_local, mudanca_estado, encerrar_sessao, npcs_derrotados, conflito, estado_cena

    @commands.command(name="acao", aliases=["ação"])
    @commands.max_concurrency(25, per=commands.BucketType.default, wait=True)
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

            sessao = await buscar_sessao_ativa(ctx.channel.id)
            if not sessao:
                await ctx.send("🎬 Não há narração ativa. Use `!iniciar`: o bot perguntará quantos jogadores participarão.")
                return
            # Rede de segurança: se o watchdog perdeu um ciclo (rede/redeploy), a próxima
            # interação no canal força a resolução vencida antes de aceitar nova ação.
            if sessao['ciclo_deadline']:
                expirados = {int(x['id']) for x in await listar_ciclos_expirados()}
                if int(sessao['id']) in expirados:
                    # Já estamos sob o lock da cena; resolvemos inline sem tentar adquirir o lock novamente.
                    ciclo_vencido = sessao['ciclo_cena']
                    acoes_vencidas = await listar_acoes_cena_sessao(sessao['id'], ciclo_vencido)
                    if acoes_vencidas:
                        participantes_vencidos = await listar_participantes_ciclo(sessao['id'], ciclo_vencido)
                        ids_vencidos = {int(a['user_id']) for a in acoes_vencidas}
                        ausentes_vencidos = [p for p in participantes_vencidos if int(p['user_id']) not in ids_vencidos]
                        await self.resolver_cena_multiplayer(ctx, sessao, acoes_vencidas, timeout=True)
                        for p in ausentes_vencidos:
                            await marcar_participante_sessao(sessao['id'], p['user_id'], 'ausente')
                        if ausentes_vencidos:
                            mencoes = ' '.join(f"<@{p['user_id']}>" for p in ausentes_vencidos)
                            await ctx.send(f"{mencoes} 💤 **Tempo de ação esgotado.** A cena continuou sem travar os demais. Use `!entrar` para voltar.", delete_after=120)
                        sessao = await buscar_sessao_ativa(ctx.channel.id)
                        if not sessao:
                            return
                    else:
                        await limpar_deadline_ciclo(sessao['id'])
            participantes_ativos = await listar_participantes_sessao(sessao["id"], True)
            if ctx.author.id not in {p["user_id"] for p in participantes_ativos}:
                await ctx.send("🎭 Você não entrou nesta narração. Use `!entrar`.")
                return
            esperados = sessao["jogadores_esperados"] or 1
            if not sessao["iniciada"]:
                await ctx.send(f"⏳ Aguardando o grupo: **{len(participantes_ativos)}/{esperados}**. Os demais usam `!entrar`.")
                return

            # Combate agora é estado orgânico da cena. Registros antigos de rodada são
            # encerrados para não criar um segundo jogo paralelo ao !acao.
            combate_legado = await buscar_combate_ativo(sessao["id"])
            if combate_legado:
                await encerrar_combate_sessao(combate_legado["id"])

            ciclo = sessao["ciclo_cena"] if "ciclo_cena" in sessao else 1
            participantes_ciclo = await listar_participantes_ciclo(sessao["id"],ciclo)
            if ctx.author.id not in {p["user_id"] for p in participantes_ciclo}:
                await ctx.send("⏳ Você entrou com um ciclo já em andamento. Aguarde a resolução atual; você participa do próximo.")
                return

            # MULTIPLAYER NORMAL: primeiro coletamos UMA ação de cada participante.
            # Só depois decidimos/resolvemos a cena em conjunto. Isso impede que uma
            # ação agressiva do segundo player desvie para combate antes de incluir o primeiro.
            if len(participantes_ciclo)>1:
                declaradas_antes=await listar_acoes_cena_sessao(sessao["id"],ciclo)
                if ctx.author.id in {a["user_id"] for a in declaradas_antes}:
                    await self.aviso(ctx,f"{ctx.author.mention} ⏳ **{ficha['nome']} já declarou a ação deste ciclo.** Aguarde os demais participantes.")
                    return
                await registrar_acao_cena_sessao(sessao["id"],ciclo,ctx.author.id,ficha["nome"],texto)
                declaradas=await listar_acoes_cena_sessao(sessao["id"],ciclo)
                feitos={a["user_id"] for a in declaradas}
                faltantes=[p for p in participantes_ciclo if p["user_id"] not in feitos]
                if faltantes:
                    await definir_deadline_ciclo(sessao["id"],300)
                    mencoes=" ".join(f"<@{p['user_id']}>" for p in faltantes)
                    nomes=", ".join(p["personagem_nome"] for p in faltantes)
                    await self.aviso(ctx,f"{mencoes} 🎭 **Ação de {ficha['nome']} registrada — {len(feitos)}/{len(participantes_ciclo)}.**\n⏳ Aguardando: **{nomes}**. Vocês têm **5 min desde esta última ação**; cada nova declaração reinicia os 5 min. Use `!passar` para não agir neste ciclo.",segundos=120)
                    return
                try:
                    async with ctx.typing():
                        await self.resolver_cena_multiplayer(ctx,sessao,declaradas)
                except Exception as erro_multi:
                    print(f"❌ ERRO CENA MULTIPLAYER — {type(erro_multi).__name__}: {erro_multi}")
                    await ctx.send("⚠️ Não consegui resolver a cena coletiva agora. As ações já registradas foram preservadas; tente `!resolvercena`.")
                return

            # SOLO também usa o mesmo fluxo narrativo vivo; hostilidade é estado da cena.
            especializacoes = list(await buscar_especializacoes(ctx.author.id))
            try:
                async with ctx.typing():
                    narracao, morte_player, mudanca_local, mudanca_estado, encerrar_sessao_auto, npcs_derrotados, conflito_cena, estado_cena = await self.gerar_narracao(
                        ctx, texto, ficha, especializacoes, sessao["id"]
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
            await registrar_turno_sessao(
                sessao["id"], ctx.author.id, ficha["nome"], texto, narracao
            )
            if conflito_cena is not None or estado_cena:
                await atualizar_estado_cena_sessao(sessao["id"], conflito_cena, estado_cena)
            if conflito_cena is not None and not mudanca_estado:
                loc_now=await buscar_localizacao_jogador(ctx.author.id)
                await definir_estado_jogador(ctx.author.id, (loc_now["estado"] if loc_now and loc_now["estado"] else "livre"), (loc_now["custodia"] if loc_now else None), (loc_now["restricoes"] if loc_now else None), conflito_cena)

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


            # Resposta visível primeiro; memórias, reputação e consequências secundárias vêm depois.
            partes = dividir_mensagem(narracao, limite=3800)
            total_partes = len(partes)
            for indice, parte in enumerate(partes, start=1):
                titulo = "📖 NARRADOR — SEA'S PARADISE"
                if indice > 1:
                    titulo += f" — CONTINUAÇÃO {indice}/{total_partes}"
                embed = discord.Embed(title=titulo, description=parte, color=discord.Color.blue())
                embed.set_footer(text=f"Ação de {ficha['nome']} • Narração automática")
                await ctx.send(embed=embed)


            # Recompensas de NPCs marcantes: uma vez por personagem/NPC no mundo.
            # O marcador só é aceito quando o próprio Narrador confirmou derrota consumada.
            if npcs_derrotados:
                ranks_npc = {
                    'morgan':'D','buggy':'C','kuro':'C','don krieg':'B','arlong':'B',
                    'crocodile':'S','bellamy':'B','enel':'S','rob lucci':'S','gecko moria':'S',
                    'doflamingo':'SS','kaido':'LENDARIO','big mom':'LENDARIO','charlotte linlin':'LENDARIO'
                }
                participantes_reward = await listar_participantes_sessao(sessao['id'], True)
                for npc_nome in npcs_derrotados:
                    key=npc_nome.casefold(); rank=next((r for n,r in ranks_npc.items() if n in key), None)
                    if not rank: continue
                    cfg=BOSS_RANKS[rank]
                    for pp in participantes_reward:
                        uid=pp['user_id']
                        ganhou=await get_pool().fetchrow(
                            "INSERT INTO recompensas_npc_marcante(user_id,npc_nome,instancia) VALUES($1,$2,'mundo') ON CONFLICT DO NOTHING RETURNING user_id",uid,npc_nome)
                        if not ganhou: continue
                        berries=max(500,cfg['berries'][0]//3); pontos=max(1,cfg['pontos'][0]//8); rep=4+list(BOSS_RANKS).index(rank)*4
                        await adicionar_berries(uid,berries); await adicionar_pontos_atributo(uid,pontos); await adicionar_reputacao(uid,rep)
                        try:
                            membro=ctx.guild.get_member(uid) if ctx.guild else None
                            await ctx.send(f"🏆 **NPC MARCANTE DERROTADO — {npc_nome}**\n{membro.mention if membro else pp['personagem_nome']}: ฿ {berries:,} • +{pontos} pontos • +{rep} reputação".replace(',', '.'))
                        except Exception: pass

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

            if mudanca_local and sessao["localizacao"] and mudanca_local[0].casefold() != str(sessao["localizacao"]).casefold():
                await marcar_participante_sessao(sessao["id"], ctx.author.id, "saiu")

            # A morte é confirmada pelo narrador através de um marcador interno.
            # Só depois de salvar a cena/memórias o personagem é resetado.
            if morte_player:
                try:
                    await marcar_participante_sessao(sessao["id"], ctx.author.id, "morto")
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

            if conflito_cena:
                encerrar_sessao_auto=False
            if not encerrar_sessao_auto and not morte_player and not conflito_cena:
                try: encerrar_sessao_auto=await self.deve_encerrar_sessao(sessao["id"],narracao,texto)
                except Exception as ex: print(f"⚠️ Verificador de encerramento: {ex}")

            if encerrar_sessao_auto and not morte_player:
                try:
                    resumo_final = await self.resumo_encerramento_sessao(sessao["id"])
                    encerrada = await encerrar_sessao_narracao(sessao["id"], resumo_final)
                    if encerrada:
                        embed_fim = discord.Embed(
                            title="🏁 FIM DA NARRAÇÃO",
                            description=resumo_final,
                            color=discord.Color.gold()
                        )
                        embed_fim.set_footer(text="Sessão arquivada • recompensas serão tratadas pelo sistema próprio")
                        await ctx.send(embed=embed_fim)
                except Exception as erro_fim:
                    print(f"⚠️ ERRO AO ENCERRAR SESSÃO — {type(erro_fim).__name__}: {erro_fim}")

    @commands.command(name="combate")
    async def combate_info(self,ctx):
        s=await buscar_sessao_ativa(ctx.channel.id)
        if not s: return await ctx.send("📭 Não há sessão ativa.")
        await ctx.send("⚔️ **Combate é dinâmico no Sea's Paradise.** Continue usando `!acao`; ataques, defesas, fugas, perseguições e reações de NPCs são resolvidos dentro da própria cena.")

    @commands.command(name="pronto")
    async def pronto_combate(self,ctx):
        await self.aviso(ctx,"🎭 `!pronto` não é mais necessário. Declare o que seu personagem faz com `!acao`; o conflito é resolvido organicamente pela cena.")

    @commands.command(name="resolver")
    async def resolver_combate(self,ctx):
        await self.aviso(ctx,"🎭 Não existe mais uma rodada separada para resolver. Use `!acao`; a cena resolve quando todos agirem ou o tempo do ciclo acabar.")


    @commands.command(name="iniciar", aliases=["iniciarnarracao", "iniciarnarração"])
    async def iniciar_narracao(self, ctx):
        treino=await buscar_treinamento_ativo(ctx.author.id)
        if treino:
            restante=max(treino['fim_em']-datetime.now(timezone.utc), timedelta(0))
            minutos=max(0,int(restante.total_seconds()//60))
            return await ctx.send(f"🏋️ **PERSONAGEM EM TREINAMENTO**\nVocê está treinando **{treino['alvo']}** e não pode iniciar uma cena.\n⏳ Restam aproximadamente **{minutos//60}h {minutos%60}min**.\nUse `!cancelartreino` para abandonar o treino sem receber recompensa.")
        if await buscar_sessao_ativa(ctx.channel.id):
            await ctx.send("🎬 Já existe narração ativa aqui. Use `!sessao` ou `!encerrar`."); return
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha: await ctx.send("❌ Você ainda não possui ficha ativa."); return
        ok,local_canal,estado=await self.validar_localizacao_do_canal(ctx)
        erro = None if ok else f"🚫 Você está em **{estado['localizacao'] if estado else 'outro local'}**, mas este canal representa **{local_canal}**."
        if not ok: await ctx.send(erro); return
        await ctx.send("🎬 **INICIAR NARRAÇÃO**\nQuantos jogadores vão participar? Envie apenas o número. **Não existe limite fixo.**")
        def check(m): return m.author.id==ctx.author.id and m.channel.id==ctx.channel.id and m.content.strip().isdigit()
        try: msg=await self.bot.wait_for("message",timeout=90,check=check)
        except asyncio.TimeoutError: await ctx.send("⌛ Início cancelado."); return
        qtd=int(msg.content.strip())
        if qtd<1: await ctx.send("❌ Informe pelo menos 1 jogador."); return
        local=estado["localizacao"] if estado else local_canal; area=estado["area"] if estado and estado["area"] else None
        s=await obter_ou_criar_sessao(getattr(ctx.guild,"id",None),ctx.channel.id,local,area)
        s=await configurar_sessao_narracao(s["id"],qtd); await entrar_sessao(s["id"],ctx.author.id,ficha["nome"])
        if qtd==1:
            await marcar_sessao_iniciada(s["id"])
            await ctx.send(f"▶️ **NARRAÇÃO INICIADA — SOLO**\n📍 {local}\nUse `!acao`. Para terminar a aventura, `!encerrar`.")
        else:
            await ctx.send(f"🎭 **Sessão para {qtd} jogadores criada.**\n✅ {ficha['nome']} — **1/{qtd}**\nOs demais usam `!entrar`. Ao chegar em {qtd}/{qtd}, começa automaticamente.")

    @commands.command(name="entrar")
    async def entrar_narracao(self,ctx):
        treino=await buscar_treinamento_ativo(ctx.author.id)
        if treino:
            restante=max(treino['fim_em']-datetime.now(timezone.utc), timedelta(0))
            minutos=max(0,int(restante.total_seconds()//60))
            return await ctx.send(f"🏋️ **PERSONAGEM EM TREINAMENTO**\nVocê está treinando **{treino['alvo']}** e não pode entrar em uma cena.\n⏳ Restam aproximadamente **{minutos//60}h {minutos%60}min**.\nUse `!cancelartreino` para abandonar o treino sem receber recompensa.")
        s=await buscar_sessao_ativa(ctx.channel.id)
        if not s: await ctx.send("📭 Não há sessão. Use `!iniciar`."); return
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha: await ctx.send("❌ Você ainda não possui ficha ativa."); return
        evento_thread=await buscar_evento_por_thread(ctx.channel.id)
        # Tópicos de evento são instâncias especiais: não representam a localização
        # canônica do personagem e portanto não passam pelo portão normal de ilha.
        if not evento_thread:
            ok,local_canal,estado=await self.validar_localizacao_do_canal(ctx)
            erro = None if ok else f"🚫 Você está em **{estado['localizacao'] if estado else 'outro local'}**, mas este canal representa **{local_canal}**."
            if not ok: await ctx.send(erro); return
        if evento_thread:
            antigo=await status_participacao_evento(evento_thread["id"],ctx.author.id)
            if antigo and antigo["status"] in ("concluido","desistiu"):
                await ctx.send("🚫 Você já encerrou sua participação nesta instância e não pode repeti-la."); return
            outro=await evento_ativo_usuario(ctx.author.id)
            if outro and outro["id"]!=evento_thread["id"]:
                await ctx.send("🎯 Você já está em outro evento."); return
            if evento_thread["exclusivo_marinha"] and "marinha" not in (ficha["faccao"] or "").casefold():
                await ctx.send("⚓ Esta missão é exclusiva da Marinha."); return
            await participar_evento_global(evento_thread["id"],ctx.author.id,ficha["nome"])
        ps=await listar_participantes_sessao(s["id"],True)
        if any(p["user_id"]==ctx.author.id for p in ps):
            qtd=s["jogadores_esperados"] or 1
            if not s["iniciada"] and len(ps)>=qtd:
                await marcar_sessao_iniciada(s["id"])
                await ctx.send(f"▶️ **NARRAÇÃO INICIADA — {len(ps)} JOGADOR(ES)**\nUse `!acao`.")
            else:
                await ctx.send("✅ Você já está na sessão.")
            return
        await entrar_sessao(s["id"],ctx.author.id,ficha["nome"])
        ps=await listar_participantes_sessao(s["id"],True); qtd=s["jogadores_esperados"] or 1
        if s["iniciada"]:
            ciclo=s["ciclo_cena"] if "ciclo_cena" in s else 1
            declaradas=await listar_acoes_cena_sessao(s["id"],ciclo)
            inicio=ciclo+1 if declaradas else ciclo
            await definir_inicio_ciclo_participante(s["id"],ctx.author.id,inicio)
            detalhe=(" Participa a partir do **próximo ciclo**." if inicio>ciclo else " Participa do **ciclo atual**.")
            await ctx.send(f"➕ **{ficha['nome']} entrou na narração em andamento.**"+detalhe); return
        if len(ps)>=qtd:
            await marcar_sessao_iniciada(s["id"])
            await ctx.send(f"▶️ **NARRAÇÃO INICIADA — {len(ps)} JOGADORES**\n👥 "+", ".join(p["personagem_nome"] for p in ps)+"\nCada `!acao` entra no ciclo vivo da cena; todos agiram = resolve na hora, ausência por 5 min = a cena continua sem travar.")
        else: await ctx.send(f"✅ **{ficha['nome']} entrou — {len(ps)}/{qtd}.**")

    @commands.command(name="sessao", aliases=["sessão"])
    async def sessao_info(self, ctx):
        sessao = await buscar_sessao_ativa(ctx.channel.id)
        if not sessao:
            await ctx.send("📭 Não há sessão de narração ativa neste canal.")
            return
        participantes = await listar_participantes_sessao(sessao["id"], somente_ativos=True)
        nomes = [f"• **{p['personagem_nome']}**" for p in participantes]
        await ctx.send(
            f"🎭 **Sessão #{sessao['id']} ativa**\n"
            f"📍 {sessao['localizacao'] or 'Local não definido'}\n"
            f"👥 Participantes ativos: **{len(participantes)}**\n"
            + ("\n".join(nomes) if nomes else "Nenhum participante ativo.")
        )

    @commands.command(name="passar", aliases=["passo"])
    async def passar_ciclo(self,ctx):
        sessao=await buscar_sessao_ativa(ctx.channel.id)
        if not sessao or not sessao["iniciada"]:
            return await self.aviso(ctx,"📭 Não há ciclo narrativo ativo para passar.")
        participantes=await listar_participantes_ciclo(sessao["id"],sessao["ciclo_cena"])
        if ctx.author.id not in {p["user_id"] for p in participantes}:
            return await self.aviso(ctx,"🎭 Você não participa deste ciclo.")
        acoes=await listar_acoes_cena_sessao(sessao["id"],sessao["ciclo_cena"])
        if ctx.author.id in {a["user_id"] for a in acoes}:
            return await self.aviso(ctx,"⏳ Você já declarou neste ciclo.")
        ficha=await buscar_ficha(ctx.author.id)
        await registrar_acao_cena_sessao(sessao["id"],sessao["ciclo_cena"],ctx.author.id,ficha["nome"],"[PASSOU O CICLO — nenhuma nova ação voluntária]")
        acoes=await listar_acoes_cena_sessao(sessao["id"],sessao["ciclo_cena"])
        feitos={a["user_id"] for a in acoes}
        faltantes=[p for p in participantes if p["user_id"] not in feitos]
        if faltantes:
            await definir_deadline_ciclo(sessao["id"],300)
            mencoes=" ".join(f"<@{p['user_id']}>" for p in faltantes)
            nomes=", ".join(p["personagem_nome"] for p in faltantes)
            return await self.aviso(ctx,f"{mencoes} ⏭️ **{ficha['nome']} passou.** Aguardando: **{nomes}**. O prazo foi renovado para **5 min**.")
        await limpar_deadline_ciclo(sessao["id"])
        async with ctx.typing():
            await self.resolver_cena_multiplayer(ctx,sessao,acoes)

    @commands.command(name="resolvercena")
    async def resolver_cena_pendente(self,ctx):
        sessao=await buscar_sessao_ativa(ctx.channel.id)
        if not sessao:
            await ctx.send("📭 Não há sessão ativa neste canal."); return
        legado=await buscar_combate_ativo(sessao["id"])
        if legado:
            await encerrar_combate_sessao(legado["id"])
        ciclo=sessao["ciclo_cena"] if "ciclo_cena" in sessao else 1
        participantes=await listar_participantes_ciclo(sessao["id"],ciclo)
        acoes=await listar_acoes_cena_sessao(sessao["id"],ciclo)
        feitos={a["user_id"] for a in acoes}
        faltam=[p["personagem_nome"] for p in participantes if p["user_id"] not in feitos]
        if faltam and acoes:
            await self.aviso(ctx,f"⏩ Resolvendo com quem já agiu. Sem declaração neste ciclo: **{', '.join(faltam)}**.")
        if not acoes:
            await ctx.send("📭 Não há ações pendentes neste ciclo."); return
        try:
            async with ctx.typing():
                await self.resolver_cena_multiplayer(ctx,sessao,acoes)
        except Exception as erro:
            print(f"❌ ERRO !resolvercena — {type(erro).__name__}: {erro}")
            await ctx.send(f"⚠️ A cena coletiva continua pendente. Erro: `{type(erro).__name__}`.")

    @commands.command(name="resumo")
    async def resumo_sessao(self,ctx):
        sessao=await buscar_sessao_ativa(ctx.channel.id)
        if not sessao:
            await ctx.send("📭 Não há sessão ativa neste canal."); return
        turnos=await buscar_turnos_sessao(sessao["id"],limite=100)
        if not turnos:
            await ctx.send("📖 Ainda não há acontecimentos narrados para resumir."); return
        async with ctx.typing(): resumo=await self.resumo_encerramento_sessao(sessao["id"])
        await ctx.send(embed=discord.Embed(title="📖 RESUMO DA NARRAÇÃO",description=resumo,color=discord.Color.gold()))

    @commands.command(name="encerrar")
    @commands.has_permissions(administrator=True)
    async def encerrar_narracao(self, ctx):
        sessao = await buscar_sessao_ativa(ctx.channel.id)
        if not sessao:
            await ctx.send("📭 Não há sessão ativa para encerrar neste canal.")
            return
        participantes=await listar_participantes_sessao(sessao["id"],True)
        conflito=bool(sessao["conflito_ativo"]) if "conflito_ativo" in sessao else False
        if not conflito:
            for pp in participantes:
                loc=await buscar_localizacao_jogador(pp["user_id"])
                if loc and "combate_ativo" in loc and loc["combate_ativo"]:
                    conflito=True; break
        if conflito:
            await self.aviso(ctx,"⚔️ **A cena não pode ser encerrada enquanto existe conflito imediato pendente.** Resolva a situação com `!acao` (fugir, render-se, vencer, ser capturado, negociar etc.). O mundo não congela só porque a sessão foi fechada.",segundos=18)
            return
        async with ctx.typing():
            resumo_final = await self.resumo_encerramento_sessao(sessao["id"])
        encerrada = await encerrar_sessao_narracao(sessao["id"], resumo_final)
        if not encerrada:
            await ctx.send("⚠️ A sessão já foi encerrada.")
            return
        embed = discord.Embed(
            title="🏁 FIM DA NARRAÇÃO",
            description=resumo_final,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Sessão arquivada • pronta para avaliação de recompensas")
        await ctx.send(embed=embed)

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
        # Antes de montar a edição, materializa fatos públicos recentes que ainda não ganharam matéria.
        await sincronizar_noticias_recentes(30)
        noticias = await buscar_noticias_mundo(10)
        if not noticias:
            await ctx.send("📰 Ainda não há notícias relevantes circulando pelo mundo.")
            return
        texto = "\n\n".join(
            f"**{n['manchete']}**\n{n['corpo']}" for n in noticias
        )
        for parte in dividir_mensagem(texto, limite=3800):
            await ctx.send(embed=discord.Embed(
                title="📰 JORNAL ECONÔMICO MUNDIAL",
                description=parte,
                color=discord.Color.gold()
            ))



async def setup(bot):
    await bot.add_cog(Narrador(bot))
