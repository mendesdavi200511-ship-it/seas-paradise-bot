import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    criar_ficha,
    deletar_ficha,
    buscar_especializacoes,
    buscar_pontos_percentuais,
    distribuir_atributo,
    distribuir_percentual
)

from views.criacao import (
    criando,
    novo_rascunho,
    criar_embed,
    CriacaoView
)


ATRIBUTO_MAXIMO = 50000


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor):
    return f"{valor:,}".replace(",", ".")


def nome_atributo(atributo):

    nomes = {
        "forca": "Força",
        "resistencia": "Resistência",
        "velocidade": "Velocidade/Agilidade"
    }

    return nomes.get(
        atributo,
        atributo
    )


def emoji_atributo(atributo):

    emojis = {
        "forca": "💪",
        "resistencia": "🛡️",
        "velocidade": "💨"
    }

    return emojis.get(
        atributo,
        "⚔️"
    )


# =========================================================
# EMBED DA FICHA
# =========================================================

async def criar_embed_ficha(
    membro,
    personagem
):

    especializacoes = (
        await buscar_especializacoes(
            membro.id
        )
    )

    pontos_percentuais = (
        await buscar_pontos_percentuais(
            membro.id
        )
    )

    embed = discord.Embed(
        title=(
            f"🏴‍☠️ "
            f"{personagem['nome']}"
        ),
        description=(
            "**Ficha de Personagem — "
            "Sea's Paradise**"
        )
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    # =====================================================
    # IDENTIDADE
    # =====================================================

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Raça:** "
            f"{personagem['raca']}\n"

            f"**Família:** "
            f"{personagem['familia']}\n"

            f"**Facção:** "
            f"{personagem['faccao']}"
        ),
        inline=False
    )

    # =====================================================
    # CAMINHO
    # =====================================================

    embed.add_field(
        name="🧭 Caminho",
        value=(
            f"**Profissão:** "
            f"{personagem['profissao']}\n"

            f"**Classe:** "
            f"{personagem['classe']}"
        ),
        inline=False
    )

    # =====================================================
    # ATRIBUTOS
    # =====================================================

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** "
            f"{formatar_numero(personagem['forca'])}\n"

            f"🛡️ **Resistência:** "
            f"{formatar_numero(personagem['resistencia'])}\n"

            f"💨 **Velocidade/Agilidade:** "
            f"{formatar_numero(personagem['velocidade'])}\n\n"

            f"✨ **Pontos disponíveis:** "
            f"{formatar_numero(personagem['pontos_atributo'])}"
        ),
        inline=False
    )

    # =====================================================
    # ESPECIALIZAÇÕES
    # =====================================================

    if especializacoes:

        categorias = {}

        for item in especializacoes:

            categoria = (
                item["categoria"]
                .strip()
                .lower()
            )

            if categoria not in categorias:
                categorias[categoria] = []

            categorias[categoria].append(
                item
            )

        emojis_categoria = {
            "estilo": "🥋",
            "classe": "⚔️",
            "profissao": "🛠️",
            "haki": "👁️",
            "akuma": "🍈",
            "akuma no mi": "🍈",
            "tecnica": "💥"
        }

        for categoria, itens in categorias.items():

            emoji = emojis_categoria.get(
                categoria,
                "📚"
            )

            linhas = []

            for item in itens:

                linhas.append(
                    f"**{item['nome']}** — "
                    f"{item['porcentagem']}%"
                    f"/{item['limite']}%"
                )

            texto = "\n".join(
                linhas
            )

            if len(texto) > 1024:
                texto = (
                    texto[:1000]
                    + "\n..."
                )

            embed.add_field(
                name=(
                    f"{emoji} "
                    f"{categoria.title()}"
                ),
                value=texto,
                inline=False
            )

    else:

        embed.add_field(
            name="📚 Domínios",
            value=(
                "Nenhuma especialização "
                "desbloqueada."
            ),
            inline=False
        )

    # =====================================================
    # PONTOS %
    # =====================================================

    embed.add_field(
        name="📈 Pontos de Domínio",
        value=(
            f"**{formatar_numero(pontos_percentuais)}%** "
            "disponíveis"
        ),
        inline=False
    )

    # =====================================================
    # ECONOMIA
    # =====================================================

    embed.add_field(
        name="💰 Berries",
        value=(
            f"฿ "
            f"{formatar_numero(personagem['berries'])}"
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=(
            formatar_numero(
                personagem["reputacao"]
            )
        ),
        inline=True
    )

    embed.set_footer(
        text=(
            "Sea's Paradise • "
            f"ID: {membro.id}"
        )
    )

    return embed


# =========================================================
# MODAL DE NOME
# =========================================================

class EditarNomeModal(
    discord.ui.Modal,
    title="Editar Nome"
):

    nome = discord.ui.TextInput(
        label="Novo nome",
        placeholder="Nome do personagem",
        min_length=2,
        max_length=40
    )

    async def on_submit(
        self,
        interaction
    ):

        from database.database import alterar_nome

        await alterar_nome(
            interaction.user.id,
            self.nome.value.strip()
        )

        await interaction.response.send_message(
            "✅ Nome alterado com sucesso.",
            ephemeral=True
        )


# =========================================================
# PAINEL DE EDIÇÃO
# =========================================================

class EditarFichaView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Editar Nome",
        emoji="✏️",
        style=discord.ButtonStyle.primary
    )
    async def editar_nome(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            EditarNomeModal()
        )

    @discord.ui.button(
        label="Atributos",
        emoji="💪",
        style=discord.ButtonStyle.primary
    )
    async def atributos(
        self,
        interaction,
        button
    ):

        await abrir_painel_atributos(
            interaction
        )

    @discord.ui.button(
        label="Domínios",
        emoji="📈",
        style=discord.ButtonStyle.primary
    )
    async def dominios(
        self,
        interaction,
        button
    ):

        await abrir_painel_dominios(
            interaction
        )


