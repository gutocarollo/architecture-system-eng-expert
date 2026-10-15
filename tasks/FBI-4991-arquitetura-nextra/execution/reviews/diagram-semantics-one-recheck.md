# Rechecagem delimitada do diagrama 72

**PASS_BOUNDED.** O HIGH D72-DIRECT-EDGE está fechado. A única mudança na página foi substituir a seta de captação para ranking pela seta de dashboard para ranking. O corpo e o PNG atual mostram `fct_captacao` alimentando `fct_advisor_dashboard`, e este alimentando `fct_ranking`, como a captura primária do snapshot de 13/10.

O documento atual tem SHA-256 `8f29603bce6224121926258212263058d4e83b48234a4c5a8477ffae1ca4a42c`. O corpo reparado tem SHA-256 `1077e189725d51f5e09b820a545132ee030ca65697f4ae8b84e19faaa748b6f1`, e o PNG tem SHA-256 `b9f87f91474d94ff6ba8750a4e30e60642eea1796a97096ea3e2639daba4981d`. A captura primária conserva o SHA-256 `7cfe6e8a3dbe814ffd6858b04a7883047d6a9339be9f72430a57104efac4b5c5`; não houve nova medição de fonte.

As outras três fences desta página conservaram os corpos byte por byte. O JSON registra somente a associação delas ao novo hash do documento, preservando os donos e os pareceres anteriores. Os outros 45 julgamentos desta lane e os MEDIUM dos diagramas 42 e 94 não foram reabertos.

O limite continua sendo a representação do snapshot, sem afirmar execução atual, deploy ou frescor dos dados. A única rechecagem autorizada terminou e o revisor fica estacionado.
