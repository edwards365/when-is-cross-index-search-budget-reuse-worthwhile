import os,platform,sys,json
from pathlib import Path
GIB=1<<30
def preflight(cfg,output,sources,growth):
    if platform.system()!='Linux' or list(sys.version_info[:2])!=cfg['python_minor'] or sys.flags.optimize:
        raise ValueError('Preparation requires Linux / Python 3.11, without -O')
    plan=cfg['resource_plan']
    if output.exists() or output.is_symlink():raise FileExistsError('Exclusive output exists')
    parent=output.parent.resolve(strict=True);out=parent/output.name
    if output.name in ('','..','.') or any(p.resolve(strict=True).is_relative_to(out) for p in sources.values()):
        raise ValueError('Output conflicts with inputs')
    if not plan['max_output_growth_bytes']<=growth<=plan['remaining_project_growth_limit_bytes']:
        raise ValueError('Invalid total outstanding growth; include this stage')
    import time
    mem={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if ':' in s}
    rss=0;unreadable=0
    for p in Path('/proc').glob('[0-9]*/status'):
        try:
            rss+=sum(int(s.split()[1])*1024 for s in p.read_text().splitlines() if s.startswith('VmRSS:'))
        except (OSError,ValueError):unreadable+=1
    stat=lambda:list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    first=stat();time.sleep(.2);diff=[b-a for a,b in zip(first,stat())]
    iowait=diff[4]/sum(diff) if sum(diff)>0 else None
    v=os.statvfs(parent);free=v.f_bavail*v.f_frsize
    if mem['MemAvailable']<160*GIB or mem['MemAvailable']-plan['expected_rss_bytes']<80*GIB:
        raise OSError('RAM availability floor')
    if rss+64*GIB>.6*mem['MemTotal']:raise OSError('Machine RSS/reserve gate')
    if free-growth<plan['minimum_projected_disk_free_bytes']:raise OSError('Projected disk floor')
    if iowait is None or iowait>=.15:raise OSError('I/O wait gate')
    cpus=set(plan['cpu_affinity'])
    if not cpus.issubset(os.sched_getaffinity(0)):raise OSError('Unavailable historical CPU affinity')
    return out,{'available_ram_bytes':mem['MemAvailable'],'observed_machine_rss_bytes':rss,
                'unreadable_proc_status':unreadable,'disk_free_bytes':free,'declared_outstanding_growth':growth,
                'iowait':iowait,'snapshot_not_continuous_quota':True}

def write_json(path,data):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
