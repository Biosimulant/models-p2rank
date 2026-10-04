import hashlib,json,zipfile,tarfile
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'sources/p2rank_2.5.1';lab=r/'labs/binding-pockets';out=lab/'sources';out.mkdir(exist_ok=True)
records=[]
for p in sorted((d/'bin').rglob('*.jar')):
 z=zipfile.ZipFile(p);notices=[];coords=[]
 for n in z.namelist():
  if not n.endswith('/') and ('license' in n.lower() or 'notice' in n.lower()):
   target=out/'jar-notices'/p.name/n.replace('/','__');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n));notices.append(str(target.relative_to(lab)))
  if n.endswith('pom.properties'):
   coords.append(z.read(n).decode('utf-8'))
 records.append({'path':str(p.relative_to(d)),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'notices':notices,'maven_properties':coords})
(out/'jar-inventory.json').write_text(json.dumps(records,indent=2))
# Excluded: vecmath-1.3.1 (Sun notice restricts redistribution; classes duplicated by GPL+CE vecmath-1.5.2) and
# openchart-1.4.2 (LGPL GUI charting, no retained corresponding source). Outputs on all reference structures are
# byte-identical without them; see reports/runtime-trim-verification.json.
EXCLUDED={'bin/lib/vecmath-1.3.1.jar','bin/lib/openchart-1.4.2.jar'}
paths=[p for p in d.rglob('*')if p.is_file()and str(p.relative_to(d)) not in EXCLUDED and (p.relative_to(d).parts[0] in ['bin','config'] or str(p.relative_to(d)).startswith('models/default/') or str(p.relative_to(d)).startswith('models/_score_transform/') or p.name=='LICENSE.txt')]
chunks=[];group=[];size=0
for p in sorted(paths):
 if size+p.stat().st_size>48*1024*1024:
  chunks.append(group);group=[];size=0
 group.append(p);size+=p.stat().st_size
chunks.append(group)
assets=lab/'assets';assets.mkdir(exist_ok=True)
for i,files in enumerate(chunks):
 p=assets/f'p2rank-runtime-{i}.zip'
 with zipfile.ZipFile(p,"w",zipfile.ZIP_STORED)as z:
  for f in files:
   info=zipfile.ZipInfo(str(f.relative_to(d)),date_time=(2025,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o644<<16;z.writestr(info,f.read_bytes())
 print(p.name,p.stat().st_size)
members=[{'path':str(p.relative_to(d)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size}for p in sorted(paths)]
(out/'runtime-members.json').write_text(json.dumps(members,indent=2))
manifest={'excluded_members':sorted(EXCLUDED),'source_commit':'9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e','distribution_sha256':'d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274','distribution_size_bytes':275625956,
          'members_list':'sources/runtime-members.json','assets':[{'path':p.name,'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'members':len(zipfile.ZipFile(p).infolist())}for p in sorted(assets.glob('p2rank*.zip'))]}
(assets/'runtime-lock.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('jar count',len(records),'with notices',sum(bool(x['notices'])for x in records))
