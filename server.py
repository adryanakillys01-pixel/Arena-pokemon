from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import json, secrets, random, threading, os, time, copy
ROOT=Path(__file__).parent
# name, dex id, types, official base stats (HP,A,D,SA,SD,Spe), ability, moves
RAW=[
('Marowak',105,'Terra',[60,80,110,50,80,45],'Rock Head','Terremoto|Deslizamento de Rochas|Investida Dupla|Dança das Espadas'),
('Cubone',104,'Terra',[50,50,95,40,50,35],'Battle Armor','Bumerangue de Osso|Soco de Fogo|Soco de Trovão|Cabeçada'),
('Wooloo',831,'Normal',[42,40,55,40,45,48],'Fluffy','Cabeçada|Chute Duplo|Guarda de Algodão|Descanso'),
('Charmander',4,'Fogo',[39,52,43,60,50,65],'Blaze','Lança-chamas|Pulso do Dragão|Corte|Fogo-fátuo'),
('Bulbasaur',1,'Planta/Veneno',[45,49,49,65,65,45],'Overgrow','Giga Dreno|Bomba de Lodo|Pó do Sono|Semente Sanguessuga'),
('Jigglypuff',39,'Normal/Fada',[115,45,20,45,25,20],'Competitive','Hipervoz|Brilho Deslumbrante|Cantar|Onda de Trovão'),
('Psyduck',54,'Água',[50,52,48,65,50,55],'Cloud Nine','Surf|Raio de Gelo|Psíquico|Mente Calma'),
('Torterra',389,'Planta/Terra',[95,109,105,75,85,56],'Overgrow','Terremoto|Martelo de Madeira|Deslizamento de Rochas|Síntese'),
('Flareon',136,'Fogo',[65,130,60,95,110,65],'Flash Fire','Investida Flamejante|Ataque Rápido|Mordida|Fogo-fátuo'),
('Corviknight',823,'Aço/Voador',[98,87,105,53,85,67],'Mirror Armor','Pássaro Bravo|Cabeça de Ferro|Pressão Corporal|Roost'),
('Talonflame',663,'Fogo/Voador',[78,81,71,74,69,126],'Gale Wings','Pássaro Bravo|Investida Flamejante|U-turn|Roost'),
('Meowth',52,'Normal',[40,45,35,40,40,90],'Technician','Ataque Surpresa|Mordida|Corte|Jogo Duro'),
('Electabuzz',125,'Elétrico',[65,83,57,95,85,105],'Static','Thunderbolt|Soco de Gelo|Quebra-tijolos|Onda de Trovão'),
('Haxorus',612,'Dragão',[76,147,90,60,70,97],'Mold Breaker','Garra do Dragão|Terremoto|Golpe Venenoso|Dança do Dragão'),
('Goodra',706,'Dragão',[90,100,70,110,150,80],'Sap Sipper','Pulso do Dragão|Bomba de Lodo|Água Lamacenta|Lança-chamas'),
('Wobbuffet',202,'Psíquico',[190,33,58,33,58,33],'Shadow Tag','Contra-ataque|Espelho Refletor|Encore|Laço do Destino'),
('Alakazam',65,'Psíquico',[55,50,45,135,95,120],'Magic Guard','Psíquico|Bola Sombria|Explosão Focal|Recuperação'),
('Luxray',405,'Elétrico',[80,120,79,95,79,70],'Intimidação','Carga Selvagem|Triturar|Presa de Gelo|Onda de Trovão'),
('Pikachu',25,'Elétrico',[35,55,40,50,50,90],'Static','Thunderbolt|Ataque Rápido|Cauda de Ferro|Nó de Grama'),
('Nidoking',34,'Veneno/Terra',[81,102,77,85,75,85],'Sheer Force','Poder da Terra|Bomba de Lodo|Raio de Gelo|Lança-chamas'),
('Lunala',792,'Psíquico/Fantasma',[137,113,89,137,107,97],'Shadow Shield','Raio Espectral|Psíquico|Explosão Lunar|Mente Calma'),
('Gengar',94,'Fantasma/Veneno',[60,65,60,130,75,110],'Cursed Body','Bola Sombria|Bomba de Lodo|Explosão Focal|Psíquico'),
('Yveltal',717,'Sombrio/Voador',[126,131,95,131,98,99],'Dark Aura','Asa da Oblivion|Pássaro Bravo|Pulso Sombrio|Bola Sombria'),
]
# type, category, power, accuracy, effect, priority
MOVES={}
def m(n,t,c,p=0,a=100,e='',pr=0): MOVES[n]=dict(type=t,cat=c,power=p,acc=a,effect=e,priority=pr)
for n,t,c,p,a,e,pr in [
('Asa da Oblivion','Voador','E',80,100,'drain75',0),('Terremoto','Terra','F',100,100,'',0),('Deslizamento de Rochas','Pedra','F',75,90,'flinch30',0),('Investida Dupla','Normal','F',120,100,'recoil3',0),('Dança das Espadas','Normal','S',0,100,'atk2',0),('Bumerangue de Osso','Terra','F',50,90,'twice',0),('Soco de Fogo','Fogo','F',75,100,'burn10',0),('Soco de Trovão','Elétrico','F',75,100,'para10',0),('Cabeçada','Normal','F',70,100,'flinch30',0),('Chute Duplo','Lutador','F',30,100,'twice',0),('Guarda de Algodão','Planta','S',0,100,'def3',0),('Descanso','Psíquico','S',0,100,'rest',0),('Lança-chamas','Fogo','E',90,100,'burn10',0),('Pulso do Dragão','Dragão','E',85,100,'',0),('Corte','Normal','F',70,100,'highcrit',0),('Fogo-fátuo','Fogo','S',0,85,'burn',0),('Giga Dreno','Planta','E',75,100,'drain',0),('Bomba de Lodo','Veneno','E',90,100,'poison30',0),('Pó do Sono','Planta','S',0,75,'sleep',0),('Semente Sanguessuga','Planta','S',0,90,'seed',0),('Hipervoz','Normal','E',90,100,'',0),('Brilho Deslumbrante','Fada','E',80,100,'',0),('Cantar','Normal','S',0,55,'sleep',0),('Onda de Trovão','Elétrico','S',0,90,'para',0),('Surf','Água','E',90,100,'',0),('Raio de Gelo','Gelo','E',90,100,'freeze10',0),('Psíquico','Psíquico','E',90,100,'sd10',0),('Mente Calma','Psíquico','S',0,100,'calm',0),('Martelo de Madeira','Planta','F',120,100,'recoil3',0),('Síntese','Planta','S',0,100,'heal',0),('Investida Flamejante','Fogo','F',120,100,'flare',0),('Ataque Rápido','Normal','F',40,100,'',1),('Mordida','Sombrio','F',60,100,'flinch30',0),('Pássaro Bravo','Voador','F',120,100,'recoil3',0),('Cabeça de Ferro','Aço','F',80,100,'flinch30',0),('Pressão Corporal','Lutador','F',80,100,'body',0),('Roost','Voador','S',0,100,'roost',0),('U-turn','Inseto','F',70,100,'pivot',0),('Ataque Surpresa','Normal','F',40,100,'fakeout',3),('Jogo Duro','Fada','F',90,90,'atkdown10',0),('Thunderbolt','Elétrico','E',90,100,'para10',0),('Soco de Gelo','Gelo','F',75,100,'freeze10',0),('Quebra-tijolos','Lutador','F',75,100,'',0),('Garra do Dragão','Dragão','F',80,100,'',0),('Golpe Venenoso','Veneno','F',80,100,'poison30',0),('Dança do Dragão','Dragão','S',0,100,'dance',0),('Água Lamacenta','Água','E',90,85,'acc30',0),('Contra-ataque','Lutador','F',0,100,'counter',-5),('Espelho Refletor','Psíquico','E',0,100,'mirror',-5),('Encore','Normal','S',0,100,'encore',0),('Laço do Destino','Fantasma','S',0,100,'destiny',0),('Bola Sombria','Fantasma','E',80,100,'sd20',0),('Explosão Focal','Lutador','E',120,70,'sd10',0),('Recuperação','Normal','S',0,100,'heal',0),('Carga Selvagem','Elétrico','F',90,100,'recoil4',0),('Triturar','Sombrio','F',80,100,'def20',0),('Presa de Gelo','Gelo','F',65,95,'freeze10',0),('Cauda de Ferro','Aço','F',100,75,'def30',0),('Nó de Grama','Planta','E',80,100,'',0),('Poder da Terra','Terra','E',90,100,'sd10',0),('Raio Espectral','Fantasma','E',100,100,'',0),('Explosão Lunar','Fada','E',95,100,'sadown30',0),('Pulso Sombrio','Sombrio','E',80,100,'flinch20',0)]: m(n,t,c,p,a,e,pr)
DEX={n:dict(name=n,id=i,types=t.split('/'),stats=[s[0]+75]+[x+20 for x in s[1:]],ability=ab,moves=ms.split('|')) for n,i,t,s,ab,ms in RAW}
# Load complete PokéAPI catalog (generated during startup if not packaged).
def load_catalog():
    path=ROOT/'catalog.json'
    if not path.exists():
        from build_catalog import main
        main()
    data=json.loads(path.read_text(encoding='utf-8'))
    if data['speciesCount']<1000:raise RuntimeError('Catálogo incompleto')
    for name,p in data['dex'].items():
        if p['ability']=='Intimidate':p['ability']='Intimidação'
        if name in DEX:
            p.update(DEX[name])
        DEX[name]=p
    for n,m in data['moves'].items():MOVES.setdefault(n,m)
    for n,m in MOVES.items():m['pp']=data.get('movePP',{}).get(n,10)
    MOVES.setdefault('Debater-se',dict(type='Normal',cat='F',power=50,acc=100,effect='recoil4',priority=0,pp=1))
    print(f"Pokédex: {data['speciesCount']} espécies, {len(DEX)} entradas, {len(MOVES)} golpes",flush=True)
    return data['speciesCount']
