// node shot.js page.html out.png W H [scale]
const {chromium}=require('playwright');
(async()=>{const [,,page,out,w,h,sc]=process.argv;const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:+w,height:+h},deviceScaleFactor:+(sc||1)});
p.on('console',m=>console.log('console:',m.text()));p.on('pageerror',e=>{console.log('ERR',e.message);process.exit(1)});
await p.goto(page.startsWith('http')?page:'file://'+require('path').resolve(page));await p.waitForFunction('window.READY===true',null,{timeout:600000});
await p.waitForTimeout(300);
await p.screenshot({path:out,clip:{x:0,y:0,width:+w,height:+h},omitBackground:true,timeout:0});await b.close();})();
