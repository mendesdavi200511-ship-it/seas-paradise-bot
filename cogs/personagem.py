import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    criar_ficha,
    deletar_ficha,
    buscar_especializacoes
)

from views.criacao import (
    criando,
    novo_rascunho,
    criar_embed,
    CriacaoView
)


# =========================================================
# BOTÃO DE CONFIRMAÇÃO
# =========================================================

class ConfirmarCriacaoView(CriacaoView):

    def __init__(self, dono_id):
        super().__init__(dono_id)

    @discord.ui.button(
        label="Confirmar Personagem",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def confirmar(
        self,
        interaction,
        button
    ):
        user_id = interaction.user.id
        dados = criando.get(user_id)

        if not dados:
            await interaction.response.send_message(
                "❌ Sua criação expirou. Use `!criar` novamente.",
                ephemeral=True
            )
            return

        if not dados["nome"]:
            await interaction.response.send_message(
                "❌ Defina o **nome do personagem** primeiro.",
                ephemeral=True
            )
            return

        if dados["raca"] == "Não definida":
            await interaction.response.send_message(
                "❌ Escolha sua **raça** primeiro.",
                ephemeral=True
            )
            return

        if dados["familia"] == "Não definida":
            await interaction.response.send_message(
                "❌ Escolha sua **família** primeiro.",
                ephemeral=True
            )
            return

        if dados["profissao"] == "Nenhuma":
            await interaction.response.send_message(
                "❌ Escolha sua **profissão** primeiro.",
                ephemeral=True
            )
            return

        if dados["classe"] == "Nenhuma":
            await interaction.response.send_message(
                "❌ Escolha sua **classe** primeiro.",
                ephemeral=True
            )
            return

        if dados["pontos"] > 0:
            await interaction.response.send_message(
                f"❌ Você ainda possui **{dados['pontos']:,} "
                "pontos de atributo** para distribuir.",
                ephemeral=True
            )
            return

        if await possui_ficha(user_id):
            await interaction.response.send_message(
                "❌ Você já possui uma ficha registrada.",
                ephemeral=True
            )
            return

        ficha = {
            "user_id": user_id,
            "nome": dados["nome"],
            "raca": dados["raca"],
            "familia": dados["familia"],
            "faccao": dados["faccao"],
            "profissao": dados["profissao"],
            "classe": dados["classe"],

            "forca": dados["forca"],
            "resistencia": dados["resistencia"],
            "velocidade": dados["velocidade"],

            "pontos_atributo": 0,
            "pontos_porcentagem": 0,

            "berries": 0,
            "reputacao": 0
        }

        await criar_ficha(ficha)

        nome = dados["nome"]

        criando.pop(user_id, None)

        embed = discord.Embed(
            title="🏴‍☠️ PERSONAGEM CRIADO!",
            description=(
                f"**{nome}** entrou oficialmente no mundo de "
                "**Sea's Paradise**."
            )
        )

        embed.add_field(
            name="📜 Próximo passo",
            value="Use `!ficha` para visualizar seu personagem.",
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )


# =========================================================
# COG
# =========================================================

class Personagem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # CRIAR
    # =====================================================

    @commands.command()
    async def criar(self, ctx):

        if await possui_ficha(ctx.author.id):
            await ctx.send(
                "❌ Você já possui um personagem registrado.\n"
                "Use `!ficha` para visualizá-lo."
            )
            return

        criando[ctx.author.id] = novo_rascunho()

        await ctx.send(
            embed=criar_embed(ctx.author),
            view=ConfirmarCriacaoView(ctx.author.id)
        )

    # =====================================================
    # FICHA
    # =====================================================

    @commands.command()
    async def ficha(
        self,
        ctx,
        membro: discord.Member = None
    ):

        membro = membro or ctx.author

        personagem = await buscar_ficha(membro.id)

        if not personagem:
            await ctx.send(
                f"❌ {membro.mention} ainda não possui personagem.\n"
                "Use `!criar` para criar uma ficha."
            )
            return

        especializacoes = await buscar_especializacoes(
            membro.id
        )

        embed = discord.Embed(
            title=f"🏴‍☠️ {personagem['nome']}",
            description=(
                "**Ficha de Personagem — Sea's Paradise**"
            )
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.add_field(
            name="👤 Identidade",
            value=(
                f"**Raça:** {personagem['raca']}\n"
                f"**Família:** {personagem['familia']}\n"
                f"**Facção:** {personagem['faccao']}"
            ),
            inline=False
        )

        embed.add_field(
            name="🧭 Caminho",
            value=(
                f"**Profissão:** {personagem['profissao']}\n"
                f"**Classe:** {personagem['classe']}"
            ),
            inline=False
        )

        embed.add_field(
            name="⚔️ Atributos",
            value=(
                f"💪 **Força:** "
                f"{personagem['forca']:,}\n"

                f"🛡️ **Resistência:** "
                f"{personagem['resistencia']:,}\n"

                f"💨 **Velocidade/Agilidade:** "
                f"{personagem['velocidade']:,}\n\n"

                f"✨ **Pontos disponíveis:** "
                f"{personagem['pontos_atributo']:,}"
            ),
            inline=False
        )

        # =================================================
        # ESPECIALIZAÇÕES
        # =================================================

        if especializacoes:

            linhas = []

            for item in especializacoes:

                despertar = ""

                if item["despertar"]:
                    despertar = " 🌟"

                linhas.append(
                    f"**{item['tipo'].title()} • "
                    f"{item['nome']}** — "
                    f"{item['porcentagem']}%"
                    f"{despertar}"
                )

            texto = "\n".join(linhas)

            # Proteção contra limite do campo do Discord.
            if len(texto) > 1024:
                texto = texto[:1000] + "\n..."

            embed.add_field(
                name="📚 Especializações",
                value=texto,
                inline=False
            )

        else:

            embed.add_field(
                name="📚 Especializações",
                value="Nenhuma especialização adquirida.",
                inline=False
            )

        embed.add_field(
            name="📈 Pontos de domínio",
            value=(
                f"**{personagem['pontos_porcentagem']:,}%** "
                "disponíveis"
            ),
            inline=False
        )

        embed.add_field(
            name="💰 Berries",
            value=f"฿ {personagem['berries']:,}",
            inline=True
        )

        embed.add_field(
            name="⭐ Reputação",
            value=f"{personagem['reputacao']:,}",
            inline=True
        )

        embed.set_footer(
            text=(
                f"Sea's Paradise • "
                f"ID: {membro.id}"
            )
        )

        await ctx.send(embed=embed)

    # =====================================================
    # RESET DE TESTE
    # =====================================================

    @commands.command()
    @commands.has_permissions(
        administrator=True
    )
    async def resetarficha(
        self,
        ctx,
        membro: discord.Member = None
    ):

        membro = membro or ctx.author

        resultado = await deletar_ficha(
            membro.id
        )

        criando.pop(
            membro.id,
            None
        )

        if resultado == "DELETE 0":

            await ctx.send(
                f"❌ {membro.mention} "
                "não possui ficha registrada."
            )

            return

        await ctx.send(
            f"🗑️ A ficha de "
            f"{membro.mention} foi resetada."
        )


# =========================================================
# CARREGAR COG
# =========================================================

async def setup(bot):
    await bot.add_cog(
        Personagem(bot)
      ) 