# =========================================================
# ATRIBUTOS
# =========================================================

class AtributoSelect(
    discord.ui.Select
):

    def __init__(self):

        super().__init__(
            placeholder=(
                "Escolha o atributo..."
            ),
            options=[
                discord.SelectOption(
                    label="Força",
                    value="forca",
                    emoji="💪"
                ),
                discord.SelectOption(
                    label="Resistência",
                    value="resistencia",
                    emoji="🛡️"
                ),
                discord.SelectOption(
                    label="Velocidade/Agilidade",
                    value="velocidade",
                    emoji="💨"
                )
            ],
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        self.view.atributo = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=(
                await self.view.gerar_embed(
                    interaction.user
                )
            ),
            view=self.view
        )


class QuantidadeAtributoButton(
    discord.ui.Button
):

    def __init__(
        self,
        quantidade
    ):

        super().__init__(
            label=f"+{quantidade}",
            style=discord.ButtonStyle.primary,
            row=1
        )

        self.quantidade = quantidade

    async def callback(
        self,
        interaction
    ):

        view = self.view

        if not view.atributo:

            await interaction.response.send_message(
                "❌ Escolha primeiro "
                "qual atributo deseja aumentar.",
                ephemeral=True
            )

            return

        sucesso = await distribuir_atributo(
            interaction.user.id,
            view.atributo,
            self.quantidade,
            ATRIBUTO_MAXIMO
        )

        if not sucesso:

            await interaction.response.send_message(
                "❌ Não foi possível distribuir "
                "essa quantidade.\n"
                "Verifique seus pontos disponíveis "
                "e o limite do atributo.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=(
                await view.gerar_embed(
                    interaction.user
                )
            ),
            view=view
        )


