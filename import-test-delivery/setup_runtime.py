from pathlib import Path
import zipfile,shutil,json,os
r=Path(__file__).resolve().parent
baseline=Path(os.environ.get('BASE_GAME_ZIP',str(r/'base-game.zip')))
with zipfile.ZipFile(baseline) as z:z.extractall(r/'game')
rt=r/'game/runtime';air=rt/'aircraft';shutil.copytree(r/'payload',air/'su34_import',dirs_exist_ok=True)
dat=(air/'su34.dat').read_text().replace('"SU-34_FULLBACK"','"SU-34_IMPORT_TEST"')
dat=dat.replace('COCKPITP -.39m 1.02m 5.05m','COCKPITP -.49m 1.22m 7.60m')
dat=dat.replace('HTRADIUS 13m','HTRADIUS 16m')
(air/'su34_import.dat').write_text(dat)
reg=air/'aircraft.lst';reg.write_text(reg.read_text()+'\naircraft/su34_import.dat aircraft/su34_import_fallback.dnm aircraft/su34coll.srf aircraft/su34cockpit.srf aircraft/su34_import_fallback.dnm\n')
vertices=[(x*1.5,y*1.5,z*1.5) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
mesh=['SURF']+['V %g %g %g'%p for p in vertices]
for ids,normal in [((0,3,2,1),(0,0,-1)),((4,5,6,7),(0,0,1)),((0,4,7,3),(-1,0,0)),((1,2,6,5),(1,0,0)),((0,1,5,4),(0,-1,0)),((3,7,6,2),(0,1,0))]:mesh+=['F','C 255 0 255','N %g %g %g'%normal,'V '+' '.join(map(str,ids)),'E']
mesh+=['E'];node=['SRF "IMPORT_FAILED"','FIL IMPORT_FAILED.srf','CLA 99','NST 1','STA 0 0 0 0 0 0 1','POS 0 0 0 0 0 0 1','CNT 0 0 0','PAX 1 0 0','REL DEP','NCH 0','END']
(air/'su34_import_fallback.dnm').write_text('\n'.join(['DYNAMODEL','DNMVER 2',f'PCK IMPORT_FAILED.srf {len(mesh)}']+mesh+node+['END'])+'\n')
fixture='YFSVERSI 20180930\nFIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE\nINITPLYR AIR 1\nCANCONTI TRUE\nENVIRONM DAY\nAIRPLANE SU-34_IMPORT_TEST TRUE\nIDENTIFY 0\nIDANDTAG 1 "SU34_MODEL_PRESERVATION_TEST"\nAIRPCMND UNLOADWP\nAIRPCMND INITFUEL 50%\nAIRPCMND ATTITUDE 0deg 0deg 0deg\nAIRPCMND POSITION 0m 2500m 0m\nAIRPCMND INITSPED 160m/s\nAIRPCMND CTLLDGEA FALSE\nAIRPCMND CTLTHROT 0.4\n'
(rt/'Su34_Import_Test.yfs').write_text(fixture)
(rt/'Start_Su34_Import.script').write_text('WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:500\nFILE:OPEN Su34_Import_Test.yfs\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nBTNFUNC:COCKPITVIEW\n')
(rt/'Play_Su34_Import.bat').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\nstart "" ysflight32_gl1.exe -script Start_Su34_Import.script\r\n')
(r/'game/PLAY_SU34_IMPORT.bat').write_bytes(b'@echo off\r\ncd /d "%~dp0runtime"\r\ncall Play_Su34_Import.bat\r\n')
(r/'game/START_HERE_IMPORT_RU.txt').write_text('Отдельный тест переноса новой модели Су-34. Запуск runtime/Play_Su34_Import.bat.\nМодель показана в исходной статической позе. Шасси, органы управления, сопла и приборы пока не анимированы. Кабина настоящая объёмная, кнопки пока не нажимаются. Динамика и коллизия взяты из прежнего теста и не подогнаны под новую модель. Нужен OpenGL 2.1 с GLSL; при ошибке загрузки вместо самолёта будет яркий пурпурный куб. Старые самолёты доступны и сохранены.\n')
(rt/'licenses/Su34_Import_NOTICE.txt').write_text('Russian Su-34 "35 Red", Sketchfab uploader 42manako.\nhttps://sketchfab.com/3d-models/russian-su-34-35-red-4d11c7ff85c74c7a91d623d1c0c40594\nPage-declared license: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nUploaded original ZIP SHA256 df72f7b90544610d64574c83df31759feaaac203a9ee6edc5711d3f66d98e59f.\nNested source names explicitly mention War Thunder. Original game-asset rights are not independently established; retain in authenticated personal test only.\nChanges: static indexed mesh bridge, reconstructed vertex normals because OBJ supplied none, original texture pixel preservation including outer replacement livery, separate test aircraft entry. No decimation.\n')
print('Runtime prepared',rt)
