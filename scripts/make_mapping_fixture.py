"""Build the A2 software-verification fixture from RCSB 1STP (CC0).

Two copies of the 1STP chain with multi-character author/label chain IDs reuse
the same author residue numbers. Author numbers are doubled (residue-number
gaps) and label_seq 24 (inside the 1STP biotin pocket) becomes an insertion-code residue sharing label_seq 23's
author number. Copy B is translated +40 Angstrom in x so the copies do not
overlap. Biotin and waters stay inside the declared polymer entity so the
preprocessor must exclude them by residue chemistry. This is a transformed
software fixture, not a deposited structure.
"""
from pathlib import Path
import gemmi

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/binding-pockets'


def author_id(label_seq, fallback):
    if label_seq is None:
        return gemmi.SeqId(2 * fallback, ' ')
    if label_seq == 24:
        return gemmi.SeqId(2 * 23 - 16, 'A')
    return gemmi.SeqId(2 * label_seq - 16, ' ')


def build():
    source = gemmi.read_structure(str(LAB / 'fixtures/1STP.cif'))
    source.setup_entities()
    original = source[0]['A']
    out = gemmi.Structure()
    out.name = 'model'
    out.cell = gemmi.UnitCell(1, 1, 1, 90, 90, 90)
    model = gemmi.Model('1')
    for copy, (auth, label, shift) in enumerate([('AUTH_A', 'LABEL_0', 0.0), ('AUTH_B', 'LABEL_1', 40.0)]):
        chain = gemmi.Chain(auth)
        for res in original:
            new = gemmi.Residue()
            new.name = res.name
            new.seqid = author_id(res.label_seq, res.seqid.num)
            new.subchain = label
            new.entity_id = '1'
            new.entity_type = gemmi.EntityType.Polymer
            new.label_seq = res.label_seq if res.label_seq is not None else 0
            new.het_flag = 'A'
            for atom in res:
                a = atom.clone()
                a.pos = gemmi.Position(a.pos.x + shift, a.pos.y, a.pos.z)
                new.add_atom(a)
            chain.add_residue(new)
        model.add_chain(chain)
    out.add_model(model)
    entity = gemmi.Entity('1')
    entity.entity_type = gemmi.EntityType.Polymer
    entity.polymer_type = gemmi.PolymerType.PeptideL
    entity.subchains = ['LABEL_0', 'LABEL_1']
    out.entities.append(entity)
    doc = out.make_mmcif_document()
    return doc.as_string()


if __name__ == '__main__':
    target = LAB / 'fixtures/mapping-edge.cif'
    target.write_text(build())
    print(target, target.stat().st_size)
