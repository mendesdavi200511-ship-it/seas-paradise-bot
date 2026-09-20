import discord

from data.racas import RACAS
from data.familias import FAMILIAS
from data.profissoes import PROFISSOES
from data.classes import CLASSES


# =========================================================
# RASCUNHOS DE CRIAÇÃO
# =========================================================

criando = {}

PONTOS_INICIAIS = 100


def novo_rascunho():
    return {
        "nome": None,
        "raca": "Não definida",
        "familia": "Não definida",
        "faccao": "Civil",
        "profissao": "Nenhuma",
        "classe": "Nenhuma",

        "forca": 0,
        "resistencia": 0,
        "velocidade": 0,

        "pontos": PONTOS_INICIAIS
    }


# =========================================================
# EMBED PRINCIPAL
# =========================================================

def criar_embed(usuario):
    dados = criando.get(usuario.id)

    if not dados:
        return discord.Embed(
            title="❌ Criação encerrada",
            description="Use `!criar` para começar novamente."
        )

    embed = discord.Embed(
        title="🏴‍☠️ CRIAÇÃO DE PERSONAGEM",
        description=(
            "Monte seu personagem para entrar no mundo de "
            "**Sea's Paradise**."
        )
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Nome:** {dados['nome'] or 'Não definido'}\n"
            f"**Raça:** {dados['raca']}\n"
            f"**Família:** {dados['familia']}"
        ),
        inline=False
    )

    embed.add_field(
        name="🌊 Caminho",
        value=(
            f"**Facção:** {dados['faccao']}\n"
            f"**Profissão:** {dados['profissao']}\n"
            f"**Classe:** {dados['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** {dados['forca']:,}\n"
            f"🛡️ **Resistência:** {dados['resistencia']:,}\n"
            f"💨 **Velocidade/Agilidade:** "
            f"{dados['velocidade']:,}\n\n"
            f"✨ **Pontos disponíveis:** "
            f"{dados['pontos']:,}"
        ),
        inline=False
    )

    embed.set_footer(
        text="Sea's Paradise • Criação de Personagem"
    )

    return embed


# =========================================================
# NOME
# =========================================================

class NomeModal(
    discord.ui.Modal,
    title="Nome do Personagem"
):

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Ex: Monkey D. Luffy",
        min_length=2,
        max_length=40
    )

    async def on_submit(self, interaction):
        dados = criando.get(interaction.user.id)

        if not dados:
            await interaction.response.send_message(
                "❌ Sua criação não está mais ativa.",
                ephemeral=True
            )
            return

        dados["nome"] = self.nome.value.strip()

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(interaction.user.id)
        )


# =========================================================
# SELECT GENÉRICO
# =========================================================

class CatalogoSelect(discord.ui.Select):

    def __init__(
        self,
        dono_id,
        campo,
        catalogo,
        placeholder
    ):
        self.dono_id = dono_id
        self.campo = campo

        opcoes = []

        # Discord permite no máximo 25 opções por Select.
        for nome, dados in list(catalogo.items())[:25]:

            emoji = None

            if isinstance(dados, dict):
                emoji = dados.get("emoji")

            opcoes.append(
                discord.SelectOption(
                    label=str(nome)[:100],
                    value=str(nome)[:100],
                    emoji=emoji
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=opcoes
        )

    async def callback(self, interaction):
        dados = criando.get(interaction.user.id)

        if not dados:
            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )
            return

        dados[self.campo] = self.values[0]

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(self.dono_id)
        )


# =========================================================
# VIEW GENÉRICA DE CATÁLOGO
# =========================================================

class CatalogoView(discord.ui.View):

    def __init__(
        self,
        dono_id,
        campo,
        catalogo,
        placeholder
    ):
        super().__init__(timeout=180)

        self.dono_id = dono_id

        self.add_item(
            CatalogoSelect(
                dono_id,
                campo,
                catalogo,
                placeholder
            )
        )

    async def interaction_check(
        self,
        interaction
    ):
        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse menu pertence a outro jogador.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def voltar(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(self.dono_id)
        )


# =========================================================
# FACÇÕES
# =========================================================

