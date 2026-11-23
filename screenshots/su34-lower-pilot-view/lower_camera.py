"""Camera-only follow-up to orientation-lighting.patch; no model edits."""
from pathlib import Path
import re,sys,json
runtime=Path(sys.argv[1])
path=runtime/'aircraft/su34_import.dat'
before=path.read_text()
assert len(re.findall(r'^COCKPITP .*$',before,re.M))==1
after=re.sub(r'^COCKPITP .*$', 'COCKPITP -.49m 1.00m 7.42m',before,flags=re.M)
# Keep normal forward framing. A -18deg pitch was used only for the panel photo.
assert re.sub(r'^COCKPITP .*$', '',before,flags=re.M)==re.sub(r'^COCKPITP .*$', '',after,flags=re.M)
path.write_text(after)
print(json.dumps({'eye_before':[-.49,1.12,7.60],'eye_after':[-.49,1.,7.42],'lower_cm':12,'back_cm':18,'unchanged':'geometry, texture pixels, lighting, zoom, normal view pitch'}))
