import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    adicionar_pontos_atributo,
    adicionar_pontos_percentuais,
    adicionar_especializacao,
    remover_especializacao,
    adicionar_berries,
    adicionar_reputacao,
    buscar_especializacoes,
)


# =========================================================
# FUNÇÕES
# =========================================================

def formatar_numero(valor):
    return f"{valor:,}".replace(",", ".")


async def verificar_jogador(interaction, user_id):
    if not await possui_ficha(user_id):
        await interaction.response.send_message(
            "❌ Esse jogador não possui ficha.",
            ephemeral=True
        )
        return False

    return True


# =========================================================
# EMBED ADMIN
# =========================================================

async def criar_embed_admin(membro):

    ficha = await buscar_ficha(membro.id)

    if not ficha:
        return discord.Embed(
            title="❌ Ficha não encontrada",
            description=f"{membro.mention} ainda não possui personagem."
        )

    especializacoes = await buscar_especializacoes(
        membro.id
    )

    embed = discord.Embed(
        title="👑 PAINEL ADMINISTRATIVO",
        description=(
            f"Gerenciando **{ficha['nome']}**\n"
            f"Jogador: {membro.mention}"
        )
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 Força: **{formatar_numero(ficha['forca'])}**\n"
            f"🛡️ Resistência: "
            f"**{formatar_numero(ficha['resistencia'])}**\n"
            f"💨 Velocidade/Agilidade: "
            f"**{formatar_numero(ficha['velocidade'])}**\n\n"
            f"✨ Pontos disponíveis: "
            f"**{formatar_numero(ficha['pontos_atributo'])}**"
        ),
        inline=False
    )

    embed.add_field(
        name="📚 Especializações",
        value=(
            f"**{len(especializacoes)}** desbloqueadas"
        ),
        inline=True
    )

    embed.add_field(
        name="💰 Berries",
        value=f"฿ {formatar_numero(ficha['berries'])}",
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=formatar_numero(ficha["reputacao"]),
        inline=True
    )

    embed.set_footer(
        text="Sea's Paradise • Administração"
    )

    return embed


# =========================================================
# MODAL — PONTOS DE ATRIBUTO
# =========================================================

class PontosAtributoModal(
    discord.ui.Modal,
    title="Dar Pontos de Atributo"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 300",
        min_length=1,
        max_length=8
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(self, interaction):

        try:
            quantidade = int(
                self.quantidade.value
            )

            if quantidade <= 0:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "❌ Digite uma quantidade válida.",
                ephemeral=True
            )
            return

        await adicionar_pontos_atributo(
            self.membro.id,
            quantidade
        )

        await interaction.response.send_message(
            f"✨ **{formatar_numero(quantidade)} pontos** "
            f"de atributo adicionados para "
            f"{self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# MODAL — PONTOS %
# =========================================================

class PontosPercentuaisModal(
    discord.ui.Modal,
    title="Dar Pontos de Domínio"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade de %",
        placeholder="Ex: 50",
        min_length=1,
        max_length=8
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(self, interaction):

        try:
            quantidade = int(
                self.quantidade.value
            )

            if quantidade <= 0:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "❌ Digite uma quantidade válida.",
                ephemeral=True
            )
            return

        await adicionar_pontos_percentuais(
            self.membro.id,
            quantidade
        )

        await interaction.response.send_message(
            f"📈 **{formatar_numero(quantidade)}%** "
            f"adicionados para {self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# MODAL — ESPECIALIZAÇÃO
# =========================================================

class EspecializacaoModal(discord.ui.Modal):

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Ex: Ittoryu",
        min_length=2,
        max_length=100
    )

    limite = discord.ui.TextInput(
        label="Limite de domínio (%)",
        placeholder="200",
        default="200",
        min_length=1,
        max_length=4
    )

    def __init__(
        self,
        membro,
        categoria
    ):

        self.membro = membro
        self.categoria = categoria

        titulo = (
            f"Adicionar {categoria.title()}"
        )

        super().__init__(
            title=titulo[:45]
        )

    async def on_submit(self, interaction):

        nome = self.nome.value.strip()

        try:
            limite = int(
                self.limite.value
            )

            if limite <= 0:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "❌ O limite precisa ser um número válido.",
                ephemeral=True
            )
            return

        resultado = await adicionar_especializacao(
            user_id=self.membro.id,
            categoria=self.categoria,
            nome=nome,
            limite=limite,
            desbloqueado_por=str(
                interaction.user.id
            )
        )

        if resultado == "INSERT 0 0":
            await interaction.response.send_message(
                f"⚠️ **{nome}** já está desbloqueado "
                f"para {self.membro.mention}.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ **{nome}** foi desbloqueado para "
            f"{self.membro.mention}.\n"
            f"📈 Limite: **{limite}%**",
            ephemeral=True
        )


# =========================================================
# MODAL — REMOVER ESPECIALIZAÇÃO
# =========================================================

