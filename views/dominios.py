import discord

from data.profissoes import PROFISSOES
from data.classes import CLASSES
from data.skills import ESTILOS


# =========================================================
# SEA'S PARADISE
# VIEW — DISTRIBUIÇÃO DE DOMÍNIOS
# =========================================================

# Valores usados pelos botões
VALORES_DOMINIO = [1, 5, 10, 25, 50]

# Limite padrão para domínios que não possuem
# um máximo próprio definido no catálogo.
DOMINIO_MAXIMO_PADRAO = 200


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def obter_limite_dominio(tipo, nome):
    """
    Limites oficiais:
    - Classe: 100%
    - Estilo: 100%
    - Profissão: 200%, exceto máximo próprio (Cientista = 400%)
    - Haki: sem limite
    """
    tipo = (tipo or "").strip().lower()

    if tipo == "classe":
        return 100

    if tipo == "estilo":
        return 100

    if tipo == "profissao":
        profissao = PROFISSOES.get(nome)
        if profissao:
            return profissao.get("maximo", 200)
        return 200

    if tipo == "haki":
        return None

    return DOMINIO_MAXIMO_PADRAO


def formatar_limite(limite):
    return "∞" if limite is None else f"{limite}%"


def formatar_tipo(tipo):
    nomes = {
        "classe": "⚔️ Classe",
        "estilo": "🥋 Estilo",
        "profissao": "🛠️ Profissão",
        "haki": "🔥 Haki",
        "akuma": "🍈 Akuma no Mi",
        "especializacao": "✨ Especialização",
    }

    return nomes.get(tipo, "📚 Domínio")


def formatar_nome_dominio(dominio):
    tipo = dominio.get("tipo", "")
    nome = dominio.get("nome", "Desconhecido")

    return f"{formatar_tipo(tipo)} • {nome}"



def progressao_dominio(tipo, nome, porcentagem):
    tipo=(tipo or "").lower(); itens=[]
    if tipo=="profissao":
        itens=PROFISSOES.get(nome,{}).get("estagios",[])
        norm=[(i.get("porcentagem",0),i.get("emoji","•"),i.get("nome","Etapa"),i.get("descricao","")) for i in itens]
    elif tipo=="estilo":
        itens=ESTILOS.get(nome,{}).get("skills",[])
        if not itens:
            itens=[{"pct":25,"nome":"Fundamentos","descricao":"Domínio dos fundamentos do estilo."},{"pct":50,"nome":"Técnica Intermediária","descricao":"Aprofundamento técnico do estilo."},{"pct":75,"nome":"Técnica Avançada","descricao":"Aplicação avançada do estilo."},{"pct":100,"nome":"Maestria","descricao":"Domínio completo do estilo."}]
        norm=[(i.get("pct",0),"💥",i.get("nome","Técnica"),i.get("descricao","")) for i in itens]
    elif tipo=="classe":
        esp=CLASSES.get(nome,{}).get("especialidade","")
        norm=[(25,"⚪","Fundamentos",esp),(50,"🔵","Especialização",esp),(75,"🟣","Domínio Avançado",esp),(100,"🟡","Maestria",esp)]
    else:
        return ""
    linhas=[]
    for pct,emoji,titulo,desc in norm:
        estado="✅" if porcentagem>=pct else "🔒"
        linhas.append(f"{estado} **{pct}% • {titulo}**\n└ {desc}")
    return "\n".join(linhas)[:1000]

# =========================================================
# EMBED
# =========================================================

