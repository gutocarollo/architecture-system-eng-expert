"""Reconnect the PostgreSQL cases after either author regenerates the course."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PG_CASES=json.loads((Path(__file__).parent/'families.json').read_text())['families']
AIRFLOW_PATH=Path(__file__).parent.parent/'airflow-learning/families.json'
AIRFLOW_CASES=json.loads(AIRFLOW_PATH.read_text())['families'] if AIRFLOW_PATH.exists() else []
CASES=PG_CASES+AIRFLOW_CASES
for folder in ['jornadas','explicacoes/casos','tutoriais/casos','guias/casos','referencia/casos']:
    meta=ROOT/'content'/folder/'_meta.js'
    values=json.loads(meta.read_text().removeprefix('export default ').strip().removesuffix(';')) if meta.exists() else {'index':'Contratos dos casos', **{item['case_id']:item['title'] for item in json.loads((ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/families.json').read_text())['families']}}
    for case in CASES: values[case['case_id']]=case['title']
    meta.write_text('export default '+json.dumps(values,ensure_ascii=False,indent=2)+'\n')
    index=ROOT/'content'/folder/'index.mdx'
    text=index.read_text() if index.exists() else '---\ntitle: Contratos dos casos\ndiataxis: reference\n---\n\n# Contratos dos casos\n\nCada contrato conserva a identidade da jornada, as entradas, as garantias e os limites observados. Consulte também as [jornadas por caso](/jornadas/).\n'
    if folder=='referencia/casos' and '## Contratos dos percursos' not in text:
        rows=json.loads((ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/families.json').read_text())['families']
        section='\n\n## Contratos dos percursos\n\n'
        section+='| Caso | Contrato para consulta |\n| --- | --- |\n'
        for item in rows:
            section+=f"| {item['title']} | [Entradas, garantias e limites]({item['destinations']['reference']}) |\n"
        text=text.replace('\n\n## Dois casos executados no PostgreSQL',section+'\n\n## Dois casos executados no PostgreSQL') if '## Dois casos executados no PostgreSQL' in text else text+section
    if '## Dois casos executados no PostgreSQL' not in text:
        text+='\n\n## Dois casos executados no PostgreSQL\n\n'
        for case in PG_CASES:
            key='journey' if folder=='jornadas' else {'explicacoes/casos':'explanation','tutoriais/casos':'tutorial','guias/casos':'how_to','referencia/casos':'reference'}[folder]
            text+=f"- [{case['title']}]({case['destinations'][key]}). O caso conserva o SQL histórico, o patch e o contrato de uma execução isolada.\n"
    if AIRFLOW_CASES and '## Uma mudança histórica do Airflow' not in text:
        text+='\n\n## Uma mudança histórica do Airflow\n\n'
        for case in AIRFLOW_CASES:
            key='journey' if folder=='jornadas' else {'explicacoes/casos':'explanation','tutoriais/casos':'tutorial','guias/casos':'how_to','referencia/casos':'reference'}[folder]
            text+=f"- [{case['title']}]({case['destinations'][key]}). Você executa a função Python com respostas externas controladas e confere quais erros recebem uma nova tentativa.\n"
    if folder=='jornadas':
        text=text.replace('Quinze casos ligam explicação, tutorial, guia e referência.','Dezessete casos ligam explicação, tutorial, guia e referência.')
        text=text.replace('Os quatro primeiros usam versões históricas do MakersHub; os demais são modelos financeiros hipotéticos para mecanismos ainda sem uma linhagem interna completa na trilha.','Seis casos usam versões históricas do MakersHub. Os onze modelos financeiros hipotéticos apresentam mecanismos que ainda não têm uma linhagem interna completa nesta trilha.')
    if folder=='jornadas' and AIRFLOW_CASES:
        text=text.replace('Dezessete casos ligam','Dezoito casos ligam').replace('Seis casos usam versões históricas','Sete casos usam versões históricas')
    index.write_text(text)

home=ROOT/'content/index.mdx'
text=home.read_text()
if '](/jornadas/query-grain-postgres)' not in text:
    needle='Cada percurso informa se reconstrói uma mudança documentada'
    extra='- [Uma comissão de R$ 100 aparece como R$ 200](/jornadas/query-grain-postgres). Execute a junção histórica no PostgreSQL e corrija a granularidade.\n- [Uma única versão atual ainda perde uma alteração](/jornadas/revision-cas-postgres). Compare a revisão lida antes de permitir a escrita atrasada.\n\n'
    text=text.replace(needle,extra+needle)
if AIRFLOW_CASES and '](/jornadas/airflow-lock-retry)' not in text:
    text=text.replace('Cada percurso informa se reconstrói uma mudança documentada','- [Uma falha de lock derruba a tarefa do Airflow](/jornadas/airflow-lock-retry). Execute o retry histórico e confira os erros que continuam falhando cedo.\n\nCada percurso informa se reconstrói uma mudança documentada')
home.write_text(text)
print('Integrated '+str(15+len(CASES))+' cases across five navigation trees without replacing the original cases.')
