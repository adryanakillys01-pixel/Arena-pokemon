"""Build a playable catalog from the official PokéAPI public CSV dataset."""
import csv, io, json, time, urllib.request
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE='https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/'
ROOT=Path(__file__).resolve().parent
FILES=['pokemon','pokemon_species','pokemon_species_names','pokemon_stats','pokemon_types','pokemon_abilities','abilities','moves','move_names','pokemon_moves']
TYPE={1:'Normal',2:'Lutador',3:'Voador',4:'Veneno',5:'Terra',6:'Pedra',7:'Inseto',8:'Fantasma',9:'Aço',10:'Fogo',11:'Água',12:'Planta',13:'Elétrico',14:'Psíquico',15:'Gelo',16:'Dragão',17:'Sombrio',18:'Fada'}
# These names refer to the existing engine's translated moves.
NAMES=dict(zip(
'earthquake rock-slide double-edge swords-dance bonemerang fire-punch thunder-punch headbutt double-kick cotton-guard rest flamethrower dragon-pulse slash will-o-wisp giga-drain sludge-bomb sleep-powder leech-seed hyper-voice dazzling-gleam sing thunder-wave surf ice-beam psychic calm-mind wood-hammer synthesis flare-blitz quick-attack bite brave-bird iron-head body-press roost u-turn fake-out play-rough thunderbolt ice-punch brick-break dragon-claw poison-jab dragon-dance muddy-water counter mirror-coat encore destiny-bond shadow-ball focus-blast recover wild-charge crunch ice-fang iron-tail grass-knot earth-power moongeist-beam moonblast dark-pulse oblivion-wing'.split(),
'Terremoto|Deslizamento de Rochas|Investida Dupla|Dança das Espadas|Bumerangue de Osso|Soco de Fogo|Soco de Trovão|Cabeçada|Chute Duplo|Guarda de Algodão|Descanso|Lança-chamas|Pulso do Dragão|Corte|Fogo-fátuo|Giga Dreno|Bomba de Lodo|Pó do Sono|Semente Sanguessuga|Hipervoz|Brilho Deslumbrante|Cantar|Onda de Trovão|Surf|Raio de Gelo|Psíquico|Mente Calma|Martelo de Madeira|Síntese|Investida Flamejante|Ataque Rápido|Mordida|Pássaro Bravo|Cabeça de Ferro|Pressão Corporal|Roost|U-turn|Ataque Surpresa|Jogo Duro|Thunderbolt|Soco de Gelo|Quebra-tijolos|Garra do Dragão|Golpe Venenoso|Dança do Dragão|Água Lamacenta|Contra-ataque|Espelho Refletor|Encore|Laço do Destino|Bola Sombria|Explosão Focal|Recuperação|Carga Selvagem|Triturar|Presa de Gelo|Cauda de Ferro|Nó de Grama|Poder da Terra|Raio Espectral|Explosão Lunar|Pulso Sombrio|Asa da Oblivion'.split('|')))
# Additional familiar attacks with fixed damage formula. Effects not explicitly listed
# here are not simulated by the simplified battle engine.
EXTRA={
'tackle':('Investida',''),'scratch':('Arranhão',''),'pound':('Pancada',''),'ember':('Brasas','burn10'),
'water-gun':('Jato de Água',''),'vine-whip':('Chicote de Vinha',''),'razor-leaf':('Folha Navalha','highcrit'),
'confusion':('Confusão',''),'gust':('Rajada de Vento',''),'wing-attack':('Ataque de Asa',''),
'peck':('Bicada',''),'aerial-ace':('Ás Aéreo',''),'air-slash':('Corte de Ar','flinch30'),
'thunder-shock':('Choque do Trovão','para10'),'spark':('Faísca','para30'),'discharge':('Descarga','para30'),
'thunder':('Trovão','para30'),'fire-blast':('Explosão de Fogo','burn10'),'hydro-pump':('Hidro Bomba',''),
'bubble-beam':('Raio de Bolhas',''),'water-pulse':('Pulso de Água',''),'aqua-tail':('Cauda de Água',''),
'aqua-jet':('Jato Aqua',''),'waterfall':('Cachoeira','flinch20'),'leaf-blade':('Lâmina de Folha','highcrit'),
'energy-ball':('Bola de Energia','sd10'),'seed-bomb':('Bomba de Sementes',''),'petal-blizzard':('Nevasca de Pétalas',''),
'blizzard':('Nevasca','freeze10'),'ice-shard':('Estilhaço de Gelo',''),'icicle-crash':('Queda de Gelo','flinch30'),
'rock-throw':('Arremesso de Pedra',''),'stone-edge':('Gume de Pedra','highcrit'),'power-gem':('Gema de Poder',''),
'rock-tomb':('Tumba de Pedra',''),'mud-slap':('Tapa de Lama','acc100'),'bulldoze':('Terraplanagem',''),
'dig':('Escavar (turno único)',''),'shadow-claw':('Garra Sombria','highcrit'),'shadow-sneak':('Sombra Furtiva',''),
'lick':('Lambida','para30'),'hex':('Feitiço',''),'night-slash':('Corte Noturno','highcrit'),
'knock-off':('Derrubar',''),'sucker-punch':('Golpe Baixo',''),'snarl':('Rosnado','sadown100'),
'dragon-breath':('Sopro do Dragão','para30'),'dragon-tail':('Cauda do Dragão',''),'dragon-rush':('Investida do Dragão','flinch20'),
'bug-bite':('Mordida de Inseto',''),'x-scissor':('Tesoura X',''),'bug-buzz':('Zumbido','sd10'),
'signal-beam':('Raio Sinalizador',''),'poison-sting':('Ferrão Venenoso','poison30'),'sludge':('Lodo','poison30'),
'sludge-wave':('Onda de Lodo','poison10'),'acid':('Ácido','sd10'),'metal-claw':('Garra Metálica',''),
'flash-cannon':('Canhão de Luz','sd10'),'bullet-punch':('Soco Bala',''),'steel-wing':('Asa de Aço',''),
'metal-burst':('Explosão Metálica',''),'mach-punch':('Soco Mach',''),'force-palm':('Palma da Força','para30'),
'drain-punch':('Soco Drenante','drain'),'close-combat':('Combate Próximo',''),'low-sweep':('Rasteira',''),
'karate-chop':('Golpe de Karatê','highcrit'),'psybeam':('Raio Psíquico',''),'psyshock':('Choque Psíquico',''),
'extrasensory':('Extrassensorial','flinch10'),'fairy-wind':('Vento Feérico',''),'disarming-voice':('Voz Encantadora',''),
'draining-kiss':('Beijo Drenante','drain75'),'swift':('Estrelas Cadentes',''),'return':('Retorno',''),
'body-slam':('Impacto Corporal','para30'),'slam':('Batida',''),'strength':('Força',''),'mega-punch':('Mega Soco',''),
'mega-kick':('Mega Chute',''),'take-down':('Derrubada','recoil4'),'hyper-beam':('Hiper Raio (sem recarga)',''),
'giga-impact':('Giga Impacto (sem recarga)',''),'struggle-bug':('Luta de Inseto','sadown100'),
'flame-wheel':('Roda de Fogo','burn10'),'flame-charge':('Carga de Fogo',''),'fire-fang':('Presa de Fogo','burn10'),
'thunder-fang':('Presa de Trovão','para10'),'zen-headbutt':('Cabeçada Zen','flinch20'),
'liquidation':('Liquidação','def20'),'water-shuriken':('Shuriken de Água',''),'astonish':('Espanto','flinch30'),
'payback':('Vingança',''),'head-smash':('Esmagamento de Cabeça','recoil3'),'smack-down':('Derrubar Rocha',''),
'power-up-punch':('Soco Poderoso',''),'magical-leaf':('Folha Mágica',''),'fury-cutter':('Cortador de Fúria',''),
'rollout':('Rolagem',''),'thief':('Ladrão',''),'covet':('Cobiça',''),'present':('Presente',''),
'confide':('Confidência',''),'transform':('Transformação','transform'),'splash':('Salpico','splash'),
'harden':('Endurecer','def1'),'protect':('Proteção','protect'),'struggle':('Debater-se','recoil4')
}
# Exclude complex moves whose special mechanics would be misleading in this engine.
EXCLUDE=set('metal-burst return present confide dig sucker-punch close-combat psyshock hyper-beam giga-impact water-shuriken payback head-smash power-up-punch fury-cutter rollout knock-off flame-charge rock-tomb bulldoze dragon-tail hex'.split())
def download(name):
    for attempt in range(3):
        try:
            req=urllib.request.Request(BASE+name+'.csv',headers={'User-Agent':'Arena-Pokemon/2'})
            with urllib.request.urlopen(req,timeout=90) as res:return res.read().decode('utf-8-sig')
        except Exception:
            if attempt==2:raise
            time.sleep(2)
