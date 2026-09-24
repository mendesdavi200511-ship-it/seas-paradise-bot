import discord

from database.database import atualizar_atributos


ATRIBUTO_MAXIMO = 50000

VALORES_DISTRIBUICAO = [
    ("+1", 1),
    ("+5", 5),
    ("+50", 50),
    ("+100", 100),
    ("+300", 300)
]


# =========================================================
# ESCALAS OFICIAIS / APRESENTAÇÃO
# =========================================================
from data.sistema import atributo_efetivo

def formatar_numero(valor):
    if isinstance(valor, float) and not valor.is_integer():
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{int(valor):,}".replace(",", ".")

def formatar_atributo(tipo, valor, raca=None, familia=None):
    info, bonus, efetivo = atributo_efetivo(tipo, valor, raca, familia)
    linhas=[f"**{info['nome']}** • `{formatar_numero(valor)} pts`", f"└ Base física: **{formatar_numero(info['valor'])} {info['unidade']}**"]
    if bonus:
        linhas += [f"└ Bônus passivo: **+{bonus}%**", f"└ Valor efetivo: **{formatar_numero(efetivo)} {info['unidade']}**"]
    return "\n".join(linhas)

# =========================================================
# EMBED
# =========================================================

def embed_atributos(dados):

    embed = discord.Embed(
        title="⚔️ DISTRIBUIÇÃO DE ATRIBUTOS",
        description=(
            "Distribua seus pontos entre os atributos.\n\n"
            "Selecione primeiro o **atributo** e depois "
            "a quantidade que deseja adicionar."
        )
    )

    embed.add_field(
        name="💪 Força",
        value=formatar_atributo(
            "forca", dados["forca"], dados.get("raca"), dados.get("familia")
        ),
        inline=True
    )

    embed.add_field(
        name="🛡️ Resistência",
        value=formatar_atributo(
            "resistencia", dados["resistencia"], dados.get("raca"), dados.get("familia")
        ),
        inline=True
    )

    embed.add_field(
        name="💨 Velocidade/Agilidade",
        value=formatar_atributo(
            "velocidade", dados["velocidade"], dados.get("raca"), dados.get("familia")
        ),
        inline=True
    )

    embed.add_field(
        name="✨ Pontos disponíveis",
        value=(
            f"**{formatar_numero(dados['pontos'])}**"
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "Limite máximo por atributo: 50.000"
        )
    )

    return embed


# =========================================================
# SELECIONAR ATRIBUTO
# =========================================================

class AtributoSelect(
    discord.ui.Select
):

    def __init__(
        self
    ):

        opcoes = [
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
        ]

        super().__init__(
            placeholder="Escolha um atributo...",
            options=opcoes,
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view

        view.atributo_selecionado = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=embed_atributos(
                view.dados
            ),
            view=view
        )


# =========================================================
# BOTÃO DE QUANTIDADE
# =========================================================

class BotaoQuantidade(
    discord.ui.Button
):

    def __init__(
        self,
        texto,
        quantidade,
        row=1
    ):

        super().__init__(
            label=texto,
            style=discord.ButtonStyle.primary,
            row=row
        )

        self.quantidade = quantidade

    async def callback(
        self,
        interaction
    ):

        view = self.view

        atributo = (
            view.atributo_selecionado
        )

        if atributo is None:

            await interaction.response.send_message(
                "❌ Primeiro escolha **Força, Resistência "
                "ou Velocidade/Agilidade**.",
                ephemeral=True
            )

            return

        dados = view.dados

        if dados["pontos"] < self.quantidade:

            await interaction.response.send_message(
                "❌ Você não possui pontos suficientes.",
                ephemeral=True
            )

            return

        if (
            dados[atributo]
            + self.quantidade
            > ATRIBUTO_MAXIMO
        ):

            await interaction.response.send_message(
                "❌ Esse atributo não pode ultrapassar "
                "**50.000 pontos**.",
                ephemeral=True
            )

            return

        dados[
            atributo
        ] += self.quantidade

        dados[
            "pontos"
        ] -= self.quantidade

        await view.salvar()

        await interaction.response.edit_message(
            embed=embed_atributos(
                dados
            ),
            view=view
        )


# =========================================================
# RESETAR DISTRIBUIÇÃO
# =========================================================

class ResetarButton(
    discord.ui.Button
):

    def __init__(
        self
    ):

        super().__init__(
            label="Resetar distribuição",
            emoji="♻️",
            style=discord.ButtonStyle.danger,
            row=2
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view
        dados = view.dados

        dados["forca"] = (
            view.inicial["forca"]
        )

        dados["resistencia"] = (
            view.inicial["resistencia"]
        )

        dados["velocidade"] = (
            view.inicial["velocidade"]
        )

        dados["pontos"] = (
            view.inicial["pontos"]
        )

        await view.salvar()

        await interaction.response.edit_message(
            embed=embed_atributos(
                dados
            ),
            view=view
        )


# =========================================================
# VIEW PRINCIPAL
# =========================================================

class AtributosView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        dados,
        voltar_callback=None
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id

        self.dados = {
            "forca": dados["forca"],
            "resistencia": dados["resistencia"],
            "velocidade": dados["velocidade"],
            "pontos": dados["pontos"]
        }

        self.inicial = (
            self.dados.copy()
        )

        self.atributo_selecionado = None

        self.voltar_callback = (
            voltar_callback
        )

        self.add_item(
            AtributoSelect()
        )

        for texto, quantidade in VALORES_DISTRIBUICAO:

            self.add_item(
                BotaoQuantidade(
                    texto,
                    quantidade,
                    row=1
                )
            )

        self.add_item(
            ResetarButton()
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

    async def salvar(
        self
    ):

        await atualizar_atributos(
            self.dono_id,
            self.dados["forca"],
            self.dados["resistencia"],
            self.dados["velocidade"],
            self.dados["pontos"]
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

        if self.voltar_callback:

            await self.voltar_callback(
                interaction
            )

            return

        await interaction.response.send_message(
            "✅ Distribuição salva.",
            ephemeral=True
            )
