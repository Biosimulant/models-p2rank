"""Offline finite adapter to exact P2Rank 2.5.1 native inference."""
from __future__ import annotations
import base64,csv,gzip,hashlib,html,io,json,math,os,shutil,signal,subprocess,tempfile,time,zipfile
from pathlib import Path
import jdk4py
from biosim import BioModule,ExecutionPolicy,SignalSpec
from .structure import InputError,preprocess,MAX_BYTES

LAB=Path(__file__).resolve().parents[3]
CAVEAT='P2Rank scores and upstream probabilities are model estimates; predicted pockets are not experimentally confirmed binding sites. Default model uses B-factors. Parity and one held-out holo demonstration are not broad biological validation.'
TIMEOUT_SECONDS=300
PALETTE=['#f97316','#3b82f6','#22c55e','#a855f7','#eab308','#ef4444','#14b8a6','#ec4899','#6366f1','#84cc16']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def table(path):
    with Path(path).open(newline='')as f:
        reader=csv.DictReader(f);reader.fieldnames=[x.strip()for x in reader.fieldnames]
        return [{k:v.strip()for k,v in row.items()}for row in reader]

def pinned_member(archive,member):
    """Read one member of a checksum-pinned asset archive listed in runtime-lock.json."""
    lock=json.loads((LAB/'assets/runtime-lock.json').read_text())
    entry=next(a for a in lock['bundles'] if a['path']==archive)
    p=LAB/'assets'/archive;raw=p.read_bytes()
    if len(raw)!=entry['size_bytes'] or sha(raw)!=entry['sha256']:raise RuntimeError('Pinned asset bundle missing or checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(raw))as z:return z.read(member)

def bundled_example(rel):
    """Resolve a Lab-relative example path; bundled RCSB examples live in a pinned archive."""
    p=LAB/rel
    if p.is_file():return p
    if len(rel.parts)==2 and rel.parts[0]=='fixtures':
        out=Path(tempfile.mkdtemp(prefix='p2rank-example-'))/rel.name
        out.write_bytes(pinned_member('reference-structures.zip',rel.name));return out
    return p

def runtime(target):
    lock=json.loads((LAB/'assets/runtime-lock.json').read_text())
    for asset in lock['assets']:
        p=LAB/'assets'/asset['path']
        if not p.is_file()or p.stat().st_size!=asset['size_bytes']or sha(p.read_bytes())!=asset['sha256']:
            raise RuntimeError('Pinned offline predictor asset missing or checksum mismatch')
        with zipfile.ZipFile(p)as z:
            if len(z.infolist())!=asset['members']:raise RuntimeError('Pinned runtime archive member count differs')
            for m in z.infolist():
                rel=Path(m.filename)
                if rel.is_absolute()or '..'in rel.parts or m.file_size>64*1024*1024:
                    raise RuntimeError('Unsafe runtime archive')
                dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(m))
    # Archive SHA-256 pins every member byte; per-member digests are retained in sources/runtime-members.json.
    return lock

def invoke(install,pdb,out,timeout):
    java=Path(jdk4py.JAVA_HOME)/'bin/java'
    cmd=[str(java),'-Xmx2048m','-cp',str(install/'bin/p2rank.jar')+os.pathsep+str(install/'bin/lib/*'),
         'cz.siret.prank.program.Main','predict','-f',str(pdb),'-o',str(out),'-threads','1','-visualizations','1','-vis_copy_proteins','0']
    env={**os.environ,'INSTALL_DIR':str(install)}
    with (Path(pdb).parent/'predictor.log').open('wb')as log:
        process=subprocess.Popen(cmd,cwd=install,env=env,stdout=log,stderr=log,start_new_session=True)
        try:
            code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError(f'Invocation exceeded frozen {TIMEOUT_SECONDS} second limit')
    if code:raise RuntimeError(f'P2Rank exited with code {code}; retained predictor.log has diagnostic detail')
    return cmd