def rows(data,name):return csv.DictReader(io.StringIO(data[name]))
def main():
    with ThreadPoolExecutor(max_workers=5) as pool:data=dict(zip(FILES,pool.map(download,FILES)))
    species={int(r['id']):r for r in rows(data,'pokemon_species')}
    species_names={int(r['pokemon_species_id']):r['name'] for r in rows(data,'pokemon_species_names') if r['local_language_id']=='9'}
    stats=defaultdict(dict);types=defaultdict(dict);abilities=defaultdict(dict)
    for r in rows(data,'pokemon_stats'):stats[int(r['pokemon_id'])][int(r['stat_id'])]=int(r['base_stat'])
    for r in rows(data,'pokemon_types'):types[int(r['pokemon_id'])][int(r['slot'])]=TYPE.get(int(r['type_id']))
    ability_names={int(r['id']):r['identifier'].replace('-',' ').title() for r in rows(data,'abilities')}
    for r in rows(data,'pokemon_abilities'):
        if r['is_hidden']=='0':abilities[int(r['pokemon_id'])][int(r['slot'])]=ability_names.get(int(r['ability_id']),'')
    move_names={int(r['move_id']):r['name'] for r in rows(data,'move_names') if r['local_language_id']=='9'}
    supported={};definitions={}
    for r in rows(data,'moves'):
        mid=int(r['id']);key=r['identifier'];tp=TYPE.get(int(r['type_id']));cat={'1':'S','2':'F','3':'E'}.get(r['damage_class_id'])
        if not tp or not cat:continue
        if key in NAMES:
            supported[mid]=(NAMES[key],tp,cat,int(r['power'] or 0));continue
        if key not in EXTRA or key in EXCLUDE:continue
        name,effect=EXTRA[key];power=int(r['power'] or 0)
        if cat!='S' and power<=0:continue
        if cat=='S' and effect not in ('transform','splash','def1','protect'):continue
        definitions[name]=dict(type=tp,cat=cat,power=power,acc=int(r['accuracy'] or 100),effect=effect,priority=int(r['priority'] or 0))
        supported[mid]=(name,tp,cat,power)
    learn=defaultdict(set)
    for r in rows(data,'pokemon_moves'):
        mid=int(r['move_id'])
        if mid in supported:learn[int(r['pokemon_id'])].add(mid)
    catalog={};default_ids=set()
    for r in rows(data,'pokemon'):
        pid=int(r['id']);sid=int(r['species_id']);sp=species.get(sid);st=stats[pid];tp=[v for _,v in sorted(types[pid].items())]
        if not sp or len(st)<6 or not tp or any(v is None for v in tp):continue
        default=r['is_default']=='1';name=species_names.get(sid,r['identifier'].replace('-',' ').title()) if default else r['identifier'].replace('-',' ').title()
        # Keep every species and data-backed alternative form, including regional and Mega variants.
        if name in catalog:name+=' (#'+str(pid)+')'
        preferred='F' if st[2]>=st[4] else 'E'
        candidates=[supported[mid] for mid in sorted(learn[pid])]
        attacks=[v for v in candidates if v[2]!='S' and v[3]>0]
        def rank(v):return (min(v[3],120)*(1.3 if v[1] in tp else 1)*(1.15 if v[2]==preferred else 1),v[0])
        attacks.sort(key=rank,reverse=True);chosen=[];covered=set()
        for v in attacks:
            if v[1] not in covered:chosen.append(v[0]);covered.add(v[1])
            if len(chosen)>=3:break
        statuses=[v for v in candidates if v[2]=='S' and v[0]!='Salpico']
        statuses.sort(key=lambda v:(v[0] in ('Transformação','Recuperação','Dança das Espadas','Mente Calma','Dança do Dragão','Proteção'),v[0]),reverse=True)
        if statuses and len(chosen)<4:chosen.append(statuses[0][0])
        for v in attacks+statuses+candidates:
            if v[0] not in chosen and len(chosen)<4:chosen.append(v[0])
        if not any(v[0] in chosen for v in attacks) and 'Transformação' not in chosen:chosen.append('Debater-se')
        if not chosen:chosen=['Debater-se']
        # Pokémon with limited legal moves may have fewer than four, rather than invent moves.
        ab=abilities[pid];ability=ab[min(ab)] if ab else ''
        catalog[name]=dict(name=name,id=pid,speciesId=sid,default=default,generation=int(sp['generation_id']),legendary=sp['is_legendary']=='1' or sp['is_mythical']=='1',types=tp,stats=[st[1]+75]+[st[j]+20 for j in range(2,7)],ability=ability,moves=chosen[:4])
        if default:default_ids.add(sid)
    definitions.setdefault('Debater-se',dict(type='Normal',cat='F',power=50,acc=100,effect='recoil4',priority=0))
    if len(default_ids)!=len(species) or len(default_ids)<1000:raise RuntimeError(f'Incomplete species catalog: {len(default_ids)}/{len(species)}')
    out={'dex':catalog,'moves':definitions,'speciesCount':len(default_ids),'formsCount':len(catalog)}
    (ROOT/'catalog.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'CATALOG OK: {len(default_ids)} species; {len(catalog)} playable entries; {len(definitions)} extra moves',flush=True)
if __name__=='__main__':main()
