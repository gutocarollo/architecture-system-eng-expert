# Revisão independente de ensino — REPAIR

Medição: 2026-10-15T01:45:17.746751+00:00. Base: 23d5d158d3a964dceba296296368ec14bcd8970b.

Os quinze casos e os 23 mecanismos de objetos executaram com saída zero. Os dois desafios editáveis falharam antes do patch e passaram depois. Os 75 destinos existem e conservam links para os outros destinos do mesmo caso. Os quatro pares históricos correspondem aos objetos Git e ao pai correto. Esses resultados não encerram os achados semânticos abaixo.

## T1 — HIGH — A matriz oferece probes de outro mecanismo como prática do conceito

Cache Aside e Message Filter/Splitter têm LOCAL_MECHANISM sem miss/load/store, filtro ou split. A/B usa execução shadow; Negative Caching usa isolamento de tenant; Gossip e Stateless Services contam maioria. Limitar o claim não cria a ligação que falta.

Correção exigida: Adjudicar os vínculos por mecanismo; adicionar uma observação/contraste que ensine o conceito e seu resultado específico, ou manter a lacuna pendente. Não classificar 310 entradas como jornada cumprida apenas porque todas possuem um comando.

Fontes: labs/architecture/map_concepts.py:20, content/jornadas/cache-policy/conceitos.mdx:15, content/jornadas/queue-workflow/conceitos.mdx:527, content/jornadas/safe-release/conceitos.mdx:15, labs/architecture/financial.py:121

## T2 — HIGH — comparison=PASS não verifica a garantia financeira declarada

Mutação somente em memória troca a soma deduplicada pela soma das três entregas. Before e after ficam com debit=250, mas effects muda de 3 para 2 e o runner imprime comparison=PASS. O aluno é informado de que esse PASS prova a garantia, embora a cobrança duplicada permaneça.

Correção exigida: Verificar invariantes observáveis próprios de cada probe e exigir que a condição protegida viole o contrato quando a proteção é removida. Para a deduplicação: três entregas, dois efeitos e débito 150. Validar o antes e o depois, não apenas que dois objetos diferem.

Fontes: labs/architecture/financial.py:11, content/tutoriais/casos/safe-release/index.mdx:34, tasks/FBI-4991-arquitetura-nextra/execution/reviews/teaching.mutation.json

## T3 — HIGH — O exercício de métricas conta spans como requests e usa o denominador errado

A fixture tem REQUEST-1 e REQUEST-2 em três spans. measure-signals publica requests=3 e error_ratio=0.333. No grão de request relatado na história são duas tentativas e uma delas falha: 1/2 = 0.5.

Correção exigida: Definir o grão da métrica e conservar a distinção entre span, request e operação; calcular requests e erro por request, ou rotular explicitamente uma métrica de spans sem apresentá-la como contagem de requests/RED. Atualizar as saídas dos destinos afetados.

Fontes: labs/architecture/financial.py:271, content/explicacoes/casos/diagnostics/index.mdx:11

O recibo estruturado teaching.json registra hashes dos arquivos lidos, comandos, limites e a versão examinada. Não há veredito de renderização ou produção.