def parse_outputs(out,name,prep,top_n):
    raw_p=out/f'{name}_predictions.csv';raw_r=out/f'{name}_residues.csv'
    prediction_rows=table(raw_p);residue_rows=table(raw_r)
    lookup={(r['internal_chain'],str(r['internal_residue'])):r for r in prep['mapping']}
    residues=[]
    for row in residue_rows:
        key=(row['chain'],row['residue_label'])
        if key not in lookup:raise RuntimeError('Upstream residue has no reversible identity mapping')
        residues.append({**lookup[key],'upstream_score':float(row['score']),'upstream_probability':float(row['probability'])if row.get('probability')else None,'pocket_rank':int(row['pocket'])})
    points=[]
    point_file=out/'visualizations/data'/f'{name}_points.pdb.gz'
    if point_file.exists():
        for line in gzip.decompress(point_file.read_bytes()).decode().splitlines():
            if line.startswith(('ATOM  ','HETATM')):
                points.append({'pocket_rank':int(line[22:26]),'xyz_angstrom':[float(line[30:38]),float(line[38:46]),float(line[46:54])],'ligandability':float(line[60:66])})
    pockets=[]
    for row in prediction_rows[:top_n]:
        rank=int(row['rank']);keys=[]
        for token in row['residue_ids'].split():
            chain,num=token.rsplit('_',1);key=(chain,num)
            if key not in lookup:raise RuntimeError('Pocket residue has no identity mapping')
            keys.append(lookup[key])
        pockets.append({'rank':rank,'upstream_score':float(row['score']),
                        'upstream_probability':float(row['probability'])if row.get('probability')else None,
                        'center_angstrom':[float(row[f'center_{a}'])for a in 'xyz'],
                        'residues':keys,'surface_point_count':sum(p['pocket_rank']==rank for p in points),
                        'surface_atom_ids':[int(x)for x in row['surf_atom_ids'].split()],
                        'upstream_sas_points':int(row['sas_points'])})
    if [p['rank']for p in pockets]!=list(range(1,len(pockets)+1)):
        raise RuntimeError('Unexpected upstream pocket ordering')
    return pockets,residues,points,str(raw_p),str(raw_r)

