from pathlib import Path
import sys,subprocess,time,ctypes as C,ctypes.wintypes as W,json,re,base64,os
from PIL import ImageGrab,ImageChops
from common import *
bits=int(sys.argv[1]);work=Path('native')/str(bits);work.mkdir(parents=True,exist_ok=True);p=baseline(bits,work);model=generate(p,work)
with zipfile.ZipFile(p) as z:z.extractall(work)
rt=work/'runtime';(rt/'aircraft/su34.dnm').write_bytes(model);(rt/'aircraft/su34_coarse.dnm').write_bytes(model);exe=(rt/f'ysflight{bits}_gl1.exe').resolve();pe(exe.read_bytes(),bits)
profile=(work/'profile').resolve();(profile/'config').mkdir(parents=True,exist_ok=True);(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
yfs=work/'start.yfs';yfs.write_text('YFSVERSI 20180930\nFIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE\nINITPLYR AIR 1\nCANCONTI TRUE\nENVIRONM DAY\nEXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35\nAIRPLANE SU-34_FULLBACK TRUE\nIDENTIFY 0\nIDANDTAG 1 "SU34_SEAM"\nAIRPCMND UNLOADWP\nAIRPCMND INITFUEL 50%\nAIRPCMND POSITION 0m 2500m 0m\nAIRPCMND ATTITUDE 0deg 0deg 0deg\nAIRPCMND INITSPED 160m/s\nAIRPCMND CTLLDGEA TRUE\nAIRPCMND CTLTHROT 0.4\n')
script=work/'run.script';script.write_text('WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:5000\nFILE:OPEN '+yfs.resolve().as_posix()+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nBTNFUNC:PAUSESIMULATION\nBTNFUNC:OUTSIDEPLAYERVIEW\n'+'BTNFUNC:VIEWZOOM\n'*18+'REM READY\n'+('FLIGHTCMD:REPORT\nFLIGHTCMD:MODELCHECK\nSLEEP:100\n'*600)+'SLEEP:60000\n')
log=work/'game.log';f=log.open('w');game=subprocess.Popen([str(exe),'-userdir',str(profile),'-configdir',str(profile/'config'),'-script',str(script.resolve())],cwd=rt,stdout=f,stderr=f);u=C.windll.user32
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.IsWindowVisible.argtypes=[W.HWND];u.SetForegroundWindow.argtypes=[W.HWND];u.SetWindowLongW.argtypes=[W.HWND,C.c_int,C.c_long];u.MoveWindow.argtypes=[W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.BOOL]
def wait(s):
 end=time.monotonic()+100
 while time.monotonic()<end:
  if s in log.read_text(errors='replace'):return
  if game.poll() is not None:raise RuntimeError('Game exited')
  time.sleep(.1)
 raise RuntimeError(s)
def tap(k):u.keybd_event(k,0,0,0);time.sleep(.6);u.keybd_event(k,0,2,0);time.sleep(.3)
def shot(name):
 im=ImageGrab.grab();im.save(work/(name+'.png'));return im
try:
 wait('Script>>SLEEP:5000');wins=[]
 @C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
 def each(hwnd,param):
  pid=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(pid))
  if pid.value==game.pid and u.IsWindowVisible(hwnd):wins.append(hwnd)
  return True
 u.EnumWindows(each,0);assert wins;h=wins[-1];u.SetWindowLongW(h,-16,0x90000000);u.MoveWindow(h,0,0,1024,768,True);u.SetForegroundWindow(h)
 wait('Script>>REM READY');time.sleep(.3);down=shot('down');tap(0x13);tap(0x47);time.sleep(10);up=shot('up');tap(0x47);time.sleep(10);back=shot('down-again');assert ImageChops.difference(down,up).getbbox() is not None
 text=log.read_text(errors='replace');states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in text.splitlines() if s.startswith('MODELCHECK ')]
 if bits==64:
  assert states and min(float(s['gear']) for s in states)<.05 and float(states[-1]['gear'])>.95
 result=dict(passed=True,bits=bits,native_windows=True,model_sha256=MODEL,exe_sha256=sha(exe.read_bytes()),scope='Actual G retraction and extension, images; x64 gear telemetry, x86 launch/keys/images',states=states)
 def upload(path,content):
  data=dict(message='Su34 actual Windows gear-cycle evidence',branch=os.environ['TASK_BRANCH'],content=base64.b64encode(content).decode())
  for attempt in range(4):
   p=subprocess.run(['gh','api','--method','PUT',f'repos/{os.environ["GITHUB_REPOSITORY"]}/contents/{path}','--input','-'],input=json.dumps(data),text=True,capture_output=True)
   if p.returncode==0:return
   time.sleep(1)
  raise RuntimeError(p.stderr)
 for name in ['down','up','down-again']:upload(f'screenshots/su34-intake-front/native-{bits}-{name}.png',(work/(name+'.png')).read_bytes())
 upload(f'aircraft/su34/work/intake-front/native-{bits}.json',json.dumps(result,indent=2).encode())
finally:
 game.terminate()
 try:game.wait(timeout=10)
 except subprocess.TimeoutExpired:game.kill()
 f.close()
