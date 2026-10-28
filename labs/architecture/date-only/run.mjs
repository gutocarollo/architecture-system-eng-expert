import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
const root = path.dirname(fileURLToPath(import.meta.url));
const beforeSource = fs.readFileSync(path.join(root, 'before-card.tsx'), 'utf8');
const match = beforeSource.match(/const formatDate = useCallback\((\(dateStr:[\s\S]*?)\}, \[\]\);/);
if (!match) throw new Error('historical before function not found');
const beforeTs = 'export const formatDate = ' + match[1] + '};';
const candidateIndex = process.argv.indexOf('--candidate');
const afterTs = fs.readFileSync(candidateIndex < 0 ? path.join(root, 'after.ts') : process.argv[candidateIndex+1], 'utf8');
async function load(source) {
  const js = ts.transpileModule(source, {compilerOptions:{target:ts.ScriptTarget.ES2022, module:ts.ModuleKind.ESNext}}).outputText;
  return await import('data:text/javascript;base64,' + Buffer.from(js).toString('base64'));
}
const before = await load(beforeTs);
const after = await load(afterTs);
const value = '2026-10-05';
const observedBefore = before.formatDate(value);
const observedAfter = after.formatBrDate(value, {year:'2-digit'});
console.log(`zone=${process.env.TZ} input=${value} before=${observedBefore} after=${observedAfter}`);
if (process.env.TZ !== 'America/Sao_Paulo' || observedBefore !== '04/10/26' || observedAfter !== '05/10/26') throw new Error('date-only comparison failed');
const instant = '2026-10-05T00:00:00Z';
const formattedInstant = after.formatBrDate(instant, {year:'2-digit'});
console.log(`timestamp=${instant} after=${formattedInstant} preserves_instant=true`);
if (formattedInstant !== '04/10/26') throw new Error('timestamp semantics changed');
console.log('comparison=PASS date_only_and_instant_are_distinct=True');
