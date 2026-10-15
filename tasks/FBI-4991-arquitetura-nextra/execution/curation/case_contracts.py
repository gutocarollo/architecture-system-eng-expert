#!/usr/bin/env python3
"""Publish case reference contracts from the authored registry and observed lab receipts."""
import hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
LEARNING=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning'
registry=json.loads((LEARNING/'families.json').read_text())
receipts=json.loads((LEARNING/'receipts.json').read_text())
by_case={r['case_id']:r for r in receipts['receipts']}
concepts=json.loads((LEARNING/'concept-matrix.json').read_text())['concepts']
output=[]
for case in registry['families']:
 case=dict(case)
 for field in ['input','purpose','result','fix','limit']:
  case[field]=case[field].replace('{', '\\{').replace('}', '\\}')
 case_id=case['case_id']; receipt=by_case[case_id]
 title='Contratos: '+case['group'].lower()
 text='---\ntitle: '+json.dumps(title,ensure_ascii=False)+'\ndescription: '+json.dumps('Entradas, parâmetros, versões, resultados e limites do caso '+case['title']+'.',ensure_ascii=False)+'\ndiataxis: reference\n---\n\n# '+title+'\n\n'
 text+='Esta página reúne os contratos que a prática compara. '+case['purpose']+' Os valores descritos pertencem a um laboratório local com entradas fictícias.\n\n'
 text+=f'Para continuar o mesmo problema, [volte à jornada]({case["destinations"]["journey"]}), [entenda o mecanismo]({case["destinations"]["explanation"]}), [execute o tutorial]({case["destinations"]["tutorial"]}) ou [consulte o guia da tarefa]({case["destinations"]["how_to"]}).\n\n'
 text+='## Entradas e ambiente\n\n'+case['input']+'\n\n'
 text+='| Contrato | Valor do caso |\n| --- | --- |\n'
 text+='| Identidade do caso | `'+case_id+'`. |\n'
 text+='| Símbolos a consultar | `'+case['symbol']+'`. |\n'
 text+='| Comando completo | `'+case['command']+'`. |\n'
 text+='| Dados e efeito externo | As entradas são sintéticas. A prática conserva os efeitos em memória ou em um arquivo temporário local. |\n'
 text+='| Versões da execução registrada | Python `'+receipt['environment']['python']+'` e Node `'+receipt['environment']['node']+'`. |\n'
 text+='| Horário e escopo do recibo | `'+receipt['observed_at_utc']+'`, no laboratório local. |\n\n'
 text+='O tutorial explica a preparação e como reiniciar. O comando acima é uma consulta rápida para quem já preparou o ambiente.\n\n'
 historical=case.get('before_sha') is not None
 if historical:
  manifest=json.loads((ROOT/f'labs/architecture/{case_id}/manifest.json').read_text())
  text+='## Versões e fronteiras da reprodução\n\n'+case['provenance_text']+'\n\n'
  text+='| Fase | Fonte histórica | SHA | Cópia do laboratório |\n| --- | --- | --- | --- |\n'
  for snapshot in manifest['snapshots']:
   link='https://bitbucket.org/fazcapital/makershub/src/'+snapshot['sha']+'/'+snapshot['source_path']
   text+='| '+('Anterior' if snapshot['phase']=='before' else 'Posterior')+' | ['+snapshot['source_path']+']('+link+') | `'+snapshot['sha']+'` | `'+snapshot['local_path']+'`. |\n'
  text+='\nO diff preservado é `labs/architecture/'+case_id+'/source.diff`; seu SHA-256 é `'+manifest['diff_sha256']+'`. As cópias possuem hashes no manifesto do mesmo diretório. Esses hashes identificam o recorte reproduzido; não certificam o checkout ou o deploy que alguém abrir em outra ocasião.\n\n'
 else:
  text+='## Fonte do modelo financeiro\n\n'+case['provenance_text']+'\n\n'
  text+='A função `'+case_id.replace('-','_')+'` está em `labs/architecture/financial.py`. O artefato `tasks/FBI-4991-arquitetura-nextra/execution/learning/searches/'+case_id+'.json` conserva o alcance da busca por um caso interno. O modelo serve para comparar uma garantia com uma falha delimitada; ele não implementa integralmente todas as tecnologias relacionadas.\n\n'
 text+='## Resultados que o contrato compara\n\n'+case['result']+'\n\n'
 records=[]
 for line in receipt['stdout'].splitlines():
  if line.startswith('{'):
   try:records.append(json.loads(line))
   except json.JSONDecodeError:pass
 for record in records:
  probe=record['probe']; matches=[c for c in concepts if c['case_id']==case_id and c.get('probe')==probe]
  text+='### `'+probe+'`\n\n'
  actions=list(dict.fromkeys(c['exercise_action'] for c in matches))
  if actions:text+='A comparação permite executar a seguinte ação de estudo: '+actions[0]+'\n\n'
  text+='| Campo de saída | Condição anterior | Condição posterior |\n| --- | --- | --- |\n'
  before=record['before'];after=record['after']
  if isinstance(before,dict) and isinstance(after,dict):
   for key in list(dict.fromkeys([*before,*after])):
    def value(v,key):return '`'+json.dumps(v[key],ensure_ascii=False,sort_keys=True).replace('|','\\|')+'`' if key in v else 'O campo não é emitido nesta condição.'
    text+='| `'+key+'` | '+value(before,key)+' | '+value(after,key)+' |\n'
  else:
   text+='| Valor retornado | `'+json.dumps(before,ensure_ascii=False).replace('|','\\|')+'` | `'+json.dumps(after,ensure_ascii=False).replace('|','\\|')+'` |\n'
  text+='\n'
  if matches:
   text+='Os conceitos relacionados e seus limites estão na [matriz do mesmo caso]('+case['destinations']['journey']+'conceitos/). Eles compartilham esta comparação; a presença de um nome nessa matriz não amplia a garantia do programa.\n\n'
 if not records:
  text+='A reprodução histórica emite o resultado completo abaixo. Os rótulos `before` e `after` distinguem as versões; `comparison=PASS` significa que as condições esperadas apareceram nos dois recortes.\n\n```text\n'+receipt['stdout'].rstrip()+'\n```\n\n'
 text+='## Garantia, parâmetros e limites\n\n'+case['fix']+' '+case['limit']+'\n\n'
 text+='Uma repetição usa a mesma entrada conhecida. Nos modelos financeiros, `--probe <nome>` restringe a comparação ao probe escolhido. Um nome desconhecido encerra o programa; o argumento não cria um novo cenário. Nos recortes históricos, os parâmetros e doubles estão nos runners de cada pasta.\n\n'
 text+='Para localizar as bibliotecas e os produtos OSS correspondentes, use a [curadoria dos 310 conceitos](/referencia/curadoria/). Ela mantém separadas a implementação pública verificada, a demonstração e a lacuna de evidência.\n\n'
 text+='## Recibo e rastreabilidade\n\n'
 text+='A captura fica em `tasks/FBI-4991-arquitetura-nextra/execution/learning/receipts.json`, na entrada `'+case_id+'`. O hash SHA-256 da saída capturada é `'+hashlib.sha256(receipt['stdout'].encode()).hexdigest()+'`. O recibo registra `exit_code='+str(receipt['exit_code'])+'`. Uma execução futura precisa produzir seu próprio recibo; estes números descrevem somente a execução e a versão indicadas.\n\n'
 text+=f'Quando precisar da explicação ou dos passos, [volte à jornada]({case["destinations"]["journey"]}), [leia a explicação]({case["destinations"]["explanation"]}), [abra o tutorial]({case["destinations"]["tutorial"]}) ou [consulte o guia]({case["destinations"]["how_to"]}).\n'
 target=ROOT/f'content/referencia/casos/{case_id}/index.mdx';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
 output.append({'case_id':case_id,'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(text.encode()).hexdigest(),'probes':len(records),'receipt_observed_utc':receipt['observed_at_utc'],'links':case['destinations']})
(BASE/'case-reference-receipts.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print('Case references written:',len(output))
