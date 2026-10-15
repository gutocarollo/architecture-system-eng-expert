# Medições iniciais

- [2026-10-14 15:54 UTC] PostgreSQL pelo MCP `postgres` — `SELECT clock_timestamp() AT TIME ZONE 'UTC', inet_server_addr()::text, inet_server_port(), current_database(), current_user` → `192.168.254.137/32`, `5432`, `faz_capital`, `augusto_carollo`.
- [2026-10-14 15:52 UTC] FazGraph MCP — `status()` → `status=ok`, `graph_source=full`, `source_mode=built`, `graph_mtime_utc=2026-10-13T03:08:04+00:00`, `data_dir=/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4/data`.
- [2026-10-14 15:53 UTC] Mac — `Path('/Users/augustocarollo/Developer/fazgraph-canonical-v4/data').resolve()` → `/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4/data`. O caminho é o alvo físico do endereço canônico, não uma instância remota diferente.
- [2026-10-14 15:55 UTC] FazGraph MCP — `pipeline('captacao', max_matches=1)` → `dbt.fct_captacao`, produtor `dbt_model fct_captacao`, upstream `public.rpt_inflow__movement_adjusted`, downstream `dbt.fct_advisor_dashboard`, `dbt.fct_goals`, `dbt.fct_ranking`. A própria resposta marca `db_stats` e `airflow_runs` como stale; seus números não serão tratados como medições atuais. A regra de negócio é inferida, sem confirmação humana.

## Fontes de formato

- [2026-10-14 15:56 UTC] FazGraph MCP — `blast_radius('public.rpt_inflow__movement_adjusted')` → `43 downstream table(s), 424 Metabase card(s), 27 endpoint(s). Direct on this table: 322 card(s), 3 endpoint(s).` O grafo foi construído em `2026-10-13T03:08:04+00:00`; estes valores são contagens da linhagem desse snapshot, não prova de que cada consumidor está ativo hoje. Entre os nós aparecem `makershub.rpt_goals__employee_kpi_scorecard_monthly`, `dbt.fct_captacao`, `makershub_endpoint.api:my_kpis` e `makershub_endpoint.api:kpi_scorecard`.

Context7 resolveu `/websites/nextra_site`. A consulta sobre Nextra 4 confirmou `content/` com páginas MDX e `_meta.js` em cada diretório. A documentação oficial https://nextra.site/docs/advanced/mermaid confirma fences `mermaid`. Diátaxis https://diataxis.fr/ separa tutorial, guia, referência e explicação por necessidade do leitor.

## Limite de memória

Hindsight search e list retornaram zero páginas. A tentativa de capture_initiative retornou `500` com `column cannot have more than 2000 dimensions for hnsw index`; portanto não há recibo de iniciativa capturada. O bank retornado pela ferramenta foi `coding-agent::data-engineer-handbook`, que não será tratado como contexto confirmado deste repositório. Nenhuma configuração ou índice foi alterado.
