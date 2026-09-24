import random
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands
from database.database import *
from data.mundo import BOSS_RANKS, BOSSES_ESPECIAIS

# Bosses locais são conteúdo canônico do mundo do RP e NÃO substituem Bosses globais.
# Recompensa de progressão é propositalmente baixa; o grosso é Berries/reputação.
LOCAL_BOSSES = {nome.casefold(): (nome, rank, local, desc) for nome,rank,local,desc in BOSSES_ESPECIAIS}
RANK_ORDER={'E':0,'D':1,'C':2,'B':3,'A':4,'S':5,'SS':6,'LENDARIO':7}

def _fmt(n): return f"{int(n):,}".replace(',', '.')

def _reward(rank):
    d=BOSS_RANKS[rank]
    # abaixo dos globais: repetível, mas com cooldown e recompensa individual única por janela
    return {
        'berries': random.randint(d['berries'][0], d['berries'][1])//4,
        'pontos': max(1, random.randint(d['pontos'][0], d['pontos'][1])//6),
        'pct': 1 if rank in ('A','S','SS','LENDARIO') and random.random()<0.35 else 0,
        'rep': 3 + RANK_ORDER[rank]*4,
    }

class Progressao(commands.Cog):
    def __init__(self,bot): self.bot=bot

    async def _ativo(self,uid):
        return await get_pool().fetchrow("SELECT * FROM bosses_rp_ativos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1",uid)

    @commands.command(name='bosses',aliases=['bosslocal','chefes'])
    async def bosses(self,ctx):
        loc=await buscar_localizacao_jogador(ctx.author.id)
        if not loc:return await ctx.send('❌ Sua localização ainda não foi definida.')
        nome_loc=loc['localizacao']
        xs=[x for x in LOCAL_BOSSES.values() if x[2].casefold()==nome_loc.casefold()]
        if not xs:return await ctx.send(f'👹 Não há Boss on-RP catalogado em **{nome_loc}** neste momento.')
        e=discord.Embed(title=f'👹 BOSSES — {nome_loc}',description='Bosses locais podem ser enfrentados fora do mural global. Use `!boss <nome>`.')
        for nome,rank,_,desc in xs:
            d=BOSS_RANKS[rank]; e.add_field(name=f'{nome} • Rank {rank}',value=f'❤️ {d["hp"]} HP\n{desc}',inline=False)
        e.set_footer(text='Progressão repetível é limitada por cooldown para evitar farm.')
        await ctx.send(embed=e)

    @commands.command(name='boss')
    async def boss(self,ctx,*,nome:str):
        if await self._ativo(ctx.author.id):return await ctx.send('❌ Você já está enfrentando um Boss. Use `!bossacao <ação>` ou `!desistirboss`.')
        if await buscar_sessao_ativa_usuario(ctx.author.id):return await ctx.send('🎭 Termine sua cena atual antes de iniciar um Boss local.')
        if await buscar_treinamento_ativo(ctx.author.id) or await buscar_viagem_ativa(ctx.author.id):return await ctx.send('❌ Você não pode iniciar Boss enquanto treina ou viaja.')
        key=nome.casefold().strip(); item=LOCAL_BOSSES.get(key)
        if not item:
            # aceita trecho inequívoco
            cand=[v for k,v in LOCAL_BOSSES.items() if key in k]
            if len(cand)!=1:return await ctx.send('❌ Boss não encontrado. Use `!bosses` no local.')
            item=cand[0]
        bn,rank,local,desc=item; loc=await buscar_localizacao_jogador(ctx.author.id)
        if not loc or loc['localizacao'].casefold()!=local.casefold():return await ctx.send(f'📍 **{bn}** está em **{local}**. Sua localização atual é **{loc["localizacao"] if loc else "desconhecida"}**.')
        now=datetime.now(timezone.utc)
        global_cd=await buscar_cooldown(ctx.author.id,'boss:progressao_global')
        if global_cd and global_cd['disponivel_em']>now:
            mins=int((global_cd['disponivel_em']-now).total_seconds()//60)+1
            return await ctx.send(f'⏳ Seu personagem ainda está se recuperando do último Boss. Nova progressão de Boss em ~**{mins//60}h {mins%60}min**.')
        cd=await buscar_cooldown(ctx.author.id,'boss:'+bn.casefold())
        if cd and cd['disponivel_em']>now:
            mins=int((cd['disponivel_em']-now).total_seconds()//60)+1; return await ctx.send(f'⏳ Você já recebeu progressão de **{bn}** recentemente. Tente novamente em ~**{mins//60}h {mins%60}min**.')
        d=BOSS_RANKS[rank]
        row=await get_pool().fetchrow("INSERT INTO bosses_rp_ativos(user_id,boss_nome,localizacao,rank,hp_max,hp_atual) VALUES($1,$2,$3,$4,$5,$5) RETURNING *",ctx.author.id,bn,local,rank,d['hp'])
        e=discord.Embed(title=f'👹 BOSS ON-RP — {bn}',description=desc,color=discord.Color.dark_red())
        e.add_field(name='Rank',value=rank); e.add_field(name='HP',value=f'{row["hp_atual"]}/{row["hp_max"]}')
        e.add_field(name='Como lutar',value='Descreva cada investida com `!bossacao <ação>`. Seus atributos influenciam o resultado; ações não garantem sucesso.',inline=False)
        await ctx.send(embed=e)

    @commands.command(name='bossacao',aliases=['bossação'])
    @commands.cooldown(1,3,commands.BucketType.user)
    async def bossacao(self,ctx,*,acao:str):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Você não está enfrentando um Boss local.')
        ficha=await buscar_ficha(ctx.author.id); d=BOSS_RANKS[b['rank']]
        poder=max(1,int(ficha['forca'])+int(ficha['resistencia'])+int(ficha['velocidade']))
        alvo=max(100,d['attr']*3); chance=max(.08,min(.88,.48+(poder-alvo)/max(alvo,1)*.28))
        sucesso=random.random()<chance
        if sucesso:
            dano=max(1,int(d['hp']*(.055+min(.12,poder/max(alvo,1)*.045))*random.uniform(.75,1.2)))
            novo=max(0,b['hp_atual']-dano)
            await get_pool().execute("UPDATE bosses_rp_ativos SET hp_atual=$2 WHERE id=$1",b['id'],novo)
            await ctx.send(f'⚔️ **{ficha["nome"]}** — {acao}\n💥 A investida funciona e pressiona **{b["boss_nome"]}**.\n❤️ Boss: **{novo}/{b["hp_max"]} HP**')
            if novo<=0: await self._vitoria(ctx,b)
        else:
            falhas=b['falhas']+1; await get_pool().execute("UPDATE bosses_rp_ativos SET falhas=$2 WHERE id=$1",b['id'],falhas)
            if falhas>=5:
                await get_pool().execute("UPDATE bosses_rp_ativos SET status='derrota',finalizado_em=NOW() WHERE id=$1",b['id'])
                return await ctx.send(f'💢 **{b["boss_nome"]}** domina o confronto. Você foi derrotado e não recebe recompensa. O Boss poderá ser tentado novamente sem recompensa duplicada indevida.')
            await ctx.send(f'🛡️ **{b["boss_nome"]}** lê/aguenta sua ação e contra-ataca.\n⚠️ Pressão sofrida: **{falhas}/5**. Adapte sua estratégia.')

    async def _vitoria(self,ctx,b):
        async with get_pool().acquire() as c:
            async with c.transaction():
                locked=await c.fetchrow("SELECT * FROM bosses_rp_ativos WHERE id=$1 FOR UPDATE",b['id'])
                if not locked or locked['status']!='ativo' or locked['hp_atual']>0:return
                r=_reward(locked['rank'])
                await c.execute("UPDATE bosses_rp_ativos SET status='vitoria',finalizado_em=NOW() WHERE id=$1",b['id'])
                await c.execute("UPDATE fichas SET berries=berries+$2,pontos_atributo=pontos_atributo+$3,reputacao=reputacao+$4 WHERE user_id=$1",ctx.author.id,r['berries'],r['pontos'],r['rep'])
                if r['pct']:
                    await c.execute("INSERT INTO pontos_percentuais(user_id,disponiveis) VALUES($1,$2) ON CONFLICT(user_id) DO UPDATE SET disponiveis=pontos_percentuais.disponiveis+EXCLUDED.disponiveis",ctx.author.id,r['pct'])
                await c.execute("INSERT INTO recompensas_npc_marcante(user_id,npc_nome,instancia) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",ctx.author.id,locked['boss_nome'],f"boss:{locked['id']}")
        await definir_cooldown(ctx.author.id,'boss:'+b['boss_nome'].casefold(),datetime.now(timezone.utc)+timedelta(hours=6))
        await definir_cooldown(ctx.author.id,'boss:progressao_global',datetime.now(timezone.utc)+timedelta(hours=2))
        await ctx.send(f'🏆 **{b["boss_nome"]} DERROTADO!**\n💰 ฿ {_fmt(r["berries"])}\n📈 +{r["pontos"]} pontos de atributo'+(f' • +{r["pct"]}% disponível' if r['pct'] else '')+f'\n🌍 +{r["rep"]} reputação\n✅ Recompensas aplicadas automaticamente.')

    @commands.command(name='desistirboss')
    async def desistirboss(self,ctx):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Nenhum Boss local ativo.')
        await get_pool().execute("UPDATE bosses_rp_ativos SET status='desistiu',finalizado_em=NOW() WHERE id=$1",b['id']); await ctx.send('🏳️ Confronto encerrado sem recompensa.')

async def setup(bot): await bot.add_cog(Progressao(bot))
