# Preflight da edição unitária da Story FBI-4991

A alteração autorizada escreve somente `customfield_10054`, com o ADF completo atual acrescido do requisito de comparar o curso Nextra ao MakersHub e entregar jornadas encapsuladas nos quatro quadrantes do Diátaxis. As jornadas usam casos reais de conceitos, prática e antes/depois sustentado por commits, descrições de PR e bugs Jira; o fallback financeiro é hipotético e identificado. O MakersHub continua sendo fonte consultada. As classificações materiais permanecem iguais.

O catálogo e seu audit devem ser preservados integralmente. Não é necessário reenviar `customfield_10521` nem gerar outra decisão de catálogo numa edição que toca somente a descrição. O audit persistido contém o hash do preview da criação; ele não deve ser apresentado como hash desta nova edição. O novo hash pertence ao preview externo da edição.

## Receita executável

1. Ler novamente o card com `responseContentFormat: "adf"`, incluindo `updated`, `issuetype`, `status`, `customfield_10054`, `components`, `labels` e `customfield_10514` até `customfield_10522`. Parsear o JSON de `content[].text`; não usar a conversão Markdown normalizada de Paragraph.
2. Comparar `updated`, ADF anterior e catálogo com a preimage do preview. Divergência exige recompor o preview sobre a nova leitura antes de escrever. O MCP não oferece precondição atômica: essa comparação reduz a janela de conflito, sem eliminar corrida.
3. Montar o novo ADF por cópia dos nós existentes, com acréscimos autorizados. Aplicar as equivalências abaixo se o texto original ainda contiver essas frases.
4. Executar ambos os gates físicos sobre o envelope exato do preview, por stdin. O envelope usa `hook_event_name: "PreToolUse"`, `tool_name` igual à tool oficial de edição e `tool_input` igual aos argumentos abaixo.
5. O root publica uma única edição e faz novo GET explícito dos mesmos campos. O ADF esperado deve coincidir com o persistido; catálogo e status devem coincidir com a preimage.

```json
{
  "cloudId": "941be6d6-e8c6-481a-9346-6c425e72d22f",
  "issueIdOrKey": "FBI-4991",
  "contentFormat": "adf",
  "responseContentFormat": "adf",
  "fields": {
    "customfield_10054": "SUBSTITUIR PELO OBJETO ADF FINAL"
  }
}
```

O valor ilustrativo acima é documentação da forma, não um payload válido. A ferramenta real é `mcp__codex_apps__atlassian_rovo__legacy__atlassian_rovo_legacy_editjiraissue`. Ela não aceita `expectedCurrentState`. O gate tampouco interpreta essa chave; a precondição fica no controle externo do root.

```sh
node /Users/augustocarollo/.agents/skills/jira-fbi/scripts/jira-fbi-gate.mjs < preview.json
node /Users/augustocarollo/.agents/skills/jira-fbi/scripts/claude-hook-wrapper.cjs < preview.json
```

## Equivalências necessárias para o wrapper

O regex `PLACEHOLDER_RE` contém `TODO` com flag `i` e sem fronteira de palavra. O wrapper recusou oito parágrafos reais por conterem “todo/todos”. O preview aprovado manteve os requisitos usando estas substituições, que ocorreram dez vezes:

| Texto existente | Redação equivalente |
| --- | --- |
| todo o texto fornecido | a íntegra do texto fornecido |
| todos os conceitos | a totalidade dos conceitos |
| todos os commits | a totalidade dos commits |
| todo esse histórico | a íntegra desse histórico |
| todos os itens | a totalidade dos itens |
| todo o histórico | o histórico integral |
| todos os critérios cumpridos | cada critério cumprido |

A mudança não exige alterar a skill. Cada chave Jira citada no novo conteúdo deve ser um nó text com mark link para o card correspondente.

## Recibos

- [2026-10-15 00:15 UTC] checkout — `pwd; git branch --show-current` → `/Users/augustocarollo/.superset/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`; `perfect-citizen-a30f5998`.
- [2026-10-15 00:15 UTC] Jira, GET FBI-4991 em ADF → `issuetype.id="10006"`; `customfield_10054.type="doc"`; 43 nós; `updated="2026-10-14T20:29:15.360-0300"`; `customfield_10520.value="blocked"`.
- [2026-10-15 00:16 UTC] Jira, GET FBI-4991 incluindo o campo e `expand="editmeta"` → `editmeta.customfield_10054.name="Story Description"`; `operations=["set"]`. Nesse retorno raw a chave apareceu diretamente em editmeta, fora de editmeta.fields.
- [2026-10-15 00:16 UTC] Jira, GET status → `status.name="To Do"`; `status.id="10003"`; updated inalterado.
- [2026-10-15 00:16 UTC] gates físicos sobre o preview de um campo, com equivalências e acréscimo → gate mjs: `permissionDecision="allow"`, exit 0; wrapper: exit 0, stdout vazio. A função `allow()` do wrapper termina com `process.exit(0)` e não imprime JSON; o ramo deny imprime JSON.

SHA256 do ADF anterior, com JSON compacto, chaves ordenadas e UTF-8: `bb854d56406ffab12f926bdbd6e3d89d6947bf9992428a03beada0955dd474a3`. O root deve calcular outro hash para sua redação final. Esta análise não alterou o Jira.
