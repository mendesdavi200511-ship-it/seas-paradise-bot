import os
import asyncio
import discord

from discord.ext import commands

from database.database import (
    conectar_banco,
    fechar_banco
)


TOKEN = os.getenv("DISCORD_TOKEN")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# =========================================================
# BOT
# =========================================================

class SeasParadiseBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):

        print("⚙️ Iniciando Sea's Paradise...")

        # =================================================
        # BANCO DE DADOS
        # =================================================

        try:

            await conectar_banco()

            print("🐘 PostgreSQL conectado.")
            print("🧭 Schema persistente verificado/migrado sem apagar progresso.")

        except Exception as erro:

            print(
                "❌ Erro ao conectar ao banco:"
            )

            print(
                f"{type(erro).__name__}: {erro}"
            )

            raise

        # =================================================
        # COGS
        # =================================================

        extensoes = [
            "cogs.personagem",
            "cogs.admin",
            "cogs.narrador",
            "cogs.economia",
            "cogs.treinamento",
            "cogs.mundo",
            "cogs.finalizacao",
            "cogs.progressao"
        ]

        for extensao in extensoes:

            try:

                await self.load_extension(
                    extensao
                )

                print(
                    f"✅ {extensao} carregado."
                )

            except Exception as erro:

                print(
                    f"❌ Erro ao carregar "
                    f"{extensao}:"
                )

                print(
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )

                raise

    async def close(self):

        print(
            "🔌 Encerrando Sea's Paradise..."
        )

        try:

            await fechar_banco()

            print(
                "🐘 PostgreSQL desconectado."
            )

        except Exception as erro:

            print(
                "⚠️ Erro ao fechar banco:"
            )

            print(
                f"{type(erro).__name__}: "
                f"{erro}"
            )

        await super().close()


# =========================================================
# INSTÂNCIA
# =========================================================

bot = SeasParadiseBot()


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print()
    print("=" * 50)
    print("🏴‍☠️ SEA'S PARADISE ONLINE")
    print("=" * 50)

    print(
        f"🤖 Bot: {bot.user}"
    )

    print(
        f"🆔 ID: {bot.user.id}"
    )

    print(
        f"🌊 Servidores: "
        f"{len(bot.guilds)}"
    )

    print(
        f"📜 Comandos carregados: "
        f"{len(bot.commands)}"
    )

    print("=" * 50)
    print()


# =========================================================
# COMANDO — PING
# =========================================================

@bot.command(
    name="ping"
)
async def ping(ctx):

    latencia = round(
        bot.latency * 1000
    )

    await ctx.send(
        f"🏓 Pong! **{latencia}ms**"
    )


# =========================================================
# COMANDO — AJUDA
# =========================================================

@bot.command(name="ajuda", aliases=["help", "comandos"])
async def ajuda(ctx):
    embed=discord.Embed(title="🏴‍☠️ SEA'S PARADISE — GUIA DO JOGADOR",description="Os comandos que você realmente precisa durante a aventura. Use `!` antes do comando.",color=discord.Color.from_rgb(32,104,160))
    embed.add_field(name="👤 Personagem",value="""`!ficha` — sua ficha e progressão
`!poderes` — Haki, Akuma e transformações
`!manual` — manual completo do RP
`!inventario` — itens e saques
`!treinar` / `!treinostatus` — treinamento
`!cancelartreino` — abandonar treino""",inline=False)
    embed.add_field(name="🎭 Narrativa",value="""`!iniciar` — iniciar cena
`!entrar` — entrar em cena multiplayer
`!acao <ação>` — agir
`!pronto` — combate coletivo
`!resumo` — resumo da sessão
`!encerrar` — encerrar cena""",inline=False)
    embed.add_field(name="🌊 Mundo & Navegação",value="""`!ilha [nome]` — informações da ilha
`!explorar` — procurar descobertas/tesouros
`!rotas` / `!viajar <destino>` — navegar
`!viagemstatus` / `!resolverviagem` — viagem
`!navio` / `!repararnavio` — embarcação
`!pescar` — pesca com localização, cooldown e progressão de Pescador
`!tesouro` — usa um Mapa de Tesouro
`!roubar <alvo>` — tentativa de roubo contra NPC/estabelecimento
`!formas` / `!transformar <forma>` — transformações desbloqueadas""",inline=False)
    embed.add_field(name="💰 Economia",value="""`!loja` — comércio local
`!doar <item> @player [qtd]` — doar item
`!procurar-akuma` — busca diária por Akuma
`!tripulacao` — tripulações
`!organizacoes` — organizações
`!alcunhas` — alcunhas conquistadas
`!estaleiro` — comprar embarcação
`!contratar <função> <nome>` — subordinado
`!subordinados` — sua equipe""",inline=False)
    embed.add_field(name="⚔️ Eventos",value="""Use os **botões do mural** para aceitar Missões da Marinha e Bosses.
`!eventostatus` — evento atual
`!desistirevento` — desistir (não poderá repetir a instância)
`!cacadas` — perseguidores ativos
`!bosses` — Bosses locais disponíveis
`!boss <nome>` — enfrentar Boss on-RP
`!bossacao <ação>` — agir contra o Boss local
`!desistirboss` — abandonar confronto""",inline=False)
    embed.add_field(name="🐛 Suporte",value="`!report <descrição>` — abre um tópico de acompanhamento com a equipe.",inline=False)
    embed.set_footer(text="Sea's Paradise • o mundo continua mesmo sem staff online")
    await ctx.send(embed=embed)


# =========================================================
# ERROS DE COMANDO
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    # =====================================================
    # COMANDO NÃO EXISTE
    # =====================================================

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    # =====================================================
    # SEM PERMISSÃO
    # =====================================================

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Você não possui permissão "
            "para usar esse comando."
        )

        return

    # =====================================================
    # USUÁRIO NÃO ENCONTRADO
    # =====================================================

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Não encontrei esse usuário."
        )

        return

    # =====================================================
    # ARGUMENTO FALTANDO
    # =====================================================

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Está faltando uma informação "
            "nesse comando."
        )

        return

    # =====================================================
    # ARGUMENTO INVÁLIDO
    # =====================================================

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Alguma informação enviada "
            "nesse comando é inválida."
        )

        return

    # =====================================================
    # ERRO INTERNO
    # =====================================================

    erro_original = getattr(
        error,
        "original",
        error
    )

    print()
    print("=" * 50)

    print(
        f"❌ ERRO NO COMANDO: "
        f"{ctx.command}"
    )

    print(
        f"Tipo: "
        f"{type(erro_original).__name__}"
    )

    print(
        f"Erro: "
        f"{erro_original}"
    )

    print("=" * 50)
    print()

    await ctx.send(
        "⚠️ Ocorreu um erro interno "
        "ao executar esse comando."
    )


# =========================================================
# INICIAR BOT
# =========================================================

async def main():

    # =====================================================
    # TOKEN
    # =====================================================

    if not TOKEN:

        raise RuntimeError(
            "DISCORD_TOKEN não foi configurado."
        )

    # =====================================================
    # EXECUTAR
    # =====================================================

    async with bot:

        await bot.start(
            TOKEN
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 Sea's Paradise encerrado."
        )
