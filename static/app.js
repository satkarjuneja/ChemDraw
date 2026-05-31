let molecules = [];
let index = 0;

function getMode() {
    return document.querySelector('input[name="mode"]:checked').value;
}

function showPage(id) {
    document.getElementById("page2d").style.display = "none";
    document.getElementById("page3d").style.display = "none";
    document.getElementById(id).style.display = "flex";
}

function setStatus(message, state = "info") {
    const bar = document.getElementById("statusBar");
    if (!bar) {
        return;
    }
    bar.textContent = message;
    bar.dataset.state = state;
}

function setViewStatus(message, state = "info") {
    const bar = document.getElementById("viewStatusBar");
    if (!bar) {
        return;
    }
    bar.textContent = message;
    bar.dataset.state = state;
}

async function requestGeneration(formula) {
    const start = performance.now();
    let resp;
    try {
        resp = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ formula })
        });
    } catch (err) {
        setStatus(`Network error: ${err.message || err}`, "error");
        return null;
    }

    const elapsed = (performance.now() - start) / 1000;
    const text = await resp.text();
    let data = null;
    try {
        data = JSON.parse(text);
    } catch (err) {
        data = null;
    }

    if (!resp.ok) {
        const detail = data && data.detail ? data.detail : (text || resp.statusText);
        setStatus(`Error: ${detail} (${elapsed.toFixed(2)}s)`, "error");
        return null;
    }

    if (!data) {
        setStatus(`Error: invalid server response (${elapsed.toFixed(2)}s)`, "error");
        return null;
    }

    return { data, elapsed };
}

async function requestView(url, options) {
    const start = performance.now();
    let resp;
    try {
        resp = await fetch(url, options);
    } catch (err) {
        setViewStatus(`Network error: ${err.message || err}`, "error");
        return null;
    }

    const elapsed = (performance.now() - start) / 1000;
    const text = await resp.text();
    let data = null;
    try {
        data = JSON.parse(text);
    } catch (err) {
        data = null;
    }

    if (!resp.ok) {
        const detail = data && data.detail ? data.detail : (text || resp.statusText);
        setViewStatus(`Error: ${detail} (${elapsed.toFixed(2)}s)`, "error");
        return null;
    }

    if (!data) {
        setViewStatus(`Error: invalid server response (${elapsed.toFixed(2)}s)`, "error");
        return null;
    }

    return { data, elapsed };
}

async function run() {
    getMode() === "2d" ? run2D() : run3D();
}

async function run2D() {
    showPage("page2d");
    const formula = document.getElementById("formula").value;
    if (!formula) {
        setStatus("Enter a formula", "error");
        return;
    }

    setStatus("Generating...", "info");
    const result = await requestGeneration(formula);
    if (!result) return;

    const { data, elapsed } = result;
    document.getElementById("page2d").innerHTML =
        `<img id="result" src="${data.img}">`;
    setStatus(`Generated 2D image in ${elapsed.toFixed(2)}s`, "success");
}

async function run3D() {
    showPage("page3d");

    const formula = document.getElementById("formula").value;
    if (!formula) {
        setStatus("Enter a formula", "error");
        return;
    }

    setStatus("Generating...", "info");
    const result = await requestGeneration(formula);
    if (!result) return;

    const { data, elapsed } = result;
    molecules = data.molecules || [];

    if (!molecules.length) {
        setStatus("No molecules generated", "error");
        return;
    }

    index = 0;
    renderMol();
    setStatus(`Generated ${molecules.length} isomers in ${elapsed.toFixed(2)}s`, "success");
}

function renderMol() {
    const box = document.getElementById("viewer3d");
    box.innerHTML = "";

    box.getBoundingClientRect();

    const viewer = $3Dmol.createViewer(box, { backgroundColor: "black" });
    viewer.addModel(molecules[index].pdb, "pdb");
    viewer.setStyle({}, { stick: {} });
    viewer.zoomTo();

    viewer.resize();
    viewer.render();

    document.getElementById("indexLabel").textContent =
        `Molecule ${index + 1} / ${molecules.length}`;
}

function nextMol() {
    if (index < molecules.length - 1) {
        index++;
        renderMol();
    }
}

function prevMol() {
    if (index > 0) {
        index--;
        renderMol();
    }
}

function renderSinglePdb(pdbText) {
    const box = document.getElementById("viewer3dSingle");
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

async function viewSmiles() {
    const smiles = document.getElementById("smilesInput").value.trim();
    if (!smiles) {
        setViewStatus("Enter a SMILES string", "error");
        return;
    }

    setViewStatus("Rendering...", "info");
    const result = await requestView("/view/smiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ smiles })
    });
    if (!result) return;

    const { data, elapsed } = result;
    document.getElementById("view2d").innerHTML = `<img src="${data.img}" alt="2D view">`;
    renderSinglePdb(data.pdb);
    setViewStatus(`Rendered in ${elapsed.toFixed(2)}s`, "success");
}

async function viewPdb() {
    const fileInput = document.getElementById("pdbFile");
    const file = fileInput ? fileInput.files[0] : null;
    if (!file) {
        setViewStatus("Select a PDB file first", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setViewStatus("Rendering...", "info");
    const result = await requestView("/view/pdb", {
        method: "POST",
        body: formData
    });
    if (!result) return;

    const { data, elapsed } = result;
    document.getElementById("view2d").innerHTML = `<img src="${data.img}" alt="2D view">`;
    renderSinglePdb(data.pdb);
    setViewStatus(`Rendered in ${elapsed.toFixed(2)}s`, "success");
}

const downloadBtn = document.getElementById("downloadBtn");
if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {
        const img = document.getElementById("result");
        if (!img) {
            setStatus("No 2D image to download yet", "error");
            return;
        }
        const link = document.createElement("a");
        link.href = img.src;
        link.download = "molecule.png";
        link.click();
    });
}

setStatus("Ready", "info");
setViewStatus("Ready", "info");