def pocket_html(prep,pockets,points,receipt):
    # Serialize untrusted identity text safely as JSON; DOM labels use textContent.
    data=json.dumps({'pdb':prep['pdb'],'pockets':pockets,'points':points,'receipt':receipt},separators=(',',':')).encode()
    # Deterministic gzip+base64 keeps the self-contained view small; the browser inflates it locally (no network).
    payload=json.dumps(base64.b64encode(gzip.compress(data,mtime=0)).decode())
    library=pinned_member('viewer-3dmol-2.5.5.zip','3Dmol-min.js').decode().replace('</script','<\\/script')
    notice=html.escape(pinned_member('viewer-3dmol-2.5.5.zip','LICENSE').decode())
    return '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P2Rank pocket result</title><style>body{font:15px system-ui;background:#0b1020;color:#e2e8f0;margin:0}header,aside{padding:18px}main{display:grid;grid-template-columns:340px 1fr}#viewer{height:75vh;position:relative}button,select{padding:8px;margin:5px;background:#1e293b;color:white;border:1px solid #64748b;border-radius:6px}label{display:block;padding:5px}pre{white-space:pre-wrap}#error{color:#f87171}</style></head><body><header><h1>P2Rank candidate binding pockets</h1><p>Centers and surface points in Å. Model estimates, not experimentally confirmed sites.</p><button id="receipt">Download receipt</button><button id="reset">Reset camera</button><select id="limit"><option value="1">Top 1</option><option value="3" selected>Top 3</option><option value="10">All returned</option></select><p id="error"></p></header><main><aside id="pockets"></aside><div id="viewer"></div></main><details><summary>Attribution and licenses</summary><p>P2Rank: Krivák and Hoksza (2018). Structures from RCSB PDB / wwPDB, CC0. Visualization: 3Dmol.js 2.5.5 (BSD-3-Clause).</p><pre>'''+notice+'''</pre></details><script>'''+library+'''</script><script>const packed='''+payload+''';let result;const colors='''+json.dumps(PALETTE)+''';let viewer;window.verification={ready:false,selectedResidues:[],centers:[],surfacePoints:0};
function render(){viewer.removeAllShapes();viewer.removeAllLabels();viewer.setStyle({},{cartoon:{color:'#94a3b8'},line:{color:'#94a3b8',opacity:0.25}});const limit=Number(document.getElementById('limit').value);const box=document.getElementById('pockets');box.replaceChildren();window.verification.selectedResidues=[];window.verification.centers=[];window.verification.surfacePoints=0;for(const p of result.pockets.filter(p=>p.rank<=limit)){const c=colors[p.rank-1];const center={x:p.center_angstrom[0],y:p.center_angstrom[1],z:p.center_angstrom[2]};viewer.addSphere({center,radius:0.8,color:c});viewer.addLabel('Pocket '+p.rank,{position:center,backgroundColor:c,fontColor:'white'});window.verification.centers.push(p.center_angstrom);for(const s of result.points.filter(s=>s.pocket_rank===p.rank)){viewer.addSphere({center:{x:s.xyz_angstrom[0],y:s.xyz_angstrom[1],z:s.xyz_angstrom[2]},radius:0.18,color:c,opacity:0.65});window.verification.surfacePoints++;}const title=document.createElement('h3');title.style.color=c;title.textContent='Pocket '+p.rank+' — score '+p.upstream_score+(p.upstream_probability===null?'':' / probability '+p.upstream_probability);box.append(title);for(const r of p.residues){const label=document.createElement('label'),checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=true;const text=document.createTextNode(' '+r.author_chain+':'+r.author_residue_number+r.insertion_code+' '+r.residue_name+' (label '+(r.label_chain||'?')+':'+(r.label_seq_id===null?'?':r.label_seq_id)+')');label.append(checkbox,text);box.append(label);const selection={chain:r.internal_chain,resi:r.internal_residue};function apply(){viewer.setStyle(selection,checkbox.checked?{stick:{color:c,radius:0.17},cartoon:{color:c}}:{cartoon:{color:'#94a3b8'}});viewer.render();}checkbox.addEventListener('change',apply);apply();window.verification.selectedResidues.push({author_chain:r.author_chain,author_residue_number:r.author_residue_number,insertion_code:r.insertion_code,internal_chain:r.internal_chain,internal_residue:r.internal_residue,atomCount:viewer.getModel().selectedAtoms(selection).length});}}if(!result.pockets.length)box.textContent='No pockets predicted. This is a valid empty result.';viewer.render();}
(async()=>{try{const bytes=Uint8Array.from(atob(packed),c=>c.charCodeAt(0));result=JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());viewer=$3Dmol.createViewer(document.getElementById('viewer'),{backgroundColor:'#0b1020'});viewer.addModel(result.pdb,'pdb');render();viewer.zoomTo();viewer.render();window.verification.ready=true;}catch(e){document.getElementById('error').textContent='3D unavailable: '+e.message;}})();
document.getElementById('limit').addEventListener('change',render);document.getElementById('reset').onclick=()=>{viewer.zoomTo();viewer.render();};document.getElementById('receipt').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result.receipt,null,2)],{type:'application/json'}));a.download='receipt.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};</script></body></html>'''

