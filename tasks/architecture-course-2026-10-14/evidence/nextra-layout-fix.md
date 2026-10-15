# Correção de compatibilidade do tema Nextra

O build de 14/10/2026 compilou os MDX, mas falhou no prerender com `Invalid input: expected nonoptional, received undefined → at children`. O `Layout` de nextra-theme-docs 4.6.1 retira `children` antes de validar `themeConfig`; o schema ainda exigia a chave. A issue primária [Nextra #5036](https://github.com/shuding/nextra/issues/5036) descreve o mesmo mecanismo.

Foi aplicada a correção mínima proposta pelo upstream: `children: reactNode.optional()`. O patch-package registra o delta no projeto e o reaplica no postinstall. A versão permanece fixada em 4.6.1; não houve troca de tema ou alteração do conteúdo. O resultado do build seguinte decide se a correção resolveu este projeto.

- [2026-10-14 18:42 UTC] `node_modules/nextra-theme-docs/dist/layout.js` — leitura de `LayoutPropsSchema.safeParse(themeConfig)` após destructuring de `children` → `safeParse(themeConfig)`.
- [2026-10-14 18:42 UTC] `node_modules/nextra-theme-docs/dist/schemas.js` — leitura do schema → `children: reactNode,` antes do patch.
