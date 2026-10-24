# Laboratórios de arquitetura aplicada

Estes programas permitem repetir uma condição com dados conhecidos e comparar o que muda quando uma proteção é aplicada. Os quatro primeiros casos preservam versões históricas do MakersHub. Os demais usam participantes, ordens e posições fictícios de uma corretora hipotética. A XP contextualiza somente o setor; nenhum programa descreve sua operação interna.

Abra o terminal na raiz deste repositório. Use Python 3.11 ou posterior e a CLI OpenSSL 3.x. Confira sua versão com `openssl version`; a execução registrada usou 3.6.5. Prepare o SDK isolado com `python3 labs/architecture/setup_labs.py`; o lock fixa OpenTelemetry 1.45.1 e suas dependências. A instalação baixa os pacotes, e as práticas posteriores usam exportação somente para memória. O caso de data também usa Node e o TypeScript fixado no lock dos laboratórios; execute `npm ci --prefix labs/architecture` para instalar essa dependência. Os recibos informam as versões que foram efetivamente usadas.

Para executar todos os casos e registrar as saídas literais, use:

```sh
python3 labs/architecture/run_all.py
```

Para conferir a atividade em que uma cópia anterior falha, recebe o patch histórico e passa na mesma condição, use:

```sh
python3 labs/architecture/check_challenges.py
```

Os tutoriais de cancelamento compartilhado e de data civil apresentam os passos manuais dessa mesma atividade. Cada cópia nasce em uma pasta temporária. O comando de patch atua somente nessa cópia.

Para conferir os invariantes de todos os probes, os controles negativos e a mutação que troca o débito deduplicado de 150 por 250, use:

```sh
python3 labs/architecture/check_invariants.py
```

Os contratos fixos ficam em `financial_contracts.json` e `object_contracts.json`. O runner compara todos os campos esperados antes e depois; ele não aceita apenas que as saídas sejam diferentes. Os controles retiram o resultado protegido durante a execução e corrompem cada campo observado. O teste também remove `shield`, renovação antecipada e reaproveitamento de OPP em cópias temporárias para confirmar a rejeição.

Para executar todos os comandos distintos ligados aos 310 conceitos, use:

```sh
python3 labs/architecture/check_matrix.py
```

Um comando compartilhado roda uma vez e o recibo lista os conceitos que usam sua saída. O sucesso da execução comprova a observação delimitada do modelo. Ele não transforma as comparações de princípio em implementações completas de protocolos, serviços ou arquiteturas.

Para conferir o parsing do MDX produzido por esta frente, use:

```sh
node labs/architecture/check_mdx.mjs
```

As páginas estão em `content/jornadas`, `content/explicacoes/casos`, `content/tutoriais/casos` e `content/guias/casos`. A referência de cada caso é mantida pela frente de referência. Os recibos ficam em `tasks/FBI-4991-arquitetura-nextra/execution/learning`.

O arquivo `extract_historical.py` é uma ferramenta opcional de procedência. Ele lê os SHAs fixados no checkout MakersHub somente de leitura e regenera os snapshots locais; exige acesso àquele histórico. Os snapshots já entregues permitem executar as práticas sem esse checkout. Eles conservam os bytes e comentários da fonte original. O runner de oportunidade compila somente os corpos selecionados da árvore sintática e injeta doubles locais nos pontos de integração; ele não importa o sistema MakersHub inteiro.

A geração editorial usa `author_learning.py` e depois `map_concepts.py`. Execute-os nessa ordem se precisar regenerar as páginas. O primeiro usa as saídas registradas pelo runner; o segundo recompõe os vínculos. Uma alteração no programa exige uma nova execução antes da regeneração. Os scripts de geração não assinam a revisão independente.

As propriedades adicionais estão nos módulos `models_architecture.py`, `models_distribution.py`, `models_concurrency.py`, `models_domain.py`, `models_api.py`, `models_ops.py`, `models_workflow.py` e `models_security.py`. Cada observação informa o conceito, a ação, o resultado e o limite. O mTLS executa handshakes SSLContext em socketpair com certificados efêmeros; o OpenTelemetry executa o SDK fixado e exporta spans para memória. Nenhuma dessas duas práticas altera um serviço externo.
