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
from data.navegacao import normalizar_destino, LOCAIS
from data.combat_rules import COMBAT_LOGIC_RULES

RANK_ORDER={'E':0,'D':1,'C':2,'B':3,'A':4,'S':5,'SS':6,'LENDARIO':7}
RANK_LABEL={'E':'Iniciante','D':'Baixo','C':'Intermediário','B':'Experiente','A':'Elite','S':'Monstruoso','SS':'Extremo','LENDARIO':'Lendário'}
BOSS_ARCHETYPES=[
    ('Espadachim Errante','espada, contra-ataques e pressão corpo a corpo',(.92,1.00,1.10)),
    ('Lutador Brutal','golpes físicos, agarrões e avanço agressivo',(1.12,1.08,.84)),
    ('Caçador Veloz','mobilidade, fintas e ataques rápidos',(.88,.90,1.22)),
    ('Veterano de Combate','defesa disciplinada, leitura de abertura e contra-ataques',(1.00,1.08,1.00)),
    ('Guerreiro Implacável','resistência alta, pressão constante e golpes pesados',(1.08,1.18,.82)),
]
BOSS_CD_HOURS=1
AI_LIMIT=asyncio.Semaphore(max(2,int(os.getenv('BOSS_AI_CONCURRENCY','8'))))
SEVERITY_FRACTIONS={'nenhum':0.0,'raspao':.03,'leve':.08,'solido':.16,'grave':.28,'critico':.45,'letal':1.0}

CHANNEL_ALIASES={
    'sabaody':'Sabaody Archipelago','sabaody-park':'Sabaody Archipelago','sabaody-park-rp':'Sabaody Archipelago',
    'vila-foosha':'Dawn Island','foosha':'Dawn Island','vila-syrup':'Syrup Village','ilhas-conomi':'Conomi Islands','arlong-park':'Conomi Islands',
}
NON_LOCATION={'geral','general','chat','bate-papo','comandos','commands','fichas','ficha','regras','rules','off-topic','offtopic','anuncios','anúncios','logs','log','staff','admin','tickets'}