def criar_embed_dominios(dados, dominio_selecionado=None):

    pontos = dados.get("pontos_dominio", 0)
    dominios = dados.get("dominios", [])

    embed = discord.Embed(
        title="📈 DOMÍNIOS DO PERSONAGEM",
        description=(
            "Distribua seus **pontos de domínio** entre "
            "as habilidades que já foram liberadas pela staff."
        )
    )

    embed.add_field(
        name="✨ Pontos disponíveis",
        value=f"**{pontos}%**",
        inline=False
    )

    if not dominios:
        embed.add_field(
            name="📚 Domínios",
            value=(
                "Você ainda não possui nenhum domínio "
                "liberado pela staff."
            ),
            inline=False
        )

        return embed

    linhas = []

    for dominio in dominios:

        nome = dominio.get(
            "nome",
            "Desconhecido"
        )

        tipo = dominio.get(
            "tipo",
            "especializacao"
        )

        porcentagem = dominio.get(
            "porcentagem",
            0
        )

        limite = obter_limite_dominio(
            tipo,
            nome
        )

        linhas.append(
            f"{formatar_tipo(tipo)} "
            f"**{nome}** — "
            f"`{porcentagem}% / {formatar_limite(limite)}`"
        )

    # Evita estourar o limite de caracteres
    texto = "\n".join(linhas)

    if len(texto) > 1000:
        texto = texto[:997] + "..."

    embed.add_field(
        name="📚 Seus Domínios",
        value=texto,
        inline=False
    )

    if dominio_selecionado:

        nome = dominio_selecionado.get(
            "nome",
            "Desconhecido"
        )

        tipo = dominio_selecionado.get(
            "tipo",
            "especializacao"
        )

        porcentagem = dominio_selecionado.get(
            "porcentagem",
            0
        )

        limite = obter_limite_dominio(
            tipo,
            nome
        )

        embed.add_field(
            name="🎯 Selecionado",
            value=(
                f"{formatar_tipo(tipo)}\n"
                f"**{nome}**\n\n"
                f"Domínio atual: **{porcentagem}%**\n"
                f"Limite: **{formatar_limite(limite)}**"
            ),
            inline=False
        )

        progressao = progressao_dominio(tipo, nome, porcentagem)
        if progressao:
            embed.add_field(name="🧭 Progressão e Benefícios", value=progressao, inline=False)

    embed.set_footer(
        text=(
            "Sea's Paradise • "
            "Apenas conteúdos liberados podem receber pontos"
        )
    )

    return embed


# =========================================================
# SELECT DE DOMÍNIO
# =========================================================

