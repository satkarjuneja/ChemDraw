function setStatus(id, message, state = "info") {
    const bar = document.getElementById(id);
    if (!bar) {
        return;
    }
    bar.textContent = message;
    bar.dataset.state = state;
}

function getMode(name) {
    const input = document.querySelector(`input[name="${name}"]:checked`);
    return input ? input.value : "2d";
}

function showViewer(mode, id2d, id3d) {
    const box2d = document.getElementById(id2d);
    const box3d = document.getElementById(id3d);
    if (!box2d || !box3d) {
        return;
    }
    box2d.style.display = mode === "2d" ? "block" : "none";
    box3d.style.display = mode === "3d" ? "block" : "none";
}

function renderPdb(targetId, pdbText) {
    const box = document.getElementById(targetId);
    if (!box) {
        return;
    }
    box.innerHTML = "";
    box.getBoundingClientRect();

    const viewer = $3Dmol.createViewer(box, { backgroundColor: "black" });
    viewer.addModel(pdbText, "pdb");
    viewer.setStyle({}, { stick: {} });
    viewer.zoomTo();
    viewer.resize();
    viewer.render();
}

async function requestSmiles(smiles, is3d) {
    const start = performance.now();
    let resp;
    try {
        resp = await fetch("/viewer/smiles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ smiles, is_3d: is3d })
        });
    } catch (err) {
        return { error: `Network error: ${err.message || err}` };
    }

    const elapsed = (performance.now() - start) / 1000;
    let data;
    try {
        data = await resp.json();
    } catch (err) {
        return { error: `Invalid server response (${elapsed.toFixed(2)}s)` };
    }

    if (!resp.ok) {
        const detail = data && data.detail ? data.detail : resp.statusText;
        return { error: `Error: ${detail} (${elapsed.toFixed(2)}s)` };
    }

    return { data, elapsed };
}

async function requestPdb(file, is3d) {
    const start = performance.now();
    let resp;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("is_3d", is3d ? "true" : "false");

    try {
        resp = await fetch("/viewer/pdb", {
            method: "POST",
            body: formData
        });
    } catch (err) {
        return { error: `Network error: ${err.message || err}` };
    }

    const elapsed = (performance.now() - start) / 1000;
    let data;
    try {
        data = await resp.json();
    } catch (err) {
        return { error: `Invalid server response (${elapsed.toFixed(2)}s)` };
    }

    if (!resp.ok) {
        const detail = data && data.detail ? data.detail : resp.statusText;
        return { error: `Error: ${detail} (${elapsed.toFixed(2)}s)` };
    }

    return { data, elapsed };
}

async function runSmiles() {
    const smilesInput = document.getElementById("smilesInput");
    const smiles = smilesInput ? smilesInput.value.trim() : "";
    const mode = getMode("smilesMode");
    const is3d = mode === "3d";

    if (!smiles) {
        setStatus("smilesStatusBar", "Enter a SMILES string", "error");
        return;
    }

    setStatus("smilesStatusBar", "Rendering...", "info");
    showViewer(mode, "smiles2d", "smiles3d");

    const result = await requestSmiles(smiles, is3d);
    if (result.error) {
        setStatus("smilesStatusBar", result.error, "error");
        return;
    }

    const { data, elapsed } = result;
    if (is3d) {
        if (!data.pdb) {
            setStatus("smilesStatusBar", "Error: missing 3D data", "error");
            return;
        }
        renderPdb("smiles3d", data.pdb);
    } else {
        if (!data.img) {
            setStatus("smilesStatusBar", "Error: missing 2D image", "error");
            return;
        }
        const box2d = document.getElementById("smiles2d");
        if (box2d) {
            box2d.innerHTML = `<img src="${data.img}" alt="2D view">`;
        }
    }

    setStatus("smilesStatusBar", `Rendered in ${elapsed.toFixed(2)}s`, "success");
}

async function runPdb() {
    const fileInput = document.getElementById("pdbFileInput");
    const file = fileInput ? fileInput.files[0] : null;
    const mode = getMode("pdbMode");
    const is3d = mode === "3d";

    if (!file) {
        setStatus("pdbStatusBar", "Select a PDB file first", "error");
        return;
    }

    setStatus("pdbStatusBar", "Rendering...", "info");
    showViewer(mode, "pdb2d", "pdb3d");

    const result = await requestPdb(file, is3d);
    if (result.error) {
        setStatus("pdbStatusBar", result.error, "error");
        return;
    }

    const { data, elapsed } = result;
    if (is3d) {
        if (!data.pdb) {
            setStatus("pdbStatusBar", "Error: missing 3D data", "error");
            return;
        }
        renderPdb("pdb3d", data.pdb);
    } else {
        if (!data.img) {
            setStatus("pdbStatusBar", "Error: missing 2D image", "error");
            return;
        }
        const box2d = document.getElementById("pdb2d");
        if (box2d) {
            box2d.innerHTML = `<img src="${data.img}" alt="2D view">`;
        }
    }

    setStatus("pdbStatusBar", `Rendered in ${elapsed.toFixed(2)}s`, "success");
}

const smilesButton = document.getElementById("smilesGenerateBtn");
if (smilesButton) {
    smilesButton.addEventListener("click", runSmiles);
}

const pdbButton = document.getElementById("pdbGenerateBtn");
if (pdbButton) {
    pdbButton.addEventListener("click", runPdb);
}

showViewer("2d", "smiles2d", "smiles3d");
showViewer("2d", "pdb2d", "pdb3d");
setStatus("smilesStatusBar", "Ready", "info");
setStatus("pdbStatusBar", "Ready", "info");
