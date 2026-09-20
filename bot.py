import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==========================================
# SEAS PARADISE
# Sistema de RP
# ==========================================


@bot.event
async def on_ready():
    print(f"🏴‍☠️ Seas Paradise conectado como {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Bot online!")


# ==========================================
# TESTE
# ==========================================

@bot.command()
async def ping(ctx):
    await ctx.send("🏴‍☠️ **Pong! Seas Paradise está online!**")


# ==========================================
# FICHAS - versão inicial
# ==========================================

fichas = {}


@bot.command()
async def registrar(ctx, *, nome=None):

    if nome is None:
        await ctx.send(
            "❌ Informe o nome do personagem.\n"
            "Exemplo: `!registrar Monkey D. Luffy`"
        )
        return

    user_id = ctx.author.id

    if user_id in fichas:
        await ctx.send(
            "❌ Você já possui um personagem registrado."
        )
        return

    fichas[user_id] = {
        "nome": nome,
        "raca": "Não definida",
        "faccao": "Civil",
        "profissao": "Nenhuma",
        "classe": "Nenhuma",

        "forca": 0,
        "resistencia": 0,
        "velocidade": 0,

        "berries": 0,
        "reputacao": 0
    }

    embed = discord.Embed(
        title="🏴‍☠️ PERSONAGEM REGISTRADO",
        description=(
            f"**{nome}** entrou oficialmente "
            "no mundo de **Sea's Paradise**!"
        )
    )

    embed.add_field(
        name="👤 Jogador",
        value=ctx.author.mention,
        inline=False
    )

    embed.add_field(
        name="📜 Próximo passo",
        value="Use `!ficha` para visualizar seu personagem.",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# VISUALIZAR FICHA
# ==========================================

@bot.command()
async def ficha(ctx, membro: discord.Member = None):

    membro = membro or ctx.author

    user_id = membro.id

    if user_id not in fichas:
        await ctx.send(
            f"❌ {membro.mention} ainda não possui personagem.\n"
            "Use `!registrar Nome do Personagem`."
        )
        return

    personagem = fichas[user_id]

    embed = discord.Embed(
        title=f"🏴‍☠️ {personagem['nome']}",
        description="**Ficha de Personagem — Sea's Paradise**"
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="🌊 Informações",
        value=(
            f"**Raça:** {personagem['raca']}\n"
            f"**Facção:** {personagem['faccao']}\n"
            f"**Profissão:** {personagem['profissao']}\n"
            f"**Classe:** {personagem['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"**Força:** {personagem['forca']:,}\n"
            f"**Resistência:** {personagem['resistencia']:,}\n"
            f"**Velocidade/Agilidade:** "
            f"{personagem['velocidade']:,}"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 Economia",
        value=f"**Berries:** ฿ {personagem['berries']:,}",
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=f"{personagem['reputacao']:,}",
        inline=True
    )

    embed.set_footer(
        text=f"Sea's Paradise • ID do jogador: {membro.id}"
    )

    await ctx.send(embed=embed)


# ==========================================
# AJUDA
# ==========================================

@bot.command()
async def ajuda(ctx):

    embed = discord.Embed(
        title="🏴‍☠️ SEA'S PARADISE",
        description="Sistema oficial do RP"
    )

    embed.add_field(
        name="📜 Personagem",
        value=(
            "`!registrar Nome` — Cria seu personagem\n"
            "`!ficha` — Mostra sua ficha\n"
            "`!ficha @usuário` — Mostra a ficha de outro jogador"
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 Sistema",
        value="`!ping` — Testa se o bot está online",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# INICIAR BOT
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
