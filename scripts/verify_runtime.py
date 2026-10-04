"""Local composed-runtime evidence, distinct from managed or hosted checks."""
import hashlib, json, resource, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'labs/binding-pockets'
FILES=['processed_structure','raw_predictions','raw_residues','mapped_residues','residue_map','report_file','receipt_file','pocket_view']

def main():
    cases=[('example-pdb-top3',{'structure_file':'fixtures/7L13-protein.pdb','chains_json':'[]','top_n':3},'ok',3),
           ('upload-mmcif-top1',{'mmcif_file':str(LAB/'fixtures/7L13.cif'),'chains_json':'[]','top_n':1},'ok',1),
           ('chain-selection-insertion-codes',{'mmcif_file':str(LAB/'fixtures/mapping-edge.cif'),'chains_json':'["AUTH_B"]','top_n':10},'ok',1),
           ('no-pockets',{'mmcif_file':str(LAB/'fixtures/1CRN.cif'),'chains_json':'[]','top_n':3},'no_pockets',0),
           ('invalid-two-files',{'structure_file':'fixtures/1CRN-protein.pdb','mmcif_file':str(LAB/'fixtures/1CRN.cif'),'top_n':3},'invalid_input',0)]
    records=[];roots=[]
    with tempfile.TemporaryDirectory() as temp:
        for label,inputs,status,count in cases:
            run_input=Path(temp)/'input.json';result_file=Path(temp)/f'{label}.json'
            values={'predict.structure_file':'','predict.mmcif_file':'',**{'predict.'+k:v for k,v in inputs.items()}}
            run_input.write_text(json.dumps({'parameters':{'initial_inputs':values}}))
            start=time.monotonic()
            result=subprocess.run([str(Path(sys.executable).with_name('biosimulant')),'--no-open','labs','run',str(LAB),'--no-install-deps','--require-local-capability','--run-input-file',str(run_input),'--results-file',str(result_file),'--json'],cwd=ROOT,capture_output=True,timeout=400)
            elapsed=time.monotonic()-start
            assert result.returncode==0,(label,result.stderr.decode()[-3000:],result.stdout.decode()[-1500:])
            payload=json.loads(result_file.read_text());outputs=payload['outputs']['predict']
            report=outputs['report']['value']
            assert report['status']==status,(label,report['status'],report['receipt'])
            assert len(report['pockets'])==count and outputs['pocket_count']['value']==count
            visuals=payload['visuals'][0]['visuals'];renders=[v['render'] for v in visuals]
            artifacts=[]
            if status=='invalid_input':
                assert renders==['text']
            else:
                assert renders[:2]==['text','structure3d'] and (('table' in renders)==bool(count))
                assert json.loads(Path(outputs['report_file']['value']).read_text())==report
                structure=next(v for v in visuals if v['render']=='structure3d')['data']['source']['path']
                assert structure==outputs['processed_structure']['value']
                if count:
                    table=next(v for v in visuals if v['render']=='table')['data']['rows']
                    assert [r[1] for r in table]==[p['upstream_score'] for p in report['pockets']]
                    assert [r[3:6] for r in table]==[p['center_angstrom'] for p in report['pockets']]
                for port in FILES:
                    p=Path(outputs[port]['value']);raw=p.read_bytes();artifacts.append({'port':port,'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
                roots.append(Path(outputs['report_file']['value']).parent)
                if label=='example-pdb-top3':
                    (ROOT/'reports/local-example-results.json').write_text(json.dumps(payload,indent=2))
                    dest=ROOT/'outputs/example';dest.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(outputs['pocket_view']['value'],dest/'pocket-view.html')
            records.append({'case':label,'status':'PASS','report_status':status,'elapsed_seconds':elapsed,'pockets':count,
                            'scores':[p['upstream_score'] for p in report['pockets']],'renders':renders,'artifacts':artifacts,
                            'error_code':report['receipt'].get('error_code')})
        assert len(set(roots))==len(roots)
    peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    evidence={'scope':'Local composed CLI (macOS arm64) from dedicated staging source; no managed Run, hosted deployment or end-to-end platform staging evidence',
              'python':sys.version,'cases':records,'output_directory_isolation':'PASS','peak_child_rss_bytes_macos':peak}
    (ROOT/'reports/local-runtime-verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(f'{len(records)} composed cases pass; peak child RSS {peak} bytes')
if __name__=='__main__':main()
