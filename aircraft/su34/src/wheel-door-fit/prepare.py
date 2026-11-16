"""Generate once with the reviewed Linux toolchain; transfer only through an authenticated draft."""
from common import *
import os,json,urllib.error
repo=os.environ['GITHUB_REPOSITORY'];branch=os.environ['TASK_BRANCH'];tag='su34-wheel-door-fit-20261116';work=Path('prepared');work.mkdir(exist_ok=True);model=generate(baseline(64,work),work);out=work/'Su34_WheelDoorFit_Model.dnm';out.write_bytes(model)
releases=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases'],text=True));release=next((x for x in releases if x['tag_name']==tag),None)
if release is None:
 payload=dict(tag_name=tag,target_commitish=branch,draft=True,name='Су-34: подгонка боковых створок и рамки',body='Подготовка личной сборки; модель только в авторизованном черновике.')
 release=json.loads(subprocess.run(['gh','api','--method','POST',f'repos/{repo}/releases','--input','-'],input=json.dumps(payload),text=True,capture_output=True,check=True).stdout)
assert release['draft'];subprocess.run(['gh','release','upload',tag,str(out),'--clobber','--repo',repo],check=True)
release=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/{release["id"]}'],text=True));asset=next(x for x in release['assets'] if x['name']==out.name)
try:urllib.request.urlopen(asset['browser_download_url'],timeout=20);raise RuntimeError('Private model exposed')
except urllib.error.HTTPError as e:assert e.code==404
print('Reviewed canonical model prepared in authenticated draft:',MODEL)
