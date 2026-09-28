"""Registro autoritativo dos HUBs do mundo no Discord.
Somente canais desta lista são tratados como localizações jogáveis.
Sublocações continuam sendo estado narrativo, nunca HUBs separados.
"""
import re, unicodedata

HUBS_POR_REGIAO = {
"East Blue": ["Dawn Island","Goa Kingdom","Shells Town","Orange Town","Syrup Village","Baratie","Conomi Islands","Loguetown","Tequila Wolf"],
"Grand Line": ["Reverse Mountain","Twin Cape","Whisky Peak","Little Garden","Drum Island","Alabasta","Jaya"],
"Ilhas do Céu": ["Skypiea","Weatheria"],
"Paraíso": ["Long Ring Long Land","Water 7","Enies Lobby","Thriller Bark","Sabaody Archipelago","Amazon Lily","Impel Down","Marineford","Rusukaina","Kuraigana Island","Momoiro Island","Boin Archipelago","Karakuri Island","Torino Kingdom","Namakura Island"],
"Red Line": ["Fish-Man Island","Mary Geoise"],
"Novo Mundo": ["Punk Hazard","Dressrosa","Zou","Whole Cake Island","Wano Country","Egghead","Elbaf","Hachinosu","Winner Island","Karai Bari Island","Sphinx","G-14"],
"Outros Mares": ["Ohara","Ilusia Kingdom","Kano Country","Germa Kingdom","Flevance","Lvneel Kingdom","Sorbet Kingdom","Centauria","Baterilla"],
"Locais Especiais": ["God Valley","Laugh Tale"],
}

SLUGS = {
"Dawn Island":"dawn-island","Goa Kingdom":"goa-kingdom","Shells Town":"shells-town","Orange Town":"orange-town","Syrup Village":"syrup-village","Baratie":"baratie","Conomi Islands":"conomi-islands","Loguetown":"loguetown","Tequila Wolf":"tequila-wolf",
"Reverse Mountain":"reverse-mountain","Twin Cape":"twin-cape","Whisky Peak":"whisky-peak","Little Garden":"little-garden","Drum Island":"drum-island","Alabasta":"alabasta","Jaya":"jaya","Skypiea":"skypiea","Weatheria":"weatheria",
"Long Ring Long Land":"long-ring-long-land","Water 7":"water-7","Enies Lobby":"enies-lobby","Thriller Bark":"thriller-bark","Sabaody Archipelago":"sabaody","Amazon Lily":"amazon-lily","Impel Down":"impel-down","Marineford":"marineford","Rusukaina":"rusukaina","Kuraigana Island":"kuraigana-island","Momoiro Island":"momoiro-island","Boin Archipelago":"boin-archipelago","Karakuri Island":"karakuri-island","Torino Kingdom":"torino-kingdom","Namakura Island":"namakura-island",
"Fish-Man Island":"fish-man-island","Mary Geoise":"mary-geoise","Punk Hazard":"punk-hazard","Dressrosa":"dressrosa","Zou":"zou","Whole Cake Island":"whole-cake-island","Wano Country":"wano","Egghead":"egghead","Elbaf":"elbaf","Hachinosu":"hachinosu","Winner Island":"winner-island","Karai Bari Island":"karai-bari","Sphinx":"sphinx","G-14":"g-14",
"Ohara":"ohara","Ilusia Kingdom":"ilusia-kingdom","Kano Country":"kano-country","Germa Kingdom":"germa-kingdom","Flevance":"flevance","Lvneel Kingdom":"lvneel-kingdom","Sorbet Kingdom":"sorbet-kingdom","Centauria":"centauria","Baterilla":"baterilla","God Valley":"god-valley","Laugh Tale":"laugh-tale",
}

def chave(v):
    v=unicodedata.normalize("NFKD",str(v or "")).encode("ascii","ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+","",v)

HUB_POR_CHAVE={chave(slug):local for local,slug in SLUGS.items()}
# nomes canônicos também resolvem
HUB_POR_CHAVE.update({chave(local):local for local in SLUGS})

def resolver_hub_nome(nome):
    k=chave(nome)
    if not k:return None
    if k in HUB_POR_CHAVE:return HUB_POR_CHAVE[k]
    # Canal decorado: emoji + slug + sufixo japonês. Procura slug contido.
    achados=[(len(ck),local) for ck,local in HUB_POR_CHAVE.items() if ck and ck in k]
    return max(achados)[1] if achados else None

def resolver_hub_canal(channel):
    # Em thread, o pai é sempre a autoridade da ilha.
    parent=getattr(channel,"parent",None)
    if parent is not None:
        x=resolver_hub_nome(getattr(parent,"name",None))
        if x:return x
    return resolver_hub_nome(getattr(channel,"name",None))

TODOS_HUBS=[x for xs in HUBS_POR_REGIAO.values() for x in xs]
