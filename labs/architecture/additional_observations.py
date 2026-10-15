"""Load case-specific models once per process and preserve their narrow contracts."""
from functools import lru_cache
import importlib

MODULE_CASES={
    'models_architecture':{'order-boundaries','cache-policy'},
    'models_distribution':{'consensus','reservation','order-delivery','storage-partitions'},
    'models_concurrency':{'reservation'},
    'models_domain':{'order-boundaries'},
    'models_api':{'order-boundaries'},
    'models_ops':{'consensus','queue-workflow','safe-release','diagnostics'},
    'models_workflow':{'queue-workflow'},
    'models_security':{'access-policy'},
}

@lru_cache(maxsize=None)
def for_case(case):
    result=[]
    for name,cases in MODULE_CASES.items():
        if case not in cases:continue
        module=importlib.import_module(name)
        rows=module.observations(case) if name=='models_ops' else module.observations()
        for row in rows:
            if row['case']==case:
                row['source_file']='labs/architecture/'+name+'.py'
                result.append(row)
    return tuple(result)

def all_observations():
    for case in sorted(set().union(*MODULE_CASES.values())):
        yield from for_case(case)
