import random
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands,tasks
from data.poderes import HAKIS,AKUMA_TIPOS,inferir_tipo,skills_akuma
from database.database import *

CANAL_SORTEIOS=1552747415151579197
CARGO_SORTEIOS=1542161421402644580
TZ=ZoneInfo('America/Sao_Paulo')
AKUMAS=[('Bara Bara no Mi','paramecia'),('Bomu Bomu no Mi','paramecia'),('Doru Doru no Mi','paramecia'),('Hana Hana no Mi','paramecia'),('Mane Mane no Mi','paramecia'),('Inu Inu no Mi, Modelo: Chacal','zoan'),('Tori Tori no Mi, Modelo: Falcão','zoan'),('Ushi Ushi no Mi, Modelo: Bisão','zoan'),('Moku Moku no Mi','logia'),('Suna Suna no Mi','logia'),('Mera Mera no Mi','logia')]

class SorteioView(discord.ui.View):
    def __init__(self,sid):
        super().__init__(timeout=None); self.sid=int(sid)
        b=discord.ui.Button(label='Participar',emoji='🎟️',style=discord.ButtonStyle.success,custom_id=f'sp:sorteio:{sid}'); b.callback=self.go; self.add_item(b)
    async def go(self,i):
        await participar_sorteio(self.sid,i.user.id); await i.response.send_message('🎟️ Você está participando deste sorteio.',ephemeral=True)

class PoderesView(discord.ui.View):
    def __init__(self,uid): super().__init__(timeout=180); self.uid=uid
    async def interaction_check(self,i): return i.user.id==self.uid
    @discord.ui.button(label='Transformações / Haki',emoji='✨')
    async def formas(self,i,b):
        specs=await buscar_especializacoes(self.uid); linhas=[]
        for x in specs:
            if x['categoria']=='haki':
                linhas.append(f"👁️ **{x['nome']} — {x['porcentagem']}% / ∞**")
                for n,req,d in HAKIS.get(x['nome'],[]): linhas.append(f"{'✅' if x['porcentagem']>=req else '🔒'} {n} ({req}%) — {d}")
        fs=await listar_formas(self.uid)
        for f in fs: linhas.append(f"{'🔥' if f['ativa'] else '🔹'} **{f['nome']}** — F +{f['bonus_forca']}% • R +{f['bonus_resistencia']}% • V +{f['bonus_velocidade']}%")
        await i.response.edit_message(embed=discord.Embed(title='✨ TRANSFORMAÇÕES & HAKI',description='\n'.join(linhas) or 'Nada desbloqueado.'),view=self)
    @discord.ui.button(label='Akuma no Mi',emoji='🍈')
    async def akuma(self,i,b):
        specs=await buscar_especializacoes(self.uid); aks=[x for x in specs if x['categoria'] in ('akuma','akuma no mi')]
        linhas=[]
        for a in aks:
            tipo,skills=skills_akuma(a['nome']); pct=a['porcentagem']; linhas.append(f"🍈 **{a['nome']}** • {tipo.title()} • **{pct}% / 300%**")
            for req,n,d in skills: linhas.append(f"{'✅' if pct>=req else '🔒'} {n} ({req}%) — {d}")
            if tipo=='zoan' and pct>=20:
                await liberar_forma(self.uid,f"{a['nome']} — Forma Animal",25,20,15,'Forma animal da Zoan','20% Akuma')
            if tipo=='zoan' and pct>=50:
                await liberar_forma(self.uid,f"{a['nome']} — Forma Híbrida",20,20,20,'Forma híbrida da Zoan','50% Akuma')
        await i.response.edit_message(embed=discord.Embed(title='🍈 AKUMA NO MI',description='\n'.join(linhas) or 'Nenhuma Akuma no Mi desbloqueada.'),view=self)