SPECIES_COUNT=load_catalog()
# attacker: super effective, resisted, immune
TYPES={
'Normal':('', 'Pedra Aço','Fantasma'),'Fogo':('Planta Gelo Inseto Aço','Fogo Água Pedra Dragão',''),'Água':('Fogo Terra Pedra','Água Planta Dragão',''),'Elétrico':('Água Voador','Elétrico Planta Dragão','Terra'),'Planta':('Água Terra Pedra','Fogo Planta Veneno Voador Inseto Dragão Aço',''),'Gelo':('Planta Terra Voador Dragão','Fogo Água Gelo Aço',''),'Lutador':('Normal Gelo Pedra Sombrio Aço','Veneno Voador Psíquico Inseto Fada','Fantasma'),'Veneno':('Planta Fada','Veneno Terra Pedra Fantasma','Aço'),'Terra':('Fogo Elétrico Veneno Pedra Aço','Planta Inseto','Voador'),'Voador':('Planta Lutador Inseto','Elétrico Pedra Aço',''),'Psíquico':('Lutador Veneno','Psíquico Aço','Sombrio'),'Inseto':('Planta Psíquico Sombrio','Fogo Lutador Veneno Voador Fantasma Aço Fada',''),'Pedra':('Fogo Gelo Voador Inseto','Lutador Terra Aço',''),'Fantasma':('Psíquico Fantasma','Sombrio','Normal'),'Dragão':('Dragão','Aço','Fada'),'Sombrio':('Psíquico Fantasma','Lutador Sombrio Fada',''),'Aço':('Gelo Pedra Fada','Fogo Água Elétrico Aço',''),'Fada':('Lutador Dragão Sombrio','Fogo Veneno Aço','')}
def eff(t,types):
    a,b,c=TYPES[t]; v=1
    for x in types: v*=0 if x in c.split() else 2 if x in a.split() else .5 if x in b.split() else 1
    return v
