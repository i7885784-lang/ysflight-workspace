from pathlib import Path
import os,json,base64,zlib,subprocess,zipfile,sys,hashlib,struct
r=Path('delivery');r.mkdir(exist_ok=True)
repo=os.environ['GITHUB_REPOSITORY'];sha=lambda b:hashlib.sha256(b).hexdigest()
def download(asset,path):
 with path.open('wb') as f:subprocess.run(['gh','api',f'repos/{repo}/releases/assets/{asset}','-H','Accept: application/octet-stream'],stdout=f,check=True)
download(762565494,r/'base.zip');download(762537191,r/'sources.zip')
with zipfile.ZipFile(r/'sources.zip') as z:
 for name in ['dnm.py','mesh.py']:(r/name).write_bytes(z.read('su34-intake-front/'+name))
sys.path.insert(0,str(r.resolve()));import dnm
event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());raw=event['inputs']['patch'];patch=json.loads(zlib.decompress(base64.b64decode(raw)))
with zipfile.ZipFile(r/'base.zip') as z:(r/'base.dnm').write_bytes(z.read('runtime/aircraft/su34.dnm'))
p,ns=dnm.read(r/'base.dnm');m=dnm.mesh(p['ConformalWingRootBaySides.srf']);keys=list(dict.fromkeys(m.v));assert len(keys)==len(patch['fairing']);mapping=dict(zip(keys,map(tuple,patch['fairing'])));m.v=[mapping[v] for v in m.v];normals=iter(patch['fairing_normals']);p['ConformalWingRootBaySides.srf']=[next(normals) if s.startswith('N ') else s for s in m.srf()]
m=dnm.mesh(p['SourceAirframe.srf'])
for points,color,bright in patch['append']:m.face(points,tuple(color),bright)
p['SourceAirframe.srf']=m.srf();dnm.write(r/'su34.dnm',p,ns);model=(r/'su34.dnm').read_bytes()
assert sha(model)==event['inputs']['model_sha'], 'Model must match the locally reviewed candidate'
cn=[n for n in ns if dnm.name(n) in ['Source_chassis','Source_dials','Source_steeringwheel','OwnCockpitLiner']];dnm.write(r/'su34cockpit.dnm',{dnm.fil(n):p[dnm.fil(n)] for n in cn},cn)
report=Path('delivery-code/REPORT_RU.txt').read_bytes();game=r/'Su34_VisualRepair_Preview_Windows_x86.zip'
with zipfile.ZipFile(r/'base.zip') as src,zipfile.ZipFile(game,'w',zipfile.ZIP_DEFLATED,6) as dst:
 dat=src.read('runtime/aircraft/su34.dat').decode().replace('\r\n','\n').replace('COCKPITP -.42m 1.12m 5.72m','COCKPITP -.39m 1.02m 5.05m').encode()
 registry=src.read('runtime/aircraft/aircraft.lst').decode().replace('\r\n','\n').replace('aircraft/su34cockpit.srf','aircraft/su34cockpit.dnm').encode()
 repl={'runtime/aircraft/su34.dnm':model,'runtime/aircraft/su34_coarse.dnm':model,'runtime/aircraft/su34.dat':dat,'runtime/aircraft/aircraft.lst':registry}
 for name in src.namelist():
  if not name.endswith('/'):dst.writestr(name,repl.get(name,src.read(name)))
 dst.writestr('runtime/aircraft/su34cockpit.dnm',(r/'su34cockpit.dnm').read_bytes());dst.writestr('Su34_VisualRepair_REPORT_RU.txt',report)
with zipfile.ZipFile(game) as z:
 assert z.testzip() is None
 exe=z.read('runtime/ysflight32_gl1.exe');off=struct.unpack_from('<I',exe,60)[0];assert struct.unpack_from('<H',exe,off+4)[0]==0x14c
 with zipfile.ZipFile(r/'base.zip') as src:
  changes=[name for name in src.namelist() if not name.endswith('/') and src.read(name)!=z.read(name)]
  assert sorted(changes)==sorted(repl)
sources=r/'Su34_VisualRepair_CorrespondingSources.zip'
with zipfile.ZipFile(r/'sources.zip') as src,zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as dst:
 for name in src.namelist():
  if not name.endswith('/'):dst.writestr(name,src.read(name))
 dst.writestr('su34-visual-repair/private-patch.json',json.dumps(patch));dst.write(__file__,'su34-visual-repair/deliver.py');dst.writestr('su34-visual-repair/su34.dnm',model);dst.writestr('su34-visual-repair/su34.dat',dat);dst.write(r/'su34cockpit.dnm','su34-visual-repair/su34cockpit.dnm');dst.writestr('su34-visual-repair/REPORT_RU.txt',report)
photos=Path('delivery-code/Su34_VisualRepair_Photos.zip');sums=r/'SHA256SUMS.txt';sums.write_text(''.join(sha(f.read_bytes())+'  '+f.name+'\n' for f in [game,sources,photos]))
tag='su34-visual-repair-preview-20261122';release=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/454527029'],text=True));assert release['draft']
subprocess.run(['gh','release','upload',tag,str(game),str(sources),str(photos),str(sums),'delivery-code/REPORT_RU.txt','--repo',repo,'--clobber'],check=True)
assets=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/454527029'],text=True))['assets']
for f in [game,sources,photos]:
 asset=next(a for a in assets if a['name']==f.name);assert asset['digest']=='sha256:'+sha(f.read_bytes())
 download(asset['id'],r/('verified-'+f.name));assert sha((r/('verified-'+f.name)).read_bytes())==sha(f.read_bytes())
print('Verified model',sha(model));print('Verified game/source/photo uploads and download hashes; draft only')
