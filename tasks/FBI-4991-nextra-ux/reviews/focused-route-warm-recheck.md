# Rechecagem da seta de navegação

**PASS_BOUNDED.** A correção remove somente a barra final do valor usado na comparação de foco. Não foi encontrado achado alto ou bloqueante nesse patch. Este parecer cobre a fonte; o clique no host depois do rebuild continua sendo o gate do orquestrador.

O caso do próprio grupo e o caso de um descendente ficam distintos. O foco em `/jornadas/reservation/` passa a ser comparado como `/jornadas/reservation`, portanto deixa de forçar a abertura por `focusedRouteInside`. O foco em `/jornadas/reservation/conceitos/` conserva o prefixo `/jornadas/reservation/`, portanto ainda mantém o grupo aberto enquanto um filho está focado. O separador de caminho também evita tratar `/jornadas/reservation-other/` como filho.

O hook retorna uma string e começa com `""`; a substituição é válida para esse contrato. O handler nativo da seta ainda impede navegação e alterna `TreeState`. O patch não modifica o href, a rota ativa nem os outros trechos do handler. A comparação deixa de confundir o próprio índice com um descendente sem remover a proteção de foco dos filhos.

A falha anterior está no recibo hospedado de 03:43 UTC: `before` e `after` eram `open active`, enquanto `urlUnchanged` era `true`. Esse recibo prova a falha anterior, não a correção publicada.

## Recibos da rechecagem

- [2026-10-17 03:46 UTC] `wt-FBI-4991` — `git branch --show-current` e `git rev-parse HEAD` → `docs/FBI-4991-arquitetura-aplicada` e `d5c3c1cf5808e88a2bfe4c4e109ae01fbc4f8a43`.
- [2026-10-17 03:46 UTC] `node_modules/nextra-theme-docs/dist/components/sidebar.js:57-58` — leitura direta → `const focusedRoute = useFocusedRoute().replace(/\/$/, "");` e `const focusedRouteInside = focusedRoute.startsWith(item.route + "/");`.
- [2026-10-17 03:46 UTC] `node_modules/nextra-theme-docs/dist/stores/focused-route.js` e `.d.mts` — leitura direta → `focused: ""` e `useFocusedRoute: () => string`.
- [2026-10-17 03:46 UTC] `patches/nextra-theme-docs+4.6.1.patch` — SHA-256 → `91997cc001618fed04170cbfa449c465143928c7e52299dfed5ce84e9ca52cad`.
- [2026-10-17 03:46 UTC] `node_modules/nextra-theme-docs` — `Path.resolve()` → `/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991/node_modules/nextra-theme-docs`; o pacote não é symlink.
- [2026-10-17 03:46 UTC] `sites/architecture-course/node_modules` — `Path.resolve()` → `/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991/node_modules`.

PLACAR: 0 altos ou bloqueantes. Próximo passo: confirmar no novo bundle hospedado que a seta alterna aberto/fechado sem mudar a URL e que focar um descendente mantém a árvore visível. Nenhum arquivo de produto foi alterado por este revisor.