class RemoverEspecializacaoModal(
    discord.ui.Modal,
    title="Remover Especialização"
):

    categoria = discord.ui.TextInput(
        label="Categoria",
        placeholder="Ex: estilo"
    )

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Ex: Ittoryu"
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(self, interaction):

        categoria = (
            self.categoria.value
            .strip()
            .lower()
        )

        nome = self.nome.value.strip()

        resultado = await remover_especializacao(
            self.membro.id,
            categoria,
            nome
        )

        if resultado == "DELETE 0":
            await interaction.response.send_message(
                "❌ Essa especialização não foi encontrada.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"🗑️ **{nome}** removido de "
            f"{self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# MODAL — BERRIES
# =========================================================

class BerriesModal(
    discord.ui.Modal,
    title="Alterar Berries"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 100000 ou -50000",
        min_length=1,
        max_length=20
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(self, interaction):

        try:
            quantidade = int(
                self.quantidade.value
            )

        except ValueError:
            await interaction.response.send_message(
                "❌ Digite um número válido.",
                ephemeral=True
            )
            return

        await adicionar_berries(
            self.membro.id,
            quantidade
        )

        sinal = "+" if quantidade >= 0 else ""

        await interaction.response.send_message(
            f"💰 Berries de {self.membro.mention}: "
            f"**{sinal}{formatar_numero(quantidade)}**",
            ephemeral=True
        )


# =========================================================
# MODAL — REPUTAÇÃO
# =========================================================

class ReputacaoModal(
    discord.ui.Modal,
    title="Alterar Reputação"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 100 ou -50",
        min_length=1,
        max_length=15
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(self, interaction):

        try:
            quantidade = int(
                self.quantidade.value
            )

        except ValueError:
            await interaction.response.send_message(
                "❌ Digite um número válido.",
                ephemeral=True
            )
            return

        await adicionar_reputacao(
            self.membro.id,
            quantidade
        )

        sinal = "+" if quantidade >= 0 else ""

        await interaction.response.send_message(
            f"⭐ Reputação de {self.membro.mention}: "
            f"**{sinal}{formatar_numero(quantidade)}**",
            ephemeral=True
        )


# =========================================================
# MENU DE ESPECIALIZAÇÕES
# =========================================================

class EspecializacaoSelect(
    discord.ui.Select
):

    def __init__(self, membro):

        self.membro = membro

        opcoes = [
            discord.SelectOption(
                label="Classe",
                value="classe",
                emoji="⚔️",
                description="Adicionar uma classe."
            ),
            discord.SelectOption(
                label="Estilo",
                value="estilo",
                emoji="🥋",
                description="Adicionar um estilo de luta."
            ),
            discord.SelectOption(
                label="Profissão",
                value="profissao",
                emoji="🛠️",
                description="Adicionar uma profissão."
            ),
            discord.SelectOption(
                label="Haki",
                value="haki",
                emoji="👁️",
                description="Adicionar um tipo de Haki."
            ),
            discord.SelectOption(
                label="Akuma no Mi",
                value="akuma",
                emoji="🍈",
                description="Adicionar uma Akuma no Mi."
            ),
            discord.SelectOption(
                label="Despertar",
                value="despertar",
                emoji="🌟",
                description="Liberar um despertar."
            )
        ]

        super().__init__(
            placeholder="O que deseja desbloquear?",
            options=opcoes
        )

    async def callback(self, interaction):

        categoria = self.values[0]

        await interaction.response.send_modal(
            EspecializacaoModal(
                self.membro,
                categoria
            )
        )


class EspecializacoesAdminView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        membro
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.membro = membro

        self.add_item(
            EspecializacaoSelect(
                membro
            )
        )

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse painel pertence a outro administrador.",
                ephemeral=True
            )
            return False

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar esse painel.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        label="Remover",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        row=1
    )
    async def remover(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            RemoverEspecializacaoModal(
                self.membro
            )
        )


# =========================================================
# PAINEL PRINCIPAL ADMIN
# =========================================================

class AdminView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        membro
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.membro = membro

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse painel pertence a outro administrador.",
                ephemeral=True
            )
            return False

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar esse painel.",
                ephemeral=True
            )
            return False

        return True

    # ROW 0

    @discord.ui.button(
        label="Pontos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def pontos(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            PontosAtributoModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Pontos %",
        emoji="📈",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def pontos_percentuais(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            PontosPercentuaisModal(
                self.membro
            )
        )

    # ROW 1

    @discord.ui.button(
        label="Especializações",
        emoji="📚",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def especializacoes(
        self,
        interaction,
        button
    ):

        embed = discord.Embed(
            title="📚 ESPECIALIZAÇÕES",
            description=(
                f"Gerenciando {self.membro.mention}\n\n"
                "Escolha a categoria que deseja desbloquear."
            )
        )

        await interaction.response.edit_message(
            embed=embed,
            view=EspecializacoesAdminView(
                self.dono_id,
                self.membro
            )
        )

    # ROW 2

    @discord.ui.button(
        label="Berries",
        emoji="💰",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def berries(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            BerriesModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Reputação",
        emoji="⭐",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def reputacao(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            ReputacaoModal(
                self.membro
            )
        )

    # ROW 3

    @discord.ui.button(
        label="Atualizar",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def atualizar(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=(
                await criar_embed_admin(
                    self.membro
                )
            ),
            view=AdminView(
                self.dono_id,
                self.membro
            )
        )


# =========================================================
# COG
# =========================================================

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # !ADMIN
    # =====================================================

    @commands.command()
    @commands.has_permissions(
        administrator=True
    )
    async def admin(
        self,
        ctx,
        membro: discord.Member = None
    ):

        if membro is None:
            await ctx.send(
                "❌ Use:\n"
                "`!admin @jogador`"
            )
            return

        if not await possui_ficha(
            membro.id
        ):
            await ctx.send(
                f"❌ {membro.mention} "
                "não possui ficha."
            )
            return

        embed = await criar_embed_admin(
            membro
        )

        await ctx.send(
            embed=embed,
            view=AdminView(
                ctx.author.id,
                membro
            )
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(
        Admin(bot)
      )
