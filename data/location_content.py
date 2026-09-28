"""Catálogo de lançamento por HUB.
NPCs são sementes persistentes do mundo. Sublocações ficam dentro do HUB.
Os dados mecânicos são do RP, não estatísticas oficiais de One Piece.
"""
from data.discord_world import TODOS_HUBS, HUBS_POR_REGIAO

# NPCs/figuras relevantes por HUB. Não pretende listar todo figurante do mangá;
# garante elenco inicial + infraestrutura para o narrador persistente.
NPCS = {
'Dawn Island':['Makino','Woop Slap','Higuma'], 'Goa Kingdom':['Stelly','Outlook III'],
'Shells Town':['Koby','Helmeppo','Axe-Hand Morgan','Roronoa Zoro'],
'Orange Town':['Buggy','Cabaji','Mohji','Richie'], 'Syrup Village':['Kuro','Kaya','Usopp'],
'Baratie':['Zeff','Sanji','Don Krieg','Gin','Dracule Mihawk'],
'Conomi Islands':['Arlong','Hatchan','Kuroobi','Chew'], 'Loguetown':['Smoker','Tashigi','Monkey D. Dragon'],
'Tequila Wolf':['Supervisor de Tequila Wolf'], 'Reverse Mountain':['Crocus','Laboon'], 'Twin Cape':['Crocus','Laboon'],
'Whisky Peak':['Igaram','Miss Monday','Mr. 9'], 'Little Garden':['Dorry','Brogy'],
'Drum Island':['Dalton','Kureha','Wapol'], 'Alabasta':['Nefertari Cobra','Nefertari Vivi','Pell','Chaka'],
'Jaya':['Bellamy','Mont Blanc Cricket'], 'Skypiea':['Gan Fall','Conis','Pagaya','Wyper'], 'Weatheria':['Haredas'],
'Long Ring Long Land':['Tonjit','Foxy'], 'Water 7':['Iceburg','Paulie','Franky'],
'Enies Lobby':['Spandam','Rob Lucci','Kaku','Kalifa'], 'Thriller Bark':['Gecko Moria','Perona','Absalom'],
'Sabaody Archipelago':['Silvers Rayleigh','Shakuyaku','Trafalgar Law','Kizaru (Borsalino)'],
'Amazon Lily':['Boa Hancock','Boa Sandersonia','Boa Marigold'], 'Impel Down':['Magellan','Hannyabal'],
'Marineford':['Sengoku','Monkey D. Garp','Akainu (Sakazuki)','Aokiji (Kuzan)','Kizaru (Borsalino)'],
'Rusukaina':['Guardião de Rusukaina'], 'Kuraigana Island':['Dracule Mihawk','Perona'], 'Momoiro Island':['Emporio Ivankov'],
'Boin Archipelago':['Heracles'], 'Karakuri Island':['Habitante de Karakuri'], 'Torino Kingdom':['Ancião de Torino'],
'Namakura Island':['Habitante de Namakura'], 'Fish-Man Island':['Neptune','Shirahoshi','Jinbe'],
'Mary Geoise':['Guarda de Mary Geoise'], 'Punk Hazard':['Caesar Clown','Vergo'],
'Dressrosa':['Donquixote Doflamingo','Kyros','Rebecca','Diamante','Pica','Trebol'],
'Zou':['Inuarashi','Nekomamushi','Wanda'], 'Whole Cake Island':['Charlotte Linlin','Charlotte Katakuri','Charlotte Pudding'],
'Wano Country':['Kozuki Momonosuke','Kinemon','Kaido','Yamato'], 'Egghead':['Dr. Vegapunk','Sentomaru'],
'Elbaf':['Dorry','Brogy'], 'Hachinosu':['Marshall D. Teach','Kuzan'], 'Winner Island':['Navegador de Winner Island'],
'Karai Bari Island':['Buggy','Crocodile','Dracule Mihawk'], 'Sphinx':['Marco'], 'G-14':['Vice-Almirante Doll'],
'Ohara':['Nico Olvia','Professor Clover'], 'Ilusia Kingdom':['Autoridade de Ilusia'], 'Kano Country':['Don Chinjao','Sai'],
'Germa Kingdom':['Vinsmoke Judge','Vinsmoke Reiju'], 'Flevance':['Médico de Flevance'], 'Lvneel Kingdom':['Historiador de Lvneel'],
'Sorbet Kingdom':['Habitante de Sorbet'], 'Centauria':['Resistência de Centauria'], 'Baterilla':['Morador de Baterilla'],
'God Valley':['Eco de God Valley'], 'Laugh Tale':['Mistério de Laugh Tale'],
}

LOJAS_TIPO={
'East Blue':['Taverna','Mercado','Estaleiro'], 'Grand Line':['Taverna','Mercado','Log Pose / Navegação'],
'Ilhas do Céu':['Mercado Celeste','Dials / Suprimentos'], 'Paraíso':['Mercado','Estaleiro','Suprimentos'],
'Red Line':['Suprimentos','Mercado'], 'Novo Mundo':['Mercado','Estaleiro','Suprimentos avançados'],
'Outros Mares':['Mercado','Taverna','Suprimentos'], 'Locais Especiais':[]}

EVENTOS_TIPO={
1:['Rumor local','Pedido de ajuda','Pequena descoberta'],2:['Conflito local','Caçada','Tesouro'],3:['Emboscada','Operação de facção','Tesouro raro'],4:['Crise regional','Boss local','Operação de alto risco'],5:['Evento mundial','Boss de elite','Conflito de facções']}

def regiao_de(local):
    return next((r for r,xs in HUBS_POR_REGIAO.items() if local in xs),'Desconhecida')

def perigo_de(local):
    from data.navegacao import LOCAIS
    return LOCAIS.get(local,('',2))[1]

def conteudo(local):
    reg=regiao_de(local); perigo=perigo_de(local)
    return {'npcs':NPCS.get(local,[f'Guia de {local}',f'Comerciante de {local}']),
            'lojas':LOJAS_TIPO.get(reg,['Mercado','Suprimentos']),
            'eventos':EVENTOS_TIPO.get(perigo,EVENTOS_TIPO[2])}

# Garantias de lançamento.
assert set(TODOS_HUBS)==set(NPCS), f'HUBs sem elenco: {set(TODOS_HUBS)-set(NPCS)}'
