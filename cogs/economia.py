import discord
import random
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks

from data.economia import ITENS, EMBARCACOES, LOJAS, normalizar_local
from data.navegacao import LOCAIS, ROTAS_INFO, OBSTACULOS, destinos_de, normalizar_destino
from database.database import (
    buscar_ficha, buscar_localizacao_jogador, definir_localizacao_jogador,
    buscar_inventario, buscar_item_inventario, listar_akumas_inventario, consumir_akuma_encontrada, comprar_item, vender_item,
    consumir_item, comprar_embarcacao, buscar_embarcacoes, buscar_embarcacao_ativa,
    renomear_embarcacao, reparar_embarcacao, registrar_transacao_economia, buscar_especializacoes,
    buscar_viagem_ativa, criar_viagem, viagens_pendentes, criar_evento_viagem, evento_aberto_viagem, liberar_rota_especial, rota_especial_liberada,
    resolver_evento_viagem, agendar_proximo_evento_viagem, concluir_viagem, danificar_embarcacao, mover_embarcacao,
    buscar_treinamento_ativo, buscar_sessao_ativa_usuario, evento_ativo_usuario, boss_rp_ativo_usuario,
    criar_plano_viagem, buscar_plano_viagem_user, buscar_plano_viagem_canal, listar_embarques, embarcar_plano, desembarcar_plano, cancelar_plano_viagem, fechar_plano_viagem, passageiros_viagem,
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

class AkumaSelect(discord.ui.Select):
    def __init__(self,user_id,akumas):
        self.user_id=user_id
        opts=[discord.SelectOption(label=a['nome'][:100],value=str(a['id']),emoji='🍈',description=f"{a['tipo'].title()} • consumir para obter o poder"[:100]) for a in akumas[:25]]
        super().__init__(placeholder="🍈 Selecione uma Akuma no Mi...",options=opts)
    async def callback(self,interaction):
        if interaction.user.id!=self.user_id:return await interaction.response.send_message("❌ Este painel pertence a outro jogador.",ephemeral=True)
        akumas=await listar_akumas_inventario(self.user_id)
        a=next((x for x in akumas if str(x['id'])==self.values[0]),None)
        if not a:return await interaction.response.send_message("❌ Essa fruta não está mais disponível.",ephemeral=True)
        await interaction.response.edit_message(embed=discord.Embed(title=f"🍈 {a['nome']}",description=f"**Tipo:** {a['tipo'].title()}\n\nConsumir a fruta concede seu poder ao personagem. Um personagem que já possui Akuma no Mi não pode consumir outra.",color=discord.Color.purple()),view=AkumaItemView(self.user_id,a['nome']))

class AkumaItemView(discord.ui.View):
    def __init__(self,user_id,nome):super().__init__(timeout=180);self.user_id=user_id;self.nome=nome
    @discord.ui.button(label="Consumir Akuma no Mi",emoji="🍈",style=discord.ButtonStyle.success)
    async def consumir(self,interaction,button):
        if interaction.user.id!=self.user_id:return await interaction.response.send_message("❌ Este painel não é seu.",ephemeral=True)
        ak=await consumir_akuma_encontrada(self.user_id,self.nome)
        if not ak:return await interaction.response.send_message("❌ Não foi possível consumir essa fruta. Ela pode ter expirado, já ter sido usada ou seu personagem já possuir uma Akuma no Mi.",ephemeral=True)
        await interaction.response.send_message(f"🍈 **{ak['nome']} consumida!** O poder da **{ak['nome']}** agora pertence ao seu personagem.")

class InventarioView(discord.ui.View):
    def __init__(self,user_id,rows,akumas=None):
        super().__init__(timeout=300)
        itens=[(r['item_id'],r['quantidade']) for r in rows if r['item_id'] in ITENS]
        if itens:self.add_item(ItemSelect(user_id,itens,"inventario"))
        if akumas:self.add_item(AkumaSelect(user_id,akumas))

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
    def __init__(self,bot): self.bot=bot; self.relogio_viagens.start()
    def cog_unload(self): self.relogio_viagens.cancel()

    async def local_ctx(self,ctx):
        canal=normalizar_destino(getattr(ctx.channel,"name",None))
        if canal in LOCAIS: return canal
        loc=await buscar_localizacao_jogador(ctx.author.id)
        return normalizar_destino(loc["localizacao"] if loc else None)

    @commands.command(aliases=["inv","mochila"])
    async def inventario(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        rows=await buscar_inventario(ctx.author.id)
        akumas_lista=list(await listar_akumas_inventario(ctx.author.id))
        emb=discord.Embed(title="🎒 INVENTÁRIO",description="━━━━━━━━━━━━━━━━━━",color=COR)
        emb.add_field(name="💰 Berries",value=dinheiro(ficha['berries']),inline=False)
        if not rows: emb.add_field(name="📦 Itens",value="Seu inventário está vazio.",inline=False)
        else:
            grupos={}
            akumas={a['item_id']:a for a in akumas_lista}
            for r in rows:
                d=ITENS.get(r['item_id'])
                if d:
                    grupos.setdefault(d['categoria'],[]).append(f"{d['emoji']} **{d['nome']}** ×{r['quantidade']}")
                elif r['item_id'] in akumas:
                    a=akumas[r['item_id']]
                    grupos.setdefault('akuma no mi',[]).append(f"🍈 **{a['nome']}** • {a['tipo'].title()} ×{r['quantidade']}")
                else:
                    grupos.setdefault('outros',[]).append(f"📦 **{r['item_id']}** ×{r['quantidade']}")
            for cat,linhas in grupos.items(): emb.add_field(name=f"📦 {cat.title()}",value="\n".join(linhas)[:1024],inline=False)
        await ctx.send(embed=emb,view=InventarioView(ctx.author.id,rows,akumas_lista) if rows else None)

    @commands.command()
    async def loja(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        local=await self.local_ctx(ctx); local,loja=loja_local(local)
        if not loja:return await ctx.send(f"🏪 Não há loja configurada em **{local or 'localização desconhecida'}**.")
        emb=discord.Embed(title=f"🏪 MERCADO — {local.upper()}",description=f"💰 Seus Berries: **{dinheiro(ficha['berries'])}**\n\nSelecione um item abaixo para ver detalhes e comprar.",color=COR)
        if loja['barcos']: emb.add_field(name="🚢 Estaleiro",value="Use `!estaleiro` para embarcações.",inline=False)
        await ctx.send(embed=emb,view=LojaView(ctx.author.id,loja))

    @commands.command()
    async def estaleiro(self,ctx):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        local=await self.local_ctx(ctx); local,loja=loja_local(local)
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
        local=await self.local_ctx(ctx); destinos=destinos_de(local)
        if not destinos:return await ctx.send(f"🧭 Não há rotas cadastradas partindo de **{local or 'localização desconhecida'}**.")
        linhas=[]
        for d in destinos:
            r=ROTAS_INFO[(local,d)]; linhas.append(f"• **{d}** — {r['minutos']} min base • perigo {r['perigo']}/5 • {r['suprimentos']} suprimento(s)")
        await ctx.send(f"🧭 **ROTAS — {local}**\n"+"\n".join(linhas)[:3800])

    async def bonus_navegador(self,user_id):
        specs=await buscar_especializacoes(user_id); sp=next((x for x in specs if x['categoria']=='profissao' and x['nome']=='Navegador'),None)
        p=int(sp['porcentagem']) if sp else 0
        custo=0.5 if p>=200 else 0.7 if p>=120 else 0.8 if p>=80 else 0.9 if p>=40 else 1.0
        tempo=0.5 if p>=200 else 0.8 if p>=160 else 1.0
        return p,custo,tempo

    async def pct_carpinteiro(self,user_id):
        specs=await buscar_especializacoes(user_id); sp=next((x for x in specs if x['categoria']=='profissao' and x['nome']=='Carpinteiro'),None)
        return int(sp['porcentagem']) if sp else 0

    async def pode_embarcar(self,user_id,origem):
        if await buscar_viagem_ativa(user_id): return False,"já está em uma viagem"
        if await buscar_treinamento_ativo(user_id): return False,"está treinando"
        if await buscar_sessao_ativa_usuario(user_id): return False,"está em uma cena ativa"
        if await evento_ativo_usuario(user_id): return False,"está em um evento global"
        if await boss_rp_ativo_usuario(user_id): return False,"está enfrentando um Boss de progressão"
        loc=await buscar_localizacao_jogador(user_id); atual=normalizar_destino(loc['localizacao'] if loc else None)
        if atual!=origem:return False,f"está em {atual or 'local desconhecido'}, não em {origem}"
        return True,None

    async def iniciar_plano_se_pronto(self,ctx,plano):
        embarcados=await listar_embarques(plano['id'])
        if len(embarcados)<plano['vagas']:
            return False
        # Revalida todos no instante da partida para impedir teleportes/estados concorrentes.
        for m in embarcados:
            ok,motivo=await self.pode_embarcar(m['user_id'],plano['origem'])
            if not ok:
                await ctx.send(f"❌ **{m['nome']}** não pode partir agora: {motivo}. Use `!desembarcar` (se não for o capitão) ou resolva o estado antes de `!partir`.")
                return False
        r=ROTAS_INFO.get((plano['origem'],plano['destino']))
        if not r:return False
        # O melhor Navegador realmente conduz a viagem, mesmo que não seja o dono do navio.
        navs=[]
        for m in embarcados:
            p,_,_=await self.bonus_navegador(m['user_id']); navs.append((p,m))
        pnav,navm=max(navs,key=lambda x:x[0]) if navs else (0,None)
        mult_custo=0.5 if pnav>=200 else 0.7 if pnav>=120 else 0.8 if pnav>=80 else 0.9 if pnav>=40 else 1.0
        mult_tempo=0.5 if pnav>=200 else 0.8 if pnav>=160 else 1.0
        supr=max(1,round(r['suprimentos']*len(embarcados)*mult_custo))
        inv=await buscar_item_inventario(plano['proprietario_id'],'mantimentos')
        if not inv or inv['quantidade']<supr:
            await ctx.send(f"📦 O grupo está completo, mas o capitão precisa de **{supr} Caixa(s) de Mantimentos** para {len(embarcados)} viajante(s). Depois use `!partir`.")
            return False
        await consumir_item(plano['proprietario_id'],'mantimentos',supr)
        minutos=max(10,round(r['minutos']*mult_tempo)); chegada=datetime.now(timezone.utc)+timedelta(minutes=minutos)
        eventos=max(0,r['perigo']-1); primeiro=datetime.now(timezone.utc)+timedelta(minutes=max(5,minutos/(eventos+1))) if eventos else None
        ids=[m['user_id'] for m in embarcados]
        v=await criar_viagem(plano['proprietario_id'],plano['embarcacao_id'],plano['origem'],plano['destino'],plano['canal_id'],chegada,primeiro,eventos,supr,r['desgaste'],ids)
        await fechar_plano_viagem(plano['id'])
        for uid in ids: await definir_localizacao_jogador(uid,'Em alto-mar',f"{plano['origem']} → {plano['destino']}")
        await registrar_transacao_economia(plano['proprietario_id'],'viagem',0,None,supr,f"{plano['origem']} -> {plano['destino']} ({len(ids)} pessoas)")
        nomes=', '.join(m['nome'] for m in embarcados)
        navtxt=f"{navm['nome']} — {pnav}%" if navm else 'Nenhum — 0%'
        await ctx.send(f"⛵ **VIAGEM INICIADA**\n🧭 {plano['origem']} → **{plano['destino']}**\n👥 A bordo: **{len(ids)}/{plano['vagas']}** — {nomes}\n🧭 Navegador responsável: **{navtxt}**\n⏱️ Previsão: **{minutos} min**\n📦 Mantimentos: **-{supr}**\n❤️ Desgaste previsto: **-{r['desgaste']}**\n⚠️ Perigo: **{r['perigo']}/5**\n\nObstáculos e chegada valem para **todo mundo a bordo**.")
        return True

    @commands.command()
    async def viajar(self,ctx,*,destino:str):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        if await buscar_plano_viagem_user(ctx.author.id):return await ctx.send("⛵ Você já está em um embarque aberto. Use `!embarquestatus` ou `!cancelarviagem`.")
        ok,motivo=await self.pode_embarcar(ctx.author.id,await self.local_ctx(ctx))
        if not ok:return await ctx.send(f"❌ Você não pode preparar viagem agora: {motivo}.")
        origem=await self.local_ctx(ctx); destino=normalizar_destino(destino); r=ROTAS_INFO.get((origem,destino))
        if not r:return await ctx.send(f"❌ Não há rota direta **{origem} → {destino}**. Use `!rotas`.")
        navio=await buscar_embarcacao_ativa(ctx.author.id)
        if not navio:return await ctx.send("❌ Você precisa ser dono de uma embarcação ativa para preparar a viagem.")
        if normalizar_destino(navio['localizacao'])!=origem:return await ctx.send(f"❌ Seu navio está em **{navio['localizacao']}**.")
        req=r['requisito']
        if req=='log_pose' and not await buscar_item_inventario(ctx.author.id,'log_pose'):return await ctx.send("🧭 Esta rota exige **Log Pose**.")
        if req=='revestimento' and not await buscar_item_inventario(ctx.author.id,'revestimento_navio'):return await ctx.send("🫧 Esta descida exige **Revestimento de Sabaody**.")
        if req in ('knock_up_or_special','calm_belt','government_or_special','special','road_poneglyphs','eternal_or_route'):
            liberada=await rota_especial_liberada(ctx.author.id,destino); eternal=next((iid for iid,d in ITENS.items() if d.get('destino')==destino),None); possui=bool(eternal and await buscar_item_inventario(ctx.author.id,eternal))
            if not liberada and not possui:return await ctx.send(f"🔒 Essa rota possui requisito especial (**{req}**).")
        maximo=max(1,int(navio['capacidade']))
        cog=self
        class QuantidadeModal(discord.ui.Modal,title='Definir passageiros'):
            quantidade=discord.ui.TextInput(label=f'Quantas pessoas? (1 a {maximo})',placeholder='Ex.: 5',max_length=3)
            async def on_submit(modal_self,i):
                if i.user.id!=ctx.author.id:return await i.response.send_message('❌ Apenas o dono do navio escolhe.',ephemeral=True)
                try:vagas=int(str(modal_self.quantidade.value).strip())
                except ValueError:return await i.response.send_message('❌ Digite apenas um número.',ephemeral=True)
                if vagas<1 or vagas>maximo:return await i.response.send_message(f'❌ Este navio comporta de **1 a {maximo}** pessoas.',ephemeral=True)
                p=await criar_plano_viagem(ctx.author.id,navio['id'],origem,destino,ctx.channel.id,vagas)
                if not p:return await i.response.send_message('❌ Você já possui/participa de um embarque aberto.',ephemeral=True)
                await i.response.send_message(f"⚓ **EMBARQUE ABERTO — {navio['nome']}**\n🧭 {origem} → **{destino}**\n👥 Lugares desta viagem: **1/{vagas}**\n👑 O dono do navio já está embarcado.\n\nOs demais usam **`!embarcar`** neste canal. Ao atingir **{vagas}**, o bot tenta partir automaticamente.\nUse **`!cancelarviagem`** para cancelar antes da partida.")
                if vagas==1: await cog.iniciar_plano_se_pronto(ctx,p)
        class QuantidadeView(discord.ui.View):
            def __init__(view_self):super().__init__(timeout=120)
            @discord.ui.button(label='Definir quantidade',emoji='👥',style=discord.ButtonStyle.primary)
            async def definir(view_self,i,b):
                if i.user.id!=ctx.author.id:return await i.response.send_message('❌ Apenas o dono do navio escolhe.',ephemeral=True)
                await i.response.send_modal(QuantidadeModal())
        await ctx.send(f"🚢 **PREPARAR VIAGEM — {navio['nome']}**\n🧭 {origem} → **{destino}**\nQuantas pessoas irão nesta viagem?",view=QuantidadeView())

    @commands.command()
    async def embarcar(self,ctx):
        if await buscar_plano_viagem_user(ctx.author.id):return await ctx.send('⚓ Você já está em um embarque aberto.')
        p=await buscar_plano_viagem_canal(ctx.channel.id)
        if not p:return await ctx.send('❌ Não existe embarque aberto neste canal.')
        ok,motivo=await self.pode_embarcar(ctx.author.id,p['origem'])
        if not ok:return await ctx.send(f'❌ Você não pode embarcar: {motivo}.')
        certo,msg=await embarcar_plano(p['id'],ctx.author.id)
        if not certo:return await ctx.send('❌ '+msg)
        ms=await listar_embarques(p['id']); await ctx.send(f"⚓ {ctx.author.mention} embarcou. **{len(ms)}/{p['vagas']}** a bordo.")
        if len(ms)>=p['vagas']: await self.iniciar_plano_se_pronto(ctx,p)

    @commands.command()
    async def desembarcar(self,ctx):
        p=await buscar_plano_viagem_user(ctx.author.id)
        if not p:return await ctx.send('❌ Você não está aguardando uma viagem.')
        if p['proprietario_id']==ctx.author.id:return await ctx.send('👑 O dono do navio não desembarca do próprio plano. Use `!cancelarviagem`.')
        await desembarcar_plano(ctx.author.id); await ctx.send(f'⚓ {ctx.author.mention} desembarcou antes da partida.')

    @commands.command()
    async def embarquestatus(self,ctx):
        p=await buscar_plano_viagem_user(ctx.author.id) or await buscar_plano_viagem_canal(ctx.channel.id)
        if not p:return await ctx.send('⚓ Não há embarque aberto aqui.')
        ms=await listar_embarques(p['id']); await ctx.send(f"⚓ **EMBARQUE — {p['origem']} → {p['destino']}**\n👥 **{len(ms)}/{p['vagas']}**\n"+'\n'.join(f"• {m['nome']}" for m in ms))

    @commands.command()
    async def partir(self,ctx):
        p=await buscar_plano_viagem_user(ctx.author.id)
        if not p or p['proprietario_id']!=ctx.author.id:return await ctx.send('❌ Você não possui embarque aberto como dono do navio.')
        ms=await listar_embarques(p['id'])
        if len(ms)<p['vagas']:return await ctx.send(f"⏳ Ainda faltam **{p['vagas']-len(ms)}** pessoa(s) embarcar.")
        await self.iniciar_plano_se_pronto(ctx,p)

    @commands.command()
    async def cancelarviagem(self,ctx):
        p=await buscar_plano_viagem_user(ctx.author.id)
        if p:
            if p['proprietario_id']!=ctx.author.id:return await ctx.send('❌ Apenas o dono do navio pode cancelar o embarque. Você pode usar `!desembarcar`.')
            await cancelar_plano_viagem(ctx.author.id); return await ctx.send('🛑 **Embarque cancelado.** Ninguém foi movido e nenhum mantimento foi gasto.')
        if await buscar_viagem_ativa(ctx.author.id):return await ctx.send('🌊 A embarcação já partiu. A viagem ativa não pode ser cancelada como se nunca tivesse acontecido.')
        await ctx.send('ℹ️ Você não possui embarque/viagem para cancelar.')

    @commands.command()
    async def viagemstatus(self,ctx):
        v=await buscar_viagem_ativa(ctx.author.id)
        if not v:return await ctx.send("🧭 Você não está em viagem.")
        resto=max(timedelta(),v['chegada_em']-datetime.now(timezone.utc)); mins=int(resto.total_seconds()//60)
        ev=await evento_aberto_viagem(v['id'])
        await ctx.send(f"⛵ **VIAGEM EM CURSO**\n{v['origem']} → **{v['destino']}**\n⏳ ~{mins} min restantes\n⚠️ Estado: **{'obstáculo pendente' if ev else 'navegando'}**"+(f"\n\n{ev['titulo']}: {ev['descricao']}" if ev else ''))

    @commands.command(aliases=['acaoviagem'])
    async def resolverviagem(self,ctx,*,acao:str):
        v=await buscar_viagem_ativa(ctx.author.id)
        if not v:return await ctx.send("❌ Você não está viajando.")
        ev=await evento_aberto_viagem(v['id'])
        if not ev:return await ctx.send("ℹ️ Não há obstáculo pendente.")
        # Resultado mecânico simples e imparcial; a ação do player influencia pelo conteúdo e profissões.
        pnav,_,_=await self.bonus_navegador(ctx.author.id); pcarp=await self.pct_carpinteiro(ctx.author.id)
        chance=55 + min(25,pnav//8) + min(15,pcarp//12)
        sucesso=random.randint(1,100)<=chance
        if sucesso:
            atraso=0; dano=0; resultado="A solução funcionou e a embarcação conseguiu superar o obstáculo sem consequência grave."
        else:
            atraso=random.choice([10,15,20]); dano=random.choice([5,10,15]); resultado=f"A tentativa não resolveu tudo a tempo: a viagem sofre +{atraso} min e o casco perde {dano} de integridade."
        nv=await resolver_evento_viagem(v['id'],acao[:1000],resultado,atraso,dano)
        if nv and nv['eventos_restantes']>0:
            intervalo=max(5,int((nv['chegada_em']-datetime.now(timezone.utc)).total_seconds()/60/(nv['eventos_restantes']+1)))
            await agendar_proximo_evento_viagem(nv['id'],datetime.now(timezone.utc)+timedelta(minutes=intervalo))
        await ctx.send(f"🌊 **OBSTÁCULO RESOLVIDO**\n> {acao[:700]}\n\n{resultado}")

    @commands.command()
    async def repararnavio(self,ctx,modo:str='estaleiro'):
        n=await buscar_embarcacao_ativa(ctx.author.id)
        if not n:return await ctx.send("❌ Você não possui embarcação ativa.")
        faltando=n['integridade_max']-n['integridade_atual']
        if faltando<=0:return await ctx.send("❤️ Seu navio já está em integridade máxima.")
        carp=await self.pct_carpinteiro(ctx.author.id)
        if modo.casefold() in ('kit','campo'):
            item=await buscar_item_inventario(ctx.author.id,'kit_reparo')
            if not item:return await ctx.send("🔧 Você precisa de **Kit de Reparo Naval**.")
            base=50; bonus=1.5 if carp>=200 else 1.35 if carp>=160 else 1.25 if carp>=120 else 1.15 if carp>=80 else 1.1 if carp>=40 else 1.0
            await consumir_item(ctx.author.id,'kit_reparo',1); novo=await reparar_embarcacao(n['id'],round(base*bonus))
            return await ctx.send(f"🔨 **REPARO DE CAMPO**\nCarpinteiro: **{carp}%**\n❤️ {n['integridade_atual']} → **{novo['integridade_atual']} / {novo['integridade_max']}**")
        local=await self.local_ctx(ctx)
        if local not in LOJAS:return await ctx.send("⚓ Não há estrutura de reparo naval configurada aqui. Use um kit em campo.")
        desconto=0.30 if carp>=160 else 0.20 if carp>=40 else 0
        custo=max(1000,round(faltando*100*(1-desconto)))
        if ficha:=await buscar_ficha(ctx.author.id):
            if ficha['berries']<custo:return await ctx.send(f"❌ Reparo completo custa **{dinheiro(custo)}**.")
        # reutiliza compra transacional com item técnico e devolve item imediatamente não seria ideal; débito direto via helper abaixo
        from database.database import pagar_reparo_embarcacao
        ok=await pagar_reparo_embarcacao(ctx.author.id,n['id'],custo)
        await ctx.send(f"⚓ **ESTALEIRO**\n💰 Custo: **{dinheiro(custo)}**\n🔨 Carpinteiro: **{carp}%**\n❤️ Embarcação restaurada." if ok else "❌ Não foi possível concluir o reparo.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def liberarrota(self,ctx,membro:discord.Member,*,destino:str):
        destino=normalizar_destino(destino)
        if destino not in LOCAIS:return await ctx.send("❌ Destino não reconhecido no mapa de navegação.")
        await liberar_rota_especial(membro.id,destino,None,f"liberado por {ctx.author.id}")
        await ctx.send(f"🗺️ Rota especial para **{destino}** liberada para {membro.mention}.")

    @tasks.loop(seconds=30)
    async def relogio_viagens(self):
        agora=datetime.now(timezone.utc)
        for v in await viagens_pendentes():
            ch=self.bot.get_channel(v['canal_id']) if v['canal_id'] else None
            if v['status']=='obstaculo': continue
            if v['eventos_restantes']>0 and v['proximo_evento_em'] and agora>=v['proximo_evento_em']:
                perigo=ROTAS_INFO.get((v['origem'],v['destino']),{}).get('perigo',2); emoji,titulo,desc=random.choice(OBSTACULOS.get(perigo,OBSTACULOS[2]))
                await criar_evento_viagem(v['id'],f"{emoji} {titulo}",desc)
                if ch:
                    try:
                        ps=await passageiros_viagem(v['id']); mencoes=' '.join(f"<@{x['user_id']}>" for x in ps) or f"<@{v['user_id']}>"
                        await ch.send(f"{mencoes}\n{emoji} **OBSTÁCULO DE VIAGEM — {titulo.upper()}**\n{desc}\n\nQualquer pessoa a bordo pode responder com `!resolverviagem <ação>`. **O relógio da chegada continua, mas a viagem não conclui enquanto o obstáculo estiver pendente.**")
                    except: pass
                continue
            if agora>=v['chegada_em']:
                fim=await concluir_viagem(v['id'])
                if fim and ch:
                    try:
                        ps=await passageiros_viagem(fim['id']); mencoes=' '.join(f"<@{x['user_id']}>" for x in ps) or f"<@{v['user_id']}>"
                        await ch.send(f"{mencoes} 🏝️ **DESTINO ALCANÇADO!**\n🧭 **{fim['destino']}**\n🚢 A embarcação chegou ao destino e a localização de **todos a bordo** foi atualizada. O Narrador já pode continuar a aventura normalmente daqui.")
                    except: pass
    @relogio_viagens.before_loop
    async def antes_relogio(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(Economia(bot))
