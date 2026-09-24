import discord
from discord.ext import commands

from data.economia import ITENS, EMBARCACOES, LOJAS, ROTAS, normalizar_local
from database.database import (
    buscar_ficha, buscar_localizacao_jogador, definir_localizacao_jogador,
    buscar_inventario, buscar_item_inventario, comprar_item, vender_item,
    consumir_item, comprar_embarcacao, buscar_embarcacoes, buscar_embarcacao_ativa,
    renomear_embarcacao, reparar_embarcacao, registrar_transacao_economia,
)

COR = discord.Color.from_rgb(32, 104, 160)

def dinheiro(v): return f"฿ {int(v):,}".replace(",", ".")

def loja_local(local):
    local = normalizar_local(local)
    return local, LOJAS.get(local)

class ItemSelect(discord.ui.Select):
    def __init__(self, user_id, itens, modo="loja"):
        self.user_id, self.modo = user_id, modo
        opts=[]
        for item_id, qtd in itens[:25]:
            d=ITENS[item_id]
            desc=(f"{dinheiro(d['preco'])}" if modo=="loja" else f"Quantidade: {qtd}")
            opts.append(discord.SelectOption(label=d['nome'][:100], value=item_id, emoji=d.get('emoji'), description=desc[:100]))
        super().__init__(placeholder="Selecione um item...", options=opts)
    async def callback(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Este painel pertence a outro jogador.", ephemeral=True)
        item_id=self.values[0]; d=ITENS[item_id]
        if self.modo=="loja":
            view=ComprarView(self.user_id,item_id)
            emb=discord.Embed(title=f"{d['emoji']} {d['nome']}",description=d['descricao'],color=COR)
            emb.add_field(name="💰 Preço",value=dinheiro(d['preco']))
        else:
            row=await buscar_item_inventario(self.user_id,item_id); qtd=row['quantidade'] if row else 0
            view=InventarioItemView(self.user_id,item_id)
            emb=discord.Embed(title=f"{d['emoji']} {d['nome']}",description=d['descricao'],color=COR)
            emb.add_field(name="🎒 Quantidade",value=str(qtd))
            emb.add_field(name="🏷️ Categoria",value=d['categoria'].title())
        await interaction.response.edit_message(embed=emb,view=view)

class ComprarView(discord.ui.View):
    def __init__(self,user_id,item_id): super().__init__(timeout=180); self.user_id=user_id; self.item_id=item_id
    @discord.ui.button(label="Comprar 1",emoji="💰",style=discord.ButtonStyle.success)
    async def comprar(self,interaction,button):
        if interaction.user.id!=self.user_id: return await interaction.response.send_message("❌ Este painel não é seu.",ephemeral=True)
        loc=await buscar_localizacao_jogador(self.user_id); local,loja=loja_local(loc['localizacao'] if loc else None)
        if not loja or self.item_id not in loja['itens']: return await interaction.response.send_message("❌ Esse item não está disponível na sua localização atual.",ephemeral=True)
        ok,msg=await comprar_item(self.user_id,self.item_id,ITENS[self.item_id]['preco'])
        await interaction.response.send_message(("✅ " if ok else "❌ ")+msg,ephemeral=True)

class InventarioItemView(discord.ui.View):
    def __init__(self,user_id,item_id):
        super().__init__(timeout=180); self.user_id=user_id; self.item_id=item_id; d=ITENS[item_id]
        if not d.get('consumivel'): self.remove_item(self.usar)
    @discord.ui.button(label="Usar",emoji="✨",style=discord.ButtonStyle.primary)
    async def usar(self,interaction,button):
        if interaction.user.id!=self.user_id: return await interaction.response.send_message("❌ Este painel não é seu.",ephemeral=True)
        d=ITENS[self.item_id]
        if d.get('efeito')=='reparo_navio':
            navio=await buscar_embarcacao_ativa(self.user_id)
            if not navio: return await interaction.response.send_message("❌ Você não possui embarcação ativa para reparar.",ephemeral=True)
            if navio['integridade_atual']>=navio['integridade_max']: return await interaction.response.send_message("ℹ️ Sua embarcação já está com integridade máxima.",ephemeral=True)
            ok=await consumir_item(self.user_id,self.item_id,1)
            if not ok: return await interaction.response.send_message("❌ Você não possui mais esse item.",ephemeral=True)
            novo=await reparar_embarcacao(navio['id'],int(d.get('valor_efeito',50)))
            return await interaction.response.send_message(f"🔧 Reparo concluído. Integridade: **{novo['integridade_atual']}/{novo['integridade_max']}**.",ephemeral=True)
        ok=await consumir_item(self.user_id,self.item_id,1)
        await interaction.response.send_message("✅ Item consumido e registrado no inventário." if ok else "❌ Você não possui mais esse item.",ephemeral=True)
    @discord.ui.button(label="Vender 1",emoji="💰",style=discord.ButtonStyle.secondary)
    async def vender(self,interaction,button):
        if interaction.user.id!=self.user_id: return await interaction.response.send_message("❌ Este painel não é seu.",ephemeral=True)
        d=ITENS[self.item_id]
        if not d.get('vendavel',False): return await interaction.response.send_message("❌ Este item não pode ser vendido.",ephemeral=True)
        valor=d['preco']//2; ok,msg=await vender_item(self.user_id,self.item_id,valor)
        await interaction.response.send_message(("✅ " if ok else "❌ ")+msg,ephemeral=True)

class LojaView(discord.ui.View):
    def __init__(self,user_id,loja):
        super().__init__(timeout=300); itens=[(x,0) for x in loja['itens'] if x in ITENS]
        if itens: self.add_item(ItemSelect(user_id,itens,"loja"))

class InventarioView(discord.ui.View):
    def __init__(self,user_id,rows):
        super().__init__(timeout=300); itens=[(r['item_id'],r['quantidade']) for r in rows if r['item_id'] in ITENS]
        if itens: self.add_item(ItemSelect(user_id,itens,"inventario"))

class NavioSelect(discord.ui.Select):
    def __init__(self,user_id,barcos):
        self.user_id=user_id
        super().__init__(placeholder="Selecione uma embarcação para comprar...",options=[discord.SelectOption(label=EMBARCACOES[x]['nome'],value=x,emoji=EMBARCACOES[x]['emoji'],description=dinheiro(EMBARCACOES[x]['preco'])) for x in barcos[:25]])
    async def callback(self,interaction):
        if interaction.user.id!=self.user_id:return await interaction.response.send_message("❌ Este painel não é seu.",ephemeral=True)
        tipo=self.values[0]; d=EMBARCACOES[tipo]; loc=await buscar_localizacao_jogador(self.user_id); local,loja=loja_local(loc['localizacao'] if loc else None)
        if not loja or tipo not in loja['barcos']:return await interaction.response.send_message("❌ Essa embarcação não está à venda aqui.",ephemeral=True)
        ok,msg=await comprar_embarcacao(self.user_id,tipo,d,local)
        await interaction.response.send_message(("✅ " if ok else "❌ ")+msg,ephemeral=True)

class Economia(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @commands.command(aliases=["inv","mochila"])
    async def inventario(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        rows=await buscar_inventario(ctx.author.id)
        emb=discord.Embed(title="🎒 INVENTÁRIO",description="━━━━━━━━━━━━━━━━━━",color=COR)
        emb.add_field(name="💰 Berries",value=dinheiro(ficha['berries']),inline=False)
        if not rows: emb.add_field(name="📦 Itens",value="Seu inventário está vazio.",inline=False)
        else:
            grupos={}
            for r in rows:
                d=ITENS.get(r['item_id']);
                if not d: continue
                grupos.setdefault(d['categoria'],[]).append(f"{d['emoji']} **{d['nome']}** ×{r['quantidade']}")
            for cat,linhas in grupos.items(): emb.add_field(name=f"📦 {cat.title()}",value="\n".join(linhas)[:1024],inline=False)
        await ctx.send(embed=emb,view=InventarioView(ctx.author.id,rows) if rows else None)

    @commands.command()
    async def loja(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        loc=await buscar_localizacao_jogador(ctx.author.id); local,loja=loja_local(loc['localizacao'] if loc else None)
        if not loja:return await ctx.send(f"🏪 Não há loja configurada em **{local or 'localização desconhecida'}**.")
        emb=discord.Embed(title=f"🏪 MERCADO — {local.upper()}",description=f"💰 Seus Berries: **{dinheiro(ficha['berries'])}**\n\nSelecione um item abaixo para ver detalhes e comprar.",color=COR)
        if loja['barcos']: emb.add_field(name="🚢 Estaleiro",value="Use `!estaleiro` para embarcações.",inline=False)
        await ctx.send(embed=emb,view=LojaView(ctx.author.id,loja))

    @commands.command()
    async def estaleiro(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        loc=await buscar_localizacao_jogador(ctx.author.id); local,loja=loja_local(loc['localizacao'] if loc else None)
        if not loja or not loja['barcos']:return await ctx.send("⚓ Não há embarcações à venda neste local.")
        emb=discord.Embed(title=f"⚓ ESTALEIRO — {local.upper()}",description=f"💰 **{dinheiro(ficha['berries'])}**",color=COR)
        for x in loja['barcos']:
            d=EMBARCACOES[x]; emb.add_field(name=f"{d['emoji']} {d['nome']} — {dinheiro(d['preco'])}",value=f"👥 {d['capacidade']} • 📦 {d['carga']} • ❤️ {d['integridade']}",inline=False)
        v=discord.ui.View(timeout=300); v.add_item(NavioSelect(ctx.author.id,loja['barcos'])); await ctx.send(embed=emb,view=v)

    @commands.command(aliases=["barco","embarcacao"])
    async def navio(self,ctx):
        barcos=await buscar_embarcacoes(ctx.author.id)
        if not barcos:return await ctx.send("🚢 Você ainda não possui uma embarcação.")
        emb=discord.Embed(title="🚢 SUAS EMBARCAÇÕES",color=COR)
        for n in barcos:
            d=EMBARCACOES.get(n['tipo'],{}); ativo="⭐ ATIVA" if n['ativa'] else ""
            emb.add_field(name=f"{d.get('emoji','🚢')} {n['nome']} {ativo}",value=f"Modelo: **{d.get('nome',n['tipo'])}**\n❤️ {n['integridade_atual']}/{n['integridade_max']} • 👥 {n['capacidade']} • 📦 {n['carga_max']}\n📍 {n['localizacao'] or 'Desconhecida'}",inline=False)
        await ctx.send(embed=emb)

    @commands.command()
    async def nomearnavio(self,ctx,*,nome:str):
        n=await buscar_embarcacao_ativa(ctx.author.id)
        if not n:return await ctx.send("❌ Você não possui embarcação ativa.")
        nome=nome.strip()[:60]
        if not nome:return await ctx.send("❌ Informe um nome válido.")
        await renomear_embarcacao(n['id'],ctx.author.id,nome); await ctx.send(f"🏴‍☠️ Sua embarcação agora se chama **{nome}**.")

    @commands.command()
    async def rotas(self,ctx):
        loc=await buscar_localizacao_jogador(ctx.author.id); local=normalizar_local(loc['localizacao'] if loc else None); destinos=ROTAS.get(local,[])
        if not destinos:return await ctx.send(f"🧭 Não há rotas configuradas partindo de **{local or 'localização desconhecida'}**.")
        await ctx.send("🧭 **Rotas disponíveis a partir de %s**\n%s"%(local,"\n".join(f"• {x}" for x in destinos)))

    @commands.command()
    async def viajar(self,ctx,*,destino:str):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        estado=await buscar_localizacao_jogador(ctx.author.id)
        if not estado or not estado['localizacao']:return await ctx.send("❌ Sua localização ainda não foi estabelecida pelo mundo do RP.")
        if estado['combate_ativo'] or (estado['estado'] and estado['estado']!='livre'):return await ctx.send("❌ Seu estado atual não permite iniciar uma viagem.")
        origem=normalizar_local(estado['localizacao']); destino=normalizar_local(destino)
        if destino not in ROTAS.get(origem,[]):return await ctx.send(f"❌ Não existe rota direta configurada de **{origem}** para **{destino}**. Use `!rotas`.")
        navio=await buscar_embarcacao_ativa(ctx.author.id)
        if not navio:return await ctx.send("❌ Você precisa possuir uma embarcação ativa para navegar.")
        if normalizar_local(navio['localizacao'])!=origem:return await ctx.send(f"❌ Sua embarcação ativa está em **{navio['localizacao']}**, não em **{origem}**.")
        await definir_localizacao_jogador(ctx.author.id,destino)
        from database.database import mover_embarcacao
        await mover_embarcacao(navio['id'],destino)
        await registrar_transacao_economia(ctx.author.id,"viagem",0,None,1,f"{origem} -> {destino}")
        await ctx.send(f"⛵ **Viagem concluída**\n🧭 {origem} → **{destino}**\n🚢 {navio['nome']}\n\nSua localização persistente foi atualizada.")

async def setup(bot): await bot.add_cog(Economia(bot))
