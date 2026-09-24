import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    criar_ficha,
    deletar_ficha,
    buscar_especializacoes,
    buscar_pontos_percentuais,
    distribuir_percentual,
    adicionar_especializacao,
    buscar_rolagem_criacao,
    resetar_rolagem_criacao,
)

from views.criacao import (
    criando,
    novo_rascunho,
    criar_embed,
    CriacaoView,
)

from views.atributos import (
    AtributosView,
    embed_atributos,
)

from views.dominios import (
    DominiosView,
    criar_embed_dominios,
)

from data.profissoes import PROFISSOES
from data.sistema import atributo_efetivo, rank_por_reputacao, proximo_rank, TALENTOS_AUTOMATICOS, FAMILIAS_VONTADE_D, aplicar_pisos_iniciais
from data.skills import ESTILOS


# =========================================================
# SEA'S PARADISE
# COG — PERSONAGEM
# =========================================================


# =========================================================
# CONFIGURAÇÕES
# =========================================================

TIMEOUT_PAINEL = 300


CANAL_CRIACAO_ID = 1551379201939218502


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor):

    return f"{valor:,}".replace(",", ".")


def formatar_atributo(tipo, valor, raca=None, familia=None):
    info, bonus, efetivo = atributo_efetivo(tipo, valor, raca, familia)
    texto = f"**{info['nome']}** • `{formatar_numero(valor)} pts` • {formatar_numero(info['valor'])} {info['unidade']}"
    if bonus:
        texto += f" • **+{bonus}% → {formatar_numero(efetivo)} {info['unidade']}**"
    return texto


def valor_seguro(
    registro,
    chave,
    padrao=None
):

    """
    Busca uma coluna de asyncpg.Record sem quebrar
    caso uma ficha antiga ainda não possua algum valor.
    """

    try:

        valor = registro[chave]

        if valor is None:
            return padrao

        return valor

    except (KeyError, TypeError):

        return padrao


def formatar_sim_nao(valor):

    if isinstance(valor, bool):

        return (
            "Sim"
            if valor
            else "Não"
        )

    if valor is None:
        return "Não"

    texto = str(valor).strip().lower()

    if texto in {
        "sim",
        "true",
        "1",
        "yes"
    }:
        return "Sim"

    return "Não"


def emoji_sim_nao(valor):

    return (
        "✅"
        if formatar_sim_nao(valor) == "Sim"
        else "❌"
    )


def limite_profissao(nome):

    dados = PROFISSOES.get(
        nome
    )

    if not dados:
        return 200

    return dados.get(
        "maximo",
        200
    )


# =========================================================
# ORGANIZAR DOMÍNIOS
# =========================================================

def separar_dominios(
    especializacoes
):

    principais = {
        "profissao": [],
        "classe": [],
        "estilo": [],
    }

    extras = {}

    for item in especializacoes:

        categoria = (
            item["categoria"]
            .strip()
            .lower()
        )

        if categoria in principais:

            principais[
                categoria
            ].append(item)

        else:

            extras.setdefault(
                categoria,
                []
            ).append(item)

    return principais, extras


def limite_dominio(categoria, nome=None):
    """Limites oficiais dos domínios do Sea's Paradise."""
    categoria = (categoria or "").strip().lower()

    if categoria == "classe":
        return 100

    if categoria == "estilo":
        return 100

    if categoria == "profissao":
        return limite_profissao(nome)

    if categoria == "haki":
        return None

    return 200


def texto_limite_dominio(categoria, nome=None):
    limite = limite_dominio(categoria, nome)
    return "∞" if limite is None else f"{limite}%"


def linha_dominio(
    item,
    emoji
):
    categoria = item["categoria"].strip().lower()
    limite = texto_limite_dominio(categoria, item["nome"])

    return (
        f"{emoji} **{item['nome']}** — "
        f"{item['porcentagem']}%/{limite}"
    )


# =========================================================
# EMBED DA FICHA
# =========================================================

