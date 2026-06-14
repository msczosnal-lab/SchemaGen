// COWORK_TASK: sync/prompts/001-labeler-canvas.md
// Stub — pelny canvas annotator implementuje Claude Cowork.

let currentPageId = null;
let classes = [];
let bboxes = [];

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadPages() {
  const pages = await fetchJson("/api/pages");
  const list = document.getElementById("page-list");
  list.innerHTML = "";
  pages.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p.filename || p.id;
    li.onclick = () => selectPage(p.id);
    list.appendChild(li);
  });
}

async function loadClasses() {
  const data = await fetchJson("/api/classes");
  classes = data.classes || [];
  const list = document.getElementById("class-list");
  list.innerHTML = "";
  classes.forEach((name, idx) => {
    const li = document.createElement("li");
    li.textContent = `${idx + 1}. ${name}`;
    list.appendChild(li);
  });
}

async function selectPage(pageId) {
  currentPageId = pageId;
  const img = new Image();
  img.onload = () => {
    const canvas = document.getElementById("canvas");
    canvas.width = img.width;
    canvas.height = img.height;
    canvas.getContext("2d").drawImage(img, 0, 0);
  };
  img.src = `/api/pages/${pageId}/image?t=${Date.now()}`;
  try {
    const ann = await fetchJson(`/api/annotations/${pageId}`);
    bboxes = ann.bboxes || [];
    renderAnnotationList();
  } catch {
    bboxes = [];
  }
}

function renderAnnotationList() {
  const list = document.getElementById("annotation-list");
  list.innerHTML = "";
  bboxes.forEach((b) => {
    const li = document.createElement("li");
    li.textContent = `${b.class_name || b.class}: ${b.id}`;
    list.appendChild(li);
  });
}

document.getElementById("save-btn").onclick = async () => {
  if (!currentPageId) return alert("Wybierz strone");
  const canvas = document.getElementById("canvas");
  const payload = {
    record: {
      page_id: currentPageId,
      image_path: `${currentPageId}.png`,
      image_width: canvas.width,
      image_height: canvas.height,
      bboxes,
      texts: [],
      connections: [],
    },
  };
  await fetchJson("/api/annotations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  alert("Zapisano");
};

document.getElementById("export-btn").onclick = async () => {
  if (!currentPageId) return alert("Wybierz strone");
  const paths = await fetchJson(`/api/export/${currentPageId}`, { method: "POST" });
  alert("Eksport:\n" + JSON.stringify(paths, null, 2));
};

loadPages();
loadClasses();
