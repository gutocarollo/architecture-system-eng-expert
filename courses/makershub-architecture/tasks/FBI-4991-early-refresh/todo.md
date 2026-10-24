# Execução

- [x] Confirmar repositório privado, main em 23d5d158 e destino novo.
- [x] Importar fonte por allowlist, sem caches ou virtualenvs.
- [x] Registrar checkpoint e teste vermelho.
- [x] Implementar o piloto.
- [x] Validar build, laboratório, HTML e navegador.
- [x] Revisar de forma independente.
- [ ] Commit e push no GitHub.
- [ ] Publicar imagem e verificar produção.

## Próxima ação

Checkpoint anterior à publicação: commitar e enviar ao GitHub; publicar imagem por digest e registrar o recibo final em artifacts/delivery.json, gerado e não editorial.

## Rotas de agentes

- WARM_REUSE `/root/case_sources`, default, gpt-6.1-sol/high, exploração somente leitura da portabilidade; resultado: fonte e assets portáveis, excluir caches e usar configuração de exportação.
- O principal é o único escritor. A revisão de implementação terá contexto independente.

## Evidência e decisões

- Fonte importada: commit 26e8cd6418305f7140ff19afce0feeb2f36a780c; export publicado 7bb4b097674187cadd63b483c8e0505829966142312cef339a31c6478fc60a34.
- Baseline externo reversível: imagem sha256:f4f07378fff02ac467d65e3ae4295fc46f4a3a76102d0571a2ba18e0332e718a.

- Checkpoint importado: `.checkpoints/imported-course.tar.gz`, SHA256 f6ef300b95003eb3ecdc7964a072b597af0220f928389298518336338a4e9abe; tar listado com 441 entradas. Restore restrito aos caminhos contidos no arquivo.
- Baseline HTML: 15 testes; 5 passaram e 10 falharam pelos dois comportamentos reportados. Primeiro build alterado: 15 testes passaram; 184 HTML e 181 páginas indexadas.
- Download extraído e executado em pasta temporária: 5 arquivos idênticos à fonte, exit_code=0, saída SHA256 1201e28b8a9c207c67c6dabad6fd7a4be235fee7fa305dfabfede5d2aed8f9ac.
- Verificação da fonte histórica confirmou o horário 2026-10-15T02:34:17.531499+00:00 de early-refresh; a referência do piloto foi alinhada ao recibo.

- Ruling: aplicar somente o patch Next 16.4.0 → 16.4.3 nesta pasta. O build apontou vulnerabilidade conhecida e `npm audit --omit=dev` confirmou três advisories de Next com correção disponível. Nextra e o runtime Hono permanecem nas versões existentes. O serviço usa export estático; a correção também protege futuros builds e evita conservar a versão sinalizada na fonte nova.
- Fontes do patch: https://nextjs.org/blog/nextjs-security-update-october-14-2026 e advisories GHSA-673q-mjm6-r5xr / GHSA-2464-fhr4-w9xw. A repetição simples do build funcionou, mas não foi tratada como correção da dependência.

- Review independente `/root/implementation_review`, gpt-6.1-sol/xhigh: PASS, zero bloqueadores materiais; revisão cobre código e evidência local.
- Último build após CSS e Next 16.4.3: 184 HTML, 181 páginas indexadas. Mutações em cópias: remover navegação matou 1 teste; desviar link local matou 2; remover fragmento antigo matou 1.
- Browser local: percurso completo, teclado, busca e largura CSS 390; alvo da âncora em y=303,82, abaixo da navegação com borda inferior y=231,27.
- Avisos de whitespace no diff pertencem ao conteúdo importado fora do piloto; não foram tratados como defeitos funcionais nem reformatados.
