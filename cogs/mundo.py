import os, io, json, random, asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands, tasks
from openai import AsyncOpenAI

from data.navegacao import LOCAIS, normalizar_destino
from data.mundo import BOSS_RANKS, BOSSES_ESPECIAIS, MISSOES_MARINHA, PESCAS, info_ilha
from database.database import (
    buscar_ficha,buscar_localizacao_jogador,buscar_especializacoes,buscar_treinamento_ativo,buscar_viagem_ativa,buscar_sessao_ativa_usuario,
    criar_evento_global,listar_eventos_globais_abertos,buscar_evento_global,vincular_evento_thread,participar_evento_global,status_participacao_evento,
    evento_ativo_usuario,participantes_evento,marcar_evento_andamento,desistir_evento,buscar_sessao_por_id,concluir_evento_global,finalizar_participantes_evento,
    eventos_para_finalizar,obter_ou_criar_sessao,entrar_sessao,marcar_sessao_iniciada,marcar_participante_sessao,
    adicionar_berries,adicionar_pontos_atributo,adicionar_pontos_percentuais,adicionar_reputacao,adicionar_item_inventario,
    definir_dominacao_ilha,buscar_dominacao_ilha,criar_subordinado,listar_subordinados,criar_cacada,listar_cacadas,registrar_descoberta,listar_descobertas,
    registrar_transacao_economia,definir_hp_evento,candidatos_cacada,
)

CANAL_EVENTOS_ID=1552724689485430874
CANAL_REPORT_ID=1552727936400887839
CARGO_REPORT_ID=1541858353196695632
COR=discord.Color.from_rgb(184,139,55)
COMANDOS_EVENTO={"acao","ação","pronto","combate","resolver","resolvercena","resumo","encerrar","sessao","sessão","desistirevento","eventostatus","report","ajuda","help","comandos"}


def dinheiro(v): return f"฿ {int(v):,}".replace(",", ".")

