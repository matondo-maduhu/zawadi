/* Hujenga catalog/ kutoka tools/templates-src.js
   Matokeo: catalog/catalog.json (orodha + fomu za kila template) na catalog/pages/<id>.html (skeleton).
   Matumizi:  node tools/build_catalog.js */
const fs=require('fs'),path=require('path'),S=require('./templates-src.js');
const out=path.join(__dirname,'..','catalog'),pages=path.join(out,'pages');fs.mkdirSync(pages,{recursive:true});
const list=[];let bad=0;
for(const t of S.TPL){
  const a=S.skeleton(t);
  const alt={};for(const f of t.f){alt[f.k]=f.t=='select'?f.o[f.o.length-1][0]:f.t=='images'||f.t=='image'?f.t=='images'?['x']:'x':'ALT-'+f.k+'-'+Math.random()}
  const b=S.skeleton(t,alt);
  if(a!==b){bad++;console.error('! skeleton inategemea data:',t.id)}
  for(const m of ['@@HEAD@@','@@THEME@@','@@DATA@@'])if(!a.includes(m)){bad++;console.error('! alama haipo',m,t.id)}
  fs.writeFileSync(path.join(pages,t.id+'.html'),a,'utf8');
  list.push({id:t.id,e:t.e,n:t.n,d:t.d,cats:Object.keys(S.CM).filter(c=>S.CM[c].includes(t.id)),base:S.baseFlags(t),
    fields:t.f.map(f=>({k:f.k,l:f.l,t:f.t,d:f.d,o:f.o,max:f.max,r:f.r,ph:f.ph}))});
}
const cat={themes:S.TH,cats:S.CATS.map(([id,n])=>({id,n})),templates:list};
fs.writeFileSync(path.join(out,'catalog.json'),JSON.stringify(cat,null,1),'utf8');
console.log('Templates',list.length,'| makosa',bad);process.exit(bad?1:0);