class Finalizacao(commands.Cog):
    def __init__(self,bot): self.bot=bot; bot.add_check(self.prisao_check); self.relogio.start()
    def cog_unload(self): self.relogio.cancel(); self.bot.remove_check(self.prisao_check)
    async def prisao_check(self,ctx):
        p=await buscar_prisao(ctx.author.id)
        if not p:return True
        liberados={'prisao','acao','ação','resumo','report','ajuda','help','comandos','manual'}
        if ctx.command and ctx.command.qualified_name.split()[0] in liberados:return True
        await ctx.send(f"⛓️ Você está **{p['status']}** em **{p['local']}**. Comandos de gameplay ficam bloqueados até sua situação ser resolvida.")
        return False

    @commands.command()
    async def poderes(self,ctx): await ctx.send(embed=discord.Embed(title='📚 PODERES',description='Use os botões para consultar Haki, transformações e Akuma no Mi.'),view=PoderesView(ctx.author.id))

    @commands.command(name='procurar-akuma')
    async def procurar_akuma(self,ctx):
        agora=datetime.now(timezone.utc); cd=await buscar_cooldown(ctx.author.id,'procurar_akuma')
        if cd and cd['disponivel_em']>agora:
            h=int((cd['disponivel_em']-agora).total_seconds()//3600)+1; return await ctx.send(f'🍈 Você já procurou hoje. Tente novamente em aproximadamente **{h}h**.')
        await definir_cooldown(ctx.author.id,'procurar_akuma',agora+timedelta(hours=24))
        if random.random()>.12:return await ctx.send('🌳 Você vasculhou a região, mas não encontrou nenhuma Akuma no Mi desta vez.')
        nome,tipo=random.choice(AKUMAS); item='akuma_'+str(abs(hash(nome))%10**8); await adicionar_item_inventario(ctx.author.id,item,1); exp=agora+timedelta(days=5); await registrar_akuma_encontrada(ctx.author.id,item,nome,tipo,exp)
        await ctx.send(f'🍈 **ACHADO RARÍSSIMO!** Você encontrou **{nome}** ({tipo.title()}).\n🎒 Foi para o inventário. ⏳ Se não for utilizada/doada, apodrece em **5 dias**.')

    @commands.command()
    async def doar(self,ctx,item:str,alvo:discord.Member,quantidade:int=1):
        if quantidade<1:return
        if await transferir_item(ctx.author.id,alvo.id,item,quantidade): await ctx.send(f'🎁 {alvo.mention} recebeu **{quantidade}× `{item}`**.')
        else: await ctx.send('❌ Você não possui essa quantidade no inventário.')

    @commands.command()
    async def doarnpc(self,ctx,item:str,npc_id:int,quantidade:int=1):
        subs=await listar_subordinados(ctx.author.id); n=next((x for x in subs if x['id']==npc_id),None)
        if not n:return await ctx.send('❌ Esse NPC não é seu subordinado.')
        if not await consumir_item(ctx.author.id,item,quantidade):return await ctx.send('❌ Item/quantidade indisponível.')
        await get_pool().execute('UPDATE subordinados SET lealdade=LEAST(100,lealdade+$2) WHERE id=$1',npc_id,min(10,quantidade)); await ctx.send(f'🎁 **{n["nome"]}** recebeu o presente e reagirá a isso como NPC. Lealdade aumentada.')

    @commands.group(invoke_without_command=True)
    async def tripulacao(self,ctx):
        """Painel persistente da tripulação."""
        t=await buscar_tripulacao_user(ctx.author.id)
        if not t:
            return await ctx.send('🏴‍☠️ **TRIPULAÇÕES**\nVocê ainda não pertence a uma.\n`!tripulacao criar <nome>` — criar\n`!tripulacao entrar <nome>` — entrar em uma conhecida')
        ms=await listar_membros_tripulacao(t['id'])
        linhas='\n'.join(f"• <@{m['user_id']}> **{m['nome']}** — {m['cargo']}" for m in ms)
        await ctx.send(f"🏴‍☠️ **{t['nome']}**\n👑 Capitão: <@{t['capitao_user_id']}>\n👥 Membros: **{len(ms)}**\n{linhas}\n\n⚓ Para viajar juntos, o dono do navio usa `!viajar <destino>`, escolhe quantos irão e os demais usam `!embarcar`.")

    @tripulacao.command(name='criar')
    async def trip_criar(self,ctx,*,nome):
        nome=nome.strip()[:60]
        r=await criar_tripulacao(nome,ctx.author.id)
        await ctx.send(f'🏴‍☠️ Tripulação **{nome}** criada! Você é o Capitão.' if r else '❌ Nome já usado ou você já pertence a uma tripulação.')

    @tripulacao.command(name='entrar')
    async def trip_entrar(self,ctx,*,nome):
        if await buscar_tripulacao_user(ctx.author.id):return await ctx.send('❌ Você já pertence a uma tripulação.')
        t=await buscar_tripulacao_nome(nome)
        if not t:return await ctx.send('❌ Tripulação não encontrada.')
        await entrar_tripulacao(t['id'],ctx.author.id); await ctx.send(f'🏴‍☠️ Você entrou em **{t["nome"]}**. O capitão pode organizar seu cargo.')

    @tripulacao.command(name='sair')
    async def trip_sair(self,ctx):
        t=await buscar_tripulacao_user(ctx.author.id)
        if not t:return await ctx.send('❌ Você não pertence a uma tripulação.')
        if t['capitao_user_id']==ctx.author.id:return await ctx.send('👑 O Capitão não pode abandonar a tripulação sem transferir a capitania: `!tripulacao capitao @membro`.')
        await sair_tripulacao(ctx.author.id); await ctx.send('🏴‍☠️ Você saiu da tripulação.')

    @tripulacao.command(name='expulsar')
    async def trip_expulsar(self,ctx,membro:discord.Member):
        t=await buscar_tripulacao_user(ctx.author.id)
        if not t or t['capitao_user_id']!=ctx.author.id:return await ctx.send('❌ Apenas o Capitão pode expulsar membros.')
        if membro.id==ctx.author.id:return await ctx.send('❌ Use transferência de capitania para reorganizar a liderança.')
        await remover_membro_tripulacao(t['id'],membro.id); await ctx.send(f'🏴‍☠️ {membro.mention} foi removido de **{t["nome"]}**.')

    @tripulacao.command(name='cargo')
    async def trip_cargo(self,ctx,membro:discord.Member,*,cargo:str):
        t=await buscar_tripulacao_user(ctx.author.id)
        if not t or t['capitao_user_id']!=ctx.author.id:return await ctx.send('❌ Apenas o Capitão pode definir cargos.')
        await definir_cargo_tripulacao(t['id'],membro.id,cargo); await ctx.send(f'🏴‍☠️ Cargo de {membro.mention}: **{cargo[:40]}**.')

    @tripulacao.command(name='capitao')
    async def trip_capitao(self,ctx,membro:discord.Member):
        t=await buscar_tripulacao_user(ctx.author.id)
        if not t or t['capitao_user_id']!=ctx.author.id:return await ctx.send('❌ Apenas o Capitão atual pode transferir a capitania.')
        ok=await transferir_capitania(t['id'],ctx.author.id,membro.id)
        await ctx.send(f'👑 {membro.mention} agora é o Capitão de **{t["nome"]}**.' if ok else '❌ Esse jogador precisa pertencer à sua tripulação.')

    @commands.command()
    async def alcunhas(self,ctx):
        a=await listar_alcunhas(ctx.author.id); await ctx.send('🏷️ '+('\n'.join(f"**{x['alcunha']}** — {x['motivo']}" for x in a) if a else 'Você ainda não conquistou uma alcunha.'))

    @commands.command()
    async def organizacoes(self,ctx):
        await garantir_organizacoes(); org=await organizacao_user(ctx.author.id); rows=await listar_organizacoes(); txt='\n'.join(f"• **{x['nome']}** — {x['tipo']}" for x in rows)
        await ctx.send(f"🏛️ **ORGANIZAÇÕES DO MUNDO**\n{txt}\n\nSua organização: **{org['nome']} ({org['cargo']})**" if org else f"🏛️ **ORGANIZAÇÕES DO MUNDO**\n{txt}\n\nVocê não pertence a uma organização.")

    @commands.command()
    async def prisao(self,ctx):
        p=await buscar_prisao(ctx.author.id); await ctx.send(f"⛓️ Preso em **{p['local']}** • {p['motivo']}" if p else '🔓 Você está livre.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prender(self,ctx,membro:discord.Member,local:str,*,motivo='Capturado'):
        await prender(membro.id,local,motivo); await ctx.send(f'⛓️ {membro.mention} foi preso em **{local}**.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def libertar(self,ctx,membro:discord.Member):
        await libertar(membro.id); await ctx.send(f'🔓 {membro.mention} foi libertado.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def execucao(self,ctx,membro:discord.Member,*,motivo='Sentença de execução'):
        await prender(membro.id,'Plataforma de Execução',motivo); await get_pool().execute("UPDATE prisoes SET status='execucao',execucao_em=NOW() WHERE user_id=$1",membro.id); await ctx.send(f'⚖️ {membro.mention} entrou em **estado de execução**. A resolução deve ocorrer narrativamente; a ficha não é apagada automaticamente.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def organizacaoentrar(self,ctx,membro:discord.Member,*,nome):
        await garantir_organizacoes(); o=next((x for x in await listar_organizacoes() if x['nome'].casefold()==nome.casefold()),None)
        if not o:return await ctx.send('❌ Organização não encontrada.')
        await entrar_organizacao(o['id'],membro.id); await ctx.send(f'🏛️ {membro.mention} entrou em **{o["nome"]}**.')

    @commands.command()
    async def manual(self,ctx):
        e=discord.Embed(title="📘 MANUAL — SEA'S PARADISE",description="RP persistente de One Piece: suas ações, localização, relações e consequências continuam existindo no mundo. `!acao` é o núcleo do jogo.",color=discord.Color.dark_gold())
        e.add_field(name='🎭 Cenas & !acao',value='Use `!iniciar` para abrir uma cena e `!entrar` para participar. Em multiplayer, cada jogador declara uma ação; cada nova ação renova uma janela de **5 min** para o próximo ler e escrever. Quando todos agem, resolve na hora. `!passar` abre mão do ciclo. Ausência não trava a cena.',inline=False)
        e.add_field(name='⚔️ Combate vivo',value='Não existe um minigame separado: combate nasce naturalmente da cena. Atributos medem capacidade, mas não anulam lógica, posição, armas, Haki, Akuma, estado e criatividade. Toda declaração é tentativa; NPCs e o mundo reagem.',inline=False)
        e.add_field(name='👤 Ficha & progressão',value='`!ficha`, `!poderes`, atributos, raça, família, profissão, classe, estilo, técnicas, Haki, Akuma e transformações. Treinos usam `!treinar`; Bosses de progressão ficam em `!bosses` e `!boss <rank>`.',inline=False)
        e.add_field(name='🗺️ Mundo & ilhas',value='Localização é persistente. `!ilha` consulta o local e `!explorar` busca recursos/segredos. Ilhas possuem perigos, NPCs, Bosses, tesouros, domínio e consequências persistentes. O canal não teleporta seu personagem.',inline=False)
        e.add_field(name='⛵ Mar & tripulação',value='Viagens usam navios, suprimentos, desgaste, rotas e obstáculos. Log Pose/Eternal Pose podem ser necessários. `!tripulacao` organiza grupos; embarque coletivo usa o fluxo de viagem/embarque. Navegador e Carpinteiro têm utilidade real.',inline=False)
        e.add_field(name='💰 Economia & atividades',value='Berries e inventário são persistentes. Existem mercado, pesca (`!pescar`), tesouros (`!tesouro`), roubo contextual (`!roubar`), doações, reparos e subordinados.',inline=False)
        e.add_field(name='🍈 Akuma no Mi',value='Além de `!procurar-akuma` (24h), **Akumas podem aparecer espontaneamente por 30 min em canais de ilhas**. Só personagem realmente presente naquela ilha pode pegar. Frutas encontradas vão ao inventário e apodrecem após 5 dias se não forem usadas/doadas.',inline=False)
        e.add_field(name='🌎 Eventos globais',value='O mural publica missões da Marinha e Bosses especiais. São instâncias próprias e podem ser não-canônicas quanto à localização. Recompensas são entregues automaticamente ao concluir; desistir impede repetir aquela instância.',inline=False)
        e.add_field(name='📰 Mundo vivo',value='`!jornal` mostra fatos públicos recentes. Reputação, procurado, atenção da Marinha/Governo/Piratas, caçadas, alcunhas, prisão, organizações, invasões e domínio de ilhas reagem aos acontecimentos.',inline=False)
        e.add_field(name='🏋️ Treino & exclusividade',value='Treino, viagem, evento e cenas usam estados persistentes e não podem ser empilhados de forma incompatível. Cancelar treino não concede recompensa.',inline=False)
        e.add_field(name='☠️ Derrota, morte & encerramento',value='`!encerrar` fecha uma cena somente quando não existe conflito imediato pendente. Fuga, rendição, captura, vitória etc. precisam ser resolvidas por `!acao`. Morte/execução narrativa não é tratada como simples botão de apagar ficha.',inline=False)
        e.add_field(name='🛠️ Utilidade',value='`!ajuda` lista comandos; `!resumo`/`!sessao` consultam a cena; `!report` abre suporte. Avisos operacionais somem automaticamente para manter o RP limpo; ações e narrações permanecem.',inline=False)
        e.set_footer(text="Sea's Paradise • O player declara o que tenta; o mundo resolve e reage.")
        await ctx.send(embed=e)

    async def postar_sorteios(self):
        agora=datetime.now(TZ); chave='sorteios:'+agora.date().isoformat()
        if agora.hour<10 or agora.hour>=20 or await execucao_diaria_feita(chave):return
        ch=self.bot.get_channel(CANAL_SORTEIOS)
        if not ch:return
        premios=[('Berries',random.randint(10000,30000)),('Mapa de Tesouro',1),('Kit de Reparo Naval',2)]
        random.shuffle(premios)
        for premio,valor in premios:
            fim_local=agora.replace(hour=20,minute=0,second=0,microsecond=0)
            s=await criar_sorteio(premio,valor,fim_local.astimezone(timezone.utc)); await ch.send(f'<@&{CARGO_SORTEIOS}>\n🎁 **SORTEIO DIÁRIO**\nPrêmio: **{premio}**'+(f' • {valor}' if premio!='Berries' else f' • ฿ {valor:,}'),view=SorteioView(s['id']))
        await marcar_execucao_diaria(chave)

    async def finalizar_sorteios(self):
        for s in await sorteios_encerrar():
            ps=await participantes_sorteio(s['id']); vencedor=random.choice(ps)['user_id'] if ps else None
            if vencedor:
                if s['premio']=='Berries': await adicionar_berries(vencedor,s['valor'])
                elif s['premio']=='Mapa de Tesouro': await adicionar_item_inventario(vencedor,'mapa_tesouro',s['valor'])
                else: await adicionar_item_inventario(vencedor,'kit_reparo',s['valor'])
            await encerrar_sorteio(s['id'],vencedor)
            ch=self.bot.get_channel(CANAL_SORTEIOS)
            if ch:
                if vencedor:
                    premio_txt=(f"฿ {s['valor']:,}" if s['premio']=='Berries' else f"{s['premio']} ×{s['valor']}")
                    await ch.send(f"🏆 **RESULTADO DO SORTEIO**\n<@{vencedor}> venceu **{premio_txt}**!\n✅ A recompensa já foi entregue diretamente à ficha/inventário.")
                else:
                    await ch.send(f"🎁 **RESULTADO DO SORTEIO** — **{s['premio']}**\nNenhum participante elegível neste sorteio.")

    async def alcunhas_auto(self):
        # Feitos persistentes objetivos; ON CONFLICT impede spam.
        for r in await get_pool().fetch('SELECT user_id,nome,reputacao FROM fichas WHERE reputacao>=750'):
            alc='Lenda dos Mares' if r['reputacao']>=6000 else 'Nome Temido' if r['reputacao']>=1500 else 'Nome Notável'; await registrar_alcunha(r['user_id'],alc,f"Reputação alcançada: {r['reputacao']}")

    @tasks.loop(minutes=1)
    async def relogio(self):
        try:
            await self.postar_sorteios(); await self.finalizar_sorteios(); await self.alcunhas_auto()
            for a in await akumas_expiradas(): await expirar_akuma(a['id'])
        except Exception as e: print('❌ relógio finalização:',type(e).__name__,e)
    @relogio.before_loop
    async def antes(self):
        await self.bot.wait_until_ready(); await garantir_organizacoes()
        # restaura botões persistentes após redeploy/restart
        for s in await sorteios_abertos():
            try: self.bot.add_view(SorteioView(s['id']))
            except Exception: pass

async def setup(bot): await bot.add_cog(Finalizacao(bot))
