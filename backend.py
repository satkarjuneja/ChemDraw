from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, Field

import os
import base64
import json
import uuid
import subprocess


# -------------FASTAPI SETUP---------------

app = FastAPI(title="ChemDraw API", version="1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file directories
STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

STATIC_2D = os.path.join(STATIC_DIR, "2D")
STATIC_3D = os.path.join(STATIC_DIR, "3D")

os.makedirs(STATIC_2D, exist_ok=True)
os.makedirs(STATIC_3D, exist_ok=True)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

# ============================================================================
# REQUEST/RESPONSE MODELS (Pydantic for automatic validation)
# ============================================================================


class FormulaRequest(BaseModel):
    """API request for generating molecules"""

    formula: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Chemical formula (e.g., C6H6, CH4)",
    )
    is_3d: bool = Field(
        False,
        description="When true, generate 3D data only. When false, generate 2D image only.",
    )


class GenerateResponse(BaseModel):
    """API response with base64 image and molecules"""

    img: str | None = Field(None, description="PNG image as base64 data URI")
    molecules: list | None = Field(None, description="3D molecule data")


# ============================================================================
# GLOBAL STATE
# ============================================================================


class AppState:
    """Store previous files for cleanup"""

    prev_PNG_FILE = None
    prev_PDB_FILE = None


state = AppState()


# ============================================================================
# ROUTES
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve index.html"""
    try:
        with open("templates/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>ChemDraw API</h1><p>index.html not found</p>"


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: FormulaRequest):
    """
    Generate either a 2D image or 3D data from formula.

    - Formula is automatically validated (non-empty, max 50 chars)
    - If is_3d is True, returns 3D molecule data
    - If is_3d is False, returns PNG as base64
    """

    formula = request.formula
    is_3d = request.is_3d

    try:
        from parser import run_pipeline

        if is_3d:
            if state.prev_PDB_FILE and os.path.exists(state.prev_PDB_FILE):
                os.remove(state.prev_PDB_FILE)

            PDB_FILE = os.path.join(STATIC_3D, f"{uuid.uuid4().hex}.pdb")
            print("HELO")
            run_pipeline(
                formula,
                None,
                PDB_FILE,
                timeout=60,
                render_2d=False,
                render_3d=True,
            )

            state.prev_PDB_FILE = PDB_FILE

            JSON_FILE = os.path.join(STATIC_DIR, "3d_molecules.json")
            with open(JSON_FILE) as f:
                molecules = json.load(f)

            return GenerateResponse(molecules=molecules)

        if state.prev_PNG_FILE and os.path.exists(state.prev_PNG_FILE):
            os.remove(state.prev_PNG_FILE)

        PNG_FILE = os.path.join(STATIC_2D, f"{uuid.uuid4().hex}.png")

        run_pipeline(
            formula,
            PNG_FILE,
            None,
            timeout=60,
            render_2d=True,
            render_3d=False,
        )

        with open(PNG_FILE, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        state.prev_PNG_FILE = PNG_FILE

        return GenerateResponse(img=f"data:image/png;base64,{img_b64}")

    except TimeoutError:
        raise HTTPException(
            status_code=408, detail="Generation timeout - formula too complex"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Generation failed: {e.stderr or e.stdout or e.output or str(e)}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Generation failed: {e}")

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"File not found: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ============================================================================
# RUNNING THE APP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        reload=True,  # Auto-restart on file changes
    )

# uvicorn backend_fastapi:app --host 0.0.0.0 --port 7860 --reload
