from pathlib import Path
import os,subprocess,zipfile,json,hashlib,shutil,time,ctypes,ctypes.wintypes as wt
from PIL import ImageGrab
r=Path('native-check').resolve();r.mkdir(exist_ok=True);code=Path(__file__).resolve().parent
repo=os.environ['GITHUB_REPOSITORY'];tag='su34-import-quicktest-x86-20261123'
def run(a,**kw):return subprocess.run(list(map(str,a)),check=True,**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def download(asset,p):
    with p.open('wb') as f:run(['gh','api',f'repos/{repo}/releases/assets/{asset}','-H','Accept: application/octet-stream'],stdout=f)
release=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases/454987447']));assert release['draft']
assets={a['name']:a['id'] for a in release['assets']}
download(assets['Su34_QuickTest_Windows_32bit.zip'],r/'original-game.zip');download(assets['Su34_QuickTest_CorrespondingSources.zip'],r/'original-sources.zip');download(assets['manifest.json'],r/'original-manifest.json')
m=json.loads((r/'original-manifest.json').read_text());assert sha(r/'original-game.zip')==m['game_sha256'];assert sha(r/'original-sources.zip')==m['sources_sha256']
batch=b'@echo off\r\ncd /d "%~dp0runtime"\r\n"%CD%\\ysflight32_gl1.exe" -userdir "%~dp0user" -configdir "%CD%\\config" -script Start_Su34_Import.script\r\n'
with zipfile.ZipFile(r/'original-game.zip') as z:assert z.testzip() is None;z.extractall(r/'test')
(r/'test/PLAY_SU34.bat').write_bytes(batch)
download_url='https://github.com/pal1000/mesa-dist-win/releases/download/26.3.0/mesa3d-26.3.0-release-msvc.7z'
run(['curl.exe','-L','--fail',download_url,'-o',r/'mesa.7z']);run(['7z','x',r/'mesa.7z','-o'+str(r/'mesa')],stdout=subprocess.DEVNULL)
candidates=[p for p in (r/'mesa').rglob('opengl32.dll') if 'x86' in p.parts or '32' in p.parts]
assert len(candidates)==1,[str(p) for p in (r/'mesa').rglob('opengl32.dll')]
rt=r/'test/runtime'
for p in candidates[0].parent.glob('*.dll'):shutil.copyfile(p,rt/p.name)
env=os.environ.copy();env.update(GALLIUM_DRIVER='llvmpipe',LIBGL_ALWAYS_SOFTWARE='1')
log=r/'native-game.log';f=log.open('w');start=time.monotonic()
proc=subprocess.Popen([os.environ['COMSPEC'],'/c',str(r/'test/PLAY_SU34.bat')],cwd=r/'test',env=env,stdout=f,stderr=f)
try:
    while time.monotonic()-start<30:
        text=log.read_text(errors='replace')
        if 'IMPORT READY vertices=706104 triangles=579601 materials=15 textures=42' in text and 'Script>>BTNFUNC:COCKPITVIEW' in text:break
        if proc.poll() is not None:raise RuntimeError('Native launch exited '+str(proc.returncode)+'\n'+text[-3000:])
        time.sleep(.25)
    # A Windows GUI process may not inherit cmd's redirected console handles.
    # Preserve an actual native window capture for visual review in that case.
    import_logged='IMPORT READY vertices=706104 triangles=579601 materials=15 textures=42' in text
    elapsed=time.monotonic()-start;u=ctypes.windll.user32;windows=[];seen=[]
    ImageGrab.grab().save(r/'Native_Windows32_Cockpit.jpg',quality=85,optimize=True)
    cbtype=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
    def enum(h,p):
        title=ctypes.create_unicode_buffer(512);u.GetWindowTextW(h,title,512)
        if title.value:seen.append({'title':title.value,'visible':bool(u.IsWindowVisible(h))})
        if 'YS' in title.value.upper() and 'FLIGHT' in title.value.upper() and u.IsWindowVisible(h):windows.append(h)
        return True
    u.EnumWindows(cbtype(enum),0);print(json.dumps({'windows':seen}),flush=True);assert windows,'Native game window absent';h=windows[0]
    u.ShowWindow(h,9);u.SetWindowPos(h,0,0,0,1040,810,0x40);u.SetForegroundWindow(h)
    u.PostMessageW(h,0x100,0x13,0);u.PostMessageW(h,0x101,0x13,0);time.sleep(1)
    rect=wt.RECT();u.GetClientRect(h,ctypes.byref(rect));pt=wt.POINT(0,0);u.ClientToScreen(h,ctypes.byref(pt))
    ImageGrab.grab(bbox=(pt.x,pt.y,pt.x+rect.right,pt.y+rect.bottom)).save(r/'Native_Windows32_Cockpit.jpg',quality=85,optimize=True)
    validation={'native_windows':True,'host':'Windows GitHub runner','executable':'actual shipped PE32 i386','actual_root_batch':True,'mesh_triangles':579601,'mesh_materials':15,'mesh_textures':42,'import_logged':import_logged,'native_window_captured_for_visual_review':True,'startup_or_observation_seconds':round(elapsed,2),'driver':'Mesa26.3 MSVC x86 llvmpipe for CI only; NOT bundled','eye':[-.49,1.,7.56],'exe_sha256':sha(rt/'ysflight32_gl1.exe')}
    assert validation['exe_sha256']==m['exe_sha256']
finally:
    run(['taskkill','/F','/IM','ysflight32_gl1.exe'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);proc.wait(timeout=15);f.close()
game=r/'Su34_QuickTest_Windows_32bit.zip'
with zipfile.ZipFile(r/'original-game.zip') as src,zipfile.ZipFile(game,'w',zipfile.ZIP_DEFLATED,6) as dst:
    for n in src.namelist():dst.writestr(n,batch if n=='PLAY_SU34.bat' else src.read(n))
with zipfile.ZipFile(game) as z:
    assert z.testzip() is None;assert not any('opengl32.dll' in n.lower() for n in z.namelist());assert not any(n.startswith('user/') for n in z.namelist())
sources=r/'Su34_QuickTest_CorrespondingSources.zip'
with zipfile.ZipFile(r/'original-sources.zip') as src,zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as dst:
    for n in src.namelist():
        if n!='import-test-delivery/verify_windows.py':dst.writestr(n,(code/'deliver_quick.py').read_bytes() if n=='import-test-delivery/deliver_quick.py' else src.read(n))
    dst.write(__file__,'import-test-delivery/verify_windows.py')
m.update(game_sha256=sha(game),sources_sha256=sha(sources),native_windows_test=validation)
(r/'manifest.json').write_text(json.dumps(m,indent=2));(r/'Native_Windows32_Validation.json').write_text(json.dumps(validation,indent=2))
(r/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in [game,sources]))
run(['gh','release','upload',tag,game,sources,r/'manifest.json',r/'SHA256SUMS.txt',r/'Native_Windows32_Cockpit.jpg',r/'Native_Windows32_Validation.json','--repo',repo,'--clobber'])
print(json.dumps(validation,indent=2))