FACCOES = {
    "Pirata": "🏴‍☠️",
    "Marinha": "⚓",
    "Revolucionário": "🔥",
    "Civil": "🏝️"
}


class FaccaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label=nome,
                value=nome,
                emoji=emoji
            )
            for nome, emoji in FACCOES.items()
        ]

        super().__init__(
            placeholder="Escolha sua facção...",
            options=opcoes
        )

    async def callback(self, interaction):
        dados = criando.get(interaction.user.id)

        if not dados:
            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )
            return

        dados["faccao"] = self.values[0]

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(interaction.user.id)
        )


class FaccaoView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=180)

        self.dono_id = dono_id
        self.add_item(FaccaoSelect())

    async def interaction_check(
        self,
        interaction
    ):
        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse menu pertence a outro jogador.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def voltar(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(self.dono_id)
        )


# =========================================================
# ATRIBUTOS DURANTE A CRIAÇÃO
# =========================================================

class CriacaoAtributosView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=300)

        self.dono_id = dono_id
        self.atributo = "forca"

        self.add_item(
            CriacaoAtributoSelect()
        )

        for quantidade in [
            1,
            5,
            50,
            100,
            300
        ]:
            self.add_item(
                CriacaoQuantidadeButton(
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

    @discord.ui.button(
        label="Resetar",
        emoji="♻️",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def resetar(
        self,
        interaction,
        button
    ):
        dados = criando[interaction.user.id]

        total = (
            dados["forca"]
            + dados["resistencia"]
            + dados["velocidade"]
            + dados["pontos"]
        )

        dados["forca"] = 0
        dados["resistencia"] = 0
        dados["velocidade"] = 0
        dados["pontos"] = total

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoAtributosView(
                self.dono_id
            )
        )

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def voltar(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(self.dono_id)
        )


class CriacaoAtributoSelect(
    discord.ui.Select
):

    def __init__(self):
        super().__init__(
            placeholder="Escolha o atributo...",
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
        self.view.atributo = self.values[0]

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=self.view
        )


class CriacaoQuantidadeButton(
    discord.ui.Button
):

    def __init__(self, quantidade):
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
        dados = criando[interaction.user.id]

        if dados["pontos"] < self.quantidade:
            await interaction.response.send_message(
                "❌ Pontos insuficientes.",
                ephemeral=True
            )
            return

        atributo = view.atributo

        if (
            dados[atributo]
            + self.quantidade
            > 50000
        ):
            await interaction.response.send_message(
                "❌ O limite do atributo é **50.000**.",
                ephemeral=True
            )
            return

        dados[atributo] += self.quantidade
        dados["pontos"] -= self.quantidade

        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=view
        )


# =========================================================
# PAINEL PRINCIPAL
# =========================================================

class CriacaoView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=600)

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
        label="Nome",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def nome(
        self,
        interaction,
        button
    ):
        await interaction.response.send_modal(
            NomeModal()
        )

    @discord.ui.button(
        label="Raça",
        emoji="🧬",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def raca(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CatalogoView(
                self.dono_id,
                "raca",
                RACAS,
                "Escolha sua raça..."
            )
        )

    @discord.ui.button(
        label="Família",
        emoji="🩸",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def familia(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CatalogoView(
                self.dono_id,
                "familia",
                FAMILIAS,
                "Escolha sua família..."
            )
        )

    @discord.ui.button(
        label="Facção",
        emoji="🌊",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def faccao(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=FaccaoView(
                self.dono_id
            )
        )

    @discord.ui.button(
        label="Profissão",
        emoji="🛠️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def profissao(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CatalogoView(
                self.dono_id,
                "profissao",
                PROFISSOES,
                "Escolha sua profissão..."
            )
        )

    @discord.ui.button(
        label="Classe",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def classe(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CatalogoView(
                self.dono_id,
                "classe",
                CLASSES,
                "Escolha sua classe..."
            )
        )

    @discord.ui.button(
        label="Atributos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=2
    )
    async def atributos(
        self,
        interaction,
        button
    ):
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoAtributosView(
                self.dono_id
            )
  )
