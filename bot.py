import os
import discord

from discord.ext import commands

from database.database import (
    conectar_banco,
    fechar_banco
)


# =========================================================
# CONFIGURAÇÕES
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )


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


    # =====================================================
    # INICIALIZAÇÃO
    # =====================================================

    async def setup_hook(self):

        print(
            "🔄 Conectando ao PostgreSQL..."
        )

        await conectar_banco()

        print(
            "🐘 PostgreSQL conectado!"
        )


        # -----------------------------------------------
        # CARREGAR COGS
        # -----------------------------------------------

        await self.load_extension(
            "cogs.personagem"
        )

        print(
            "📦 Cog personagem carregado!"
        )


    # =====================================================
    # ENCERRAMENTO
    # =====================================================

    async def close(self):

        print(
            "🔌 Encerrando Sea's Paradise..."
        )

        await fechar_banco()

        await super().close()


# =========================================================
# INSTÂNCIA
# =========================================================

bot = SeasParadiseBot()


# =========================================================
# ONLINE
# =========================================================

@bot.event
async def on_ready():

    print("")
    print("=" * 50)

    print(
        f"🏴‍☠️ Sea's Paradise conectado como "
        f"{bot.user}"
    )

    print(
        f"🆔 ID: {bot.user.id}"
    )

    print(
        f"🌊 Servidores: {len(bot.guilds)}"
    )

    print("✅ BOT ONLINE")

    print("=" * 50)
    print("")


# =========================================================
# ERROS DE COMANDO
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return


    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Você não possui permissão "
            "para usar esse comando."
        )

        return


    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Jogador não encontrado."
        )

        return


    print(
        "❌ ERRO EM COMANDO:"
    )

    raise error


# =========================================================
# COMANDOS BÁSICOS
# =========================================================

@bot.command()
async def ping(ctx):

    await ctx.send(
        "🏴‍☠️ **Pong! Sea's Paradise está online!**"
    )


@bot.command()
async def ajuda(ctx):

    embed = discord.Embed(
        title="🏴‍☠️ SEA'S PARADISE",
        description="Sistema oficial do RP"
    )

    embed.add_field(
        name="📜 Personagem",
        value=(
            "`!criar` — Criar personagem\n"
            "`!ficha` — Ver sua ficha\n"
            "`!ficha @usuário` — Ver outra ficha"
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 Sistema",
        value=(
            "`!ping` — Verificar se o bot está online"
        ),
        inline=False
    )

    embed.set_footer(
        text="Sea's Paradise"
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# INICIAR
# =========================================================

bot.run(TOKEN)