def _fmt(n): return f"{int(n):,}".replace(',', '.')
def _reward(rank):
    d=BOSS_RANKS[rank]
    return {'berries':random.randint(d['berries'][0],d['berries'][1])//4,'pontos':max(1,random.randint(d['pontos'][0],d['pontos'][1])//6),'pct':1 if rank in ('A','S','SS','LENDARIO') and random.random()<.35 else 0,'rep':3+RANK_ORDER[rank]*4}

def _clean_json(text):
    text=(text or '').strip(); text=re.sub(r'^```(?:json)?\s*|\s*```$','',text,flags=re.I|re.S).strip()
    a=text.find('{'); b=text.rfind('}')
    if a>=0 and b>a: text=text[a:b+1]
    return json.loads(text)

def _clip(s,n=900):
    s=(s or '').strip(); return s if len(s)<=n else s[-n:]

class Progressao(commands.Cog):
    """Boss Rank: instância não-canônica para progressão, com combate contextual persistente."""
    def __init__(self,bot):
        self.bot=bot; self.client=AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')); self._locks={}

    async def _ativo(self,uid):
        return await get_pool().fetchrow("SELECT * FROM bosses_rp_ativos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1",uid)

    def _canal_local(self,ctx):
        nome=getattr(ctx.channel,'name',None)
        if not nome:return None
        k=nome.casefold().strip().replace('_','-')
        if k in NON_LOCATION:return None
        if k in CHANNEL_ALIASES:return CHANNEL_ALIASES[k]
        return normalizar_destino(k.replace('-',' '))

    async def _validar_local(self,ctx):
        canal=self._canal_local(ctx)
        if not canal:return True,None,None
        estado=await buscar_localizacao_jogador(ctx.author.id)
        if not estado or not estado['localizacao']:
            return False,canal,estado
        atual=normalizar_destino(estado['localizacao'])
        # legado: o Narrador antigo chamava a área de Sabaody Park.
        if str(estado['localizacao']).casefold()=='sabaody park': atual='Sabaody Archipelago'
        return str(atual).casefold()==str(canal).casefold(),canal,estado

    async def _stats_player(self,uid,ficha):
        forma=await forma_ativa(uid)
        bf=int(forma['bonus_forca']) if forma else 0; br=int(forma['bonus_resistencia']) if forma else 0; bv=int(forma['bonus_velocidade']) if forma else 0
        return {'forca':max(1,round(int(ficha['forca'])*(1+bf/100))),'resistencia':max(1,round(int(ficha['resistencia'])*(1+br/100))),'velocidade':max(1,round(int(ficha['velocidade'])*(1+bv/100))),'forma':forma}

    def _estado_inicial(self,ficha,boss):
        return (f"{ficha['nome']} e {boss} estão conscientes, livres e em distância de combate neutra. "
                "Nenhum agarrão, ferimento, cobertura, arma preparada ou vantagem posicional foi estabelecido ainda.")

    async def _resolver_troca(self,acao,ficha,esp,boss,stats):
        dominios='; '.join(f"{x['categoria']}:{x['nome']}={x['porcentagem']}%" for x in esp) or 'nenhum'
        forma=(f"{stats['forma']['nome']} — {stats['forma']['capacidades']}" if stats['forma'] else 'nenhuma')
        estado=boss['estado_contexto'] or self._estado_inicial(ficha,boss['boss_nome'])
        hist=boss['historico_contexto'] or 'Nenhuma troca anterior.'
        bf=int(boss['boss_forca'] or BOSS_RANKS[boss['rank']]['attr']); br=int(boss['boss_resistencia'] or BOSS_RANKS[boss['rank']]['attr']); bv=int(boss['boss_velocidade'] or BOSS_RANKS[boss['rank']]['attr'])
        prompt=f'''Você é o ÁRBITRO DE COMBATE do Sea's Paradise. Resolva UMA troca viva e causal. Não seja um gerador de acerto aleatório.

{COMBAT_LOGIC_RULES}

PLAYER: {ficha['nome']}
Força={stats['forca']} | Resistência={stats['resistencia']} | Velocidade={stats['velocidade']}
Akuma={ficha['akuma']} | Forma={forma}
Domínios/capacidades registradas: {dominios}

BOSS: {boss['boss_nome']} | Rank={boss['rank']} | perfil={boss['boss_estilo'] or 'combatente equilibrado'}
Força={bf} | Resistência={br} | Velocidade={bv}

ESTADO FÍSICO AUTORITATIVO ANTES DA AÇÃO:
{estado}

HISTÓRICO RECENTE:
{hist}

DECLARAÇÃO LITERAL DO PLAYER:
{acao}

TAREFA:
1. Separe o que o player EXECUTA do resultado que ele tentou impor. Preserve agência, mas não aceite "acertei", "não tomei dano", "ele não consegue" como fato.
2. Resolva em ordem causal todas as etapas realmente executadas. Use o estado anterior. Se uma etapa depende de outra e a anterior falha, respeite isso.
3. Decida a reação do Boss somente com movimentos possíveis no estado atual e capacidades plausíveis. Ele pode atacar, defender, escapar, agarrar, usar terreno etc.
4. Atributos pesam, mas LÓGICA vem primeiro. Explique concretamente como uma diferença de atributo permitiu uma reação; não use rank como trava.
5. NÃO use HP, barra de vida, pontos de condição nem dano numérico. Ferimentos existem somente como fatos narrativos persistentes no estado (ex.: corte no braço, perna quebrada, inconsciente, morto).
6. Um tiro, lâmina, impacto ou poder deve ser resolvido pela cadeia causal concreta: alcance, trajetória, reação possível, proteção, natureza do ataque e capacidades relevantes. Rank/status sozinho nunca decide acerto, defesa ou sobrevivência.
7. Produza NOVO ESTADO concreto para o próximo turno: distância, postura, agarrões, armas em mãos/no chão, cobertura, ferimentos e vantagens. Não apague fatos sem resolvê-los.
8. Narração curta, natural, sem falar em rolagem, fórmula, IA ou "chance".

Responda SOMENTE JSON válido:
{{
 "acao_interpretada":"o que o player realmente tentou/executou",
 "resolucao_player":"resultado concreto da ação do player",
 "reacao_boss":"ação/reação concreta do Boss após/entre as etapas, se possível",
 "resolucao_boss":"resultado concreto da ação do Boss",
 "novo_estado":"estado físico completo e autoritativo após a troca, incluindo ferimentos narrativos",
 "desfecho":"continua|boss_derrotado|player_derrotado",
 "resumo_turno":"uma frase factual para memória"
}}'''
        async with AI_LIMIT:
            r=await self.client.responses.create(model='gpt-5.6-luna',input=prompt,max_output_tokens=850)
        out=_clean_json(r.output_text)
        desfecho=str(out.get('desfecho','continua')).casefold().strip()
        if desfecho not in ('continua','boss_derrotado','player_derrotado'):desfecho='continua'
        out['desfecho']=desfecho
        return out

    def _fallback_troca(self, acao, ficha, boss, stats):
        """Fallback narrativo conservador: preserva a cena sem inventar HP ou vitória automática."""
        estado=boss['estado_contexto'] or self._estado_inicial(ficha,boss['boss_nome'])
        return {'acao_interpretada':acao,'resolucao_player':'A ação é executada até o ponto que o estado atual permite, sem presumir automaticamente o resultado pretendido.','reacao_boss':'O Boss reage a partir da posição e das condições já estabelecidas na cena.','resolucao_boss':'A troca permanece aberta; nenhum desfecho irreversível é imposto sem base causal suficiente.','novo_estado':estado,'desfecho':'continua','resumo_turno':'A troca continuou sem desfecho automático por falta de resolução segura.'}

    def _dano_por_severidade(self,severity,hp_max):
        return max(0,round(int(hp_max)*SEVERITY_FRACTIONS.get(severity,0)))

    async def _aplicar_cd(self,uid):
        await definir_cooldown(uid,'boss:progressao_global',datetime.now(timezone.utc)+timedelta(hours=BOSS_CD_HOURS))

    @commands.command(name='bosses',aliases=['bosslocal','chefes'])
    async def bosses(self,ctx):
        e=discord.Embed(title='👹 BOSSES DE PROGRESSÃO',description='Lutas **não-canônicas** para evolução. Estão sempre disponíveis, mas só podem ser iniciadas no canal da sua localização atual. Escolha `!boss <rank>`.',color=discord.Color.dark_red())
        for rank,d in BOSS_RANKS.items():e.add_field(name=f'Rank {rank} • {RANK_LABEL.get(rank,rank)}',value=f'⚔️ referência física {d["attr"]:,}\n`!boss {rank}`',inline=True)
        e.set_footer(text='Após vitória, derrota ou desistência: 1h de cooldown.')
        await ctx.send(embed=e)

    @commands.command(name='boss')
    async def boss(self,ctx,*,nome:str):
        ok,canal,estado=await self._validar_local(ctx)
        if not ok:
            atual=estado['localizacao'] if estado and estado['localizacao'] else 'não definida'
            return await ctx.send(f'❌ Você não está neste local.\n📍 Localização atual: **{atual}**\n🗺️ Este canal representa: **{canal}**')
        if await self._ativo(ctx.author.id):return await ctx.send('❌ Você já está enfrentando um Boss. Use `!bossacao <ação>` ou `!desistirboss`.')
        if await buscar_sessao_ativa_usuario(ctx.author.id):return await ctx.send('🎭 Termine sua cena atual antes de iniciar um Boss de progressão.')
        if await buscar_treinamento_ativo(ctx.author.id) or await buscar_viagem_ativa(ctx.author.id):return await ctx.send('❌ Você não pode iniciar Boss enquanto treina ou viaja.')
        rank=nome.upper().strip().replace('Á','A'); rank='LENDARIO' if rank=='LENDÁRIO' else rank
        if rank not in BOSS_RANKS:return await ctx.send('❌ Rank inválido. Use `!bosses` e escolha **E, D, C, B, A, S, SS ou LENDARIO**.')
        now=datetime.now(timezone.utc); cd=await buscar_cooldown(ctx.author.id,'boss:progressao_global')
        if cd and cd['disponivel_em']>now:
            mins=max(1,int((cd['disponivel_em']-now).total_seconds()//60)+1);return await ctx.send(f'⏳ Você acabou uma luta recentemente. Novo Boss em ~**{mins//60}h {mins%60}min**.')
        ficha=await buscar_ficha(ctx.author.id); stats=await self._stats_player(ctx.author.id,ficha); d=BOSS_RANKS[rank]
        hp_player=max(100,round(100+stats['resistencia']*1.5)); titulo,estilo,mults=random.choice(BOSS_ARCHETYPES); bn=f'{titulo} • Rank {rank}'
        bf=max(1,round(d['attr']*mults[0])); br=max(1,round(d['attr']*mults[1])); bv=max(1,round(d['attr']*mults[2]))
        estado0=self._estado_inicial(ficha,bn)
        row=await get_pool().fetchrow('''INSERT INTO bosses_rp_ativos(user_id,boss_nome,localizacao,rank,hp_max,hp_atual,player_hp_max,player_hp_atual,boss_estilo,turno,player_focus,boss_forca,boss_resistencia,boss_velocidade,estado_contexto,historico_contexto)
            VALUES($1,$2,$3,$4,$5,$5,$6,$6,$7,1,0,$8,$9,$10,$11,'') RETURNING *''',ctx.author.id,bn,normalizar_destino(estado['localizacao']) if estado else canal,rank,d['hp'],hp_player,estilo,bf,br,bv,estado0)
        e=discord.Embed(title=f'👹 {bn}',description='Instância **não-canônica** de progressão, mas a luta segue as mesmas leis físicas/narrativas do Sea\'s Paradise. Rank não decide ação sozinho.',color=discord.Color.dark_red())
        e.add_field(name='🎬 Resolução',value='Sem barra de vida: ferimentos, incapacitação, derrota e morte são resolvidos pela lógica da narração e ficam registrados no estado da luta.',inline=False)
        e.add_field(name='⚔️ Perfil',value=estilo,inline=False); e.add_field(name='Como lutar',value='`!bossacao <sua ação>` — descreva livremente o que tenta fazer.',inline=False)
        await ctx.send(embed=e)

    @commands.command(name='bossacao',aliases=['bossação'])
    @commands.cooldown(1,3,commands.BucketType.user)
    async def bossacao(self,ctx,*,acao:str):
        lock=self._locks.setdefault(ctx.author.id,asyncio.Lock())
        async with lock:
            b=await self._ativo(ctx.author.id)
            if not b:return await ctx.send('❌ Você não está enfrentando um Boss de progressão.')
            ok,canal,estado=await self._validar_local(ctx)
            if not ok:
                atual=estado['localizacao'] if estado and estado['localizacao'] else 'não definida'
                return await ctx.send(f'❌ Sua luta existe, mas você só pode agir no canal da sua localização real.\n📍 **{atual}** • Canal atual: **{canal}**')
            # A luta nasce no local real e continua vinculada a ele; não pode ser carregada para outro canal após viagem/admin move.
            real=normalizar_destino(estado['localizacao']) if estado else None
            salvo=normalizar_destino(b['localizacao']) if b['localizacao']!='Instância não-canônica' else real
            if real and salvo and str(real).casefold()!=str(salvo).casefold():
                return await ctx.send(f'❌ Este Boss foi iniciado em **{b["localizacao"]}**. Encerre/desista antes de lutar em outro local.')
            ficha=await buscar_ficha(ctx.author.id); esp=list(await buscar_especializacoes(ctx.author.id)); stats=await self._stats_player(ctx.author.id,ficha); d=BOSS_RANKS[b['rank']]
            # migra luta 56 já ativa sem apagar progresso.
            updates=[]; vals=[]
            if b['player_hp_max'] is None:
                hp=max(100,round(100+stats['resistencia']*1.5)); updates += ['player_hp_max=$2','player_hp_atual=$2']; vals=[hp]
            if b['boss_forca'] is None:
                base=d['attr']; updates += [f'boss_forca=${len(vals)+2}',f'boss_resistencia=${len(vals)+3}',f'boss_velocidade=${len(vals)+4}']; vals += [base,base,base]
            if not b['estado_contexto']:
                updates += [f'estado_contexto=${len(vals)+2}']; vals += [self._estado_inicial(ficha,b['boss_nome'])]
            if b['localizacao']=='Instância não-canônica' and real:
                updates += [f'localizacao=${len(vals)+2}']; vals += [real]
            if updates:
                q='UPDATE bosses_rp_ativos SET '+','.join(updates)+' WHERE id=$1 RETURNING *'; b=await get_pool().fetchrow(q,b['id'],*vals)
            try:
                out=await self._resolver_troca(acao,ficha,esp,b,stats)
            except Exception as ex:
                print(f'⚠️ Árbitro Boss IA falhou; usando fallback mecânico: {type(ex).__name__}: {ex}')
                out=self._fallback_troca(acao,ficha,b,stats)
            resumo=_clip(out.get('resumo_turno') or f"{out.get('resolucao_player','')} {out.get('resolucao_boss','')}",500)
            hist=_clip((b['historico_contexto'] or '')+f"\nT{b['turno']}: {resumo}",1800)
            novo=_clip(out.get('novo_estado') or b['estado_contexto'],1400)
            await get_pool().execute('UPDATE bosses_rp_ativos SET turno=turno+1,estado_contexto=$2,historico_contexto=$3 WHERE id=$1',b['id'],novo,hist)
            lines=[f'⚔️ **Turno {b["turno"]} — {ficha["nome"]} vs. {b["boss_nome"]}**',f'🗣️ *{out.get("acao_interpretada",acao)}*',f'\n🎬 {out.get("resolucao_player","A ação é resolvida.")}']
            if out.get('reacao_boss'):lines.append(f'\n👹 *{out["reacao_boss"]}*')
            if out.get('resolucao_boss'):lines.append(f'🎬 {out["resolucao_boss"]}')
            await ctx.send('\n'.join(lines))
            desfecho=out.get('desfecho','continua')
            if desfecho=='boss_derrotado':
                await get_pool().execute("UPDATE bosses_rp_ativos SET hp_atual=0 WHERE id=$1",b['id'])
                return await self._vitoria(ctx,b)
            if desfecho=='player_derrotado':
                await get_pool().execute("UPDATE bosses_rp_ativos SET status='derrota',finalizado_em=NOW() WHERE id=$1 AND status='ativo'",b['id']); await self._aplicar_cd(ctx.author.id)
                return await ctx.send('🏳️ **DERROTA NARRATIVA.** O confronto terminou conforme o estado descrito acima; isso não mata automaticamente seu personagem no cânone.\n⏳ Novo Boss em **1 hora**.')

    async def _vitoria(self,ctx,b):
        async with get_pool().acquire() as c:
            async with c.transaction():
                locked=await c.fetchrow("SELECT * FROM bosses_rp_ativos WHERE id=$1 FOR UPDATE",b['id'])
                if not locked or locked['status']!='ativo':return
                r=_reward(locked['rank']); await c.execute("UPDATE bosses_rp_ativos SET status='vitoria',finalizado_em=NOW() WHERE id=$1",b['id']); await c.execute("UPDATE fichas SET berries=berries+$2,pontos_atributo=pontos_atributo+$3,reputacao=reputacao+$4 WHERE user_id=$1",ctx.author.id,r['berries'],r['pontos'],r['rep'])
                if r['pct']:await c.execute("INSERT INTO pontos_percentuais(user_id,disponiveis) VALUES($1,$2) ON CONFLICT(user_id) DO UPDATE SET disponiveis=pontos_percentuais.disponiveis+EXCLUDED.disponiveis",ctx.author.id,r['pct'])
        await self._aplicar_cd(ctx.author.id); await ctx.send(f'🏆 **BOSS RANK {b["rank"]} DERROTADO!**\n💰 ฿ {_fmt(r["berries"])}\n📈 +{r["pontos"]} pontos de atributo'+(f' • +{r["pct"]}% disponível' if r['pct'] else '')+f'\n🌍 +{r["rep"]} reputação\n⏳ Próximo Boss em **1 hora**.')

    @commands.command(name='desistirboss')
    async def desistirboss(self,ctx):
        b=await self._ativo(ctx.author.id)
        if not b:return await ctx.send('❌ Nenhum Boss de progressão ativo.')
        await get_pool().execute("UPDATE bosses_rp_ativos SET status='desistiu',finalizado_em=NOW() WHERE id=$1",b['id']); await self._aplicar_cd(ctx.author.id); await ctx.send('🏳️ Confronto encerrado sem recompensa.\n⏳ Novo Boss disponível em **1 hora**.')

async def setup(bot):await bot.add_cog(Progressao(bot))
