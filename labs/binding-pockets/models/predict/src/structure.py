"""Reversible protein-only preprocessing; no reference ligand enters inference."""
from __future__ import annotations
import json, math, string
from pathlib import Path
import gemmi

MAX_BYTES=2*1024*1024
MAX_ATOMS=10000
MAX_RESIDUES=2000
CHAIN_IDS=string.ascii_uppercase+string.ascii_lowercase+string.digits

class InputError(ValueError):
    def __init__(self,code,message):
        super().__init__(message);self.code=code

def load(raw:bytes,format:str):
    if format not in ('pdb','cif','mmcif'):
        raise InputError('unsupported_format','Only PDB and text mmCIF uploads are supported')
    if not raw or len(raw)>MAX_BYTES:
        raise InputError('input_size','Structure must contain 1..2097152 bytes')
    try:
        text=raw.decode('utf-8')
        st=gemmi.read_pdb_string(text) if format=='pdb' else gemmi.make_structure_from_block(gemmi.cif.read_string(text).sole_block())
        st.setup_entities()
    except Exception as e:
        raise InputError('parse_error','Cannot parse the declared coordinate format') from e
    if len(st)==0:
        raise InputError('no_protein','Input has no coordinate models')
    return st

def preprocess(raw,format,chains):
    st=load(raw,format)
    if not isinstance(chains,list) or any(not isinstance(c,str) for c in chains) or len(set(chains))!=len(chains):
        raise InputError('chain_selection','Selected chains must be a unique list of author chain IDs')
    present={c.name for c in st[0]}
    if set(chains)-present:
        raise InputError('missing_chain','A selected author chain is absent from the first coordinate model')
    out=gemmi.Structure();model=gemmi.Model('1');mapping=[];atom_map=[];count=0; seen_auth=set()
    for chain in st[0]:
        if chains and chain.name not in chains:continue
        proteins=[]
        for res in chain:
            info=gemmi.find_tabulated_residue(res.name)
            # PDB entity inference and mmCIF declared polymer must agree with protein residue chemistry.
            if res.entity_type!=gemmi.EntityType.Polymer or not info.is_amino_acid():continue
            atoms={}
            for a in res:
                if a.element.is_hydrogen:continue
                xyz=[a.pos.x,a.pos.y,a.pos.z]
                if not all(math.isfinite(x) and abs(x)<10000 for x in xyz) or not math.isfinite(a.occ) or not math.isfinite(a.b_iso):
                    raise InputError('invalid_coordinate','Coordinates, occupancy and B-factors must be finite and within PDB limits')
                alt=a.altloc.strip('\x00 ');tie=(0 if not alt else 1 if alt=='A' else 2,alt)
                order=(-a.occ,tie)
                if a.name not in atoms or order<atoms[a.name][0]:atoms[a.name]=(order,a)
            if atoms:proteins.append((res,[x[1]for x in atoms.values()]))
        if not proteins:continue
        ci=len(model)
        if ci>=len(CHAIN_IDS):raise InputError('chain_limit','Maximum 62 protein chains')
        internal=CHAIN_IDS[ci];new_chain=gemmi.Chain(internal)
        for n,(res,atoms) in enumerate(proteins,1):
            key=(chain.name,res.seqid.num,res.seqid.icode.strip(),res.subchain)
            if key in seen_auth:raise InputError('ambiguous_residue','Duplicate author residue identity in selected model')
            seen_auth.add(key)
            row={'internal_chain':internal,'internal_residue':n,'author_chain':chain.name,'label_chain':res.subchain or None,
                 'author_residue_number':res.seqid.num,'insertion_code':res.seqid.icode.strip(),
                 'label_seq_id':res.label_seq,'residue_name':res.name}
            mapping.append(row)
            new=gemmi.Residue();new.name=res.name;new.seqid=gemmi.SeqId(n,' ');new.het_flag='A'
            for a in atoms:
                copy=a.clone();copy.altloc='\x00';new.add_atom(copy);count+=1
                atom_map.append({'atom_serial':count,'atom_name':a.name,'internal_chain':internal,'internal_residue':n})
            new_chain.add_residue(new)
        model.add_chain(new_chain)
    if count==0:raise InputError('no_protein','No usable protein heavy-atom coordinates in selected chains')
    if count>MAX_ATOMS or len(mapping)>MAX_RESIDUES:raise InputError('structure_limit','Maximum 10000 protein heavy atoms and 2000 residues')
    out.add_model(model)
    pdb=out.make_pdb_string()
    return {'pdb':pdb,'mapping':mapping,'atom_mapping':atom_map,'protein_atoms':count,
            'selected_author_chains':list(dict.fromkeys(r['author_chain'] for r in mapping)),
            'coordinate_models_in_input':len(st),'selected_model_index':0}
