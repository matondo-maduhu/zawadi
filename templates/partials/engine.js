/* Injini ya muziki + fataki + mioyo. Inatumika na zawadi zote. */
const $=id=>document.getElementById(id);
const rnd=(a,b)=>a+Math.random()*(b-a);
for(let i=0;i<90;i++){const s=document.createElement("i");s.className="st";const z=rnd(1,3);Object.assign(s.style,{width:z+"px",height:z+"px",left:rnd(0,100)+"%",top:rnd(0,100)+"%",animationDelay:rnd(0,3)+"s"});$("stars").appendChild(s)}

/* ===== MUSIC ===== */
const TR=[
 {n:"Mapenzi",bpm:66,root:65,sc:[0,2,4,5,7,9,11],ch:[[53,57,60],[50,53,57],[58,62,65],[48,52,55]],arp:"0.1.2.3.2.1.0.1.",mel:"x.....x...x.....",aw:"sine",mw:"triangle",v:.07},
 {n:"Ndoto Tamu",bpm:72,root:69,sc:[0,3,5,7,10],ch:[[57,60,64],[53,57,60],[48,52,55],[52,55,59]],arp:"0.1.2.1.3.2.1.0.",mel:"x...x.x.....x...",aw:"triangle",mw:"sine",v:.05},
 {n:"Lala Salama",bpm:56,root:74,sc:[0,2,4,7,9],ch:[[57,61,64],[55,59,62],[59,62,66],[52,56,59]],arp:"3.4.5.4.3.4.5.4.",mel:"x.......x.......",aw:"triangle",mw:"sine",v:.06}
];
let AC,master,dIn,nb,bus,timer,step=0,nextT=0,walk=0,muted=false,tn=0;
const mtof=m=>440*Math.pow(2,(m-69)/12);
function initA(){
  AC=new(window.AudioContext||window.webkitAudioContext)();
  master=AC.createGain();master.gain.value=.85;
  const c=AC.createDynamicsCompressor();master.connect(c);c.connect(AC.destination);
  const d=AC.createDelay(1);d.delayTime.value=.34;const fb=AC.createGain();fb.gain.value=.38;
  const lp=AC.createBiquadFilter();lp.frequency.value=2600;
  dIn=AC.createGain();dIn.connect(d);d.connect(lp);lp.connect(fb);fb.connect(d);lp.connect(master);
  nb=AC.createBuffer(1,AC.sampleRate*2,AC.sampleRate);const a=nb.getChannelData(0);for(let i=0;i<a.length;i++)a[i]=Math.random()*2-1;
}
function note(f,t,d,ty,v,o,a=.015){const os=AC.createOscillator(),g=AC.createGain();os.type=ty;os.frequency.value=f;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(v,t+a);g.gain.exponentialRampToValueAtTime(.0001,t+d);os.connect(g);g.connect(o);os.start(t);os.stop(t+d+.05)}
function noise(t,d,ty,fr,v){const s=AC.createBufferSource(),f=AC.createBiquadFilter(),g=AC.createGain();s.buffer=nb;f.type=ty;f.frequency.value=fr;g.gain.setValueAtTime(v,t);g.gain.exponentialRampToValueAtTime(.0001,t+d);s.connect(f);f.connect(g);g.connect(master);s.start(t,Math.random());s.stop(t+d+.05)}
function pstep(T,o,s,t){
  const i=s%16,ch=T.ch[Math.floor(s/16)%4],b=60/T.bpm;
  if(i===0){ch.forEach(m=>{note(mtof(m),t,b*4,"sine",T.v*.8,o,.5);note(mtof(m+12),t,b*4,"triangle",T.v*.3,o,.6)});note(mtof(ch[0]-12),t,b*3,"sine",.2,o,.05)}
  const a=T.arp[i];
  if(a!=="."){const n=+a,m=ch[n%3]+12*(1+Math.floor(n/3));note(mtof(m),t,b*.9,T.aw,T.v,o);note(mtof(m),t+b*.33,b*.6,T.aw,T.v*.4,dIn)}
  if(T.mel[i]==="x"){walk+=[-2,-1,1,2,0,1][Math.random()*6|0];walk=Math.max(0,Math.min(T.sc.length*2-1,walk));
    const m=T.root+T.sc[walk%T.sc.length]+12*Math.floor(walk/T.sc.length);note(mtof(m),t,b*1.7,T.mw,T.v*1.3,o);note(mtof(m),t,b*1.7,T.mw,T.v*.7,dIn)}
}
function play(i){
  if(!AC)initA();if(AC.state==="suspended")AC.resume();
  const T=TR[i%TR.length],now=AC.currentTime;
  if(bus){const ob=bus;ob.gain.setValueAtTime(ob.gain.value,now);ob.gain.linearRampToValueAtTime(0,now+1);setTimeout(()=>ob.disconnect(),1300)}
  clearInterval(timer);
  const g=AC.createGain();g.gain.setValueAtTime(0,now);g.gain.linearRampToValueAtTime(1,now+1.2);g.connect(master);bus=g;
  step=0;walk=2;nextT=now+.1;
  timer=setInterval(()=>{while(nextT<AC.currentTime+.2){pstep(T,g,step,nextT+(step%2?.012:0));nextT+=60/T.bpm/4;step++}},25);
  toast("🎵 "+T.n);
}
let tt;function toast(m){const e=$("now");e.textContent=m;e.classList.add("on");clearTimeout(tt);tt=setTimeout(()=>e.classList.remove("on"),2500)}
$("mute").onclick=()=>{muted=!muted;master.gain.setTargetAtTime(muted?0:.85,AC.currentTime,.05);$("mute").textContent=muted?"🔇":"🔊"};