R=random.SystemRandom(); LOCK=threading.RLock(); ROOMS={}; STORE=Path(os.environ.get('ARENA_DATA',str(ROOT/'rooms.json')))
try: ROOMS=json.loads(STORE.read_text())
except (OSError,ValueError): pass
def save():
    tmp=STORE.with_suffix('.tmp');tmp.write_text(json.dumps(ROOMS,ensure_ascii=False));tmp.replace(STORE)
def chance(n):return R.random()*100<n
def maxpp(n):return MOVES[n].get('pp',10)
def pp_for(p):return p.setdefault('pp',{n:maxpp(n) for n in p['moves']})
def legal_moves(p):
    usable=[n for n in p['moves'] if pp_for(p).get(n,0)>0]
    return usable or ['Debater-se']
def fighter(n):
    p=copy.deepcopy(DEX[n]);p.update(pp={n:maxpp(n) for n in p['moves']},hp=p['stats'][0],status='',sleep=0,st=[0]*6,seed=False,age=0,last='',encore=0,destiny=False,flash=False,roost=False,protect=False,transformed=None);return p
def active(r,i):return r['players'][i]['team'][r['players'][i]['active']]
def living(r,i):return [j for j,p in enumerate(r['players'][i]['team']) if p['hp']>0]
def log(r,s):r['log'].append(s);r['log']=r['log'][-100:]
def stat(p,j,critical=False,defending=False):
    s=p['st'][j-1]
    if critical:s=min(s,0) if defending else max(s,0)
    v=p['stats'][j]*(2+s)/2 if s>=0 else p['stats'][j]*2/(2-s)
    if j==1 and p['ability'] in ('Huge Power','Pure Power'):v*=2
    if j==5 and p['status']=='Paralisado' and p['ability']!='Quick Feet':v*=.5
    if j==5 and p['status'] and p['ability']=='Quick Feet':v*=1.5
    return max(1,int(v))
