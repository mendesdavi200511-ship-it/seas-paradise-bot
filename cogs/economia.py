import discord
import random
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks

from data.economia import ITENS, EMBARCACOES, LOJAS, normalizar_local
from data.navegacao import LOCAIS, ROTAS_INFO, OBSTACULOS, destinos_de, normalizar_destino
from database.database import (
    buscar_ficha, buscar_localizacao_jogador, definir_localizacao_jogador,
    buscar_inventario, buscar_item_inventario, comprar_item, vender_item,
    consumir_item, comprar_embarcacao, buscar_embarcacoes, buscar_embarcacao_ativa,
    renomear_embarcacao, reparar_embarcacao, registrar_transacao_economia, buscar_especializacoes,
    buscar_viagem_ativa, criar_viagem, viagens_pendentes, criar_evento_viagem, evento_aberto_viagem, liberar_rota_especial, rota_especial_liberada,
    resolver_evento_viagem, agendar_proximo_evento_viagem, concluir_viagem, danificar_embarcacao, mover_embarcacao,
    buscar_treinamento_ativo, buscar_sessao_ativa_usuario,
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

    @commands.command()
    async def viajar(self,ctx,*,destino:str):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        if await buscar_viagem_ativa(ctx.author.id):return await ctx.send("⛵ Você já está em viagem. Use `!viagemstatus`.")
        treino=await buscar_treinamento_ativo(ctx.author.id)
        if treino:return await ctx.send(f"🏋️ Você está treinando **{treino['alvo']}** e não pode viajar até concluir ou usar `!cancelartreino`.")
        sessao=await buscar_sessao_ativa_usuario(ctx.author.id)
        if sessao:return await ctx.send("🎭 Você está participando de uma cena ativa e não pode iniciar uma viagem agora.")
        origem=await self.local_ctx(ctx); destino=normalizar_destino(destino)
        r=ROTAS_INFO.get((origem,destino))
        if not r:return await ctx.send(f"❌ Não há rota direta **{origem} → {destino}**. Use `!rotas`.")
        navio=await buscar_embarcacao_ativa(ctx.author.id)
        if not navio:return await ctx.send("❌ Você precisa de uma embarcação ativa.")
        if normalizar_destino(navio['localizacao'])!=origem:return await ctx.send(f"❌ Seu navio está em **{navio['localizacao']}**.")
        req=r['requisito']
        if req=='log_pose' and not await buscar_item_inventario(ctx.author.id,'log_pose'):return await ctx.send("🧭 Esta rota exige **Log Pose**.")
        if req=='revestimento' and not await buscar_item_inventario(ctx.author.id,'revestimento_navio'):return await ctx.send("🫧 Esta descida exige **Revestimento de Sabaody**.")
        if req in ('knock_up_or_special','calm_belt','government_or_special','special','road_poneglyphs','eternal_or_route'):
            liberada=await rota_especial_liberada(ctx.author.id,destino)
            eternal=next((iid for iid,d in ITENS.items() if d.get('destino')==destino),None)
            possui_eternal=bool(eternal and await buscar_item_inventario(ctx.author.id,eternal))
            if not liberada and not possui_eternal:
                return await ctx.send(f"🔒 Essa rota possui requisito especial (**{req}**). Ela precisa ser conquistada no RP/liberada pelo Mestre ou possuir um Eternal Pose válido para o destino.")
        pnav,mult_custo,mult_tempo=await self.bonus_navegador(ctx.author.id)
        supr=max(1,round(r['suprimentos']*mult_custo)); inv=await buscar_item_inventario(ctx.author.id,'mantimentos')
        if not inv or inv['quantidade']<supr:return await ctx.send(f"📦 A viagem exige **{supr} Caixa(s) de Mantimentos**.")
        await consumir_item(ctx.author.id,'mantimentos',supr)
        minutos=max(10,round(r['minutos']*mult_tempo)); chegada=datetime.now(timezone.utc)+timedelta(minutes=minutos)
        eventos=max(0,r['perigo']-1); primeiro=None
        if eventos: primeiro=datetime.now(timezone.utc)+timedelta(minutes=max(5,minutos/(eventos+1)))
        v=await criar_viagem(ctx.author.id,navio['id'],origem,destino,ctx.channel.id,chegada,primeiro,eventos,supr,r['desgaste'])
        await definir_localizacao_jogador(ctx.author.id,f"Em alto-mar",f"{origem} → {destino}")
        await registrar_transacao_economia(ctx.author.id,'viagem',0,None,supr,f"{origem} -> {destino}")
        await ctx.send(f"⛵ **VIAGEM INICIADA**\n🧭 {origem} → **{destino}**\n🚢 {navio['nome']}\n⏱️ Previsão: **{minutos} min**\n📦 Mantimentos: **-{supr}**\n❤️ Desgaste previsto: **-{r['desgaste']}**\n⚠️ Perigo: **{r['perigo']}/5**\n🧭 Navegador: **{pnav}%**\n\nDurante a viagem o Narrador pode narrar normalmente em **alto-mar**. Eu aviso obstáculos e a chegada automaticamente.")

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
                    try: await ch.send(f"<@{v['user_id']}>\n{emoji} **OBSTÁCULO DE VIAGEM — {titulo.upper()}**\n{desc}\n\nDescreva o que fará com `!resolverviagem <ação>`. **O relógio da chegada continua, mas a viagem não conclui enquanto o obstáculo estiver pendente.**")
                    except: pass
                continue
            if agora>=v['chegada_em']:
                fim=await concluir_viagem(v['id'])
                if fim and ch:
                    try: await ch.send(f"<@{v['user_id']}> 🏝️ **DESTINO ALCANÇADO!**\n🧭 **{fim['destino']}**\n🚢 A embarcação chegou ao destino e sua localização foi atualizada. O Narrador já pode continuar a aventura normalmente daqui.")
                    except: pass
    @relogio_viagens.before_loop
    async def antes_relogio(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(Economia(bot))
