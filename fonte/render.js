const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
 fs.mkdirSync('frames',{recursive:true});
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+process.cwd()+'/film.html');
 const FPS=24,N=30*FPS;
 for(let i=0;i<N;i++){
   const d=await p.evaluate(t=>{window.render(t);return document.getElementById('c').toDataURL('image/jpeg',0.93)},i/FPS);
   fs.writeFileSync(`frames/f${String(i).padStart(4,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64'));
 }
 await b.close();console.log('done',N);
})();
