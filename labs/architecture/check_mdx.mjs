import {compile} from '@mdx-js/mdx';
import fs from 'node:fs';
import crypto from 'node:crypto';
const dirs=['content/jornadas','content/explicacoes/casos','content/tutoriais/casos','content/guias/casos'];
const files=dirs.flatMap(dir=>fs.readdirSync(dir,{recursive:true}).filter(file=>file.endsWith('.mdx')).map(file=>dir+'/'+file)).filter(file=>!file.includes('/query-grain-postgres/')&&!file.includes('/revision-cas-postgres/'));
const receipts=[];
for(const file of files){
  const source=fs.readFileSync(file);
  try{
    await compile(source);
    receipts.push({file,sha256:crypto.createHash('sha256').update(source).digest('hex'),verdict:'PASS'});
  }catch(error){
    receipts.push({file,verdict:'FAIL',line:error.line,column:error.column,reason:error.reason});
  }
}
const failures=receipts.filter(r=>r.verdict==='FAIL');
fs.writeFileSync('tasks/FBI-4991-arquitetura-nextra/execution/learning/mdx-parse.json',JSON.stringify({observed_at_utc:new Date().toISOString(),parser:'@mdx-js/mdx',files:files.length,failures,receipts},null,2)+'\n');
console.log(JSON.stringify({files:files.length,failures:failures.length}));
if(failures.length)process.exit(1);
