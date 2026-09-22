import os
import asyncio
import discord
from discord.ext import commands
from openai import AsyncOpenAI

from database.database import buscar_ficha, buscar_especializacoes

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

    async def gerar_narracao(self, ctx, acao, ficha, especializacoes):
        entrada = f"""
{formatar_ficha(ficha, especializacoes)}

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

async def setup(bot):
    await bot.add_cog(Narrador(bot))
