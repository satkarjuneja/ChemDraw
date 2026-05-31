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

async function requestGeneration(formula, is3d) {
    const start = performance.now();
    let resp;
    try {
        resp = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ formula, is_3d: is3d })
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
    const result = await requestGeneration(formula, false);
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
    const result = await requestGeneration(formula, true);
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

const generateBtn = document.getElementById("generateBtn");
if (generateBtn) {
    generateBtn.addEventListener("click", () => {
        run();
    });
}

const nextBtn = document.getElementById("nextBtn");
if (nextBtn) {
    nextBtn.addEventListener("click", () => {
        nextMol();
    });
}

const prevBtn = document.getElementById("prevBtn");
if (prevBtn) {
    prevBtn.addEventListener("click", () => {
        prevMol();
    });
}

setStatus("Ready", "info");