/* ===== FIREWORKS ===== */
const fc=$("fw"),fx=fc.getContext("2d");let W,H,P=[],R=[],pend=0,run=false;
function size(){const d=Math.min(devicePixelRatio||1,2);fc.width=innerWidth*d;fc.height=innerHeight*d;fx.setTransform(d,0,0,d,0,0);W=innerWidth;H=innerHeight}
addEventListener("resize",size);size();
function boomS(){if(!AC||muted)return;const t=AC.currentTime;noise(t,.7,"lowpass",420,.5);const o=AC.createOscillator(),g=AC.createGain();o.frequency.setValueAtTime(90,t);o.frequency.exponentialRampToValueAtTime(28,t+.4);g.gain.setValueAtTime(.45,t);g.gain.exponentialRampToValueAtTime(.001,t+.5);o.connect(g);g.connect(master);o.start(t);o.stop(t+.55);for(let k=0;k<4;k++)noise(t+.15+Math.random()*.5,.04,"highpass",5000,.15)}
function launch(){R.push({x:W*rnd(.15,.85),y:H,vx:rnd(-.6,.6),vy:-rnd(9,12),ty:H*rnd(.12,.45),h:rnd(0,360)})}
function boom(x,y,hue){
  const ty=["peony","ring","heart","willow","double","crackle","spiral"][Math.random()*7|0],n=ty==="heart"?80:100;
  const add=(vx,vy,h,o={})=>P.push({x,y,px:x,py:y,vx,vy,l:1,d:o.d||rnd(.011,.019),g:o.g??.04,f:o.f||.972,h,w:o.w||2.2,tw:o.tw});
  for(let i=0;i<n;i++){const a=Math.PI*2*i/n,c=Math.cos(a),s=Math.sin(a);
    if(ty==="peony"){const k=rnd(1.5,6);add(c*k,s*k,hue+rnd(0,30))}
    else if(ty==="ring")add(c*5,s*5,hue,{f:.968});
    else if(ty==="heart"){add(16*s*s*s*.3,-(13*c-5*Math.cos(2*a)-2*Math.cos(3*a)-Math.cos(4*a))*.3,340+rnd(0,20),{f:.975,g:.02,d:.009,w:2.6})}
    else if(ty==="willow"){const k=rnd(1,4.6);add(c*k,s*k,42,{g:.035,d:.005,f:.982,w:1.8})}
    else if(ty==="double"){add(c*2.4,s*2.4,hue);add(c*5,s*5,hue+150)}
    else if(ty==="crackle"){const k=rnd(1.5,6);add(c*k,s*k,hue,{tw:1,d:.01})}
    else{const k=1+i/n*5,b=a*3;add(Math.cos(b)*k,Math.sin(b)*k,hue+i*3,{f:.97})}}
  boomS();
}
function loop(){
  fx.globalCompositeOperation="destination-out";fx.fillStyle="rgba(0,0,0,.2)";fx.fillRect(0,0,W,H);
  fx.globalCompositeOperation="lighter";fx.lineCap="round";
  for(let i=R.length-1;i>=0;i--){const r=R[i],px=r.x,py=r.y;r.x+=r.vx;r.y+=r.vy;r.vy*=.985;
    fx.strokeStyle="hsla(40,100%,75%,.9)";fx.lineWidth=2.5;fx.beginPath();fx.moveTo(px,py);fx.lineTo(r.x,r.y);fx.stroke();
    P.push({x:r.x,y:r.y,px:r.x,py:r.y,vx:rnd(-.3,.3),vy:rnd(0,.6),l:.6,d:.04,g:.02,f:.95,h:35,w:1.4});
    if(r.y<=r.ty||r.vy>-1.5){boom(r.x,r.y,r.h);R.splice(i,1)}}
  for(let i=P.length-1;i>=0;i--){const p=P[i];p.px=p.x;p.py=p.y;p.vx*=p.f;p.vy*=p.f;p.vy+=p.g;p.x+=p.vx;p.y+=p.vy;p.l-=p.d;
    if(p.l<=0){P.splice(i,1);continue}
    const a=p.tw&&Math.random()<.4?.1:Math.min(1,p.l*1.4);
    fx.strokeStyle="hsla("+p.h+",100%,"+(55+p.l*25)+"%,"+a+")";fx.lineWidth=p.w*p.l+.4;fx.beginPath();fx.moveTo(p.px,p.py);fx.lineTo(p.x,p.y);fx.stroke()}
  if(R.length||P.length||pend>0)requestAnimationFrame(loop);else{fx.clearRect(0,0,W,H);run=false}
}
function fireworks(n=7){size();for(let k=0;k<n;k++){pend++;setTimeout(()=>{launch();pend--},k*380+rnd(0,250))}if(!run){run=true;requestAnimationFrame(loop)}}
function hearts(n=30){const s=["💖","🌸","✨","⭐","🎉","💙","🌹"];for(let i=0;i<n;i++){const e=document.createElement("span");e.className="hearts";e.textContent=s[Math.random()*s.length|0];e.style.left=rnd(0,100)+"vw";e.style.top=rnd(35,95)+"vh";e.style.fontSize=rnd(16,40)+"px";e.style.animationDuration=rnd(2,4)+"s";document.body.appendChild(e);setTimeout(()=>e.remove(),4500)}}