def recompensa_rank(rank):
    d=BOSS_RANKS[rank]
    return {"berries":random.randint(*d['berries']),"pontos":random.randint(*d['pontos']),"percentual":random.randint(*d['pct']),"reputacao":max(5,d['pontos'][0]//2)}

async def gerar_poster_fallback(titulo,rank,local):
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGB',(1024,1024),(38,28,18)); dr=ImageDraw.Draw(im)
    for x in range(35,990,95): dr.line((x,0,x-120,1024),fill=(58,42,26),width=3)
    try: f1=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',64); f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',38)
    except: f1=f2=None
    dr.rounded_rectangle((90,100,934,924),radius=20,fill=(224,204,157),outline=(72,45,24),width=12)
    dr.text((512,165),'WANTED / BOSS',anchor='mm',fill=(85,25,18),font=f1)
    dr.ellipse((340,280,684,624),fill=(45,40,38)); dr.text((512,680),titulo[:28],anchor='mm',fill=(40,25,18),font=f1)
    dr.text((512,770),f'RANK {rank}  •  {local}',anchor='mm',fill=(70,40,20),font=f2)
    b=io.BytesIO(); im.save(b,'PNG'); b.seek(0); return b

class EventoView(discord.ui.View):
    def __init__(self,cog,evento_id):
        super().__init__(timeout=None); self.cog=cog; self.evento_id=int(evento_id)
        b=discord.ui.Button(label='Participar',emoji='⚔️',style=discord.ButtonStyle.success,custom_id=f'sp:evento:{evento_id}')
        b.callback=self.aceitar; self.add_item(b)
    async def aceitar(self,interaction): await self.cog.aceitar_evento(interaction,self.evento_id)

class Mundo(commands.Cog):
    def __init__(self,bot):
        self.bot=bot; self.client=AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        bot.add_check(self.estado_global_check)
        self.relogio_mundo.start()
    def cog_unload(self):
        self.relogio_mundo.cancel(); self.bot.remove_check(self.estado_global_check)

    async def estado_global_check(self,ctx):
        if not ctx.command:return True
        ev=await evento_ativo_usuario(ctx.author.id)
        if not ev:return True
        if ctx.command.name in COMANDOS_EVENTO:return True
        if getattr(ctx.channel,'id',None)==ev['thread_id'] and ctx.command.name in COMANDOS_EVENTO:return True
        await ctx.send(f"🎯 **EVENTO ATIVO — {ev['titulo']}**\nEnquanto participa, seu personagem fica dedicado a este evento. Termine a narrativa ou use `!desistirevento`.")
        return False

    async def restaurar_views(self):
        for e in await listar_eventos_globais_abertos():
            if e['mensagem_id']:
                try:self.bot.add_view(EventoView(self,e['id']),message_id=e['mensagem_id'])
                except:pass

    async def gerar_imagem_boss(self,nome,rank,local):
        if self.client:
            try:
                r=await self.client.images.generate(model='gpt-image-1',prompt=f"Original One Piece-inspired anime pirate RPG boss poster, full body fictional boss named {nome}, Rank {rank}, setting inspired by {local}, dramatic wanted poster composition, no copyrighted character likeness, no logos, readable title only: {nome}",size='1024x1024')
                import base64
                return io.BytesIO(base64.b64decode(r.data[0].b64_json))
            except Exception as e: print('⚠️ imagem boss fallback:',type(e).__name__,e)
        return await gerar_poster_fallback(nome,rank,local)

    async def publicar_evento(self,tipo,titulo,descricao,local,rank,exclusivo=False):
        ch=self.bot.get_channel(CANAL_EVENTOS_ID)
        if not ch:return None
        rec=recompensa_rank(rank); exp=datetime.now(timezone.utc)+timedelta(hours=24)
        e=await criar_evento_global(tipo,titulo,descricao,local,rank,rec,ch.id,exp,exclusivo)
        hp=BOSS_RANKS[rank]['hp'] if tipo in ('boss','invasao') else None
        if hp: await definir_hp_evento(e['id'],hp)
        emb=discord.Embed(title=("⚓ MISSÃO DA MARINHA" if tipo=='missao' else "👹 BOSS ESPECIAL")+f" — {titulo}",description=descricao,color=discord.Color.blue() if tipo=='missao' else discord.Color.red())
        emb.add_field(name='📍 Localização',value=local); emb.add_field(name='⚠️ Rank',value=rank); emb.add_field(name='⏳ Disponível',value='24 horas')
        if hp: emb.add_field(name='❤️ HP do Boss',value=f'{hp:,}'.replace(',', '.'),inline=True)
        emb.add_field(name='🎁 Recompensas',value=f"{dinheiro(rec['berries'])}\n+{rec['pontos']} pontos de atributo\n+{rec['percentual']}% percentual\n+{rec['reputacao']} reputação",inline=False)
        if exclusivo: emb.set_footer(text='Exclusivo para personagens da Marinha • uma tentativa por instância')
        else: emb.set_footer(text='Boss global • você pode participar de outros bosses, mas não repetir esta instância')
        file=None
        if tipo=='boss':
            buf=await self.gerar_imagem_boss(titulo,rank,local); file=discord.File(buf,filename=f'boss_{e["id"]}.png'); emb.set_image(url=f'attachment://boss_{e["id"]}.png')
        msg=await ch.send(embed=emb,view=EventoView(self,e['id']),file=file)
        from database.database import get_pool
        await get_pool().execute('UPDATE eventos_globais SET mensagem_id=$2 WHERE id=$1;',e['id'],msg.id)
        return e

    async def aceitar_evento(self,interaction,evento_id):
        e=await buscar_evento_global(evento_id)
        if not e or e['status'] not in ('aberto','andamento') or e['expira_em']<=datetime.now(timezone.utc):
            return await interaction.response.send_message('⌛ Este evento não está mais disponível.',ephemeral=True)
        ficha=await buscar_ficha(interaction.user.id)
        if not ficha:return await interaction.response.send_message('❌ Você não possui ficha.',ephemeral=True)
        antigo=await status_participacao_evento(evento_id,interaction.user.id)
        if antigo and antigo['status'] in ('concluido','desistiu'):
            return await interaction.response.send_message('🚫 Você já encerrou sua participação nesta instância e não pode repeti-la.',ephemeral=True)
        outro=await evento_ativo_usuario(interaction.user.id)
        if outro and outro['id']!=evento_id:return await interaction.response.send_message('🎯 Você já está em outro evento.',ephemeral=True)
        if await buscar_treinamento_ativo(interaction.user.id) or await buscar_viagem_ativa(interaction.user.id) or await buscar_sessao_ativa_usuario(interaction.user.id):
            return await interaction.response.send_message('🚫 Termine seu treino, viagem ou cena atual antes de aceitar.',ephemeral=True)
        if e['exclusivo_marinha'] and 'marinha' not in (ficha['faccao'] or '').casefold():
            return await interaction.response.send_message('⚓ Esta missão é exclusiva da Marinha.',ephemeral=True)
        thread=None
        if e['thread_id']:
            try:thread=interaction.guild.get_thread(e['thread_id']) or await interaction.guild.fetch_channel(e['thread_id'])
            except:pass
        if not thread:
            await interaction.response.defer(ephemeral=True)
            thread=await interaction.message.create_thread(name=f"{e['tipo'].upper()} • {e['titulo']}"[:100],auto_archive_duration=1440)
            s=await obter_ou_criar_sessao(interaction.guild.id,thread.id,e['localizacao'],None); await marcar_sessao_iniciada(s['id']); await marcar_evento_andamento(e['id']); await vincular_evento_thread(e['id'],thread.id,s['id'])
            await thread.send(f"🎭 **EVENTO INICIADO — {e['titulo']}**\n📍 {e['localizacao']} • Rank {e['rank']}\nUse `!acao` normalmente. Outros jogadores elegíveis podem entrar pelo botão do mural.\nPara abandonar: `!desistirevento`. Quando a sessão for encerrada, as recompensas são entregues automaticamente.")
            e=await buscar_evento_global(evento_id)
        else:
            if not interaction.response.is_done(): await interaction.response.defer(ephemeral=True)
        s=await buscar_sessao_por_id(e['sessao_id']); await participar_evento_global(e['id'],interaction.user.id,ficha['nome']); await entrar_sessao(s['id'],interaction.user.id,ficha['nome'])
        try: await thread.add_user(interaction.user)
        except:pass
        await interaction.followup.send(f"✅ Você entrou em **{e['titulo']}**. Continue em {thread.mention}.",ephemeral=True)
        await thread.send(f"➕ {interaction.user.mention} (**{ficha['nome']}**) entrou no evento.")

    @commands.command()
    async def desistirevento(self,ctx):
        e=await evento_ativo_usuario(ctx.author.id)
        if not e:return await ctx.send('ℹ️ Você não está em evento global.')
        p=await desistir_evento(e['id'],ctx.author.id)
        if p and e['sessao_id']: await marcar_participante_sessao(e['sessao_id'],ctx.author.id,'saiu')
        await ctx.send('🏳️ Você desistiu deste evento. **Esta instância não poderá ser repetida por você.**')

    @commands.command()
    async def eventostatus(self,ctx):
        e=await evento_ativo_usuario(ctx.author.id)
        if not e:return await ctx.send('📭 Você não está participando de evento.')
        await ctx.send(f"🎯 **{e['titulo']}** • Rank {e['rank']}\n📍 {e['localizacao']}\n<#${e['thread_id']}>".replace('<#$','<#'))

    @commands.command()
    async def bossstatus(self,ctx):
        e=await evento_ativo_usuario(ctx.author.id)
        if not e or e['tipo'] not in ('boss','invasao'): return await ctx.send('👹 Você não está em um evento de Boss.')
        hp=e['hp_atual'] if 'hp_atual' in e else None; mx=e['hp_max'] if 'hp_max' in e else None
        await ctx.send(f"👹 **{e['titulo']}** • Rank **{e['rank']}**\n❤️ HP: **{hp if hp is not None else '?'} / {mx if mx is not None else '?'}**\n📍 {e['localizacao']}")

    @commands.command()
    async def ilha(self,ctx,*,nome:str=None):
        if not nome:
            loc=await buscar_localizacao_jogador(ctx.author.id); nome=loc['localizacao'] if loc else None
        nome=normalizar_destino(nome)
        if nome not in LOCAIS:return await ctx.send('❌ Ilha/local não encontrado no mapa.')
        i=info_ilha(nome); dom=await buscar_dominacao_ilha(nome); desc={r['chave'] for r in await listar_descobertas(ctx.author.id,nome)}
        emb=discord.Embed(title=f"🏝️ {nome.upper()}",description=f"🌊 {i['regiao']} • ⚠️ Perigo {i['perigo']}/5",color=COR)
        emb.add_field(name='⚔️ Inimigos principais',value='\n'.join('• '+x for x in i['inimigos']) or 'Nenhum catalogado',inline=False)
        emb.add_field(name='👹 Bosses conhecidos',value='\n'.join('• '+x for x in i['bosses']) or 'Nenhum conhecido',inline=False)
        seg=[]
        for x in i['segredos']: seg.append(('🔓 '+x) if x.casefold() in desc else '🔒 ???')
        emb.add_field(name='💎 Exploração / Segredos',value='\n'.join(seg) if seg else 'Nenhum registro conhecido.',inline=False)
        if dom: emb.add_field(name='👑 Domínio global',value=f"**{dom['dono_nome'] or 'Sem dono'}** • {dom['faccao'] or 'Independente'}\nEstado: {dom['estado']} • Integridade: {dom['integridade']}%",inline=False)
        else: emb.add_field(name='👑 Domínio global',value='Livre / não dominada',inline=False)
        await ctx.send(embed=emb)

    @commands.command()
    async def explorar(self,ctx):
        loc=await buscar_localizacao_jogador(ctx.author.id); nome=normalizar_destino(loc['localizacao'] if loc else None)
        if nome not in LOCAIS:return await ctx.send('❌ Você precisa estar em uma localização explorável.')
        i=info_ilha(nome); roll=random.randint(1,1000)
        if roll<=5:
            await adicionar_item_inventario(ctx.author.id,'akuma_misteriosa',1)
            return await ctx.send('🍈 **ACHADO LENDÁRIO!** Você encontrou uma **Akuma no Mi Misteriosa**. Ela foi diretamente para seu inventário. Encontrá-la não concede poder automaticamente.')
        if roll<=25:
            await adicionar_item_inventario(ctx.author.id,'mapa_tesouro',1)
            return await ctx.send('🗺️ **MAPA DE TESOURO!** O mapa foi enviado diretamente ao seu inventário.')
        roll=roll%100 or 100
        if roll<=45:
            berries=random.randint(500,5000)*i['perigo']; await adicionar_berries(ctx.author.id,berries); await registrar_transacao_economia(ctx.author.id,'tesouro',berries,None,1,nome)
            return await ctx.send(f"💰 **TESOURO ENCONTRADO!** Você encontrou **{dinheiro(berries)}**. Foi direto para sua carteira.")
        if roll<=70:
            item=random.choice(['mantimentos','kit_reparo','kit_medico','mapa_east_blue']); await adicionar_item_inventario(ctx.author.id,item,1)
            return await ctx.send(f"📦 **SAQUE!** Um item foi enviado diretamente ao seu inventário: `{item}`.")
        if i['segredos']:
            segredo=random.choice(i['segredos']); await registrar_descoberta(ctx.author.id,nome,segredo.casefold())
            return await ctx.send(f"🗿 **DESCOBERTA EM {nome.upper()}**\nVocê descobriu: **{segredo}**. `!ilha {nome}` agora registra essa descoberta.")
        await ctx.send('🌫️ Você explorou a região, mas desta vez não encontrou nada valioso.')

    @commands.command()
    async def pescar(self,ctx):
        if await buscar_treinamento_ativo(ctx.author.id) or await evento_ativo_usuario(ctx.author.id) or await buscar_sessao_ativa_usuario(ctx.author.id): return await ctx.send('🚫 Você está ocupado e não pode pescar agora.')
        specs=await buscar_especializacoes(ctx.author.id); p=next((int(x['porcentagem']) for x in specs if x['nome'].casefold()=='pescador'),0)
        r=random.randint(1,100); raro=1+min(20,p//10)
        rar='lendario' if r<=max(1,p//50) else 'raro' if r<=raro else 'incomum' if r<=35+min(25,p//5) else 'comum'
        peixe=random.choice(PESCAS[rar]); qtd=1+(1 if p>=80 and random.random()<.4 else 0)+(1 if p>=160 and random.random()<.3 else 0)
        item_id='peixe_'+rar; await adicionar_item_inventario(ctx.author.id,item_id,qtd)
        await ctx.send(f"🎣 **PESCA — {rar.upper()}**\nVocê fisgou **{peixe} ×{qtd}**.\n🎒 A captura foi enviada ao inventário.\n🐟 Pescador: **{p}%**")

    @commands.command()
    async def contratar(self,ctx,funcao:str='Marinheiro',*,nome:str=None):
        if not nome:return await ctx.send('👥 Use `!contratar <função> <nome>`.')
        custos={'Marinheiro':5000,'Navegador':12000,'Carpinteiro':12000,'Médico':15000,'Cozinheiro':10000,'Atirador':14000,'Lutador':14000}
        fn=next((x for x in custos if x.casefold()==funcao.casefold()),'Marinheiro'); custo=custos[fn]; ficha=await buscar_ficha(ctx.author.id)
        if not ficha or ficha['berries']<custo:return await ctx.send(f"❌ Contratar custa **{dinheiro(custo)}**.")
        await adicionar_berries(ctx.author.id,-custo); pers=random.choice(['leal e cauteloso','corajoso e impulsivo','calmo e observador','ambicioso, mas disciplinado'])
        sub=await criar_subordinado(ctx.author.id,nome[:60],fn,'E',max(500,custo//10),pers)
        await ctx.send(f"👥 **SUBORDINADO CONTRATADO**\n**{sub['nome']}** • {fn}\nPersonalidade: {pers}\n💰 Contratação: {dinheiro(custo)} • Salário-base: {dinheiro(sub['salario'])}\n🤖 Ele é um NPC persistente e poderá reagir em cenas/eventos conforme sua função.")

    @commands.command()
    async def subordinados(self,ctx):
        rows=await listar_subordinados(ctx.author.id)
        await ctx.send('👥 **SEUS SUBORDINADOS**\n'+('\n'.join(f"• **{x['nome']}** — {x['funcao']} • Rank {x['rank']} • Lealdade {x['lealdade']}" for x in rows) if rows else 'Nenhum contratado.'))

    @commands.command()
    async def cacadas(self,ctx):
        rows=await listar_cacadas(ctx.author.id)
        await ctx.send('🎯 **CAÇADAS ATIVAS CONTRA VOCÊ**\n'+('\n'.join(f"• **{x['cacador_nome']}** • Rank {x['rank']} — {x['motivo'] or 'motivo desconhecido'}" for x in rows) if rows else 'Nenhum caçador persistente no seu encalço.'))

    @commands.command()
    async def invadir(self,ctx,*,ilha:str):
        ilha=normalizar_destino(ilha); loc=await buscar_localizacao_jogador(ctx.author.id); atual=normalizar_destino(loc['localizacao'] if loc else None)
        if ilha not in LOCAIS:return await ctx.send('❌ Ilha não reconhecida.')
        if atual!=ilha:return await ctx.send(f'🚫 Você precisa estar em **{ilha}** para iniciar uma invasão.')
        if await evento_ativo_usuario(ctx.author.id) or await buscar_sessao_ativa_usuario(ctx.author.id):return await ctx.send('🚫 Termine seu evento/cena atual primeiro.')
        i=info_ilha(ilha); rank='SS' if i['perigo']>=5 else 'S' if i['perigo']>=4 else 'A' if i['perigo']>=3 else 'B'
        await self.publicar_evento('invasao',f'INVASÃO DE {ilha}',f'Uma força tenta conquistar ou destruir **{ilha}**. A resolução deste evento altera o estado global da ilha.',ilha,rank,False)
        await ctx.send(f'🏴‍☠️ **INVASÃO DECLARADA!** O evento global de **{ilha}** foi publicado. A ilha só muda de dono após a conclusão da campanha.')

    @commands.command()
    async def destruirilha(self,ctx,*,ilha:str):
        ilha=normalizar_destino(ilha); loc=await buscar_localizacao_jogador(ctx.author.id); atual=normalizar_destino(loc['localizacao'] if loc else None)
        if ilha not in LOCAIS:return await ctx.send('❌ Ilha não reconhecida.')
        if atual!=ilha:return await ctx.send(f'🚫 Você precisa estar em **{ilha}**.')
        if await evento_ativo_usuario(ctx.author.id) or await buscar_sessao_ativa_usuario(ctx.author.id):return await ctx.send('🚫 Termine seu evento/cena atual primeiro.')
        i=info_ilha(ilha); rank='LENDARIO' if i['perigo']>=5 else 'SS' if i['perigo']>=4 else 'S'
        await self.publicar_evento('destruicao',f'DESTRUIÇÃO DE {ilha}',f'Uma campanha foi iniciada para devastar **{ilha}**. Se concluída, o estado global da ilha será alterado para destruída.',ilha,rank,False)
        await ctx.send(f'🔥 **CAMPANHA DE DESTRUIÇÃO DECLARADA — {ilha}**')

    @commands.command()
    async def report(self,ctx,*,descricao:str='Erro não descrito'):
        ch=self.bot.get_channel(CANAL_REPORT_ID)
        if not ch:return await ctx.send('❌ Canal de reports não encontrado.')
        try:
            msg=await ch.send(f'<@&{CARGO_REPORT_ID}> 🐛 **NOVO REPORT** de {ctx.author.mention}\n{descricao[:1500]}',allowed_mentions=discord.AllowedMentions(roles=True,users=True))
            th=await msg.create_thread(name=f'Report • {ctx.author.display_name}'[:100],auto_archive_duration=1440)
            await th.send(f'{ctx.author.mention}, descreva aqui tudo que aconteceu, envie prints/logs e passos para reproduzir.\n<@&{CARGO_REPORT_ID}>',allowed_mentions=discord.AllowedMentions(roles=True,users=True))
            await ctx.send(f'🐛 Report aberto: {th.mention}')
        except Exception as e: await ctx.send(f'❌ Não consegui abrir o tópico de report: `{type(e).__name__}`.')

    async def aplicar_recompensa(self,e):
        rec=e['recompensa'] if isinstance(e['recompensa'],dict) else json.loads(e['recompensa'])
        ps=await participantes_evento(e['id'],'participando')
        for p in ps:
            await adicionar_berries(p['user_id'],int(rec.get('berries',0))); await adicionar_pontos_atributo(p['user_id'],int(rec.get('pontos',0)))
            if int(rec.get('percentual',0))>0: await adicionar_pontos_percentuais(p['user_id'],int(rec['percentual']))
            await adicionar_reputacao(p['user_id'],int(rec.get('reputacao',0))); await registrar_transacao_economia(p['user_id'],'recompensa_evento',int(rec.get('berries',0)),None,1,e['titulo'])
        await finalizar_participantes_evento(e['id']); await concluir_evento_global(e['id'])
        if e['tipo']=='invasao' and ps:
            ficha=await buscar_ficha(ps[0]['user_id']); await definir_dominacao_ilha(e['localizacao'],ps[0]['user_id'],ficha['nome'],ficha['faccao'],'dominada',100)
        elif e['tipo']=='destruicao' and ps:
            ficha=await buscar_ficha(ps[0]['user_id']); await definir_dominacao_ilha(e['localizacao'],ps[0]['user_id'],ficha['nome'],ficha['faccao'],'destruida',0)
        ch=self.bot.get_channel(e['thread_id']) if e['thread_id'] else None
        if ch:
            try: await ch.send(f"🏆 **EVENTO CONCLUÍDO — RECOMPENSAS ENTREGUES**\n💰 {dinheiro(rec.get('berries',0))}\n📈 +{rec.get('pontos',0)} pontos • +{rec.get('percentual',0)}% • +{rec.get('reputacao',0)} reputação\nAs recompensas foram aplicadas automaticamente a todos que concluíram.")
            except:pass

    async def gerar_diario(self):
        ch=self.bot.get_channel(CANAL_EVENTOS_ID)
        if not ch:return
        abertos=await listar_eventos_globais_abertos()
        recentes=[e for e in abertos if e['criado_em']>datetime.now(timezone.utc)-timedelta(hours=20)]
        if recentes:return
        # mural visual sempre acompanha o ciclo diário
        from PIL import Image,ImageDraw,ImageFont
        im=Image.new('RGB',(1200,700),(87,55,30)); d=ImageDraw.Draw(im)
        try:f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',54); sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
        except:f=sm=None
        d.text((600,55),'MURAL DE MISSÕES DA MARINHA',anchor='mm',fill=(240,220,170),font=f)
        for x,y,rot in [(90,130,0),(440,145,0),(790,120,0),(260,390,0),(650,380,0)]:
            d.rectangle((x,y,x+300,y+210),fill=(229,214,171),outline=(65,40,25),width=5); d.text((x+150,y+45),'MISSÃO',anchor='mm',fill=(55,40,28),font=sm); d.line((x+35,y+90,x+265,y+90),fill=(80,60,40),width=3); d.line((x+35,y+125,x+240,y+125),fill=(80,60,40),width=3)
        b=io.BytesIO(); im.save(b,'PNG'); b.seek(0)
        await ch.send('📌 **O mural foi atualizado. Novas ordens e ameaças foram registradas.**',file=discord.File(b,filename='mural_marinha.png'))
        locais=list(LOCAIS.keys())
        for _ in range(2):
            nome,rank,desc=random.choice(MISSOES_MARINHA); await self.publicar_evento('missao',nome,desc,random.choice(locais),rank,True)
        for _ in range(2):
            nome,rank,local,desc=random.choice(BOSSES_ESPECIAIS); await self.publicar_evento('boss',nome,desc,local,rank,False)

    @tasks.loop(minutes=1)
    async def relogio_mundo(self):
        try:
            await self.gerar_diario()
            for e in await eventos_para_finalizar(): await self.aplicar_recompensa(e)
            # Caçadores persistentes: reputação alta passa a gerar perseguição sem intervenção de staff.
            for alvo in await candidatos_cacada():
                if random.random() < 0.08:
                    rank='S' if alvo['reputacao']>=10000 else 'A' if alvo['reputacao']>=4000 else 'B' if alvo['reputacao']>=1500 else 'C'
                    nome=random.choice(['Caçador Sem-Rosto','Mercenário do Novo Mundo','Agente de Captura','Caçador de Recompensas'])
                    await criar_cacada(alvo['user_id'],nome,rank,f"Notoriedade/reputação: {alvo['reputacao']}",alvo['localizacao'])
        except Exception as e: print('❌ relógio mundo:',type(e).__name__,e)
    @relogio_mundo.before_loop
    async def antes(self):
        await self.bot.wait_until_ready(); await self.restaurar_views()

async def setup(bot): await bot.add_cog(Mundo(bot))