def heal(p,n):p['hp']=min(p['stats'][0],p['hp']+n)
def hurt(p,n):d=min(p['hp'],max(0,n));p['hp']-=d;return d
def stage(r,p,j,n,other=None):
    if n<0 and other and p['ability']=='Mirror Armor':return stage(r,other,j,n)
    old=p['st'][j];p['st'][j]=max(-6,min(6,old+n));log(r,f"{p['name']}: atributo {'↑' if n>0 else '↓'} {abs(p['st'][j]-old)}.")
    if n<0 and other and p['ability']=='Competitive':stage(r,p,2,2)
def status(r,p,s):
    if (s=='Dormindo' and p['ability'] in ('Insomnia','Vital Spirit')) or (s=='Queimado' and p['ability']=='Water Veil') or (s=='Paralisado' and p['ability']=='Limber') or (s=='Envenenado' and p['ability']=='Immunity') or (s=='Congelado' and p['ability']=='Magma Armor'):return False
    if p['status'] or (s=='Queimado' and 'Fogo' in p['types']) or (s=='Paralisado' and 'Elétrico' in p['types']) or (s=='Congelado' and 'Gelo' in p['types']) or (s=='Envenenado' and any(t in p['types'] for t in ['Aço','Veneno'])):return False
    p['status']=s;p['sleep']=R.randint(1,3) if s=='Dormindo' else 0;log(r,f"{p['name']} está {s.lower()}!");return True
def enter(r,i,j):
    old=active(r,i);original=old.get('transformed');
    if original:old.update(original);old['transformed']=None
    old.update(st=[0]*6,seed=False,encore=0,destiny=False,roost=False,flash=False,protect=False);r['players'][i]['active']=j;p=active(r,i);p['age']=0;log(r,f"{r['players'][i]['name']} envia {p['name']}!")
    if p['ability']=='Intimidação' and living(r,1-i):stage(r,active(r,1-i),0,-1,p)
def finish(r):
    alive=[bool(living(r,i)) for i in range(2)]
    if all(alive):return False
    r['phase']='end';r['winner']=alive.index(True) if any(alive) else -1
    if r['winner']>=0:r['score'][r['winner']]+=1;log(r,f"🏆 {r['players'][r['winner']]['name']} venceu!")
    else:log(r,'Empate!')
    return True