def predict(raw,format,chains,top_n,root=None):
    start=time.monotonic();root=Path(root or tempfile.mkdtemp(prefix='p2rank-',suffix='-result'));root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
    if type(top_n)is not int or not 1<=top_n<=10:raise InputError('top_n','top_n must be an integer from 1 to 10')
    prep=preprocess(raw,format,chains);pdb=root/'processed.pdb';pdb.write_text(prep['pdb'])
    # Runtime extraction and native scratch output stay outside retained results and are removed afterwards.
    work=Path(tempfile.mkdtemp(prefix='p2rank-work-'))
    try:
        install=work/'runtime';install.mkdir();lock=runtime(install);out=work/'upstream';out.mkdir()
        cmd=invoke(install,pdb,out,max(1,TIMEOUT_SECONDS-(time.monotonic()-start)))
        pockets,residues,points,rawp,rawr=parse_outputs(out,pdb.name,prep,top_n)
        rawp=shutil.copy(rawp,root/'predictions.csv');rawr=shutil.copy(rawr,root/'residues.csv')
    finally:
        shutil.rmtree(work,ignore_errors=True)
    receipt={'predictor':'P2Rank','version':'2.5.1','adapter_version':'0.1.0','source_commit':lock['source_commit'],'distribution_sha256':lock['distribution_sha256'],
             'input_sha256':sha(raw),'input_size_bytes':len(raw),'processed_sha256':sha(pdb.read_bytes()),'input_format':format,
             'selected_author_chains':prep['selected_author_chains'],'coordinate_models_in_input':prep['coordinate_models_in_input'],'selected_model_index':0,
             'preprocessing':'Protein heavy atoms only; first model; altloc highest occupancy/tie blank,A,lexical; internal chain/residue IDs reversible; waters/ligands removed',
             'protein_atoms':prep['protein_atoms'],'protein_residues':len(prep['mapping']),'top_n':top_n,'returned_pockets':len(pockets),
             'limits':{'bytes':MAX_BYTES,'protein_atoms':10000,'residues':2000,'timeout_seconds':300},
             'java_package':'jdk4py==21.0.8.1','java_version':subprocess.check_output([str(Path(jdk4py.JAVA_HOME)/'bin/java'),'-version'],stderr=subprocess.STDOUT).decode(),
             'gemmi_version':'0.7.3','threads':1,'seed':42,'center_unit':'angstrom','surface_point_unit':'angstrom','score_unit':'1','probability_unit':'1','elapsed_seconds':time.monotonic()-start,'caveat':CAVEAT}
    # Typed report stays bounded: returned pockets only; every residue score remains in mapped_residues.csv.
    points=[x for x in points if 1<=x['pocket_rank']<=len(pockets)]
    report={'status':'ok'if pockets else'no_pockets','pockets':pockets,'residues':[r for r in residues if 1<=r['pocket_rank']<=len(pockets)],'surface_points':points,'receipt':receipt}
    files={'processed_structure':str(pdb),'raw_predictions':str(rawp),'raw_residues':str(rawr)}
    for key,value in [('report_file',report),('receipt_file',receipt),('residue_map',prep['mapping'])]:
        p=root/(key+'.json');p.write_text(json.dumps(value,separators=(',',':')));files[key]=str(p)
    p=root/'mapped_residues.csv'
    with p.open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(residues[0])if residues else list(prep['mapping'][0])+['upstream_score','upstream_probability','pocket_rank']);writer.writeheader();writer.writerows(residues)
    files['mapped_residues']=str(p)
    p=root/'pocket-view.html';p.write_text(pocket_html(prep,pockets,points,receipt));files['pocket_view']=str(p)
    return report,files

FILES={'processed_structure':'pdb','raw_predictions':'csv','raw_residues':'csv','mapped_residues':'csv','residue_map':'json','report_file':'json','receipt_file':'json','pocket_view':'html'}