class DominioSelect(discord.ui.Select):

    def __init__(self, view_principal):

        self.view_principal = view_principal

        dominios = view_principal.dados.get(
            "dominios",
            []
        )

        opcoes = []

        for indice, dominio in enumerate(
            dominios[:25]
        ):

            nome = dominio.get(
                "nome",
                "Desconhecido"
            )

            tipo = dominio.get(
                "tipo",
                "especializacao"
            )

            porcentagem = dominio.get(
                "porcentagem",
                0
            )

            limite = obter_limite_dominio(
                tipo,
                nome
            )

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    value=str(indice),
                    description=(
                        f"{porcentagem}% / "
                        f"{limite}%"
                    )[:100]
                )
            )

        # Discord não aceita Select sem opção
        if not opcoes:
            opcoes.append(
                discord.SelectOption(
                    label="Nenhum domínio disponível",
                    value="nenhum"
                )
            )

        super().__init__(
            placeholder="Escolha um domínio...",
            options=opcoes,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if self.values[0] == "nenhum":
            await interaction.response.send_message(
                "❌ Você não possui domínios liberados.",
                ephemeral=True
            )
            return

        indice = int(self.values[0])

        dominios = self.view_principal.dados.get(
            "dominios",
            []
        )

        if indice >= len(dominios):
            await interaction.response.send_message(
                "❌ Esse domínio não está mais disponível.",
                ephemeral=True
            )
            return

        self.view_principal.indice_selecionado = indice

        # Confirma a interação imediatamente. Assim o Discord não mostra
        # "o aplicativo não respondeu" caso a atualização leve alguns segundos.
        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.view_principal.atualizar(
            interaction
        )


# =========================================================
# BOTÃO GENÉRICO DE DOMÍNIO
# =========================================================

class BotaoDominio(discord.ui.Button):

    def __init__(
        self,
        quantidade,
        adicionar=True,
        row=1
    ):

        self.quantidade = quantidade
        self.adicionar = adicionar

        sinal = "+" if adicionar else "-"

        estilo = (
            discord.ButtonStyle.success
            if adicionar
            else discord.ButtonStyle.danger
        )

        super().__init__(
            label=f"{sinal}{quantidade}%",
            style=estilo,
            row=row
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        view = self.view

        if not isinstance(
            view,
            DominiosView
        ):
            return

        await view.alterar_dominio(
            interaction,
            self.quantidade,
            self.adicionar
        )


# =========================================================
# VIEW PRINCIPAL
# =========================================================

class DominiosView(discord.ui.View):

    def __init__(
        self,
        dono_id,
        dados,
        salvar_callback=None,
        voltar_callback=None
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.dados = dados

        self.salvar_callback = salvar_callback
        self.voltar_callback = voltar_callback

        self.indice_selecionado = None

        # -------------------------
        # SELECT
        # -------------------------

        self.add_item(
            DominioSelect(self)
        )

        # -------------------------
        # BOTÕES +
        # -------------------------

        for quantidade in VALORES_DOMINIO:
            self.add_item(
                BotaoDominio(
                    quantidade,
                    adicionar=True,
                    row=1
                )
            )

        # -------------------------
        # BOTÕES -
        # -------------------------

        for quantidade in VALORES_DOMINIO:
            self.add_item(
                BotaoDominio(
                    quantidade,
                    adicionar=False,
                    row=2
                )
            )

    # =====================================================
    # SEGURANÇA
    # =====================================================

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esse painel pertence a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    # =====================================================
    # DOMÍNIO ATUAL
    # =====================================================

    def dominio_atual(self):

        if self.indice_selecionado is None:
            return None

        dominios = self.dados.get(
            "dominios",
            []
        )

        if self.indice_selecionado >= len(
            dominios
        ):
            return None

        return dominios[
            self.indice_selecionado
        ]

    # =====================================================
    # ALTERAR %
    # =====================================================

    async def alterar_dominio(
        self,
        interaction,
        quantidade,
        adicionar
    ):

        # Reconhece imediatamente o clique para o Discord não exibir
        # "o aplicativo não respondeu" enquanto salvamos no banco.
        if not interaction.response.is_done():
            await interaction.response.defer()

        dominio = self.dominio_atual()

        if dominio is None:

            await interaction.followup.send(
                "❌ Escolha primeiro um domínio.",
                ephemeral=True
            )

            return

        nome = dominio.get(
            "nome",
            "Desconhecido"
        )

        tipo = dominio.get(
            "tipo",
            "especializacao"
        )

        atual = dominio.get(
            "porcentagem",
            0
        )

        limite = obter_limite_dominio(
            tipo,
            nome
        )

        # =================================================
        # ADICIONAR
        # =================================================

        if adicionar:

            pontos = self.dados.get(
                "pontos_dominio",
                0
            )

            if pontos < quantidade:

                await interaction.followup.send(
                    "❌ Você não possui pontos de "
                    "domínio suficientes.",
                    ephemeral=True
                )

                return

            if limite is not None and atual + quantidade > limite:

                await interaction.followup.send(
                    f"❌ **{nome}** possui limite "
                    f"de **{limite}%**.",
                    ephemeral=True
                )

                return

            dominio["porcentagem"] = (
                atual + quantidade
            )

            self.dados["pontos_dominio"] = (
                pontos - quantidade
            )

        # =================================================
        # REMOVER
        # =================================================

        else:

            if atual < quantidade:

                await interaction.followup.send(
                    "❌ Você não possui essa quantidade "
                    "de pontos nesse domínio.",
                    ephemeral=True
                )

                return

            dominio["porcentagem"] = (
                atual - quantidade
            )

            self.dados["pontos_dominio"] = (
                self.dados.get(
                    "pontos_dominio",
                    0
                )
                + quantidade
            )

        # =================================================
        # SALVAR
        # =================================================

        if self.salvar_callback:

            await self.salvar_callback(
                interaction.user.id,
                self.dados
            )

        await self.atualizar(
            interaction
        )

    # =====================================================
    # ATUALIZAR PAINEL
    # =====================================================

    async def atualizar(
        self,
        interaction
    ):

        dominio = self.dominio_atual()

        embed = criar_embed_dominios(
            self.dados,
            dominio
        )

        if interaction.response.is_done():
            await interaction.edit_original_response(
                embed=embed,
                view=self
            )
        else:
            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

    # =====================================================
    # VOLTAR
    # =====================================================

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=3
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

        await interaction.response.edit_message(
            embed=criar_embed_dominios(
                self.dados,
                self.dominio_atual()
            ),
            view=None
  )
