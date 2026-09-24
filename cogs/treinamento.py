import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands, tasks
from database.database import (buscar_ficha,buscar_especializacoes,buscar_treinamento_ativo,
    criar_treinamento,treinamentos_prontos,concluir_treinamento,cancelar_treinamento,
    buscar_viagem_ativa,buscar_sessao_ativa_usuario)

COR=discord.Color.from_rgb(82,145,72)
SESSOES={"2h":(2,20,1),"6h":(6,50,2),"12h":(12,100,3),"1d":(24,200,5),"2d":(48,500,8),"4d":(96,1000,12)}

def fmt(td):
    s=max(0,int(td.total_seconds())); d=s//86400; h=(s%86400)//3600; m=(s%3600)//60
    return (f"{d}d " if d else "")+(f"{h}h " if h else "")+f"{m}m"

def multiplicador_tempo(ficha,tipo,alvo):
    m=1.0; motivos=[]
    if ficha.get('prodigio'): m*=0.5; motivos.append("Prodígio")
    fam=(ficha.get('familia') or '').casefold()
    if fam=='rocks': m*=0.5; motivos.append("Rocks")
    if fam=='charlotte' and tipo=='atributo': m*=0.5; motivos.append("Charlotte")
    if fam=='smoker' and tipo=='atributo': m*=0.5; motivos.append("Smoker")
    return max(0.25,m),motivos

class Treinamento(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.verificar.start()
    def cog_unload(self): self.verificar.cancel()

    @commands.command(aliases=['treino'])
    async def treinar(self,ctx,tipo:str=None,alvo:str=None,duracao:str='2h'):
        ficha=await buscar_ficha(ctx.author.id)
        if not ficha:return await ctx.send("❌ Você ainda não possui ficha.")
        ativo=await buscar_treinamento_ativo(ctx.author.id)
        if ativo:return await ctx.send(f"🏋️ Você já está treinando **{ativo['alvo']}**. Use `!treinostatus`.")
        viagem=await buscar_viagem_ativa(ctx.author.id)
        if viagem:return await ctx.send("⛵ Você está em viagem e não pode iniciar treinamento até chegar ao destino.")
        sessao=await buscar_sessao_ativa_usuario(ctx.author.id)
        if sessao:return await ctx.send("🎭 Você está participando de uma cena ativa. Encerre/saia da cena antes de iniciar um treinamento.")
        if not tipo or not alvo:
            return await ctx.send("🏋️ **Treinamento**\n`!treinar atributo força 2h`\n`!treinar dominio Ittoryu 12h`\nDurações: `2h`, `6h`, `12h`, `1d`, `2d`, `4d`.")
        duracao=duracao.casefold()
        if duracao not in SESSOES:return await ctx.send("❌ Duração inválida: 2h, 6h, 12h, 1d, 2d ou 4d.")
        tipo=tipo.casefold(); alvo_limpo=alvo.strip(); horas,ganho_attr,ganho_dom=SESSOES[duracao]
        if tipo in ('atributo','attr'):
            mapa={'força':'forca','forca':'forca','resistência':'resistencia','resistencia':'resistencia','velocidade':'velocidade','agilidade':'velocidade'}
            alvo_db=mapa.get(alvo_limpo.casefold())
            if not alvo_db:return await ctx.send("❌ Atributo: Força, Resistência ou Velocidade.")
            tipo_db='atributo'; ganho=ganho_attr
        elif tipo in ('dominio','domínio'):
            specs=await buscar_especializacoes(ctx.author.id); sp=next((x for x in specs if x['nome'].casefold()==alvo_limpo.casefold()),None)
            if not sp:return await ctx.send("❌ Você só pode treinar um domínio que possui.")
            if sp['porcentagem']>=sp['limite']:return await ctx.send("🏆 Esse domínio já está no limite.")
            tipo_db='dominio'; alvo_db=sp['nome']; ganho=min(ganho_dom,sp['limite']-sp['porcentagem'])
        else:return await ctx.send("❌ Use `atributo` ou `dominio`.")
        mult,motivos=multiplicador_tempo(ficha,tipo_db,alvo_db); horas_reais=horas*mult
        fim=datetime.now(timezone.utc)+timedelta(hours=horas_reais)
        await criar_treinamento(ctx.author.id,tipo_db,alvo_db,ganho,ctx.channel.id,fim)
        extra=f"\n✨ Redução: **{', '.join(motivos)}**" if motivos else ""
        await ctx.send(f"🏋️ **TREINAMENTO INICIADO**\n🎯 {alvo_db.title()}\n⏱️ {fmt(timedelta(hours=horas_reais))}\n📈 Recompensa ao concluir: **+{ganho}**{('%' if tipo_db=='dominio' else ' pts')}{extra}\n\nEu aviso neste canal quando terminar.")

    @commands.command()
    async def treinostatus(self,ctx):
        t=await buscar_treinamento_ativo(ctx.author.id)
        if not t:return await ctx.send("🏋️ Você não possui treinamento ativo.")
        await ctx.send(f"🏋️ **Treinando {t['alvo']}**\n⏳ Restante: **{fmt(t['fim_em']-datetime.now(timezone.utc))}**\n📈 Ganho: **+{t['ganho']}**")

    @commands.command(aliases=['cancelartreinamento'])
    async def cancelartreino(self,ctx):
        t=await cancelar_treinamento(ctx.author.id)
        if not t:return await ctx.send("🏋️ Você não possui treinamento ativo.")
        await ctx.send(f"🛑 **TREINAMENTO CANCELADO**\n🎯 {t['alvo']}\n❌ Nenhuma recompensa foi recebida.\n\nVocê já pode participar de cenas, viajar ou iniciar outro treinamento.")

    @tasks.loop(seconds=30)
    async def verificar(self):
        for t in await treinamentos_prontos():
            feito=await concluir_treinamento(t['id'])
            if not feito:continue
            ch=self.bot.get_channel(t['canal_id']) if t['canal_id'] else None
            if ch:
                try: await ch.send(f"🏋️ <@{t['user_id']}> **TREINAMENTO CONCLUÍDO!**\n🎯 {t['alvo']}\n📈 +{t['ganho']}{'%' if t['tipo']=='dominio' else ' pontos'} aplicados à ficha.")
                except: pass
    @verificar.before_loop
    async def antes(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(Treinamento(bot))
