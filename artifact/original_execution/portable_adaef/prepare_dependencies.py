"""Declare installed C++ header identities for a new build; never install tools."""
import argparse,hashlib,json,re
from pathlib import Path
def record(eigen,boost):
    ep=eigen/'Eigen/src/Core/util/Macros.h';bp=boost/'boost/version.hpp';e=ep.read_bytes();b=bp.read_bytes()
    def macro(raw,name):
        match=re.search(rb'^\s*#\s*define\s+'+name.encode()+rb'\s+(\d+)\s*$',raw,re.M)
        if not match:raise ValueError('Version macro missing: '+name)
        return int(match.group(1))
    ev='.'.join(str(macro(e,'EIGEN_'+x+'_VERSION')) for x in ('WORLD','MAJOR','MINOR'));bv=macro(b,'BOOST_VERSION')
    if ep.read_bytes()!=e or bp.read_bytes()!=b:raise ValueError('Dependency header changed during capture')
    return {'eigen_include':str(eigen.resolve()),'boost_include':str(boost.resolve()),'eigen_version_header_sha256':hashlib.sha256(e).hexdigest(),'boost_version_header_sha256':hashlib.sha256(b).hexdigest(),'eigen_version':ev,'boost_version':f'{bv//100000}.{bv//100%1000}.{bv%100}','provenance':'NEW_BUILD_DEPENDENCY_DECLARATION_NOT_HISTORICAL_IDENTITY'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--eigen-include',type=Path,default=Path('/usr/include/eigen3'));p.add_argument('--boost-include',type=Path,default=Path('/usr/include'));a=p.parse_args()
    if a.output.exists():raise FileExistsError('New-only dependency declaration')
    result=record(a.eigen_include,a.boost_include)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('eigen_version','boost_version','provenance')}))
if __name__=='__main__':main()