def attack(r,i,name,received,flinched):
    p,q=active(r,i),active(r,1-i)
    if not p['hp'] or not q['hp']:return
    if i in flinched:log(r,f"{p['name']} recuou e não atacou.");return
    if p['status']=='Dormindo':
        if p['sleep']>0:p['sleep']-=1;log(r,f"{p['name']} dorme.");return
        p['status']='';log(r,f"{p['name']} acordou!")
    if p['status']=='Paralisado' and chance(25):log(r,f"{p['name']} ficou imóvel!");return
    if p['status']=='Congelado':
        if chance(20) or name=='Investida Flamejante':p['status']=''
        else:log(r,f"{p['name']} está congelado!");return
    if p['encore'] and p['last'] in legal_moves(p):name=p['last']
    if name not in legal_moves(p):name=legal_moves(p)[0]
    pp=pp_for(p)
    if name in pp:pp[name]=max(0,pp[name]-1-(1 if q['ability']=='Pressure' else 0))
    p['destiny']=False;v=MOVES[name];e=v['effect'];t=v['type'];cat=v['cat'];log(r,f"{p['name']} usa {name}!");previous=p['last'];p['last']=name
    if e=='fakeout' and p['age']>0:log(r,'Falhou: somente no primeiro turno em campo.');return
    if not chance(int(v['acc']*(3+max(0,p['st'][5]))/(3+max(0,-p['st'][5])))):log(r,'Errou!');return
    if q.get('protect') and (cat!='S' or e in ('sleep','burn','para','seed','encore','transform')):log(r,f"{q['name']} se protegeu!");return
    if cat=='S':
        if e=='protect':
            if previous==name and not chance(33):log(r,'Proteção falhou.')
            else:p['protect']=True;log(r,'Proteção ativada.')
        elif e=='splash':log(r,'Nada aconteceu.')
        elif e=='def1':stage(r,p,1,1)
        elif e=='transform':
            if p.get('transformed') or q.get('transformed'):log(r,'Transformação falhou.')
            else:
                p['transformed']={k:copy.deepcopy(p[k]) for k in ['types','stats','ability','moves','pp']}
                p.update(types=copy.deepcopy(q['types']),stats=[p['stats'][0]]+q['stats'][1:],ability=q['ability'],moves=copy.deepcopy(q['moves']),pp={n:5 for n in q['moves']},st=copy.deepcopy(q['st']))
                log(r,f"{p['name']} se transformou em {q['name']}!")
        elif e=='atk2':stage(r,p,0,2)
        elif e=='def3':stage(r,p,1,3)
        elif e=='dance':stage(r,p,0,1);stage(r,p,4,1)
        elif e=='calm':stage(r,p,2,1);stage(r,p,3,1)
        elif e in ('heal','roost'):heal(p,p['stats'][0]//2);p['roost']=e=='roost';log(r,'HP recuperado.')
        elif e=='rest':p['hp']=p['stats'][0];p['status']='Dormindo';p['sleep']=2
        elif e=='destiny':p['destiny']=previous!=name;log(r,'Laço preparado.' if p['destiny'] else 'Falhou.')
        elif e=='encore':q['encore']=3 if q['last'] else 0
        elif e=='seed':
            if 'Planta' not in q['types']:q['seed']=True;log(r,'Semente plantada.')
            else:log(r,'Imune.')
        elif e in ('sleep','burn','para'):
            if (name=='Pó do Sono' and 'Planta' in q['types']) or (e=='para' and 'Terra' in q['types']) or (e=='burn' and q['ability']=='Flash Fire'):log(r,'Imune.')
            elif not status(r,q,{'sleep':'Dormindo','burn':'Queimado','para':'Paralisado'}[e]):log(r,'Falhou.')
        return
    types=[x for x in q['types'] if not(q['roost'] and x=='Voador')]; mult=eff(t,types)
    if name=='Debater-se':mult=1
    ignore=p['ability']=='Mold Breaker' or name=='Raio Espectral'
    if not ignore and q['ability']=='Flash Fire' and t=='Fogo':q['flash']=True;mult=0
    if not ignore and q['ability']=='Sap Sipper' and t=='Planta':stage(r,q,0,1);mult=0
    if not ignore and q['ability']=='Levitate' and t=='Terra':mult=0
    if not ignore and ((q['ability'] in ('Water Absorb','Dry Skin') and t=='Água') or (q['ability']=='Volt Absorb' and t=='Elétrico')):
        heal(q,q['stats'][0]//4);log(r,f"{q['name']} absorveu o golpe e recuperou HP!");return
    if not ignore and q['ability']=='Lightning Rod' and t=='Elétrico':stage(r,q,2,1);mult=0
    if not ignore and q['ability']=='Storm Drain' and t=='Água':stage(r,q,2,1);mult=0
    if not ignore and q['ability']=='Motor Drive' and t=='Elétrico':stage(r,q,4,1);mult=0
    if not mult:log(r,'Imune!');return
    if e in ('counter','mirror'):
        rec=received.get(i,(0,''));d=2*rec[0] if rec[1]==cat else 0
        if not d:log(r,'Falhou.');return
    else:
        power=v['power'];power*=1.5 if p['ability']=='Technician' and power<=60 else 1
        if p['hp']<=p['stats'][0]//3 and ((p['ability']=='Blaze' and t=='Fogo') or (p['ability']=='Overgrow' and t=='Planta') or (p['ability']=='Torrent' and t=='Água') or (p['ability']=='Swarm' and t=='Inseto')):power*=1.5
        if p['flash'] and t=='Fogo':power*=1.5
        secondary=e in ('burn10','para10','poison30','freeze10','sd10','sd20','flinch30','flinch20','acc30','def20','def30','atkdown10','sadown30','flare')
        sheer=p['ability']=='Sheer Force' and secondary
        if sheer:power*=1.3
        crit=chance(12.5 if e=='highcrit' else 100/24) and (ignore or q['ability'] not in ('Battle Armor','Shell Armor'));roll=R.randint(85,100)
        a=stat(p,2 if e=='body' else 1 if cat=='F' else 3,crit);b=stat(q,2 if cat=='F' else 4,crit,True)
        if p['ability']=='Guts' and p['status'] and cat=='F':a=int(a*1.5)
        d=(int(22*power*a/b/50)+2)*roll/100*(1.5 if crit else 1)*((2 if p['ability']=='Adaptability' else 1.5) if t in p['types'] and name!='Debater-se' else 1)*mult
        if cat=='F' and p['status']=='Queimado' and p['ability']!='Guts':d*=.5
        if not ignore and q['ability']=='Thick Fat' and t in ('Fogo','Gelo'):d*=.5
        if not ignore and q['ability'] in ('Filter','Solid Rock','Prism Armor') and mult>1:d*=.75
        if not ignore and q['ability']=='Multiscale' and q['hp']==q['stats'][0]:d*=.5
        contact=cat=='F' and name not in ('Terremoto','Deslizamento de Rochas','Bumerangue de Osso')
        if not ignore and q['ability']=='Fluffy':d*= (2 if t=='Fogo' else 1)*(.5 if contact else 1)
        if q['ability']=='Shadow Shield' and q['hp']==q['stats'][0]:d*=.5
        if p['ability']=='Dark Aura' and t=='Sombrio':d*=4/3
        d=max(1,int(d))*(2 if e=='twice' else 1)
        if crit:log(r,'Acerto crítico!')
        if mult!=1:log(r,f'Efetividade: {mult}×.')
        if sheer:e='' if e!='flare' else 'recoil3'
        if contact and q['ability']=='Static' and chance(30):status(r,p,'Paralisado')
    if not ignore and q['ability']=='Sturdy' and q['hp']==q['stats'][0] and d>=q['hp'] and e!='twice':d=q['hp']-1;log(r,f"{q['name']} resistiu com Sturdy!")
    actual=hurt(q,d);received[1-i]=(actual,cat);log(r,f"{q['name']} perdeu {actual} HP (dano calculado: {d}).")
    if e in ('drain','drain75'):heal(p,max(1,int(actual*(.75 if e=='drain75' else .5))))
    if name=='Debater-se':log(r,f"{p['name']} sofre {hurt(p,max(1,p['stats'][0]//4))} HP de recuo.")
    elif e in ('recoil3','recoil4','flare') and p['ability']!='Rock Head':log(r,f"{p['name']} sofre {hurt(p,max(1,round(actual/(4 if e=='recoil4' else 3))))} HP de recuo.")
    if q['hp']==0:
        log(r,f"{q['name']} foi derrotado!")
        if q['destiny']:hurt(p,p['hp']);log(r,'Laço do Destino ativado!')
        return
    if e=='fakeout' or (e.startswith('flinch') and chance(int(e[6:]))):flinched.add(1-i)
    for prefix,s in [('burn','Queimado'),('para','Paralisado'),('poison','Envenenado'),('freeze','Congelado')]:
        if e.startswith(prefix) and e[len(prefix):].isdigit() and chance(int(e[len(prefix):])):status(r,q,s)
    if e=='flare' and chance(10):status(r,q,'Queimado')
    for prefix,j in [('sd',3),('def',1),('atkdown',0),('sadown',2),('acc',5)]:
        if e.startswith(prefix) and e[len(prefix):].isdigit() and chance(int(e[len(prefix):])):stage(r,q,j,-1,p)
    if e=='pivot':
        options=[j for j in living(r,i) if j!=r['players'][i]['active']]
        if options and p['hp']:enter(r,i,options[0]);active(r,i)['age']=-1
def frame_state(r):
    return [dict(active=r['players'][i]['active'],name=active(r,i)['name'],hp=active(r,i)['hp'],maxHp=active(r,i)['stats'][0],status=active(r,i)['status'],id=active(r,i)['id']) for i in range(2)]
def resolve(r):
    acts=r['actions'];received={};flinched=set();log(r,f"— Turno {r['turn']} —")
    replay=dict(id=secrets.token_hex(8),turn=r['turn'],frames=[])
    r['replay']=replay
    def frame(i,kind,move,before,lines):
        replay['frames'].append(dict(actor=i,kind=kind,move=move,before=before,after=frame_state(r),lines=lines))
    def priority(i):
        a=acts[i];p=active(r,i)
        if a['kind']=='switch':return 10
        v=MOVES[a['move']];return v['priority']+(1 if p['ability']=='Gale Wings' and p['hp']==p['stats'][0] and v['type']=='Voador' else 0)
    order=sorted([0,1],key=lambda i:(priority(i),stat(active(r,i),5),R.random()),reverse=True)
    for i in order:
        if not active(r,i)['hp'] or not active(r,1-i)['hp']:continue
        a=acts[i]
        before=frame_state(r);oldlog=list(r['log'])
        if a['kind']=='switch':enter(r,i,a['target']);active(r,i)['age']=-1
        else:attack(r,i,a['move'],received,flinched)
        ended=finish(r)
        count=next((k for k in range(min(len(oldlog),len(r['log'])), -1,-1) if oldlog[len(oldlog)-k:]==r['log'][:k]),0)
        frame(i,a['kind'],a.get('move'),before,r['log'][count:])
        if ended:break
    if r['phase']!='end':
        before=frame_state(r);oldlog=list(r['log'])
        for i in range(2):
            p=active(r,i);p['roost']=False;p['protect']=False;p['age']+=1;p['encore']=max(0,p['encore']-1)
            if p['hp'] and p['ability']!='Magic Guard':
                if p['status'] in ('Queimado','Envenenado'):log(r,f"{p['name']} perde {hurt(p,max(1,p['stats'][0]//(16 if p['status']=='Queimado' else 8)))} HP por {p['status'].lower()}.")
                if p['hp'] and p['seed']:heal(active(r,1-i),hurt(p,max(1,p['stats'][0]//8)))
        if not finish(r):r['turn']+=1;r['phase']='replace' if any(not active(r,i)['hp'] for i in range(2)) else 'battle'
        count=next((k for k in range(min(len(oldlog),len(r['log'])), -1,-1) if oldlog[len(oldlog)-k:]==r['log'][:k]),0)
        if r['log'][count:] or before!=frame_state(r):frame(-1,'residual',None,before,r['log'][count:])
    r['actions']=[None,None]
def switch_allowed(r,i):
    p,q=active(r,i),active(r,1-i);return not(q['ability']=='Shadow Tag' and p['ability']!='Shadow Tag' and 'Fantasma' not in p['types'])
def snapshot(r,i):
    out={k:copy.deepcopy(r[k]) for k in ['code','phase','turn','score','winner','log']};out['you']=i;out['ready']=[bool(x) for x in r['actions']];out['players']=[]
    for j,p in enumerate(r['players']):
        if p is None:out['players'].append(None);continue
        visible=j==i or r['phase'] not in ('lobby','teams')
        out['players'].append(dict(name=p['name'],team=p['team'] if visible else [],active=p['active'],selected=bool(p['team'])))
    out['replay']=copy.deepcopy(r.get('replay'))
    if r['players'][i]['team']:
        own=out['players'][i]['team'];
        for p in own:pp_for(p)
        out['legalMoves']=legal_moves(active(r,i))
    else:out['legalMoves']=[]
    out['canSwitch']=r['phase']=='battle' and switch_allowed(r,i) if all(r['players']) and all(p['team'] for p in r['players']) else False
    return out
class Bad(Exception):pass
def require(b,msg):
    if not b:raise Bad(msg)
def handle(d):
    op=d.get('op');code=str(d.get('code','')).upper();token=d.get('token')
    if op=='create':
        name=str(d.get('name','')).strip()[:24];require(name,'Informe seu nome.');code=''.join(R.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        while code in ROOMS:code=''.join(R.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        token=secrets.token_urlsafe(24);r=dict(code=code,phase='lobby',turn=1,score=[0,0],winner=None,log=[],actions=[None,None],players=[dict(name=name,token=token,team=[],active=0),None]);ROOMS[code]=r;save();return dict(token=token,state=snapshot(r,0))
    require(code in ROOMS,'Sala não encontrada.');r=ROOMS[code]
    if op=='join':
        require(r['players'][1] is None,'Sala já está cheia.');name=str(d.get('name','')).strip()[:24];require(name,'Informe seu nome.');token=secrets.token_urlsafe(24);r['players'][1]=dict(name=name,token=token,team=[],active=0);r['phase']='teams';save();return dict(token=token,state=snapshot(r,1))
    i=next((j for j,p in enumerate(r['players']) if p and p['token']==token),None);require(i is not None,'Sessão inválida.');p=r['players'][i]
    if op=='state':return dict(state=snapshot(r,i))
    if op in ('team','random_team'):
        names=R.sample([n for n,x in DEX.items() if x.get('default',True)],3) if op=='random_team' else d.get('team',[]);require(r['phase']=='teams' and not p['team'],'Não é possível alterar a equipe.');require(isinstance(names,list) and len(names)==3 and all(isinstance(n,str) and n in DEX for n in names) and len(set(names))==3,'Selecione três Pokémon diferentes.');p['team']=[fighter(n) for n in names];p['active']=0
        if all(x['team'] for x in r['players']):r['phase']='battle';log(r,'A batalha começou!');
        if r['phase']=='battle':
            for j in range(2):
                if active(r,j)['ability']=='Intimidação':stage(r,active(r,1-j),0,-1,active(r,j))
    elif op=='action':
        require(r['phase']=='battle' and d.get('turn')==r['turn'] and r['actions'][i] is None,'Turno desatualizado ou já confirmado.');a=d.get('action',{});kind=a.get('kind')
        if kind=='switch':require(switch_allowed(r,i) and type(a.get('target')) is int and a['target'] in living(r,i) and a['target']!=p['active'],'Troca inválida.')
        else:require(kind=='move' and a.get('move') in legal_moves(active(r,i)),'Golpe inválido.')
        r['actions'][i]=a
        if all(r['actions']):resolve(r)
    elif op=='replace':
        require(r['phase']=='replace' and not active(r,i)['hp'] and type(d.get('target')) is int and d['target'] in living(r,i),'Substituição inválida.');enter(r,i,d['target']);
        if all(active(r,j)['hp'] for j in range(2)):r['phase']='battle'
    elif op=='rematch':
        require(r['phase']=='end','Partida ainda em andamento.');r['actions'][i]={'ready':True}
        if all(r['actions']):
            for x in r['players']:x.update(team=[],active=0)
            r.update(phase='teams',turn=1,winner=None,actions=[None,None],log=[],replay=None)
    else:raise Bad('Ação desconhecida.')
    save();return dict(state=snapshot(r,i))
class HTTP(BaseHTTPRequestHandler):
    def send(self,b,typ='application/json',status=200):
        if not isinstance(b,bytes):b=json.dumps(b,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();
        if self.command!='HEAD':self.wfile.write(b)
    def do_GET(self):
        path=urlsplit(self.path).path.rstrip('/') or '/'
        if path in ('/', '/index.html'):self.send((ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        elif path=='/dex':self.send(dict(dex=DEX,moves=MOVES,speciesCount=SPECIES_COUNT))
        elif path=='/favicon.ico':self.send(b'', 'image/x-icon', 204)
        else:self.send({'error':'Não encontrado'},status=404)
    def do_HEAD(self):self.do_GET()
    def do_POST(self):
        try:
            require(urlsplit(self.path).path.rstrip('/')=='/api','Não encontrado.');n=int(self.headers.get('Content-Length','0'));require(0<n<16000,'Requisição inválida.');d=json.loads(self.rfile.read(n));require(isinstance(d,dict),'Requisição inválida.')
            with LOCK:out=handle(d)
            self.send(out)
        except (Bad,ValueError,TypeError,KeyError,IndexError,AttributeError) as e:self.send({'error':str(e) if isinstance(e,Bad) else 'Requisição inválida.'},status=400)
    def log_message(self,*args):
        super().log_message(*args)
def smoke_test():
    # An isolated deterministic setup: no rooms or player data are modified.
    r=dict(code='TEST',phase='battle',turn=1,score=[0,0],winner=None,log=[],actions=[{'kind':'move','move':'Dança das Espadas'},{'kind':'move','move':'Mente Calma'}],players=[dict(name='A',team=[fighter('Marowak')],active=0),dict(name='B',team=[fighter('Alakazam')],active=0)])
    a=active(r,0);b=active(r,1);before=pp_for(a)['Dança das Espadas']
    resolve(r)
    assert r['turn']==2 and r['phase']=='battle'
    assert a['st'][0]==2 and b['st'][2]==1 and b['st'][3]==1
    assert pp_for(a)['Dança das Espadas']==before-1
    assert len(r['replay']['frames'])>=2 and all('before' in x and 'after' in x for x in r['replay']['frames'])
    snap=snapshot(r,0);assert 'Dança das Espadas' in snap['legalMoves'] or before==1
    for name in a['moves']:pp_for(a)[name]=0
    assert legal_moves(a)==['Debater-se']
    print('V3 SMOKE TEST OK: PP, stat stages, turn order, replay, snapshot, fallback',flush=True)
if __name__=='__main__':
    smoke_test()
    port=int(os.environ.get('PORT',8000));print(f'Arena em http://0.0.0.0:{port}',flush=True);ThreadingHTTPServer(('0.0.0.0',port),HTTP).serve_forever()
