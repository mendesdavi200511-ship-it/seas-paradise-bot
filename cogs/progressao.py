import random
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands
from database.database import *
from data.mundo import BOSS_RANKS

RANK_ORDER={'E':0,'D':1,'C':2,'B':3,'A':4,'S':5,'SS':6,'LENDARIO':7}
RANK_LABEL={'E':'Iniciante','D':'Baixo','C':'Intermediário','B':'Experiente','A':'Elite','S':'Monstruoso','SS':'Extremo','LENDARIO':'Lendário'}
def _fmt(n): return f"{int(n):,}".replace(',', '.')
def _reward(rank):
    d=BOSS_RANKS[rank]
    return {'berries':random.randint(d['berries'][0],d['berries'][1])//4,'pontos':max(1,random.randint(d['pontos'][0],d['pontos'][1])//6),'pct':1 if rank in ('A','S','SS','LENDARIO') and random.random()<.35 else 0,'rep':3+RANK_ORDER[rank]*4}

class Progressao(commands.Cog):
    """Boss de progressão: instância mecânica, não-canônica e independente da localização."""
    def __init__(self,bot): self.bot=bot
    async def _ativo(self,uid): return await get_pool().fetchrow("SELECT * FROM bosses_rp_ativos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1",uid)

    @commands.command(name='bosses',aliases=['bosslocal','chefes'])
    async def bosses(self,ctx):
        e=discord.Embed(title='👹 BOSSES DE PROGRESSÃO',description='Estes Bosses são **não-canônicos** e existem somente para progressão. Você pode iniciá-los de qualquer lugar com `!boss <rank>`.\n\nPersonagens canônicos como Law, Crocodile etc. continuam sendo enfrentados **pela narração**, com registro/recompensa próprios.',color=discord.Color.dark_red())
        for rank,d in BOSS_RANKS.items(): e.add_field(name=f'Rank {rank} • {RANK_LABEL.get(rank,rank)}',value=f'❤️ {d["hp"]:,} HP • ⚔️ referência {d["attr"]:,}\nUse `!boss {rank}`',inline=True)
        e.set_footer(text='Sempre disponível • cooldown controla apenas a recompensa/progressão.')
        await ctx.send(embed=e)

    @commands.command(name='boss')
    async def boss(self,ctx,*,nome:str):
        if await self._ativo(ctx.author.id): return await ctx.send('❌ Você já está enfrentando um Boss. Use `!bossacao <ação>` ou `!desistirboss`.')
        if await buscar_sessao_ativa_usuario(ctx.author.id): return await ctx.send('🎭 Termine sua cena atual antes de iniciar um Boss de progressão.')
        if await buscar_treinamento_ativo(ctx.author.id) or await buscar_viagem_ativa(ctx.author.id): return await ctx.send('❌ Você não pode iniciar Boss enquanto treina ou viaja.')
        rank=nome.upper().strip().replace('Á','A')
        if rank=='LENDÁRIO': rank='LENDARIO'
        if rank not in BOSS_RANKS: return await ctx.send('❌ Rank inválido. Use `!bosses` e escolha **E, D, C, B, A, S, SS ou LENDARIO**.')
        now=datetime.now(timezone.utc); global_cd=await buscar_cooldown(ctx.author.id,'boss:progressao_global')
        if global_cd and global_cd['disponivel_em']>now:
            mins=int((global_cd['disponivel_em']-now).total_seconds()//60)+1; return await ctx.send(f'⏳ Nova progressão de Boss em ~**{mins//60}h {mins%60}min**.')
        bn=f'Boss de Progressão • Rank {rank}'; d=BOSS_RANKS[rank]
        row=await get_pool().fetchrow("INSERT INTO bosses_rp_ativos(user_id,boss_nome,localizacao,rank,hp_max,hp_atual) VALUES($1,$2,$3,$4,$5,$5) RETURNING *",ctx.author.id,bn,'Instância não-canônica',rank,d['hp'])
        e=discord.Embed(title=f'👹 {bn}',description='Instância de evolução **fora do cânone do mundo**. Ela não altera sua localização persistente.',color=discord.Color.dark_red())
        e.add_field(name='HP',value=f'{row["hp_atual"]}/{row["hp_max"]}'); e.add_field(name='Referência de poder',value=f'{d["attr"]:,} por atributo')
        e.add_field(name='Como lutar',value='Use `!bossacao <ação>`. Seus atributos influenciam sucesso e dano.',inline=False); await ctx.send(embed=e)

    @commands.command(name='bossacao',aliases=['bossação'])
    @commands.cooldown(1,3,commands.BucketType.user)
    async def bossacao(self,ctx,*,acao:str):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Você não está enfrentando um Boss de progressão.')
        ficha=await buscar_ficha(ctx.author.id); d=BOSS_RANKS[b['rank']]; poder=max(1,int(ficha['forca'])+int(ficha['resistencia'])+int(ficha['velocidade'])); alvo=max(100,d['attr']*3); chance=max(.08,min(.88,.48+(poder-alvo)/max(alvo,1)*.28)); sucesso=random.random()<chance
        if sucesso:
            dano=max(1,int(d['hp']*(.055+min(.12,poder/max(alvo,1)*.045))*random.uniform(.75,1.2))); novo=max(0,b['hp_atual']-dano); await get_pool().execute("UPDATE bosses_rp_ativos SET hp_atual=$2 WHERE id=$1",b['id'],novo); await ctx.send(f'⚔️ **{ficha["nome"]}** — {acao}\n💥 A investida funciona.\n❤️ Boss: **{novo}/{b["hp_max"]} HP**')
            if novo<=0: await self._vitoria(ctx,b)
        else:
            falhas=b['falhas']+1; await get_pool().execute("UPDATE bosses_rp_ativos SET falhas=$2 WHERE id=$1",b['id'],falhas)
            if falhas>=5:
                await get_pool().execute("UPDATE bosses_rp_ativos SET status='derrota',finalizado_em=NOW() WHERE id=$1",b['id']); return await ctx.send(f'💢 O **Boss Rank {b["rank"]}** venceu o confronto. Sem recompensa; depois do bloqueio global você pode tentar novamente.')
            await ctx.send(f'🛡️ O Boss resiste e contra-ataca.\n⚠️ Pressão sofrida: **{falhas}/5**.')

    async def _vitoria(self,ctx,b):
        async with get_pool().acquire() as c:
            async with c.transaction():
                locked=await c.fetchrow("SELECT * FROM bosses_rp_ativos WHERE id=$1 FOR UPDATE",b['id'])
                if not locked or locked['status']!='ativo' or locked['hp_atual']>0:return
                r=_reward(locked['rank']); await c.execute("UPDATE bosses_rp_ativos SET status='vitoria',finalizado_em=NOW() WHERE id=$1",b['id']); await c.execute("UPDATE fichas SET berries=berries+$2,pontos_atributo=pontos_atributo+$3,reputacao=reputacao+$4 WHERE user_id=$1",ctx.author.id,r['berries'],r['pontos'],r['rep'])
                if r['pct']: await c.execute("INSERT INTO pontos_percentuais(user_id,disponiveis) VALUES($1,$2) ON CONFLICT(user_id) DO UPDATE SET disponiveis=pontos_percentuais.disponiveis+EXCLUDED.disponiveis",ctx.author.id,r['pct'])
        await definir_cooldown(ctx.author.id,'boss:progressao_global',datetime.now(timezone.utc)+timedelta(hours=2)); await ctx.send(f'🏆 **BOSS RANK {b["rank"]} DERROTADO!**\n💰 ฿ {_fmt(r["berries"])}\n📈 +{r["pontos"]} pontos de atributo'+(f' • +{r["pct"]}% disponível' if r['pct'] else '')+f'\n🌍 +{r["rep"]} reputação\n✅ Progressão aplicada automaticamente.')

    @commands.command(name='desistirboss')
    async def desistirboss(self,ctx):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Nenhum Boss de progressão ativo.')
        await get_pool().execute("UPDATE bosses_rp_ativos SET status='desistiu',finalizado_em=NOW() WHERE id=$1",b['id']); await ctx.send('🏳️ Confronto encerrado sem recompensa.')

async def setup(bot): await bot.add_cog(Progressao(bot))
