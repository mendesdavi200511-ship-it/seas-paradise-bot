import discord
import re
from discord.ext import commands

GUILD_ID = 1539056186798903418
LOGS_ID = 1552100946329346099
PUNICOES_ID = 1552161840467808326
ADMIN_ID = 1554180806216388628
AVISOS_PLAYER_ID = 1554178106330316840
ESTADO_MUNDO_ID = 1554180836113387540
CONTROLE_NPCS_ID = 1554180927003824148
BOAS_VINDAS_ID = 1539056188371632160
CRIAR_ID = 1551379201939218502
FICHAS_ID = 1554178079725981869
MESTRE_ROLE_ID = 1541858353196695632
AUTO_ROLES = [1542161384039776366,1542161683739574392,1542161421402644580,1542161536016064544,1542161469817491498,1542161789960192101,1542161738517192796,1541858736241647787,1542161091227029516,1542161193358074026,1542161337667289119]
WELCOME_GIF = 'https://tenor.com/bGup1.gif'

NPC_MASTER_COMMANDS = {'npclocal','npcatributos','limparcena','npcregistrar','npcmemoria','npcrecrutar'}
WORLD_MASTER_COMMANDS = {'localplayer'}


def mestre_ou_admin(member):
    if not isinstance(member, discord.Member): return False
    return member.guild_permissions.administrator or any(r.id == MESTRE_ROLE_ID for r in member.roles)

async def _canal(bot, cid):
    c=bot.get_channel(cid)
    if c: return c
    try: return await bot.fetch_channel(cid)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException): return None

