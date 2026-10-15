def task_run_60_days_rule_hs():
    """
    Regra de 60 dias via porta Haskell compilada (SUBSTITUI a versao Python).
    Escreve dim_account_assignment + dim_advisor_coverage (PROD), atomico.
    ~13x mais rapido que o Python (16s vs 214s) e corrige periodos invalidos
    (end<start) e contas multi-current. Mede o pico de RSS (getrusage).
    Fail-loud: qualquer falha derruba a task (esta no caminho critico). Unica
    excecao: lock timeout do Postgres (55P03), repetido ate 2 vezes (FBI-4797).
    """
    import json
    import resource
    import subprocess
    import time
    from urllib.parse import quote

    binary = os.path.join(
        toolkit_path, 'sixty_days_rule_hs', 'bin', 'sixty-days-rule')
    if not os.path.exists(binary):
        raise FileNotFoundError(
            "Binario Haskell ausente em %s (rebuild via "
            "toolkit/captable_processing_utils/sixty_days_rule_hs)" % binary)

    c = get_postgres_hook().get_connection('postgres_prod')
    uri = "postgresql://{u}:{p}@{h}:{port}/{db}".format(
        u=quote(c.login or '', safe=''),
        p=quote(c.password or '', safe=''),
        h=c.host, port=c.port or 5432, db=c.schema)

    env = {**os.environ, 'PG_CONN_STRING': uri}
    # 55P03 = lock_timeout (60 s) do Postgres: o TRUNCATE de dim_account_assignment e
    # dim_advisor_coverage espera todo leitor terminar, e uma consulta longa naquelas
    # tabelas estoura a espera (05/10 22:32 UTC, 1 em 6 runs). A escrita e atomica (uma
    # transacao, a falha desfaz tudo) e idempotente: repetir e seguro. So esse erro
    # repete; qualquer outro derruba a task na hora.
    lock_retries, lock_retry_delay_s = 2, 30
    attempt = 0
    while True:
        proc = subprocess.run(
            [binary, '--mode', 'prod', '--json'],
            env=env, capture_output=True, text=True, timeout=300)
        lock_timeout = proc.returncode != 0 and '55P03' in (proc.stderr or '')
        if not lock_timeout or attempt >= lock_retries:
            break
        attempt += 1
        logger.warning(
            "[HASKELL 60d PROD] lock timeout (55P03) na escrita atomica; "
            "tentativa %s/%s em %ss", attempt, lock_retries, lock_retry_delay_s)
        time.sleep(lock_retry_delay_s)

    peak_mb = round(
        resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0, 1)

    if proc.returncode != 0:
        logger.error("[HASKELL 60d PROD] rc=%s stderr=%s",
                     proc.returncode, (proc.stderr or '')[-3000:])
        raise RuntimeError(
            "Haskell run_60_days_rule (prod) falhou rc=%s" % proc.returncode)

    last = (proc.stdout or '').strip().splitlines()[-1:] or ['{}']
    result = json.loads(last[0])
    result['peak_rss_mb'] = peak_mb
    logger.info("[HASKELL 60d PROD] %s", result)
    return result
