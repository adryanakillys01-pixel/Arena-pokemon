"""Arena RPG: authoritative, real-time 2D combat, independent of turn-based rooms."""
import math, secrets, time, random, copy
R=random.SystemRandom()
W,H=960,560
ROOMS={}
DEX={};MOVES={};EFFECT=None
TICK=.04
def configure(dex,moves,effect):
    global DEX,MOVES,EFFECT
    DEX,MOVES,EFFECT=dex,moves,effect
def clamp(x,a,b):return max(a,min(b,x))
def norm(x,y):
    n=math.hypot(x,y)
    return (x/max(1,n),y/max(1,n))
def distance(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def fail(ok,msg):
    if not ok:raise ValueError(msg)
def log(r,msg):
    r['events'].append(dict(id=r['eventId'],text=msg));r['eventId']+=1;r['events']=r['events'][-8:]
def fighter(name,i):
    d=DEX[name];s=d['stats'];attacks=[n for n in d['moves'] if n in MOVES and MOVES[n]['cat']!='S' and MOVES[n]['power']>0]
    if not attacks:attacks=['Debater-se'] if 'Debater-se' in MOVES else ['Cabeçada']
    support=[n for n in d['moves'] if n in MOVES and MOVES[n]['cat']=='S' and MOVES[n].get('effect') in ('heal','roost','rest','atk2','def3','def1','calm','dance','protect','sleep','burn','para','seed')]
    skills=(attacks+support)[:4]
    return dict(name=name,id=d['id'],types=d['types'],ability=d['ability'],stats=s,skills=skills,hp=s[0],maxHp=s[0],x=200 if i==0 else 760,y=280,dx=0,dy=0,faceX=1 if i==0 else -1,faceY=0,energy=100,cd=[0]*len(skills),dash=0,shield=0,boost=0,defense=0,status='',statusTime=0,attackFlash=0,hitFlash=0,lastInput=0,seq=-1)
def player(name):
    return dict(name=name,token=secrets.token_urlsafe(24),pick=None,p=None)
def new_room(name,solo=False):
    code=''.join(R.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
    while code in ROOMS:code=''.join(R.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
    now=time.monotonic()
    r=dict(code=code,solo=solo,phase='select' if solo else 'lobby',players=[player(name),player('Rival CPU') if solo else None],score=[0,0],winner=None,projectiles=[],events=[],eventId=1,clock=0,last=now,acc=0,touched=now,remaining=120,rematch=[False,False])
    ROOMS[code]=r
    return r
def start(r):
    for i,p in enumerate(r['players']):p['p']=fighter(p['pick'],i)
    r.update(phase='fight',last=time.monotonic(),acc=0,clock=0,remaining=120,projectiles=[],winner=None,rematch=[False,False])
    log(r,'A batalha começou!')
def resolve_end(r,w):
    if r['phase']!='fight':return
    r['phase']='end';r['winner']=w
    if w>=0:r['score'][w]+=1;log(r,r['players'][w]['name']+' venceu!')
    else:log(r,'Empate!')
def apply_hit(r,owner,target,move,power=None):
    a,b=r['players'][owner]['p'],r['players'][target]['p'];m=MOVES[move]
    if b['hp']<=0 or b['dash']>0 or b['shield']>0:
        if b['hp']>0:log(r,b['name']+' desviou ou bloqueou!')
        return
    t,c=m['type'],m['cat'];mult=1 if move=='Debater-se' else EFFECT(t,b['types'])
    if b['ability']=='Levitate' and t=='Terra':mult=0
    if b['ability']=='Flash Fire' and t=='Fogo':mult=0
    if b['ability'] in ('Water Absorb','Storm Drain') and t=='Água' or b['ability'] in ('Volt Absorb','Lightning Rod') and t=='Elétrico':mult=0
    if not mult:log(r,b['name']+' é imune!');return
    atk=a['stats'][1 if c=='F' else 3];defn=b['stats'][2 if c=='F' else 4]
    raw=(22*(power or m['power'])*atk/max(1,defn)/50+2)*.42*mult*(1.5 if t in a['types'] else 1)*(1.4 if a['boost']>0 else 1)*(.65 if b['defense']>0 else 1)*R.uniform(.9,1.08)
    if a['status']=='Queimado' and c=='F':raw*=.7
    dmg=min(b['hp'],max(1,int(raw)));b['hp']-=dmg;b['hitFlash']=.24
    log(r,f"{a['name']}: {move} · −{dmg} HP"+(' · super efetivo!' if mult>1 else ''))
    e=m.get('effect','')
    if e in ('drain','drain75'):a['hp']=min(a['maxHp'],a['hp']+int(dmg*.5))
    if e.startswith('recoil') or e=='flare':a['hp']=max(0,a['hp']-max(1,int(dmg*.25)))
    for prefix,st in [('burn','Queimado'),('para','Paralisado'),('poison','Envenenado'),('freeze','Congelado')]:
        if e.startswith(prefix) and e[len(prefix):].isdigit() and not b['status'] and R.random()*100<int(e[len(prefix):]):
            if st=='Queimado' and 'Fogo' in b['types'] or st=='Paralisado' and 'Elétrico' in b['types'] or st=='Envenenado' and any(x in b['types'] for x in ('Aço','Veneno')):continue
            b['status']=st;b['statusTime']=4
def skill(r,i,k):
    a,b=r['players'][i]['p'],r['players'][1-i]['p']
    if type(k) is not int or not 0<=k<len(a['skills']) or a['cd'][k]>0 or a['energy']<20 or a['status'] in ('Dormindo','Congelado') or a['hp']<=0:return
    n=a['skills'][k];m=MOVES[n];a['energy']-=20;a['cd'][k]=2.1 if m['cat']=='F' else 3.1 if m['cat']=='E' else 5.0;a['attackFlash']=.22
    dx,dy=b['x']-a['x'],b['y']-a['y'];d=math.hypot(dx,dy);ux,uy=(dx/max(d,1),dy/max(d,1));a['faceX'],a['faceY']=ux,uy
    if m['cat']=='S':
        e=m.get('effect','')
        if e in ('heal','roost','rest'):a['hp']=min(a['maxHp'],a['hp']+int(a['maxHp']*.22))
        elif e in ('atk2','calm','dance'):a['boost']=7
        elif e in ('def3','def1'):a['defense']=6
        elif e=='protect':a['shield']=1
        elif d<=230 and not b['status'] and b['dash']<=0 and b['shield']<=0:
            if e=='sleep' and 'Planta' not in b['types']:b['status']='Dormindo';b['statusTime']=1.3
            elif e=='burn' and 'Fogo' not in b['types']:b['status']='Queimado';b['statusTime']=5
            elif e=='para' and 'Elétrico' not in b['types'] and 'Terra' not in b['types']:b['status']='Paralisado';b['statusTime']=4
            elif e=='seed' and 'Planta' not in b['types']:b['status']='Envenenado';b['statusTime']=4
        log(r,a['name']+' usou '+n);return
    if m['cat']=='F':
        if d<=155:apply_hit(r,i,1-i,n)
        else:log(r,a['name']+' errou: fora de alcance')
    else:
        if len(r['projectiles'])<24:r['projectiles'].append(dict(id=secrets.token_hex(4),owner=i,x=a['x']+ux*35,y=a['y']+uy*35,vx=ux*470,vy=uy*470,ttl=1.7,move=n,type=m['type']))
def dodge(p):
    if p['energy']>=27 and p['dash']<=0 and p['status'] not in ('Dormindo','Congelado'):
        p['energy']-=27;p['dash']=.24
        if math.hypot(p['dx'],p['dy'])<.1:p['dx'],p['dy']=-p['faceX'],-p['faceY']
def bot(r):
    a,b=r['players'][1]['p'],r['players'][0]['p'];dx,dy=b['x']-a['x'],b['y']-a['y'];d=max(1,math.hypot(dx,dy));ux,uy=dx/d,dy/d
    ranged=any(MOVES[n]['cat']=='E' for n in a['skills'])
    want=270 if ranged else 90
    direction=1 if d>want+35 else -1 if d<want-35 else 0
    side=math.sin(r['clock']*2.1)*.5
    a['dx'],a['dy']=norm(ux*direction-uy*side,uy*direction+ux*side);a['lastInput']=r['clock']
    if any(p['owner']==0 and math.hypot(p['x']-a['x'],p['y']-a['y'])<75 for p in r['projectiles']) and R.random()<.24:dodge(a)
    if int(r['clock']*10)!=int((r['clock']-TICK)*10):
        options=[]
        for k,n in enumerate(a['skills']):
            m=MOVES[n]
            if a['cd'][k]>0:continue
            if m['cat']=='S':
                val=30 if m.get('effect') in ('heal','roost','rest') and a['hp']<a['maxHp']*.5 else 8 if m.get('effect') in ('atk2','calm','dance') and a['boost']<=0 else -1
            else:
                if m['cat']=='F' and d>145 or m['cat']=='E' and d>650:continue
                val=m['power']*EFFECT(m['type'],b['types'])*(.7 if m['cat']=='E' else 1)
            options.append((val,k))
        if options and max(options)[0]>0:skill(r,1,max(options)[1])
def tick(r):
    r['clock']+=TICK;r['remaining']=max(0,120-r['clock'])
    if r['solo']:bot(r)
    ps=[p['p'] for p in r['players']]
    for p in ps:
        for k in ('dash','shield','boost','defense','statusTime','attackFlash','hitFlash'):p[k]=max(0,p[k]-TICK)
        p['cd']=[max(0,x-TICK) for x in p['cd']]
        if p['status'] and p['statusTime']<=0:p['status']=''
        if p['status'] in ('Queimado','Envenenado') and int(r['clock'])!=int(r['clock']-TICK):p['hp']=max(0,p['hp']-max(1,p['maxHp']//35))
        p['energy']=min(100,p['energy']+15*TICK)
        if r['clock']-p['lastInput']>.35:p['dx']=p['dy']=0
        speed=clamp(135+p['stats'][5]*.42,150,215)*(2.6 if p['dash']>0 else 1)*(.62 if p['status']=='Paralisado' else 1)
        if p['status'] in ('Dormindo','Congelado'):speed=0
        p['x']=clamp(p['x']+p['dx']*speed*TICK,34,W-34);p['y']=clamp(p['y']+p['dy']*speed*TICK,34,H-34)
    a,b=ps;d=distance(a,b)
    if 0<d<64:
        ux=(b['x']-a['x'])/d;uy=(b['y']-a['y'])/d;push=(64-d)/2
        a['x']=clamp(a['x']-ux*push,34,W-34);a['y']=clamp(a['y']-uy*push,34,H-34);b['x']=clamp(b['x']+ux*push,34,W-34);b['y']=clamp(b['y']+uy*push,34,H-34)
    remain=[]
    for pr in r['projectiles']:
        pr['x']+=pr['vx']*TICK;pr['y']+=pr['vy']*TICK;pr['ttl']-=TICK
        target=1-pr['owner'];b=ps[target]
        if math.hypot(pr['x']-b['x'],pr['y']-b['y'])<39:
            if b['dash']>0:remain.append(pr)
            else:apply_hit(r,pr['owner'],target,pr['move'])
        elif pr['ttl']>0 and 0<=pr['x']<=W and 0<=pr['y']<=H:remain.append(pr)
    r['projectiles']=remain
    alive=[p['hp']>0 for p in ps]
    if not all(alive):resolve_end(r,alive.index(True) if any(alive) else -1)
    elif r['remaining']<=0:
        a,b=[p['hp']/p['maxHp'] for p in ps];resolve_end(r,0 if a>b else 1 if b>a else -1)
def advance(r,now=None):
    now=time.monotonic() if now is None else now
    dt=clamp(now-r['last'],0,.25);r['last']=now
    if r['phase']!='fight':return
    r['acc']+=dt
    while r['acc']>=TICK and r['phase']=='fight':r['acc']-=TICK;tick(r)
def snapshot(r,i):
    return dict(code=r['code'],you=i,solo=r['solo'],phase=r['phase'],score=r['score'][:],winner=r['winner'],remaining=r['remaining'],players=[None if p is None else dict(name=p['name'],picked=bool(p['pick']),pick=p['pick'] if j==i or r['phase'] in ('fight','end') else None,p=copy.deepcopy(p['p'])) for j,p in enumerate(r['players'])],projectiles=copy.deepcopy(r['projectiles']),events=copy.deepcopy(r['events']),rematch=r['rematch'][:])
def handle(d):
    op=d.get('op');now=time.monotonic()
    if op in ('create','solo'):
        name=str(d.get('name','')).strip()[:24];fail(bool(name),'Informe seu nome.')
        for k in list(ROOMS):
            if now-ROOMS[k]['touched']>7200:del ROOMS[k]
        fail(len(ROOMS)<300,'Servidor cheio. Tente novamente.')
        r=new_room(name,op=='solo');return dict(token=r['players'][0]['token'],state=snapshot(r,0))
    code=str(d.get('code','')).upper();fail(code in ROOMS,'Sala não encontrada.');r=ROOMS[code];r['touched']=now;advance(r,now)
    if op=='join':
        fail(r['players'][1] is None,'Sala cheia.');name=str(d.get('name','')).strip()[:24];fail(bool(name),'Informe seu nome.');p=player(name);r['players'][1]=p;r['phase']='select';return dict(token=p['token'],state=snapshot(r,1))
    token=d.get('token');i=next((j for j,p in enumerate(r['players']) if p and p['token']==token),None);fail(i is not None,'Sessão inválida.');p=r['players'][i]
    if op in ('pick','random'):
        fail(r['phase']=='select' and not p['pick'],'Escolha já confirmada.')
        pool=[n for n,v in DEX.items() if v.get('default',True) and not v.get('legendary',False) and 420<=sum(v['stats'])-175<=540]
        name=R.choice(pool or list(DEX)) if op=='random' else d.get('pokemon');fail(isinstance(name,str) and name in DEX,'Pokémon inválido.')
        p['pick']=name
        if r['solo']:
            power=sum(DEX[name]['stats']);near=[n for n in (pool or list(DEX)) if abs(sum(DEX[n]['stats'])-power)<=85];r['players'][1]['pick']=R.choice(near or pool or list(DEX))
        if all(x['pick'] for x in r['players']):start(r)
    elif op=='input' and r['phase']=='fight':
        a=p['p'];seq=d.get('seq',0)
        if type(seq) is int and seq>a['seq']:
            a['seq']=seq
            x,y=d.get('dx',0),d.get('dy',0)
            if type(x) in (int,float) and type(y) in (int,float) and math.isfinite(x) and math.isfinite(y):
                a['dx'],a['dy']=norm(clamp(x,-1,1),clamp(y,-1,1));a['lastInput']=r['clock']
            if d.get('dash') is True:dodge(a)
            if type(d.get('skill')) is int:skill(r,i,d['skill'])
            if a['hp']<=0 or r['players'][1-i]['p']['hp']<=0:
                alive=[q['p']['hp']>0 for q in r['players']];resolve_end(r,alive.index(True) if any(alive) else -1)
    elif op=='forfeit':
        fail(r['phase']=='fight','Partida encerrada.');resolve_end(r,1-i)
    elif op=='rematch':
        fail(r['phase']=='end','Partida em andamento.');r['rematch'][i]=True
        if r['solo'] or all(r['rematch']):
            for q in r['players']:q['pick']=None;q['p']=None
            r.update(phase='select',projectiles=[],events=[],winner=None,remaining=120,rematch=[False,False])
    elif op not in ('state','input'):raise ValueError('Ação desconhecida.')
    return dict(state=snapshot(r,i))
def smoke_test():
    r=new_room('A');r['players'][1]=player('B');r['players'][0]['pick']='Marowak';r['players'][1]['pick']='Pikachu';start(r)
    a,b=[p['p'] for p in r['players']];x=a['x'];a['dx']=1;tick(r);assert a['x']>x
    a['x']=b['x']-75;a['y']=b['y'];k=a['skills'].index('Terremoto');hp=b['hp'];skill(r,0,k);assert b['hp']<hp and a['cd'][k]>0
    hp=b['hp'];skill(r,0,k);assert b['hp']==hp
    b['energy']=100;dodge(b);assert b['dash']>0 and b['energy']<100
    a['cd'][k]=0;skill(r,0,k);assert b['hp']==hp
    b['hp']=0;tick(r);assert r['phase']=='end' and r['winner']==0
    del ROOMS[r['code']]
    print('RPG SMOKE TEST OK: movement, range, cooldown, dodge, victory',flush=True)