class Servidor(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        bot.add_check(self.regras_comandos)

    def cog_unload(self):
        self.bot.remove_check(self.regras_comandos)

    @commands.Cog.listener()
    async def on_ready(self):
        # Migração silenciosa dos tópicos v83/v84: tira IDs técnicos do nome e guarda no banco.
        guild=self.bot.get_guild(GUILD_ID)
        if not guild: return
        try:
            from database.database import salvar_topico_personagem, salvar_topico_campanha
            for th in list(guild.threads):
                m=re.search(r'sp-(\d+)',th.name)
                if m and th.parent_id==FICHAS_ID:
                    uid=int(m.group(1)); await salvar_topico_personagem(uid,th.id)
                    membro=guild.get_member(uid); nome=membro.display_name if membro else 'Personagem'
                    try: await th.edit(name=f'📋・{nome[:70]} — Minha Ficha'[:100])
                    except (discord.Forbidden,discord.HTTPException): pass
                    continue
                m=re.search(r'camp-(\d+)',th.name)
                if m and th.parent_id:
                    uid=int(m.group(1)); await salvar_topico_campanha(uid,th.parent_id,th.id)
                    limpo=re.sub(r'[・\s]*camp-\d+\.?$','',th.name).strip()[:100]
                    try: await th.edit(name=limpo or '📖・Campanha')
                    except (discord.Forbidden,discord.HTTPException): pass
        except Exception as erro:
            print(f'⚠️ Migração de tópicos: {type(erro).__name__}: {erro}')

    async def regras_comandos(self, ctx):
        if not ctx.command or not ctx.guild or ctx.guild.id != GUILD_ID: return True
        nome=ctx.command.qualified_name.split()[0].casefold()
        cid=getattr(ctx.channel,'id',0)
        if cid == CRIAR_ID and nome != 'criar':
            try: await ctx.message.delete()
            except (discord.Forbidden,discord.NotFound): pass
            await ctx.send(f'🔒 Neste canal só é permitido `!criar`. Use seu tópico em <#{FICHAS_ID}> para ficha/edição.', delete_after=10)
            return False
        if nome == 'admin':
            if cid != ADMIN_ID:
                await ctx.send(f'🔒 `!admin` só pode ser usado em <#{ADMIN_ID}>.', delete_after=10); return False
            if not mestre_ou_admin(ctx.author):
                await ctx.send('❌ Apenas Administradores e Mestres podem usar `!admin`.', delete_after=10); return False
        if nome in NPC_MASTER_COMMANDS:
            if not mestre_ou_admin(ctx.author):
                await ctx.send('❌ Apenas Administradores e Mestres podem controlar NPCs.',delete_after=10); return False
            if cid != CONTROLE_NPCS_ID:
                await ctx.send(f'🎭 Use este comando em <#{CONTROLE_NPCS_ID}>.',delete_after=10); return False
        if nome in WORLD_MASTER_COMMANDS:
            if not mestre_ou_admin(ctx.author):
                await ctx.send('❌ Apenas Administradores e Mestres podem controlar o mundo.',delete_after=10); return False
            if cid != ESTADO_MUNDO_ID:
                await ctx.send(f'🌎 Use este comando em <#{ESTADO_MUNDO_ID}>.',delete_after=10); return False
        return True

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.guild.id != GUILD_ID or message.author == self.bot.user or message.channel.id == LOGS_ID: return
        ch=await _canal(self.bot,LOGS_ID)
        if not ch:return
        texto=message.content or '*sem texto*'
        e=discord.Embed(title='🗑️ MENSAGEM APAGADA',description=texto[:3500])
        e.add_field(name='Autor',value=f'{message.author.mention} (`{message.author.id}`)',inline=False)
        e.add_field(name='Canal',value=getattr(message.channel,'mention',f'#{message.channel}'),inline=False)
        if message.attachments:e.add_field(name='Anexos',value='\n'.join(a.url for a in message.attachments)[:1000],inline=False)
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        # on_message_delete só recebe mensagens em cache; este fallback cobre as demais.
        if payload.guild_id != GUILD_ID or payload.channel_id == LOGS_ID or payload.cached_message is not None:
            return
        ch = await _canal(self.bot, LOGS_ID)
        if not ch:
            return
        e = discord.Embed(title='🗑️ MENSAGEM APAGADA (fora do cache)', description='O Discord não manteve o conteúdo desta mensagem em cache.')
        e.add_field(name='Canal', value=f'<#{payload.channel_id}>', inline=False)
        e.add_field(name='Mensagem ID', value=f'`{payload.message_id}`', inline=False)
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        # Fallback para edições de mensagens fora do cache.
        if payload.guild_id != GUILD_ID or payload.channel_id == LOGS_ID or payload.cached_message is not None:
            return
        data = payload.data or {}
        # Eventos de embed/link preview também disparam raw edit; só loga alteração com conteúdo.
        if 'content' not in data:
            return
        ch = await _canal(self.bot, LOGS_ID)
        if not ch:
            return
        autor = data.get('author') or {}
        e = discord.Embed(title='✏️ MENSAGEM EDITADA (fora do cache)', description=(data.get('content') or '*vazio*')[:3500])
        e.add_field(name='Autor', value=f"<@{autor.get('id')}> (`{autor.get('id')}`)" if autor.get('id') else 'Desconhecido', inline=False)
        e.add_field(name='Canal', value=f'<#{payload.channel_id}>', inline=False)
        e.add_field(name='Mensagem ID', value=f'`{payload.message_id}`', inline=False)
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.guild.id != GUILD_ID or before.author == self.bot.user or before.channel.id == LOGS_ID or before.content == after.content:return
        ch=await _canal(self.bot,LOGS_ID)
        if not ch:return
        e=discord.Embed(title='✏️ MENSAGEM EDITADA')
        e.add_field(name='Autor',value=f'{before.author.mention} (`{before.author.id}`)',inline=False)
        e.add_field(name='Canal',value=getattr(before.channel,'mention',f'#{before.channel}'),inline=False)
        e.add_field(name='Antes',value=(before.content or '*vazio*')[:1000],inline=False)
        e.add_field(name='Depois',value=(after.content or '*vazio*')[:1000],inline=False)
        e.add_field(name='Mensagem',value=f'[Ir para mensagem]({after.jump_url})',inline=False)
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != GUILD_ID:return
        cargos=[member.guild.get_role(x) for x in AUTO_ROLES]; cargos=[x for x in cargos if x]
        if cargos:
            try: await member.add_roles(*cargos,reason="Entrada automática — Sea's Paradise")
            except discord.Forbidden: pass
        ch=await _canal(self.bot,BOAS_VINDAS_ID)
        if ch:
            e=discord.Embed(title="🏴‍☠️ BEM-VINDO AO SEA'S PARADISE!",description=f'{member.mention} acaba de chegar aos mares.\n\nLeia as regras, prepare seu personagem e comece sua jornada!')
            e.set_footer(text=f'Membro #{member.guild.member_count}')
            e.set_image(url=WELCOME_GIF)
            await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_ban(self,guild,user):
        if guild.id==GUILD_ID: await self._punicao(user,'BANIMENTO','Usuário banido do servidor.')

    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if after.guild.id!=GUILD_ID:return
        if before.timed_out_until != after.timed_out_until and after.timed_out_until:
            await self._punicao(after,'CASTIGO / TIMEOUT',f'Até {discord.utils.format_dt(after.timed_out_until,"F")}.')

    async def _punicao(self,user,tipo,motivo):
        ch=await _canal(self.bot,PUNICOES_ID)
        if not ch:return
        e=discord.Embed(title=f'🔨 {tipo}',description=f'{getattr(user,"mention",str(user))}\n{motivo}')
        e.set_footer(text=f'ID: {user.id}')
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_message(self,message):
        if not message.guild or message.guild.id!=GUILD_ID or message.author.bot:return
        if message.channel.id==CRIAR_ID and message.content.strip().casefold()!='!criar':
            # Comandos são tratados pelo check global para não gerar aviso duplicado.
            if message.content.lstrip().startswith('!'):
                return
            try: await message.delete()
            except (discord.Forbidden,discord.NotFound): pass
            try:
                aviso=await message.channel.send(f'{message.author.mention}, aqui é permitido somente `!criar`. Sua mensagem foi removida.')
                await aviso.delete(delay=8)
            except discord.HTTPException:pass

    @commands.command(name='estadomundo')
    async def estadomundo(self,ctx):
        if not mestre_ou_admin(ctx.author): return await ctx.send('❌ Apenas Administradores e Mestres.')
        if ctx.channel.id!=ESTADO_MUNDO_ID:return await ctx.send(f'🌎 Use em <#{ESTADO_MUNDO_ID}>.')
        from database.database import listar_eventos_globais_abertos
        eventos=await listar_eventos_globais_abertos()
        e=discord.Embed(title='🌎 ESTADO ATUAL DO MUNDO',description='Painel operacional da Mestragem.')
        e.add_field(name='Eventos globais abertos',value='\n'.join(f"• {x['titulo']} — {x['localizacao']}" for x in eventos[:15]) or 'Nenhum.',inline=False)
        await ctx.send(embed=e)

    @commands.command(name='controlenpcs')
    async def controlenpcs(self,ctx):
        if not mestre_ou_admin(ctx.author):return await ctx.send('❌ Apenas Administradores e Mestres.')
        if ctx.channel.id!=CONTROLE_NPCS_ID:return await ctx.send(f'🎭 Use em <#{CONTROLE_NPCS_ID}>.')
        from database.database import listar_npcs_mundo
        try:
            rows=await listar_npcs_mundo(50)
        except Exception as erro:
            print(f"❌ ERRO PAINEL NPC — {type(erro).__name__}: {erro}")
            return await ctx.send('⚠️ Não consegui consultar os NPCs persistentes agora. O erro foi registrado no console.')
        e=discord.Embed(title='🎭 CONTROLE DE NPCs',description='NPCs persistentes conhecidos pelo mundo.', color=discord.Color.dark_teal())
        linhas=[]
        for x in rows[:30]:
            nome=x['nome'] if 'nome' in x else 'NPC'
            local=(x['localizacao'] if 'localizacao' in x else None) or 'local desconhecido'
            status=(x['status'] if 'status' in x else None) or 'desconhecido'
            linhas.append(f"• **{nome}** — {local} • {status}")
        e.add_field(name='NPCs',value='\n'.join(linhas)[:4000] or 'Nenhum NPC persistente registrado.',inline=False)
        e.set_footer(text="Sea's Paradise • Mestragem")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(Servidor(bot))
