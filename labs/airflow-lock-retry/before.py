def task_run_60_days_rule_hs():
    """
    Regra de 60 dias via porta Haskell compilada (SUBSTITUI a versao Python).
    Escreve dim_account_assignment + dim_advisor_coverage (PROD), atomico.
    ~13x mais rapido que o Python (16s vs 214s) e corrige periodos invalidos
    (end<start) e contas multi-current. Mede o pico de RSS (getrusage).
    Fail-loud: qualquer falha derruba a task (esta no caminho critico).
    """
    import json
    import resource
    import subprocess
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
    proc = subprocess.run(
        [binary, '--mode', 'prod', '--json'],
        env=env, capture_output=True, text=True, timeout=300)

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
