from __future__ import annotations

import base64
from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from rdkit import Chem
from rdkit.Chem import AllChem, Draw

router = APIRouter(prefix="/viewer", tags=["viewer"])


class SmilesRequest(BaseModel):
    smiles: str = Field(..., min_length=1, description="SMILES string")
    is_3d: bool = Field(
        False,
        description="When true, generate 3D PDB output only. When false, generate 2D image only.",
    )


class ViewerResponse(BaseModel):
    img: str | None = Field(None, description="PNG image as base64 data URI")
    pdb: str | None = Field(None, description="PDB text for 3D viewer")


def mol_to_png_data_uri(mol: Chem.Mol) -> str:
    image = Draw.MolToImage(mol, size=(700, 700))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


@router.post("/smiles", response_model=ViewerResponse)
async def view_smiles(request: SmilesRequest):
    mol = Chem.MolFromSmiles(request.smiles)
    if mol is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")

    if request.is_3d:
        mol = Chem.AddHs(mol)
        status = AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        if status != 0:
            raise HTTPException(status_code=400, detail="3D embedding failed")
        AllChem.UFFOptimizeMolecule(mol)
        pdb_block = Chem.MolToPDBBlock(mol)
        return ViewerResponse(pdb=pdb_block)

    AllChem.Compute2DCoords(mol)
    return ViewerResponse(img=mol_to_png_data_uri(mol))


@router.post("/pdb", response_model=ViewerResponse)
async def view_pdb(
    file: UploadFile = File(...),
    is_3d: bool = Form(False),
):
    pdb_bytes = await file.read()
    if not pdb_bytes:
        raise HTTPException(status_code=400, detail="PDB file is empty")

    pdb_text = pdb_bytes.decode("utf-8", errors="ignore")
    mol = Chem.MolFromPDBBlock(pdb_text, removeHs=False)
    if mol is None:
        raise HTTPException(status_code=400, detail="Invalid PDB file")

    if is_3d:
        pdb_block = Chem.MolToPDBBlock(mol)
        return ViewerResponse(pdb=pdb_block)

    AllChem.Compute2DCoords(mol)
    return ViewerResponse(img=mol_to_png_data_uri(mol))