async def criar_embed_ficha(
    membro,
    personagem
):

    especializacoes = list(
        await buscar_especializacoes(
            membro.id
        )
    )

    pontos_percentuais = (
        await buscar_pontos_percentuais(
            membro.id
        )
    )

    idade = valor_seguro(
        personagem,
        "idade",
        "Não definida"
    )

    imagem = valor_seguro(
        personagem,
        "imagem",
        None
    )

    haoshoku = valor_seguro(
        personagem,
        "haoshoku",
        False
    )

    prodigio = valor_seguro(
        personagem,
        "prodigio",
        False
    )

    principais, extras = (
        separar_dominios(
            especializacoes
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

    # =====================================================
    # IMAGEM
    # =====================================================

    if imagem:

        embed.set_thumbnail(
            url=imagem
        )

    else:

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

    # =====================================================
    # IDENTIDADE
    # =====================================================

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"🎂 **Idade:** "
            f"{idade}\n"

            f"🧬 **Raça:** "
            f"{personagem['raca']}\n"

            f"🩸 **Família:** "
            f"{personagem['familia']}\n"

            f"🌊 **Facção:** "
            f"{personagem['faccao']}"
        ),
        inline=False
    )

    # =====================================================
    # CAMINHO
    #
    # Classe, profissão e estilo são DOMÍNIOS.
    # Por isso aparecem aqui já com suas porcentagens
    # e NÃO são repetidos posteriormente.
    # =====================================================

    linhas_caminho = []

    for item in principais[
        "profissao"
    ]:

        linhas_caminho.append(
            linha_dominio(
                item,
                "🛠️"
            )
        )

    for item in principais[
        "classe"
    ]:

        linhas_caminho.append(
            linha_dominio(
                item,
                "⚔️"
            )
        )

    for item in principais[
        "estilo"
    ]:

        linhas_caminho.append(
            linha_dominio(
                item,
                "🥋"
            )
        )

    if not linhas_caminho:

        # Compatibilidade caso exista uma ficha antiga
        # ainda sem especializações registradas.

        profissao = valor_seguro(
            personagem,
            "profissao",
            "Nenhuma"
        )

        classe = valor_seguro(
            personagem,
            "classe",
            "Nenhuma"
        )

        estilo = valor_seguro(
            personagem,
            "estilo",
            "Nenhum"
        )

        if profissao != "Nenhuma":

            linhas_caminho.append(
                f"🛠️ **{profissao}**"
            )

        if classe != "Nenhuma":

            linhas_caminho.append(
                f"⚔️ **{classe}**"
            )

        if estilo not in {
            "Nenhum",
            "Nenhuma",
            None
        }:

            linhas_caminho.append(
                f"🥋 **{estilo}**"
            )

    if linhas_caminho:

        embed.add_field(
            name="🧭 Caminho",
            value="\n".join(
                linhas_caminho
            ),
            inline=False
        )

    # =====================================================
    # TALENTOS ESPECIAIS
    # =====================================================

    embed.add_field(
        name="🌟 Talentos Especiais",
        value=(
            f"{emoji_sim_nao(haoshoku)} "
            f"**Haoshoku:** "
            f"{formatar_sim_nao(haoshoku)}\n"

            f"{emoji_sim_nao(prodigio)} "
            f"**Prodígio:** "
            f"{formatar_sim_nao(prodigio)}\n"
            f"🔥 **Vontade do D.:** {formatar_sim_nao(valor_seguro(personagem, 'vontade_d', False))}\n"
            f"🌅 **Vontade de JoyBoy:** {formatar_sim_nao(valor_seguro(personagem, 'joyboy', False))}"
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
            f"{formatar_atributo('forca', personagem['forca'], personagem['raca'], personagem['familia'])}\n"

            f"🛡️ **Resistência:** "
            f"{formatar_atributo('resistencia', personagem['resistencia'], personagem['raca'], personagem['familia'])}\n"

            f"💨 **Velocidade/Agilidade:** "
            f"{formatar_atributo('velocidade', personagem['velocidade'], personagem['raca'], personagem['familia'])}\n\n"

            f"✨ **Pontos disponíveis:** "
            f"{formatar_numero(personagem['pontos_atributo'])}"
        ),
        inline=False
    )

    # =====================================================
    # OUTROS DOMÍNIOS
    #
    # Profissão, classe e estilo NÃO entram aqui.
    # Isso elimina a duplicação da ficha.
    # =====================================================

    emojis_categoria = {
        "haki": "👁️",
        "akuma": "🍈",
        "akuma no mi": "🍈",
        "tecnica": "💥",
        "especializacao": "✨",
        "despertar": "🌟",
    }

    nomes_categoria = {
        "haki": "Haki",
        "akuma": "Akuma no Mi",
        "akuma no mi": "Akuma no Mi",
        "tecnica": "Técnicas",
        "especializacao": "Especializações",
        "despertar": "Despertar",
    }

    for categoria, itens in extras.items():

        linhas = []

        for item in itens:

            limite = texto_limite_dominio(
                categoria,
                item["nome"]
            )

            linhas.append(
                f"**{item['nome']}** — "
                f"{item['porcentagem']}%/{limite}"
            )

        texto = "\n".join(
            linhas
        )

        if len(texto) > 1024:

            texto = (
                texto[:1000]
                + "\n..."
            )

        emoji = emojis_categoria.get(
            categoria,
            "📚"
        )

        nome_categoria = (
            nomes_categoria.get(
                categoria,
                categoria.title()
            )
        )

        embed.add_field(
            name=(
                f"{emoji} "
                f"{nome_categoria}"
            ),
            value=texto,
            inline=False
        )

    # =====================================================
    # PONTOS DE DOMÍNIO
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

    reputacao = personagem["reputacao"]
    rank_manual = valor_seguro(personagem, "rank_manual", None)
    rank = rank_manual or rank_por_reputacao(reputacao)
    prox_nome, prox_valor = proximo_rank(reputacao)
    progresso = f"\n└ Próximo: **{prox_nome}** em {formatar_numero(prox_valor)}" if prox_nome and not rank_manual else ""
    embed.add_field(
        name="🏆 Reputação",
        value=f"**{formatar_numero(reputacao)} pts**\n└ Rank: **{rank}**{progresso}",
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
# CRIAR DOMÍNIOS INICIAIS
# =========================================================

async def criar_dominios_iniciais(
    user_id,
    dados
):

    """
    Profissão, classe e estilo inicial fazem parte
    do sistema percentual.

    adicionar_especializacao possui UNIQUE no banco,
    então mesmo que esta função seja chamada novamente,
    não duplica o domínio.
    """

    profissao = dados.get(
        "profissao"
    )

    classe = dados.get(
        "classe"
    )

    estilo = (
        dados.get("estilo")
        or dados.get("estilo_inicial")
    )

    # =====================================================
    # PROFISSÃO
    # =====================================================

    if profissao not in {
        None,
        "",
        "Nenhuma",
        "Nenhum"
    }:

        await adicionar_especializacao(
            user_id=user_id,
            categoria="profissao",
            nome=profissao,
            limite=limite_profissao(
                profissao
            ),
            desbloqueado_por="criacao"
        )

    # =====================================================
    # CLASSE
    # =====================================================

    if classe not in {
        None,
        "",
        "Nenhuma",
        "Nenhum"
    }:

        await adicionar_especializacao(
            user_id=user_id,
            categoria="classe",
            nome=classe,
            limite=100,
            desbloqueado_por="criacao"
        )

    # =====================================================
    # ESTILO INICIAL
    # =====================================================

    if estilo not in {
        None,
        "",
        "Nenhuma",
        "Nenhum"
    }:

        await adicionar_especializacao(
            user_id=user_id,
            categoria="estilo",
            nome=estilo,
            limite=100,
            desbloqueado_por="criacao"
        )

    # Talentos adicionais declarados pelos catálogos de raça/família.
    for origem, chave in (("raca", dados.get("raca")), ("familia", dados.get("familia"))):
        for categoria, nome in TALENTOS_AUTOMATICOS.get(origem, {}).get(chave, []):
            limite = limite_profissao(nome) if categoria == "profissao" else (999999 if categoria == "haki" else 100)
            await adicionar_especializacao(user_id=user_id, categoria=categoria, nome=nome, limite=limite, desbloqueado_por=f"{origem}:{chave}")


# =========================================================
# CALLBACK — CONFIRMAR CRIAÇÃO
# =========================================================

async def confirmar_criacao(
    interaction
):

    user_id = (
        interaction.user.id
    )

    dados = criando.get(
        user_id
    )

    if not dados:

        await interaction.response.send_message(
            "❌ Sua criação não está mais ativa.",
            ephemeral=True
        )

        return

    if await possui_ficha(
        user_id
    ):

        criando.pop(
            user_id,
            None
        )

        await interaction.response.edit_message(
            content=(
                "❌ Você já possui um personagem."
            ),
            embed=None,
            view=None
        )

        return

    # =====================================================
    # DADOS NOVOS DA CRIAÇÃO
    # =====================================================

    idade = dados.get(
        "idade"
    )

    imagem = (
        dados.get("imagem")
        or dados.get("imagem_url")
    )

    haoshoku = dados.get(
        "haoshoku",
        False
    )

    prodigio = dados.get(
        "prodigio",
        False
    )

    estilo = (
        dados.get("estilo")
        or dados.get("estilo_inicial")
        or "Nenhum"
    )

    # =====================================================
    # SALVAR FICHA
    # =====================================================

    try:

        aplicar_pisos_iniciais(dados)

        await criar_ficha(
            user_id=user_id,
            nome=dados["nome"],
            idade=idade,
            imagem=imagem,
            raca=dados["raca"],
            familia=dados["familia"],
            faccao=dados["faccao"],
            profissao=dados["profissao"],
            classe=dados["classe"],
            estilo=estilo,
            haoshoku=haoshoku,
            prodigio=prodigio,
            vontade_d=bool(dados.get("vontade_d")),
            joyboy=False,
            forca=dados["forca"],
            resistencia=dados["resistencia"],
            velocidade=dados["velocidade"],
            pontos_atributo=dados["pontos"]
        )

        # =================================================
        # CRIAR DOMÍNIOS AUTOMÁTICOS
        # =================================================

        await criar_dominios_iniciais(
            user_id,
            dados
        )

    except Exception as erro:

        print()
        print("=" * 50)
        print(
            "❌ ERRO AO CRIAR PERSONAGEM"
        )
        print("=" * 50)

        print(
            f"Tipo: "
            f"{type(erro).__name__}"
        )

        print(
            f"Erro: {erro}"
        )

        print("=" * 50)
        print()

        # Caso a ficha tenha sido criada,
        # mas algo posterior tenha falhado,
        # removemos para não deixar criação incompleta.

        if await possui_ficha(
            user_id
        ):

            await deletar_ficha(
                user_id
            )

        await interaction.response.send_message(
            "❌ Não foi possível salvar "
            "seu personagem.",
            ephemeral=True
        )

        return

    # =====================================================
    # FINALIZAR
    # =====================================================

    personagem = await buscar_ficha(
        user_id
    )

    criando.pop(
        user_id,
        None
    )

    if personagem:

        await interaction.response.edit_message(
            content=None,
            embed=await criar_embed_ficha(
                interaction.user,
                personagem
            ),
            view=None
        )

    else:

        await interaction.response.edit_message(
            content=(
                "✅ Personagem criado com sucesso!"
            ),
            embed=None,
            view=None
        )


# =========================================================
# MODAL — EDITAR NOME
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

        ficha = await buscar_ficha(
            interaction.user.id
        )

        if not ficha:

            await interaction.response.send_message(
                "❌ Ficha não encontrada.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=await criar_embed_ficha(
                interaction.user,
                ficha
            ),
            view=EditarFichaView(
                interaction.user.id
            )
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
            timeout=TIMEOUT_PAINEL
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
        style=discord.ButtonStyle.secondary,
        row=0
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
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def atributos(
        self,
        interaction,
        button
    ):

        await abrir_atributos(
            interaction
        )

    @discord.ui.button(label="Reputação", emoji="🏆", style=discord.ButtonStyle.secondary, row=0)
    async def reputacao(self, interaction, button):
        ficha=await buscar_ficha(interaction.user.id)
        rep=ficha["reputacao"]; manual=valor_seguro(ficha,"rank_manual",None); rank=manual or rank_por_reputacao(rep); prox,valor=proximo_rank(rep)
        texto=f"**{formatar_numero(rep)} pontos**\n\n🏅 Rank atual: **{rank}**"
        if prox and not manual: texto += f"\n📈 Próximo Rank: **{prox}** em **{formatar_numero(valor)}**"
        if manual: texto += "\n🔧 Rank definido manualmente pela administração."
        embed=discord.Embed(title="🏆 REPUTAÇÃO",description=texto)
        embed.set_footer(text="Sea's Paradise • Sua reputação cresce com acontecimentos reconhecidos no mundo")
        await interaction.response.edit_message(embed=embed,view=EditarFichaView(self.dono_id))

    @discord.ui.button(
        label="Domínios",
        emoji="📈",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def dominios(
        self,
        interaction,
        button
    ):

        await abrir_dominios(
            interaction
        )


# =========================================================
# VOLTAR PARA EDIÇÃO
# =========================================================

async def voltar_edicao(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.edit_message(
            content="❌ Ficha não encontrada.",
            embed=None,
            view=None
        )

        return

    await interaction.response.edit_message(
        content=None,
        embed=await criar_embed_ficha(
            interaction.user,
            ficha
        ),
        view=EditarFichaView(
            interaction.user.id
        )
    )


# =========================================================
# ABRIR ATRIBUTOS
# =========================================================

async def abrir_atributos(
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

    dados = {
        "forca": ficha["forca"],
        "resistencia": ficha["resistencia"],
        "velocidade": ficha["velocidade"],
        "pontos": ficha["pontos_atributo"],
        "raca": ficha["raca"],
        "familia": ficha["familia"],
    }

    view = AtributosView(
        interaction.user.id,
        dados,
        voltar_callback=voltar_edicao
    )

    await interaction.response.edit_message(
        embed=embed_atributos(
            view.dados
        ),
        view=view
    )


# =========================================================
# SALVAR DOMÍNIOS
# =========================================================

async def salvar_dominios(
    user_id,
    dados
):

    especializacoes = list(
        await buscar_especializacoes(
            user_id
        )
    )

    atuais = {
        item["id"]: item
        for item in especializacoes
    }

    for dominio in dados.get(
        "dominios",
        []
    ):

        especializacao_id = (
            dominio.get("id")
        )

        if especializacao_id not in atuais:
            continue

        porcentagem_banco = (
            atuais[
                especializacao_id
            ]["porcentagem"]
        )

        porcentagem_nova = (
            dominio.get(
                "porcentagem",
                0
            )
        )

        diferenca = (
            porcentagem_nova
            - porcentagem_banco
        )

        if diferenca > 0:

            sucesso = await distribuir_percentual(
                user_id,
                especializacao_id,
                diferenca
            )

            if not sucesso:
                return False

        elif diferenca < 0:

            # Não devolvemos % ao jogador
            # sem uma função transacional específica
            # para isso no database.
            return False

    return True


# =========================================================
# MONTAR DADOS DOS DOMÍNIOS
# =========================================================

def montar_dados_dominios(
    especializacoes,
    pontos
):

    dominios = []

    for item in especializacoes:

        categoria = item["categoria"].strip().lower()
        limite = limite_dominio(
            categoria,
            item["nome"]
        )

        dominios.append({
            "id": item["id"],
            "nome": item["nome"],
            "tipo": categoria,
            "porcentagem": item["porcentagem"],
            "limite": limite,
        })

    return {
        "pontos_dominio": pontos,
        "dominios": dominios,
    }


# =========================================================
# ABRIR DOMÍNIOS
# =========================================================

async def abrir_dominios(
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

    especializacoes = list(
        await buscar_especializacoes(
            interaction.user.id
        )
    )

    pontos = (
        await buscar_pontos_percentuais(
            interaction.user.id
        )
    )

    dados = montar_dados_dominios(
        especializacoes,
        pontos
    )

    view = DominiosView(
        interaction.user.id,
        dados,
        salvar_callback=salvar_dominios,
        voltar_callback=voltar_edicao
    )

    await interaction.response.edit_message(
        embed=criar_embed_dominios(
            dados
        ),
        view=view
    )


# =========================================================
# COG
# =========================================================

class Personagem(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    def topico_do_jogador(self, ctx):
        """Retorna True somente no tópico individual do próprio jogador."""
        if not isinstance(ctx.channel, discord.Thread):
            return False

        if ctx.channel.parent_id != CANAL_CRIACAO_ID:
            return False

        marcador = f"sp-{ctx.author.id}"
        return ctx.channel.name.endswith(marcador)


    async def exigir_topico_do_jogador(self, ctx):
        """Bloqueia comandos de ficha fora do tópico individual."""
        if self.topico_do_jogador(ctx):
            return True

        aviso = await ctx.send(
            f"❌ Este comando só pode ser usado no seu tópico em "
            f"<#{CANAL_CRIACAO_ID}>."
        )

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        try:
            await aviso.delete(delay=10)
        except (discord.Forbidden, discord.NotFound):
            pass

        return False


    # =====================================================
    # !CRIAR
    # =====================================================

    @commands.command()
    async def criar(
        self,
        ctx
    ):

        # O !criar só pode ser iniciado no canal oficial
        # ou dentro de uma thread pertencente a ele.
        eh_thread_criacao = (
            isinstance(ctx.channel, discord.Thread)
            and ctx.channel.parent_id == CANAL_CRIACAO_ID
        )

        if (
            ctx.channel.id != CANAL_CRIACAO_ID
            and not eh_thread_criacao
        ):
            aviso = await ctx.send(
                f"❌ Use `!criar` em <#{CANAL_CRIACAO_ID}>."
            )

            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

            try:
                await aviso.delete(delay=10)
            except (discord.Forbidden, discord.NotFound):
                pass

            return

        if await possui_ficha(
            ctx.author.id
        ):
            aviso = await ctx.send(
                "❌ Você já possui um personagem.\n"
                "Use `!ficha` para visualizá-lo."
            )

            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

            try:
                await aviso.delete(delay=10)
            except (discord.Forbidden, discord.NotFound):
                pass

            return

        guild = ctx.guild

        if guild is None:
            return

        canal = guild.get_channel(
            CANAL_CRIACAO_ID
        )

        if canal is None:
            await ctx.send(
                "❌ O canal oficial de criação não foi encontrado."
            )
            return

        thread = None
        marcador = f"sp-{ctx.author.id}"

        # Se já estiver na própria thread, usa ela.
        if eh_thread_criacao:
            thread = ctx.channel

        # Procura uma thread ativa existente.
        if thread is None:
            for candidata in canal.threads:
                if candidata.name.endswith(marcador):
                    thread = candidata
                    break

        # Procura também threads arquivadas para impedir duplicação.
        if thread is None:
            try:
                async for candidata in canal.archived_threads(limit=100):
                    if candidata.name.endswith(marcador):
                        thread = candidata
                        break
            except (
                discord.Forbidden,
                discord.HTTPException,
                AttributeError
            ):
                pass

        # Só cria uma nova se o jogador realmente não possuir uma.
        if thread is None:
            nome_thread = (
                f"🏴‍☠️-{ctx.author.display_name[:45]}-{marcador}"
            )

            try:
                thread = await canal.create_thread(
                    name=nome_thread[:100],
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=1440,
                    reason=(
                        "Sea's Paradise — criação de personagem "
                        f"de {ctx.author}"
                    )
                )

            except discord.Forbidden:
                await ctx.send(
                    "❌ O bot não possui permissão para criar "
                    "tópicos neste canal."
                )
                return

            except discord.HTTPException as erro:
                print(
                    "❌ ERRO AO CRIAR THREAD:",
                    type(erro).__name__,
                    erro
                )

                await ctx.send(
                    "❌ Não consegui criar seu tópico de criação."
                )
                return

        # Se a thread antiga estiver arquivada, reabre.
        try:
            if thread.archived:
                await thread.edit(
                    archived=False,
                    reason="Jogador retomou a criação."
                )

            if thread.locked:
                await thread.edit(
                    locked=False,
                    reason="Jogador retomou a criação."
                )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        try:
            await thread.add_user(
                ctx.author
            )
        except (
            discord.Forbidden,
            discord.HTTPException,
            AttributeError
        ):
            pass

        # Limpa o comando digitado.
        try:
            await ctx.message.delete()
        except (
            discord.Forbidden,
            discord.NotFound
        ):
            pass

        # Mantém o fluxo atual. novo_rascunho() continua responsável
        # por recuperar/preservar os sorteios conforme a versão atual.
        criando[
            ctx.author.id
        ] = novo_rascunho()

        await thread.send(
            content=ctx.author.mention,
            embed=criar_embed(
                ctx.author
            ),
            view=CriacaoView(
                ctx.author.id,
                confirmar_criacao
            )
        )

        # No canal principal fica apenas um aviso temporário.
        if ctx.channel.id == CANAL_CRIACAO_ID:
            try:
                aviso = await canal.send(
                    f"{ctx.author.mention}, sua criação está em "
                    f"{thread.mention}."
                )

                await aviso.delete(
                    delay=10
                )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

    # =====================================================
    # !FICHA
    #
    # A ficha NÃO some.
    # É informação permanente do personagem.
    # =====================================================

    @commands.command()
    async def ficha(
        self,
        ctx,
        membro: discord.Member = None
    ):

        if not await self.exigir_topico_do_jogador(ctx):
            return

        membro = (
            membro
            or ctx.author
        )

        personagem = (
            await buscar_ficha(
                membro.id
            )
        )

        if not personagem:

            await ctx.send(
                f"❌ {membro.mention} "
                "ainda não possui ficha.",
                delete_after=TIMEOUT_PAINEL
            )

            return

        await ctx.send(
            embed=await criar_embed_ficha(
                membro,
                personagem
            )
        )


# =====================================================
# !EDITAR
# =====================================================

    @commands.command()
    async def editar(
        self,
        ctx
    ):

        if not await self.exigir_topico_do_jogador(ctx):
            return

        personagem = (
            await buscar_ficha(
                ctx.author.id
            )
        )

        if not personagem:

            await ctx.send(
                "❌ Você ainda não possui ficha.\n"
                "Use `!criar` primeiro.",
                delete_after=TIMEOUT_PAINEL
            )

            return

        await ctx.send(
            embed=await criar_embed_ficha(
                ctx.author,
                personagem
            ),
            view=EditarFichaView(
                ctx.author.id
            ),
            delete_after=TIMEOUT_PAINEL
        )


    # =====================================================
    # !ATRIBUTOS
    # =====================================================

    @commands.command(
        aliases=[
            "atributo"
        ]
    )
    async def atributos(
        self,
        ctx
    ):

        if not await self.exigir_topico_do_jogador(ctx):
            return

        ficha = (
            await buscar_ficha(
                ctx.author.id
            )
        )

        if not ficha:

            await ctx.send(
                "❌ Você ainda não possui ficha.",
                delete_after=TIMEOUT_PAINEL
            )

            return

        dados = {
            "forca": ficha["forca"],
            "resistencia": ficha["resistencia"],
            "velocidade": ficha["velocidade"],
            "pontos": ficha["pontos_atributo"],
            "raca": ficha["raca"],
            "familia": ficha["familia"],
        }

        view = AtributosView(
            ctx.author.id,
            dados
        )

        await ctx.send(
            embed=embed_atributos(
                view.dados
            ),
            view=view,
            delete_after=TIMEOUT_PAINEL
        )


    # =====================================================
    # !DOMINIOS
    # =====================================================

    @commands.command(
        aliases=[
            "dominio",
            "domínios",
            "domínio"
        ]
    )
    async def dominios(
        self,
        ctx
    ):

        if not await self.exigir_topico_do_jogador(ctx):
            return

        if not await possui_ficha(
            ctx.author.id
        ):

            await ctx.send(
                "❌ Você ainda não possui ficha.",
                delete_after=TIMEOUT_PAINEL
            )

            return

        especializacoes = list(
            await buscar_especializacoes(
                ctx.author.id
            )
        )

        pontos = (
            await buscar_pontos_percentuais(
                ctx.author.id
            )
        )

        dados = montar_dados_dominios(
            especializacoes,
            pontos
        )

        view = DominiosView(
            ctx.author.id,
            dados,
            salvar_callback=salvar_dominios
        )

        await ctx.send(
            embed=criar_embed_dominios(
                dados
            ),
            view=view,
            delete_after=TIMEOUT_PAINEL
        )


    # =====================================================
    # !RESETARFICHA
    # ADMIN
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

        membro = (
            membro
            or ctx.author
        )

        resultado = (
            await deletar_ficha(
                membro.id
            )
        )

        await resetar_rolagem_criacao(
            membro.id
        )

        criando.pop(
            membro.id,
            None
        )

        if resultado == "DELETE 0":

            await ctx.send(
                f"❌ {membro.mention} "
                "não possui ficha.",
                delete_after=TIMEOUT_PAINEL
            )

            return

        # Ao resetar a ficha, remove também o tópico individual do jogador.
        # A busca é feita em threads ativas + arquivadas e usa o marcador
        # sp-ID em qualquer parte do nome para não depender do cache/nome exato.
        thread_apagada = False
        guild = ctx.guild

        if guild is not None:
            marcador = f"sp-{membro.id}"
            thread = None

            # 1) Se o comando foi executado no próprio tópico do jogador,
            # já temos a referência mais confiável possível.
            if (
                isinstance(ctx.channel, discord.Thread)
                and ctx.channel.parent_id == CANAL_CRIACAO_ID
                and marcador in ctx.channel.name
            ):
                thread = ctx.channel

            # 2) Procura entre todas as threads ativas conhecidas da guild.
            if thread is None:
                for candidata in guild.threads:
                    if (
                        candidata.parent_id == CANAL_CRIACAO_ID
                        and marcador in candidata.name
                    ):
                        thread = candidata
                        break

            # 3) Procura no canal oficial, inclusive arquivadas.
            canal = guild.get_channel(CANAL_CRIACAO_ID)
            if canal is None:
                try:
                    canal = await guild.fetch_channel(CANAL_CRIACAO_ID)
                except (
                    discord.Forbidden,
                    discord.NotFound,
                    discord.HTTPException
                ):
                    canal = None

            if thread is None and canal is not None:
                for candidata in getattr(canal, "threads", []):
                    if marcador in candidata.name:
                        thread = candidata
                        break

            if thread is None and canal is not None:
                try:
                    async for candidata in canal.archived_threads(limit=None):
                        if marcador in candidata.name:
                            thread = candidata
                            break
                except (
                    discord.Forbidden,
                    discord.HTTPException,
                    AttributeError
                ) as erro:
                    print(
                        "⚠️ ERRO AO PROCURAR TÓPICO ARQUIVADO:",
                        type(erro).__name__,
                        erro
                    )

            if thread is not None:
                try:
                    await thread.delete(
                        reason=(
                            "Sea's Paradise — ficha resetada por "
                            f"{ctx.author}"
                        )
                    )
                    thread_apagada = True
                except (
                    discord.Forbidden,
                    discord.NotFound,
                    discord.HTTPException
                ) as erro:
                    print(
                        "❌ ERRO AO APAGAR TÓPICO DA FICHA:",
                        type(erro).__name__,
                        erro
                    )
            else:
                print(
                    "⚠️ TÓPICO DA FICHA NÃO ENCONTRADO:",
                    marcador
                )

        mensagem = (
            f"🗑️ Ficha de {membro.mention} resetada."
        )

        if thread_apagada:
            mensagem += "\n🧹 Tópico do personagem apagado."

        await ctx.send(
            mensagem,
            delete_after=TIMEOUT_PAINEL
        )


# =========================================================
# SETUP
# =========================================================

async def setup(
    bot
):

    await bot.add_cog(
        Personagem(bot)
    )