class PocketPredictor(BioModule):
    execution_policy=ExecutionPolicy.ONCE_BEFORE_RUN
    def __init__(self):self.report=None;self.files={}
    def inputs(self):
        return {'structure_file':SignalSpec.scalar(dtype='str',value_type='file',format='pdb'),
                'mmcif_file':SignalSpec.scalar(dtype='str',value_type='file',format='cif'),
                'chains_json':SignalSpec.scalar(dtype='str',value_type='string'),
                'top_n':SignalSpec.scalar(dtype='int64',value_type='integer')}
    def outputs(self):
        return {'report':SignalSpec.record(schema={'status':'str','pockets':'json','residues':'json','surface_points':'json','receipt':'json'},emitted_unit='1'),
                'pocket_count':SignalSpec.scalar(dtype='int64',emitted_unit='count'),
                **{k:SignalSpec.scalar(dtype='str',value_type='file',format=v)for k,v in FILES.items()}}
    def execute(self,inputs,*,context):
        v={k:s.value for k,s in inputs.items()}
        try:
            paths=[(v.get('structure_file',''),'pdb'),(v.get('mmcif_file',''),'cif')];paths=[x for x in paths if x[0]]
            if len(paths)!=1:raise InputError('structure_input','Upload exactly one PDB or mmCIF structure')
            name,format=paths[0];p=Path(name)
            if not p.is_absolute():p=bundled_example(p)
            if p.is_symlink()or not p.is_file()or p.stat().st_size>MAX_BYTES:raise InputError('structure_file','Upload must be a regular file of at most 2 MiB')
            # Platform-stored uploads may lose their name; an explicit foreign extension or compressed bytes is rejected.
            suffix=p.suffix.lower()
            if suffix and suffix not in (('.pdb','.ent') if format=='pdb' else ('.cif','.mmcif')):
                raise InputError('unsupported_format','File extension differs from declared format')
            if p.read_bytes()[:4] in (b'PK\x03\x04',) or p.read_bytes()[:2]==b'\x1f\x8b':
                raise InputError('unsupported_format','Compressed or archived uploads are not supported')
            try:chains=json.loads(v.get('chains_json','[]'))
            except Exception as e:raise InputError('chain_selection','chains_json must be a JSON list')from e
            output=Path.cwd()/'outputs';output.mkdir(exist_ok=True)
            root=Path(tempfile.mkdtemp(prefix='p2rank-pockets-',dir=output)).resolve()
            self.report,self.files=predict(p.read_bytes(),format,chains,v.get('top_n',3),root=root)
        except InputError as e:
            self.report={'status':'invalid_input','pockets':[],'residues':[],'surface_points':[],'receipt':{'error_code':e.code,'message':str(e),'caveat':CAVEAT}};self.files={}
        except TimeoutError as e:
            self.report={'status':'timeout','pockets':[],'residues':[],'surface_points':[],'receipt':{'message':str(e),'caveat':CAVEAT}};self.files={}
        except RuntimeError as e:
            # Upstream/runtime failure is explicit and never converted into an empty or fabricated pocket list.
            self.report={'status':'execution_failed','pockets':[],'residues':[],'surface_points':[],'receipt':{'message':str(e),'caveat':CAVEAT}};self.files={}
        return {'report':self.report,'pocket_count':len(self.report['pockets']),**self.files}
    def visualize(self):
        if not self.report:return []
        result=[{'schema_version':'1','render':'text','data':{'text':self.report['status']+'. '+CAVEAT}}]
        if self.files:
            result.append({'schema_version':'1','render':'structure3d','data':{'format':'pdb','source':{'kind':'artifact','path':self.files['processed_structure']},'description':'Processed protein preview. Open downloadable pocket-view.html for ranked colored centers, surface points and original residue highlights.'}})
        if self.report['pockets']:
            result.append({'schema_version':'1','render':'table','data':{'columns':['Rank','Upstream score','Upstream probability','X (Å)','Y (Å)','Z (Å)','Residue count'],'rows':[[p['rank'],p['upstream_score'],p['upstream_probability'],*p['center_angstrom'],len(p['residues'])]for p in self.report['pockets']]}})
        return result
