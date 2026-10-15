"""Run source-derived queries on a disposable, Unix-socket-only PostgreSQL."""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def source_query(case, condition):
    manifest = json.loads((HERE / 'manifest.json').read_text())[case]['sources'][condition]
    source = (HERE / manifest['template']).read_text()
    assert hashlib.sha256(source.encode()).hexdigest() == manifest['template_sha256']
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/receipt.json')
    parser.add_argument('--case', choices=['all', 'grain', 'revision'], default='all')
    parser.add_argument('--candidate-grain', type=Path)
    parser.add_argument('--candidate-revision', type=Path)
    args = parser.parse_args()
    for command in ['initdb', 'pg_ctl', 'postgres', 'psql']:
        if not shutil.which(command):
            raise SystemExit(f'Missing local prerequisite: {command}')
    cache = ROOT / '.pg-learning'
    cache.mkdir(exist_ok=True)
    report = dict(observed_at=datetime.now(timezone.utc).isoformat(), scope='ISOLATED_SYNTHETIC_POSTGRESQL',
                  production_execution=False, postgres_version=subprocess.check_output(['postgres', '--version'], text=True).strip())
    with tempfile.TemporaryDirectory(prefix='run-', dir=cache) as directory, tempfile.TemporaryDirectory(prefix='arch-pg-', dir='/tmp') as socket_directory:
        temporary = Path(directory)
        data, sockets = temporary / 'data', Path(socket_directory)
        with socket.socket() as candidate:
            candidate.bind(('127.0.0.1', 0))
            port = candidate.getsockname()[1]
        log_path = temporary / 'server.log'
        subprocess.run(['initdb', '-D', str(data), '-U', 'learning_operator', '-A', 'trust', '--locale=C', '--no-instructions'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        with log_path.open('w') as log:
            process = subprocess.Popen(['postgres', '-D', str(data), '-k', str(sockets), '-p', str(port),
                                        '-c', 'listen_addresses=', '-c', 'shared_buffers=16MB', '-c', 'max_connections=10'],
                                       stdout=log, stderr=subprocess.STDOUT)
            command = ['psql', '--no-psqlrc', '--host', str(sockets), '--port', str(port),
                       '--username', 'learning_operator', '--dbname', 'postgres', '--set', 'ON_ERROR_STOP=1', '--tuples-only', '--no-align']

            def sql(statement):
                result = subprocess.run(command + ['--command', statement], text=True, capture_output=True)
                if result.returncode:
                    raise RuntimeError(result.stderr)
                return result.stdout.strip()

            def query_json(statement):
                return json.loads(sql('SELECT COALESCE(json_agg(row_to_json(result)),\'[]\'::json) FROM (' + statement + ') AS result;'))

            try:
                for _ in range(100):
                    probe = subprocess.run(command + ['--command', 'SELECT 1'], capture_output=True)
                    if probe.returncode == 0:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(log_path.read_text())
                    time.sleep(0.05)
                else:
                    raise RuntimeError('The isolated PostgreSQL did not become ready')
                identity = query_json("SELECT current_setting('data_directory') AS data_directory, inet_server_addr() AS server_address")
                assert Path(identity[0]['data_directory']).resolve() == data.resolve()
                assert identity[0]['server_address'] is None
                report['isolation_verified'] = True

                if args.case in ['all', 'grain']:
                    sql('''CREATE TABLE public.rpt_commission__detail(date_key date, account_code integer, office_commission_brl numeric);
                        CREATE TABLE public.rpt_advisor__roa(month_end_date date, account_code integer, monthly_roa numeric);
                        CREATE TABLE public.rpt_advisor__roa_pj1(month_end_date date, account_code integer, net_assets_amount numeric);
                        INSERT INTO public.rpt_commission__detail VALUES ('2026-01-15',101,100);
                        INSERT INTO public.rpt_advisor__roa VALUES ('2026-01-31',101,0.01),('2026-01-31',101,0.01);
                        INSERT INTO public.rpt_advisor__roa_pj1 VALUES ('2026-01-31',101,1000000),('2026-01-31',101,1000000);''')
                    family = "WITH fam AS (SELECT 101::integer AS account_code, 'SYNTHETIC-FAMILY'::text AS name, 'SYNTHETIC-CLUSTER'::text AS cluster)"
                    grain = {}
                    for condition in ['before', 'after']:
                        query = args.candidate_grain.read_text() if condition == 'after' and args.candidate_grain else source_query('grain', condition)
                        query = query.replace(':start_date', "DATE '2026-01-01'").replace(':end_date', "DATE '2026-01-31'")
                        rows = query_json(family + query)
                        grain[condition] = dict(rows=len(rows), commission_sum=sum(row['commission'] for row in rows), results=rows)
                    assert grain['before']['rows'] == 2 and grain['before']['commission_sum'] == 200
                    assert grain['after']['rows'] == 1 and grain['after']['commission_sum'] == 100, grain['after']
                    assert grain['after']['results'][0]['net_assets'] == 1000000
                    report['grain'] = grain

                if args.case in ['all', 'revision']:
                    revision = {}
                    for condition in ['before', 'after']:
                        sql('''DROP TABLE IF EXISTS public.learning_employee;
                            CREATE TABLE public.learning_employee(_employee_id integer PRIMARY KEY, employee_id text,
                                azure_id text, is_current boolean, valid_to timestamptz);
                            CREATE UNIQUE INDEX learning_employee_current ON public.learning_employee(employee_id) WHERE is_current;
                            INSERT INTO public.learning_employee VALUES (1,'SYNTHETIC-EMPLOYEE','AZURE-OLD',TRUE,NULL);''')
                        read_revision = sql("SELECT _employee_id::text || ':' || xmin::text FROM public.learning_employee WHERE is_current")
                        sql("UPDATE public.learning_employee SET azure_id='AZURE-CONFIRMED' WHERE is_current")
                        template = args.candidate_revision.read_text() if condition == 'after' and args.candidate_revision else source_query('revision', condition)
                        query = template.format(EMPLOYEE_TABLE='public.learning_employee', FIELD_IS_CURRENT='is_current',
                                                FIELD_VALID_TO='valid_to', FIELD_EMPLOYEE_ID='employee_id', concurrency_predicate='')
                        query = query.replace(':current_timestamp', "TIMESTAMPTZ '2026-01-15T10:00:00Z'")
                        query = query.replace(':employee_id', "'SYNTHETIC-EMPLOYEE'").replace(':source_revision', "'" + read_revision + "'")
                        if condition == 'before':
                            sql(query)
                            rejected = False
                        elif 'RETURNING' in query.upper():
                            closed = json.loads(sql("WITH closed AS (" + query + ") SELECT COALESCE(json_agg(row_to_json(closed)), '[]'::json) FROM closed"))
                            rejected = len(closed) == 0
                        else:
                            affected = int(sql(query).splitlines()[-1].split()[-1])
                            rejected = affected == 0
                        if not rejected:
                            sql("INSERT INTO public.learning_employee VALUES (2,'SYNTHETIC-EMPLOYEE','AZURE-OLD',TRUE,NULL)")
                        row = query_json('SELECT azure_id, (SELECT COUNT(*) FROM public.learning_employee WHERE is_current) AS current_rows FROM public.learning_employee WHERE is_current')[0]
                        revision[condition] = dict(stale_writer_rejected=rejected, **row)
                    assert revision['before'] == dict(stale_writer_rejected=False, azure_id='AZURE-OLD', current_rows=1)
                    assert revision['after'] == dict(stale_writer_rejected=True, azure_id='AZURE-CONFIRMED', current_rows=1), revision['after']
                    report['revision'] = revision
                report['verdict'] = 'PASS'
            finally:
                subprocess.run(['pg_ctl', '-D', str(data), '-m', 'immediate', 'stop'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait(timeout=15)
    report['temporary_server_stopped'] = True
    report['source_manifest'] = json.loads((HERE / 'manifest.json').read_text())
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    if 'grain' in report:
        print('grain: before_rows=2 before_commission=200 after_rows=1 after_commission=100')
    if 'revision' in report:
        print('revision: before_current_rows=1 lost_azure_update=True after_current_rows=1 stale_writer_rejected=True')
    print('comparison=PASS isolation_verified=True temporary_server_stopped=True')


if __name__ == '__main__':
    main()
