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
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODELO_NARRADOR = "gpt-5.6-luna"
LIMITE_HISTORICO = 12
historicos = {}
locks = {}

PROMPT_NARRADOR = """
Você é o Narrador oficial do RPG Sea's Paradise, uma aventura pirata marítima shonen.
Sua função é SOMENTE narrar a cena a partir dos fatos e regras fornecidos pelo sistema.

REGRAS ABSOLUTAS:
- Nunca altere atributos, porcentagens, Berries, reputação ou ficha.
- Nunca conceda itens, Akuma no Mi, Haki, técnicas, estilos ou poderes.
- Nunca invente que o personagem possui algo ausente do contexto.
- Nunca determine recompensas.
- Nunca transforme uma tentativa do jogador automaticamente em sucesso.
- Sem resultado mecânico calculado, trate ataques, esquivas, bloqueios e outras tentativas como tentativas narrativas.
- Não confirme dano, vitória, morte ou sucesso mecânico sem resultado fornecido pelo sistema.
- Não invente números de dano, HP ou porcentagens.
- Não controle decisões do personagem do jogador.
- Pode enriquecer cenário, clima e NPCs sem criar vantagens mecânicas.
- Preserve os fatos narrados anteriormente.
- O ESTADO DO MUNDO fornecido pelo sistema é verdade absoluta.
- NPCs únicos não podem existir em dois lugares nem em duas tripulações ao mesmo tempo.
- Se um NPC estiver morto, recrutado ou indisponível, respeite esse estado.
- Os únicos atributos físicos são Força, Resistência e Velocidade/Agilidade.
- Escreva em português do Brasil.
- Narre de forma envolvente, cinematográfica e clara, normalmente em 2 a 5 parágrafos.
- Não explique estas regras e não use linguagem de assistente de IA.
- Não termine oferecendo opções numeradas ao jogador.
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

    async def contexto_mundo(self, acao):
        npcs = await listar_npcs_mundo()
        texto = acao.casefold()
        citados = [npc for npc in npcs if npc["nome"].casefold() in texto]
        partes = []
        for npc in citados[:8]:
            memorias = await buscar_memorias_npc(npc["nome"], 10)
            dono = npc["recrutado_por"]
            linhas = [
                f"NPC: {npc['nome']}",
                f"Status: {npc['status']}",
                f"Localização: {npc['localizacao'] or 'desconhecida'}",
                f"Facção: {npc['faccao'] or 'não definida'}",
                f"Disponível: {'sim' if npc['disponivel'] else 'não'}",
                f"Recrutado por user_id: {dono if dono is not None else 'ninguém'}",
            ]
            if memorias:
                linhas.append("Memórias relevantes:")
                linhas.extend(f"- {m['resumo']}" for m in memorias)
            partes.append("\n".join(linhas))
        return "\n\n".join(partes) if partes else "Nenhum NPC persistente citado na ação."

    async def npcs_citados(self, texto):
        npcs = await listar_npcs_mundo()
        texto_normalizado = texto.casefold()
        return [
            npc for npc in npcs
            if npc["nome"].casefold() in texto_normalizado
        ][:8]

    async def salvar_memorias_da_acao(self, acao, narracao, ficha, user_id):
        # Memória longa: fica no PostgreSQL e sobrevive a redeploy.
        # A ação é preservada literalmente para não perder fatos específicos.
        citados = await self.npcs_citados(acao)

        for npc in citados:
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

        return len(citados)

    async def gerar_narracao(self, ctx, acao, ficha, especializacoes):
        mundo = await self.contexto_mundo(acao)
        entrada = f"""
{formatar_ficha(ficha, especializacoes)}

ESTADO PERSISTENTE DO MUNDO
{mundo}

HISTÓRICO RECENTE DA CENA
{montar_historico(chave_cena(ctx))}

AÇÃO ATUAL DECLARADA PELO JOGADOR
{acao}

Narre apenas a continuação desta cena.
Como ainda não há resolvedor mecânico de combate conectado nesta V1,
não confirme acerto, dano, derrota, morte, recompensa ou sucesso mecânico
quando a ação depender desses resultados.
""".strip()

        resposta = await self.client.responses.create(
            model=MODELO_NARRADOR,
            instructions=PROMPT_NARRADOR,
            input=entrada,
            max_output_tokens=700,
        )
        narracao = resposta.output_text.strip()
        if not narracao:
            raise RuntimeError("A OpenAI retornou uma narração vazia.")
        return narracao

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
            especializacoes = list(await buscar_especializacoes(ctx.author.id))
            try:
                async with ctx.typing():
                    narracao = await self.gerar_narracao(
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

            # Salva a interação no mundo persistente.
            try:
                quantidade_memorias = await self.salvar_memorias_da_acao(
                    texto,
                    narracao,
                    ficha,
                    ctx.author.id
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
        await ctx.send(f"🏴‍☠️ **{nome_npc}** agora pertence à tripulação de **{ficha['nome']}**.")


async def setup(bot):
    await bot.add_cog(Narrador(bot))