class AtributosView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.atributo = None

        self.add_item(
            AtributoSelect()
        )

        for quantidade in (
            1,
            5,
            50,
            100,
            300
        ):

            self.add_item(
                QuantidadeAtributoButton(
                    quantidade
                )
            )

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esses atributos pertencem "
                "a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    async def gerar_embed(
        self,
        usuario
    ):

        ficha = await buscar_ficha(
            usuario.id
        )

        if not ficha:

            return discord.Embed(
                title="❌ Ficha não encontrada"
            )

        selecionado = (
            nome_atributo(
                self.atributo
            )
            if self.atributo
            else "Nenhum"
        )

        embed = discord.Embed(
            title="💪 DISTRIBUIÇÃO DE ATRIBUTOS",
            description=(
                "Escolha um atributo e depois "
                "a quantidade de pontos."
            )
        )

        embed.add_field(
            name="⚔️ Atributos",
            value=(
                f"💪 **Força:** "
                f"{formatar_numero(ficha['forca'])}\n"

                f"🛡️ **Resistência:** "
                f"{formatar_numero(ficha['resistencia'])}\n"

                f"💨 **Velocidade/Agilidade:** "
                f"{formatar_numero(ficha['velocidade'])}"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 Selecionado",
            value=selecionado,
            inline=True
        )

        embed.add_field(
            name="✨ Pontos",
            value=(
                formatar_numero(
                    ficha["pontos_atributo"]
                )
            ),
            inline=True
        )

        embed.set_footer(
            text=(
                "Limite: 50.000 "
                "por atributo"
            )
        )

        return embed


async def abrir_painel_atributos(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.send_message(
            "❌ Você ainda não possui ficha.",
            ephemeral=True
        )

        return

    view = AtributosView(
        interaction.user.id
    )

    await interaction.response.edit_message(
        embed=(
            await view.gerar_embed(
                interaction.user
            )
        ),
        view=view
    )


# =========================================================
# DOMÍNIOS
# =========================================================

class DominioSelect(
    discord.ui.Select
):

    def __init__(
        self,
        especializacoes
    ):

        opcoes = []

        for item in especializacoes[:25]:

            opcoes.append(
                discord.SelectOption(
                    label=(
                        item["nome"][:100]
                    ),
                    value=str(
                        item["id"]
                    ),
                    description=(
                        f"{item['categoria'].title()} • "
                        f"{item['porcentagem']}%"
                        f"/{item['limite']}%"
                    )[:100]
                )
            )

        super().__init__(
            placeholder=(
                "Escolha o domínio..."
            ),
            options=opcoes,
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        self.view.especializacao_id = int(
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=(
                await self.view.gerar_embed(
                    interaction.user
                )
            ),
            view=self.view
        )


class QuantidadeDominioButton(
    discord.ui.Button
):

    def __init__(
        self,
        quantidade
    ):

        super().__init__(
            label=f"+{quantidade}%",
            style=discord.ButtonStyle.primary,
            row=1
        )

        self.quantidade = quantidade

    async def callback(
        self,
        interaction
    ):

        view = self.view

        if not view.especializacao_id:

            await interaction.response.send_message(
                "❌ Escolha primeiro "
                "um domínio.",
                ephemeral=True
            )

            return

        sucesso = await distribuir_percentual(
            interaction.user.id,
            view.especializacao_id,
            self.quantidade
        )

        if not sucesso:

            await interaction.response.send_message(
                "❌ Não foi possível distribuir "
                "essa porcentagem.\n"
                "Verifique seus pontos disponíveis "
                "e o limite desse domínio.",
                ephemeral=True
            )

            return

        await view.recarregar()

        await interaction.response.edit_message(
            embed=(
                await view.gerar_embed(
                    interaction.user
                )
            ),
            view=view
        )


class DominiosView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        especializacoes
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id

        self.especializacoes = list(
            especializacoes
        )

        self.especializacao_id = None

        if self.especializacoes:

            self.add_item(
                DominioSelect(
                    self.especializacoes
                )
            )

            for quantidade in (
                1,
                5,
                10,
                25,
                50
            ):

                self.add_item(
                    QuantidadeDominioButton(
                        quantidade
                    )
                )

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    async def recarregar(self):

        self.especializacoes = list(
            await buscar_especializacoes(
                self.dono_id
            )
        )

    async def gerar_embed(
        self,
        usuario
    ):

        pontos = (
            await buscar_pontos_percentuais(
                usuario.id
            )
        )

        embed = discord.Embed(
            title="📈 DOMÍNIOS",
            description=(
                "Distribua os pontos de domínio "
                "que foram concedidos pela administração."
            )
        )

        embed.add_field(
            name="✨ Pontos disponíveis",
            value=(
                f"**{formatar_numero(pontos)}%**"
            ),
            inline=False
        )

        if not self.especializacoes:

            embed.add_field(
                name="🔒 Especializações",
                value=(
                    "Você ainda não possui "
                    "nenhuma especialização desbloqueada."
                ),
                inline=False
            )

            return embed

        linhas = []

        for item in self.especializacoes:

            marcador = ""

            if (
                self.especializacao_id
                == item["id"]
            ):
                marcador = " ➜"

            linhas.append(
                f"**{item['nome']}** — "
                f"{item['porcentagem']}%"
                f"/{item['limite']}%"
                f"{marcador}"
            )

        texto = "\n".join(
            linhas
        )

        if len(texto) > 1024:
            texto = (
                texto[:1000]
                + "\n..."
            )

        embed.add_field(
            name="📚 Seus Domínios",
            value=texto,
            inline=False
        )

        return embed


async def abrir_painel_dominios(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.send_message(
            "❌ Você ainda não possui ficha.",
            ephemeral=True
        )

        return

    especializacoes = (
        await buscar_especializacoes(
            interaction.user.id
        )
    )

    view = DominiosView(
        interaction.user.id,
        especializacoes
    )

    await interaction.response.edit_message(
        embed=(
            await view
