from pathlib import Path
import os,sys,subprocess,zipfile,json,shutil,hashlib,re,struct
code=Path(__file__).resolve().parent
root=Path('su34-quick-build').resolve();root.mkdir(exist_ok=True)
repo=os.environ['GITHUB_REPOSITORY'];tag='su34-import-quicktest-x86-20261123'
def run(args,**kw):subprocess.run(list(map(str,args)),check=True,**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def download(a,p):
    with p.open('wb') as f:run(['gh','api',f'repos/{repo}/releases/assets/{a}','-H','Accept: application/octet-stream'],stdout=f)
if sys.argv[1]=='prepare':
    for a,n in [(762537191,'sources.zip'),(779458760,'base-game.zip'),(779686356,'model.zip')]:download(a,root/n)
    assert sha(root/'model.zip')=='df72f7b90544610d64574c83df31759feaaac203a9ee6edc5711d3f66d98e59f'
    with zipfile.ZipFile(root/'sources.zip') as z:
        for n in z.namelist():
            if n.startswith('engine/') and not n.endswith('/'):z.extract(n,root)
    run(['patch','--batch','--forward','-p1','-i',code/'engine.patch'],cwd=root/'engine')
    with zipfile.ZipFile(root/'model.zip') as z:z.extractall(root/'unpacked')
    with zipfile.ZipFile(root/'unpacked/source/su-34-war-thunder.zip') as z:z.extractall(root/'inner')
    with zipfile.ZipFile(root/'inner/source/Su-34.zip') as z:z.extractall(root/'model')
    for n in ['export.py','setup_runtime.py']:shutil.copyfile(code/n,root/n)
    run([sys.executable,root/'export.py']);run([sys.executable,root/'setup_runtime.py'])
    dat=root/'game/runtime/aircraft/su34_import.dat';s=dat.read_text()
    s=re.sub(r'^COCKPITP .*$', 'COCKPITP -.49m 1.00m 7.56m',s,flags=re.M)
    s+='\nINITZOOM 0.85\nCOCKPITA 0deg -8deg 0deg\nSCRNCNTR 0 0\nINSTPANL aircraft/su34_import/empty.ist\n'
    dat.write_text(s)
    (root/'game/runtime/aircraft/su34_import/empty.ist').write_text('REM Imported 3D cockpit\nPNLRANGE 0 0 0 0\n')
    (root/'engine/mingw32.cmake').write_text('set(CMAKE_SYSTEM_NAME Windows)\nset(CMAKE_SYSTEM_PROCESSOR x86)\nset(CMAKE_C_COMPILER i686-w64-mingw32-gcc-posix)\nset(CMAKE_CXX_COMPILER i686-w64-mingw32-g++-posix)\nset(CMAKE_RC_COMPILER i686-w64-mingw32-windres)\n')
elif sys.argv[1]=='package':
    rt=root/'game/runtime';package=root/'Su34_QuickTest_Windows_32bit';dst=package/'runtime';dst.mkdir(parents=True,exist_ok=True)
    for n in ['config','language','licenses','document','ground','scenery','sound','misc']:
        if (rt/n).is_dir():shutil.copytree(rt/n,dst/n,dirs_exist_ok=True)
    option=dst/'config/option.cfg'
    opts=option.read_text()
    opts=re.sub(r'^OPENDEMO .*$', 'OPENDEMO FALSE',opts,flags=re.M)
    opts=re.sub(r'^LANGUAGE .*$', 'LANGUAGE "FILE:ru.uitxt"',opts,flags=re.M)
    opts=re.sub(r'^FONTHEIGHT .*$', 'FONTHEIGHT 18',opts,flags=re.M)
    option.write_text(opts)
    for n in ['20181124','readme.txt','ereadme.txt','jreadme.txt']:
        if (rt/n).is_file():shutil.copyfile(rt/n,dst/n)
    air=dst/'aircraft';air.mkdir(exist_ok=True)
    shutil.copytree(rt/'aircraft/su34_import',air/'su34_import')
    for n in ['su34_import.dat','su34_import_fallback.dnm','su34coll.srf','su34cockpit.srf']:shutil.copyfile(rt/'aircraft'/n,air/n)
    (air/'aircraft.lst').write_text('aircraft/su34_import.dat aircraft/su34_import_fallback.dnm aircraft/su34coll.srf aircraft/su34cockpit.srf aircraft/su34_import_fallback.dnm\n')
    for n in ['Su34_Import_Test.yfs','Start_Su34_Import.script']:shutil.copyfile(rt/n,dst/n)
    exe=root/'build32/main/ysflight32_gl1.exe';data=exe.read_bytes();pe=struct.unpack_from('<I',data,60)[0];assert struct.unpack_from('<H',data,pe+4)[0]==0x14c
    shutil.copyfile(exe,dst/exe.name)
    plugin=dst/'plugin';plugin.mkdir()
    for f in (root/'build32').rglob('*.dll'):shutil.copyfile(f,plugin/f.name)
    assert list(plugin.glob('*.dll'))
    (package/'PLAY_SU34.bat').write_bytes(b'@echo off\r\ncd /d "%~dp0runtime"\r\nstart "" "ysflight32_gl1.exe" -userdir "%~dp0user" -configdir "%CD%\\config" -script Start_Su34_Import.script\r\n')
    notice='Тест новой модели Су-34 — Windows 32-bit.\nРаспакуйте весь ZIP, затем запустите PLAY_SU34.bat. Самолёт появится в воздухе, вид из кабины.\nF1 — вид из кабины, Pause/Break — пауза, Esc — меню. Остальные клавиши см. в документации игры.\nКамера ближе к приборам, высота сохранена. Ориентация и освещение исправлены.\nЭто проба переноса: кнопки, приборы и механизмы новой модели пока статические; динамика и коллизия унаследованы от прежнего самолёта. Нужен OpenGL2.1/GLSL.\n'
    (package/'START_HERE_RU.txt').write_text(notice,encoding='utf-8-sig')
    # Keep corresponding engine source alongside the binary, without bundling model assets publicly.
    sources=root/'Su34_QuickTest_CorrespondingSources.zip'
    with zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as z:
        for p in (root/'engine').rglob('*'):
            if p.is_file():z.write(p,'engine/'+str(p.relative_to(root/'engine')))
        for p in code.iterdir():
            if p.is_file():z.write(p,'import-test-delivery/'+p.name)
        z.writestr('REBUILD.txt','Use the included workflow and source, original model.zip and base-game.zip assets referenced by deliver_quick.py. The model is kept separate.\n')
    game=root/'Su34_QuickTest_Windows_32bit.zip'
    with zipfile.ZipFile(game,'w',zipfile.ZIP_DEFLATED,6) as z:
        for p in package.rglob('*'):
            if p.is_file():z.write(p,str(p.relative_to(package)))
    with zipfile.ZipFile(game) as z:assert z.testzip() is None
    manifest={'game_sha256':sha(game),'sources_sha256':sha(sources),'exe_sha256':sha(exe),'mesh_sha256':sha(dst/'aircraft/su34_import/aircraft.mesh'),'machine':'PE32 i386','eye':[-.49,1.,7.56],'pitch_degrees':-8,'zoom':.85,'runtime_aircraft':1,'static_import':True}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in [game,sources]))
    release=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/454987447'],text=True));assert release['draft']
    run(['gh','release','upload',tag,game,sources,root/'SHA256SUMS.txt',root/'manifest.json','--repo',repo])
    release=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/454987447'],text=True))
    for p in [game,sources]:
        asset=next(a for a in release['assets'] if a['name']==p.name);assert asset['digest']=='sha256:'+sha(p)
    print(json.dumps(manifest,indent=2))
else:raise ValueError('prepare or package')
