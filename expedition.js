/* Expedition: local simulation, independent of the network. */
(function(root){
'use strict';
const W=1920,H=1240,CAMP={x:300,y:330};
const seed=[
[1,'Bulbasaur','Planta'],[4,'Charmander','Fogo'],[7,'Squirtle','Água'],[10,'Caterpie','Inseto'],[16,'Pidgey','Voador'],[19,'Rattata','Normal'],[25,'Pikachu','Elétrico'],[27,'Sandshrew','Terra'],[35,'Clefairy','Fada'],[37,'Vulpix','Fogo'],[43,'Oddish','Planta'],[54,'Psyduck','Água'],[58,'Growlithe','Fogo'],[66,'Machop','Lutador'],[74,'Geodude','Pedra'],[92,'Gastly','Fantasma'],[104,'Cubone','Terra'],[133,'Eevee','Normal'],[147,'Dratini','Dragão'],[152,'Chikorita','Planta'],[155,'Cyndaquil','Fogo'],[158,'Totodile','Água'],[179,'Mareep','Elétrico'],[183,'Marill','Água'],[194,'Wooper','Água'],[252,'Treecko','Planta'],[255,'Torchic','Fogo'],[258,'Mudkip','Água'],[280,'Ralts','Psíquico'],[304,'Aron','Aço'],[328,'Trapinch','Terra'],[333,'Swablu','Voador'],[403,'Shinx','Elétrico'],[406,'Budew','Planta'],[447,'Riolu','Lutador'],[570,'Zorua','Sombrio'],[700,'Sylveon','Fada'],[831,'Wooloo','Normal'],[885,'Dreepy','Dragão']];
const colors={Planta:'#72cf69',Fogo:'#ff8950','Água':'#66baf6','Elétrico':'#fce269',Normal:'#e2d2b3',Terra:'#c5a16b',Pedra:'#b6aa91',Voador:'#9ac9f2',Inseto:'#9dcc55',Fantasma:'#b29ae9',Fada:'#f6a4cc',Lutador:'#e29c81','Psíquico':'#f9a0b2','Aço':'#a6b5cf',Sombrio:'#9784a7','Dragão':'#9a9bea',Gelo:'#b3e9f4',Veneno:'#bd85d8'};
const DEX=Object.fromEntries(seed.map(([id,name,type])=>[id,{id,name,types:[type],stats:[120,75,75,75,75,75]}]));
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)), dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const starters=[1,4,7,25,133,104];
const xpNeed=l=>40+(l-1)*25;
const rosterEntry=(id,level=1)=>({id,level,xp:0});
const rnd=(a,b)=>a+Math.random()*(b-a);
const strong={Fogo:['Planta','Inseto','Gelo','Aço'],Planta:['Água','Terra','Pedra'],Água:['Fogo','Terra','Pedra'],Elétrico:['Água','Voador'],Terra:['Fogo','Elétrico','Pedra','Aço','Veneno'],Pedra:['Fogo','Voador','Inseto','Gelo'],Lutador:['Normal','Pedra','Aço','Gelo','Sombrio'],Fantasma:['Fantasma','Psíquico'],Psíquico:['Lutador','Veneno'],Fada:['Dragão','Lutador','Sombrio'],Dragão:['Dragão'],Gelo:['Planta','Terra','Voador','Dragão'],Voador:['Planta','Inseto','Lutador'],Inseto:['Planta','Psíquico','Sombrio'],Veneno:['Planta','Fada'],Aço:['Pedra','Gelo','Fada'],Sombrio:['Fantasma','Psíquico']};
function addDex(raw){for(const p of Object.values(raw||{})){if(!p||!Number.isInteger(p.id)||!Array.isArray(p.types)||!Array.isArray(p.stats)||p.stats.length!==6||typeof p.name!=='string'||p.default===false)continue;DEX[p.id]={id:p.id,name:p.name,types:p.types,stats:p.stats,legendary:!!p.legendary}}}
const terrain=[];
for(let i=0;i<52;i++){let x=90+((i*317+131)%1740),y=90+((i*197+93)%1050);if(dist({x,y},CAMP)>220)terrain.push({x,y,r:19+(i%3)*5,kind:i%4===0?'rock':'tree'})}
const nodes=Array.from({length:26},(_,i)=>({x:120+((i*379+320)%1660),y:120+((i*233+390)%1000),kind:['wood','stone','berry'][i%3],cool:0})).filter(p=>dist(p,CAMP)>130);
class Game{
 constructor(id,save=null){this.party=[rosterEntry(id)];this.active=0;this.base=1;this.bag={wood:0,stone:0,berry:3,balls:6};this.caught=0;this.kills=0;this.player={x:CAMP.x,y:CAMP.y,hp:100,face:1,energy:100};this.wild=[];this.nodes=nodes.map(n=>({...n}));this.fx=[];this.time=0;this.nextSpawn=0;this.cool=0;this.dash=0;this.note='Explore a floresta e enfraqueça criaturas para capturá-las.';this.dirty=true;
 if(save&&Array.isArray(save.party)&&save.party.length&&save.party.every(p=>Number.isInteger(p.id)&&p.level>=1&&p.level<=50)){this.party=save.party.slice(0,100);this.active=clamp(save.active|0,0,this.party.length-1);this.base=clamp(save.base|0,1,5);for(const k of Object.keys(this.bag))if(Number.isFinite(save.bag?.[k]))this.bag[k]=clamp(Math.floor(save.bag[k]),0,9999);this.caught=save.caught|0;this.kills=save.kills|0;}
 this.player.hp=this.maxHp();for(let i=0;i<15;i++)this.spawn();}
 get member(){return this.party[this.active]}
 get mon(){return DEX[this.member.id]||{id:this.member.id,name:'Pokémon #'+this.member.id,types:['Normal'],stats:[120,75,75,75,75,75]}}
 maxHp(){return Math.round(65+this.member.level*12+this.mon.stats[0]*.35)}
 say(t){this.note=t;this.dirty=true}
 save(){return {party:this.party,active:this.active,base:this.base,bag:this.bag,caught:this.caught,kills:this.kills}}
 spawn(){let ids=Object.values(DEX).filter(p=>!p.legendary&&p.id!==this.member.id);let d=ids[Math.floor(Math.random()*ids.length)];if(!d)return;let x=rnd(100,W-100),y=rnd(100,H-100);if(dist({x,y},CAMP)<220)x=740;let level=clamp(this.member.level+Math.floor(rnd(-1,2)),1,50);let max=35+level*8+Math.round(d.stats[0]*.16);this.wild.push({uid:Math.random().toString(36).slice(2),id:d.id,x,y,level,hp:max,max,aggro:false,hit:0,attack:0,wander:rnd(0,6.28),timer:rnd(1,4)})}
 walk(p,vx,vy,dt){let x=clamp(p.x+vx*dt,35,W-35),y=clamp(p.y+vy*dt,35,H-35);for(const t of terrain){if(Math.hypot(x-t.x,p.y-t.y)<t.r+12)x=p.x;if(Math.hypot(p.x-t.x,y-t.y)<t.r+12)y=p.y;}p.x=x;p.y=y;}
 step(dt,input={x:0,y:0}){dt=clamp(dt,0,.05);this.time+=dt;this.cool=Math.max(0,this.cool-dt);this.dash=Math.max(0,this.dash-dt);const p=this.player;p.energy=Math.min(100,p.energy+20*dt);let n=Math.max(1,Math.hypot(input.x,input.y)),v=(165+Math.min(55,this.mon.stats[5]*.35))*(this.dash>0?2.2:1);this.walk(p,input.x/n*v,input.y/n*v,dt);if(Math.abs(input.x)>.1)p.face=Math.sign(input.x);const safe=dist(p,CAMP)<110;if(safe)p.hp=Math.min(this.maxHp(),p.hp+16*dt);
 for(const w of this.wild){w.hit=Math.max(0,w.hit-dt);w.attack=Math.max(0,w.attack-dt);w.timer-=dt;if(w.timer<=0){w.wander=rnd(0,6.28);w.timer=rnd(1,4);}let d=dist(p,w);if(w.aggro&&!safe&&d<350){if(d>42)this.walk(w,(p.x-w.x)/d*95,(p.y-w.y)/d*95,dt);else if(w.attack<=0){w.attack=1.2;if(!this.dash){let damage=5+w.level*2;p.hp=Math.max(0,p.hp-damage);this.fx.push({x:p.x,y:p.y-20,text:'−'+damage,color:'#ff9990',t:.75});}}}else{if(d>350||safe)w.aggro=false;this.walk(w,Math.cos(w.wander)*17,Math.sin(w.wander)*17,dt);}}
 for(const n of this.nodes)n.cool=Math.max(0,n.cool-dt);
 for(const f of this.fx){f.t-=dt;f.y-=dt*23}this.fx=this.fx.filter(f=>f.t>0);
 if(p.hp<=0){p.x=CAMP.x;p.y=CAMP.y;p.hp=this.maxHp();this.say('Seu Pokémon desmaiou. Você voltou ao acampamento.');for(const w of this.wild)w.aggro=false;}
 if(this.wild.length<15&&this.time>this.nextSpawn){this.spawn();this.nextSpawn=this.time+3}
 }
 target(range=160){return this.wild.filter(w=>dist(this.player,w)<=range).sort((a,b)=>dist(this.player,a)-dist(this.player,b))[0]}
 gain(xp){let p=this.member;p.xp+=xp;while(p.level<50&&p.xp>=xpNeed(p.level)){p.xp-=xpNeed(p.level);p.level++;this.player.hp=this.maxHp();this.say(this.mon.name+' subiu para o nível '+p.level+'!')}this.dirty=true}
 attack(){if(this.cool>0||this.player.energy<12)return false;const w=this.target(170);if(!w){this.say('Aproxime-se de um Pokémon selvagem.');return false}this.cool=.72;this.player.energy-=12;w.aggro=true;w.hit=.22;const a=this.mon.types[0],b=DEX[w.id]?.types||['Normal'];let m=b.some(t=>strong[a]?.includes(t))?1.45:1;let d=Math.min(w.hp,Math.round((14+this.member.level*4+Math.max(this.mon.stats[1],this.mon.stats[3])*.075)*m));w.hp-=d;this.fx.push({x:w.x,y:w.y-25,text:'−'+d,color:colors[a]||'#fff',t:.7});if(w.hp<=0){this.wild=this.wild.filter(x=>x!==w);this.kills++;this.bag.berry++;this.gain(18+w.level*7);this.say('Vitória! + experiência e 1 fruta.')}return true}
 capture(){let w=this.target(125);if(!w){this.say('Aproxime-se de uma criatura selvagem.');return false}if(w.hp/w.max>.35){this.say('Enfraqueça o Pokémon até 35% de HP para capturar.');return false}if(!this.bag.balls){this.say('Sem Pokébolas. Fabrique no acampamento.');return false}if(this.party.length>=100){this.say('Coleção cheia (100).');return false}this.bag.balls--;this.party.push(rosterEntry(w.id,w.level));this.wild=this.wild.filter(x=>x!==w);this.caught++;this.gain(24);this.say('Capturou '+(DEX[w.id]?.name||'Pokémon')+'!');return true}
 gather(){const p=this.player,n=this.nodes.filter(n=>n.cool<=0&&dist(n,p)<90).sort((a,b)=>dist(a,p)-dist(b,p))[0];if(!n){this.say('Aproxime-se de uma árvore, pedra ou arbusto.');return false}this.bag[n.kind]+=n.kind==='berry'?2:3;n.cool=12;this.say('+ '+({wood:'3 madeira',stone:'3 pedra',berry:'2 frutas'}[n.kind]));return true}
 heal(){if(this.player.hp>=this.maxHp())return false;if(!this.bag.berry){this.say('Sem frutas.');return false}this.bag.berry--;this.player.hp=Math.min(this.maxHp(),this.player.hp+Math.round(this.maxHp()*.35));this.say('HP recuperado.');return true}
 dodge(){if(this.player.energy<25||this.dash>0)return false;this.player.energy-=25;this.dash=.25;return true}
 nearCamp(){return dist(this.player,CAMP)<145}
 craft(){if(!this.nearCamp()){this.say('Volte ao acampamento para fabricar.');return false}if(this.bag.wood<3||this.bag.stone<2){this.say('Precisa de 3 madeira e 2 pedra.');return false}this.bag.wood-=3;this.bag.stone-=2;this.bag.balls+=3;this.say('Fabricou 3 Pokébolas.');return true}
 upgrade(){if(!this.nearCamp()){this.say('Volte ao acampamento.');return false}if(this.base>=5){this.say('Acampamento no nível máximo.');return false}let w=6*this.base,s=4*this.base;if(this.bag.wood<w||this.bag.stone<s){this.say('Precisa de '+w+' madeira e '+s+' pedra.');return false}this.bag.wood-=w;this.bag.stone-=s;this.base++;this.bag.balls+=2;this.say('Acampamento nível '+this.base+'!');return true}
 switch(i){if(!Number.isInteger(i)||!this.party[i]||i===this.active)return false;if(!this.nearCamp()){this.say('Troque de Pokémon no acampamento.');return false}this.active=i;this.player.hp=this.maxHp();this.say('Agora você controla '+this.mon.name);return true}
}
root.Expedition={Game,DEX,addDex,starters,colors,terrain,W,H,CAMP,dist,xpNeed};
})(typeof globalThis!=='undefined'?globalThis:window);
