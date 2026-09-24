import os
import json
import random
import re
import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from openai import AsyncOpenAI

from database.database import *
from data.mundo import BOSS_RANKS

RANK_ORDER={'E':0,'D':1,'C':2,'B':3,'A':4,'S':5,'SS':6,'LENDARIO':7}
RANK_LABEL={'E':'Iniciante','D':'Baixo','C':'Intermediário','B':'Experiente','A':'Elite','S':'Monstruoso','SS':'Extremo','LENDARIO':'Lendário'}
BOSS_ARCHETYPES=[
    ('Espadachim Errante','espada, contra-ataques e pressão corpo a corpo'),
    ('Lutador Brutal','golpes físicos, agarrões e avanço agressivo'),
    ('Caçador Veloz','mobilidade, fintas e ataques rápidos'),
    ('Veterano de Combate','defesa disciplinada, leitura de abertura e contra-ataques'),
    ('Guerreiro Implacável','resistência alta, pressão constante e golpes pesados'),
]
BOSS_CD_HOURS=1
AI_LIMIT=asyncio.Semaphore(max(2,int(os.getenv('BOSS_AI_CONCURRENCY','8'))))

def _fmt(n): return f"{int(n):,}".replace(',', '.')
def _reward(rank):
    d=BOSS_RANKS[rank]
    return {'berries':random.randint(d['berries'][0],d['berries'][1])//4,'pontos':max(1,random.randint(d['pontos'][0],d['pontos'][1])//6),'pct':1 if rank in ('A','S','SS','LENDARIO') and random.random()<.35 else 0,'rep':3+RANK_ORDER[rank]*4}

def _clamp(v,a,b): return max(a,min(b,v))

def _clean_json(text):
    text=(text or '').strip()
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',text,flags=re.I|re.S).strip()
    a=text.find('{'); b=text.rfind('}')
    if a>=0 and b>a: text=text[a:b+1]
    return json.loads(text)

class Progressao(commands.Cog):
    """Boss de progressão não-canônico, mas com combate narrativo/mecânico real."""
    def __init__(self,bot):
        self.bot=bot
        self.client=AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def _ativo(self,uid):
        return await get_pool().fetchrow("SELECT * FROM bosses_rp_ativos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1",uid)

    async def _stats_player(self,uid,ficha):
        forma=await forma_ativa(uid)
        bf=int(forma['bonus_forca']) if forma else 0; br=int(forma['bonus_resistencia']) if forma else 0; bv=int(forma['bonus_velocidade']) if forma else 0
        return {
            'forca':max(1,round(int(ficha['forca'])*(1+bf/100))),
            'resistencia':max(1,round(int(ficha['resistencia'])*(1+br/100))),
            'velocidade':max(1,round(int(ficha['velocidade'])*(1+bv/100))),
            'forma':forma,
        }

    async def _interpretar(self,acao,ficha,esp,boss,stats):
        dominios='; '.join(f"{x['categoria']}:{x['nome']}={x['porcentagem']}%" for x in esp) or 'nenhum'
        forma=(f"{stats['forma']['nome']} — {stats['forma']['capacidades']}" if stats['forma'] else 'nenhuma')
        prompt=f"""Você é o árbitro de UMA troca de combate de RPG One Piece. NÃO decide dano nem vitória: só interpreta a declaração e escolhe uma reação plausível do Boss.
Ação literal do player: {acao}
Player: {ficha['nome']} | Força {stats['forca']} | Resistência {stats['resistencia']} | Velocidade {stats['velocidade']} | Akuma {ficha['akuma']} | Forma ativa {forma}
Domínios/skills disponíveis: {dominios}
Boss: {boss['boss_nome']} | Rank {boss['rank']} | estilo {boss['boss_estilo'] or 'combatente equilibrado'}

REGRAS:
- Olhar, falar, provocar, analisar, sacar arma, preparar postura ou carregar técnica NÃO é ataque.
- Não conceda técnica/poder que não apareça no contexto do player.
- Se houver ataque, descreva somente a tentativa, nunca diga que acertou antes do motor.
- O Boss tem iniciativa própria e pode atacar, defender, preparar ou observar; não precisa esperar ser atacado.
- Responda SOMENTE JSON válido, sem markdown:
{{"intencao":"ataque|defesa|observacao|preparo|movimento|fala|outro","descricao_player":"frase curta fiel à ação","intensidade":1.0,"boss_intencao":"ataque|defesa|preparo|observacao","boss_descricao":"frase curta da tentativa/reação do boss"}}
intensidade entre 0.75 e 1.20."""
        async with AI_LIMIT:
            r=await self.client.responses.create(model='gpt-5.6-luna',input=prompt,max_output_tokens=300)
        try:
            out=_clean_json(r.output_text)
            if out.get('intencao') not in {'ataque','defesa','observacao','preparo','movimento','fala','outro'}: raise ValueError
            if out.get('boss_intencao') not in {'ataque','defesa','preparo','observacao'}: out['boss_intencao']='ataque'
            out['intensidade']=float(_clamp(float(out.get('intensidade',1)),.75,1.2))
            return out
        except Exception:
            low=acao.lower()
            ataque=any(w in low for w in ('ataco','golpe','corto','corte','soco','chuto','disparo','perfuro','avanço contra','acerto','estoco'))
            defesa=any(w in low for w in ('defendo','bloqueio','bloqueio','esquivo','protejo'))
            intent='ataque' if ataque else ('defesa' if defesa else 'observacao')
            return {'intencao':intent,'descricao_player':acao[:220],'intensidade':1.0,'boss_intencao':'ataque','boss_descricao':'O Boss procura uma abertura e parte para a ofensiva.'}

    def _hit(self,atk_vel,def_vel,focus=0,defending=False):
        ratio=atk_vel/max(1,def_vel)
        chance=.58 + (ratio-1)*.18 + min(.12,focus*.04) - (.16 if defending else 0)
        return random.random() < _clamp(chance,.08,.94)

    def _damage(self,atk_force,def_res,intensity=1.0,defending=False):
        ratio=atk_force/max(1,def_res)
        base=max(1,atk_force*.18)
        scale=_clamp(.65 + ratio*.35,.35,2.25)
        dmg=base*scale*intensity*random.uniform(.86,1.14)
        if defending: dmg*=.55
        return max(1,round(dmg))

    async def _aplicar_cd(self,uid):
        await definir_cooldown(uid,'boss:progressao_global',datetime.now(timezone.utc)+timedelta(hours=BOSS_CD_HOURS))

    @commands.command(name='bosses',aliases=['bosslocal','chefes'])
    async def bosses(self,ctx):
        e=discord.Embed(title='👹 BOSSES DE PROGRESSÃO',description='Lutas **não-canônicas**, sempre disponíveis para evolução. Não mudam sua localização nem o mundo. Escolha um Rank com `!boss <rank>`.',color=discord.Color.dark_red())
        for rank,d in BOSS_RANKS.items():
            e.add_field(name=f'Rank {rank} • {RANK_LABEL.get(rank,rank)}',value=f'❤️ {d["hp"]:,} HP • ⚔️ referência {d["attr"]:,}\n`!boss {rank}`',inline=True)
        e.set_footer(text='Após encerrar uma luta: 1h de cooldown para iniciar outra.')
        await ctx.send(embed=e)

    @commands.command(name='boss')
    async def boss(self,ctx,*,nome:str):
        if await self._ativo(ctx.author.id): return await ctx.send('❌ Você já está enfrentando um Boss. Use `!bossacao <ação>` ou `!desistirboss`.')
        if await buscar_sessao_ativa_usuario(ctx.author.id): return await ctx.send('🎭 Termine sua cena atual antes de iniciar um Boss de progressão.')
        if await buscar_treinamento_ativo(ctx.author.id) or await buscar_viagem_ativa(ctx.author.id): return await ctx.send('❌ Você não pode iniciar Boss enquanto treina ou viaja.')
        rank=nome.upper().strip().replace('Á','A')
        if rank=='LENDÁRIO': rank='LENDARIO'
        if rank not in BOSS_RANKS: return await ctx.send('❌ Rank inválido. Use `!bosses` e escolha **E, D, C, B, A, S, SS ou LENDARIO**.')
        now=datetime.now(timezone.utc); cd=await buscar_cooldown(ctx.author.id,'boss:progressao_global')
        if cd and cd['disponivel_em']>now:
            mins=max(1,int((cd['disponivel_em']-now).total_seconds()//60)+1); return await ctx.send(f'⏳ Você acabou uma luta recentemente. Novo Boss em ~**{mins//60}h {mins%60}min**.')
        ficha=await buscar_ficha(ctx.author.id); stats=await self._stats_player(ctx.author.id,ficha); d=BOSS_RANKS[rank]
        hp_player=max(100,round(100+stats['resistencia']*1.5))
        titulo,estilo=random.choice(BOSS_ARCHETYPES); bn=f'{titulo} • Rank {rank}'
        row=await get_pool().fetchrow("""INSERT INTO bosses_rp_ativos(user_id,boss_nome,localizacao,rank,hp_max,hp_atual,player_hp_max,player_hp_atual,boss_estilo,turno,player_focus)
            VALUES($1,$2,$3,$4,$5,$5,$6,$6,$7,1,0) RETURNING *""",ctx.author.id,bn,'Instância não-canônica',rank,d['hp'],hp_player,estilo)
        e=discord.Embed(title=f'👹 {bn}',description='Combate de progressão **fora do cânone**. É uma luta completa: ações são interpretadas, ações não-ofensivas não causam dano e o Boss reage sozinho.',color=discord.Color.dark_red())
        e.add_field(name='❤️ Boss',value=f'{row["hp_atual"]}/{row["hp_max"]}',inline=True)
        e.add_field(name='❤️ Você',value=f'{row["player_hp_atual"]}/{row["player_hp_max"]}',inline=True)
        e.add_field(name='⚔️ Perfil',value=estilo,inline=False)
        e.add_field(name='Como lutar',value='`!bossacao <sua ação>`\nVocê pode atacar, defender, observar, preparar técnica, usar seus poderes etc.',inline=False)
        await ctx.send(embed=e)

    @commands.command(name='bossacao',aliases=['bossação'])
    @commands.cooldown(1,3,commands.BucketType.user)
    async def bossacao(self,ctx,*,acao:str):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Você não está enfrentando um Boss de progressão.')
        ficha=await buscar_ficha(ctx.author.id); esp=list(await buscar_especializacoes(ctx.author.id)); stats=await self._stats_player(ctx.author.id,ficha); d=BOSS_RANKS[b['rank']]
        # Compatibilidade com lutas que já estavam ativas antes desta atualização.
        if b['player_hp_max'] is None or b['player_hp_atual'] is None:
            hp=max(100,round(100+stats['resistencia']*1.5))
            b=await get_pool().fetchrow("UPDATE bosses_rp_ativos SET player_hp_max=$2,player_hp_atual=$2,boss_estilo=COALESCE(boss_estilo,'Veterano de Combate') WHERE id=$1 RETURNING *",b['id'],hp)
        interp=await self._interpretar(acao,ficha,esp,b,stats)
        p_int=interp['intencao']; boss_int=interp['boss_intencao']; focus=int(b['player_focus'] or 0)
        boss_hp=int(b['hp_atual']); player_hp=int(b['player_hp_atual']); boss_def=(boss_int=='defesa'); player_def=(p_int=='defesa')
        lines=[f'⚔️ **Turno {int(b["turno"] or 1)} — {ficha["nome"]} vs. {b["boss_nome"]}**',f'🗣️ *{interp["descricao_player"]}*']

        # Ação do jogador. Somente ataque declarado pode causar dano.
        if p_int=='ataque':
            if self._hit(stats['velocidade'],d['attr'],focus,boss_def):
                dano=self._damage(stats['forca'],d['attr'],interp['intensidade'],boss_def); boss_hp=max(0,boss_hp-dano)
                lines.append(f'💥 O ataque encontra abertura e causa **{dano}** de dano.')
                focus=0
            else:
                lines.append('💨 O ataque não consegue atingir o Boss nesta troca.')
                focus=max(0,focus-1)
        elif p_int=='defesa': lines.append('🛡️ Você assume uma defesa ativa, reduzindo o impacto de um possível contra-ataque.')
        elif p_int in ('observacao','preparo'):
            focus=min(3,focus+(2 if p_int=='preparo' else 1)); lines.append(f'👁️ Nenhum dano é causado. Você ganha **Foco {focus}/3** para a próxima ofensiva.')
        elif p_int=='movimento': lines.append('🏃 Você reposiciona-se; isso não causa dano por si só.')
        else: lines.append('💬 A ação não é ofensiva, então o HP do Boss permanece intacto.')

        # Se o Boss caiu, não recebe turno fantasma.
        if boss_hp<=0:
            await get_pool().execute("UPDATE bosses_rp_ativos SET hp_atual=0,player_hp_atual=$2,player_focus=$3,turno=turno+1 WHERE id=$1",b['id'],player_hp,focus)
            lines.append(f'❤️ Boss: **0/{b["hp_max"]}** • ❤️ Você: **{player_hp}/{b["player_hp_max"]}**')
            await ctx.send('\n'.join(lines)); return await self._vitoria(ctx,b)

        # Boss tem iniciativa própria em todo turno.
        lines.append(f'\n👹 *{interp["boss_descricao"]}*')
        if boss_int=='ataque':
            if self._hit(d['attr'],stats['velocidade'],0,player_def):
                dano_b=self._damage(d['attr'],stats['resistencia'],1.0,player_def); player_hp=max(0,player_hp-dano_b)
                lines.append(f'💢 O Boss acerta e causa **{dano_b}** de dano em você.')
            else: lines.append('✨ Você evita/neutraliza a ofensiva do Boss nesta troca.')
        elif boss_int=='defesa': lines.append('🛡️ O Boss fecha a guarda e prioriza a defesa.')
        elif boss_int=='preparo': lines.append('⚠️ O Boss prepara uma ação mais perigosa para a próxima abertura.')
        else: lines.append('👁️ O Boss mede seus movimentos e não ataca nesta troca.')

        await get_pool().execute("UPDATE bosses_rp_ativos SET hp_atual=$2,player_hp_atual=$3,player_focus=$4,turno=turno+1 WHERE id=$1",b['id'],boss_hp,player_hp,focus)
        lines.append(f'\n❤️ Boss: **{boss_hp}/{b["hp_max"]}** • ❤️ Você: **{player_hp}/{b["player_hp_max"]}**')
        await ctx.send('\n'.join(lines))
        if player_hp<=0:
            await get_pool().execute("UPDATE bosses_rp_ativos SET status='derrota',finalizado_em=NOW() WHERE id=$1 AND status='ativo'",b['id'])
            await self._aplicar_cd(ctx.author.id)
            await ctx.send('💀 **DERROTA.** A instância de progressão termina aqui, sem recompensa. Seu personagem não morre no mundo canônico por esta luta.\n⏳ Novo Boss disponível em **1 hora**.')

    async def _vitoria(self,ctx,b):
        async with get_pool().acquire() as c:
            async with c.transaction():
                locked=await c.fetchrow("SELECT * FROM bosses_rp_ativos WHERE id=$1 FOR UPDATE",b['id'])
                if not locked or locked['status']!='ativo' or locked['hp_atual']>0:return
                r=_reward(locked['rank'])
                await c.execute("UPDATE bosses_rp_ativos SET status='vitoria',finalizado_em=NOW() WHERE id=$1",b['id'])
                await c.execute("UPDATE fichas SET berries=berries+$2,pontos_atributo=pontos_atributo+$3,reputacao=reputacao+$4 WHERE user_id=$1",ctx.author.id,r['berries'],r['pontos'],r['rep'])
                if r['pct']: await c.execute("INSERT INTO pontos_percentuais(user_id,disponiveis) VALUES($1,$2) ON CONFLICT(user_id) DO UPDATE SET disponiveis=pontos_percentuais.disponiveis+EXCLUDED.disponiveis",ctx.author.id,r['pct'])
        await self._aplicar_cd(ctx.author.id)
        await ctx.send(f'🏆 **BOSS RANK {b["rank"]} DERROTADO!**\n💰 ฿ {_fmt(r["berries"])}\n📈 +{r["pontos"]} pontos de atributo'+(f' • +{r["pct"]}% disponível' if r['pct'] else '')+f'\n🌍 +{r["rep"]} reputação\n⏳ Próximo Boss em **1 hora**.')

    @commands.command(name='desistirboss')
    async def desistirboss(self,ctx):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Nenhum Boss de progressão ativo.')
        await get_pool().execute("UPDATE bosses_rp_ativos SET status='desistiu',finalizado_em=NOW() WHERE id=$1",b['id'])
        await self._aplicar_cd(ctx.author.id)
        await ctx.send('🏳️ Confronto encerrado sem recompensa.\n⏳ Novo Boss disponível em **1 hora**.')

async def setup(bot): await bot.add_cog(Progressao(bot))
