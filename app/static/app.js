const state = {
  map: null,
  clusterer: null,
  areaObject: null,
  area: null,
  mode: null,
  polygonPoints: [],
  rectangleStart: null,
  jobId: null,
  pollTimer: null,
  resultIds: new Set(),
};

const byId = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
  bindControls();
  await loadParameterForm();
  await initializeMap();
});

function bindControls() {
  byId("start-button").addEventListener("click", startJob);
  byId("stop-button").addEventListener("click", stopJob);
  byId("rectangle-button").addEventListener("click", () => setDrawMode("rectangle"));
  byId("polygon-button").addEventListener("click", () => setDrawMode("polygon"));
  byId("clear-area-button").addEventListener("click", clearArea);
  for (const format of ["json", "csv", "xlsx"]) {
    byId(`export-${format}`).addEventListener("click", () => exportResults(format));
  }
}

async function loadParameterForm() {
  const schema = await fetchJson("/api/params/schema");
  const form = byId("params-form");
  form.textContent = "";
  for (const parameter of schema.parameters) {
    if (["search_url", "main.session_name", "single.session_folder"].includes(parameter.name)) continue;
    const wrapper = document.createElement("label");
    wrapper.className = "parameter";
    const label = document.createElement("span");
    label.textContent = parameter.description || parameter.name;
    label.title = `${parameter.name} (${parameter.source})`;
    const input = document.createElement("input");
    input.dataset.param = parameter.name;
    if (parameter.type === "boolean") {
      input.type = "checkbox";
      input.checked = Boolean(parameter.default);
    } else {
      input.type = parameter.type === "number" || parameter.type === "integer" ? "number" : "text";
      input.value = parameter.default ?? "";
      if (input.type === "number") input.step = "any";
    }
    wrapper.append(label, input);
    form.append(wrapper);
  }
}

async function initializeMap() {
  const config = await fetchJson("/api/config");
  if (!config.map_enabled) {
    showMapPlaceholder("Добавьте YANDEX_MAPS_API_KEY в .env и перезапустите приложение. Ключ JavaScript API получают на developer.tech.yandex.ru.");
    return;
  }
  const script = document.createElement("script");
  script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(config.yandex_maps_api_key)}&lang=ru_RU`;
  script.onload = () => {
    if (typeof ymaps === "undefined") {
      showMapPlaceholder("Yandex Maps API не инициализирован. Проверьте, что ключ создан для JavaScript API и разрешает localhost.");
      return;
    }
    ymaps.ready(createMap, () => showMapPlaceholder("Yandex Maps отклонил API-ключ. Проверьте тип ключа, ограничения доменов и активацию API."));
  };
  script.onerror = () => showMapPlaceholder("Не удалось загрузить Yandex Maps API. Проверьте ключ и подключение.");
  document.head.append(script);
}

function createMap() {
  byId("map-placeholder").hidden = true;
  state.map = new ymaps.Map("map", { center: [55.751244, 37.618423], zoom: 10, controls: ["zoomControl", "geolocationControl"] });
  state.clusterer = new ymaps.Clusterer({ preset: "islands#blueClusterIcons", groupByCoordinates: false });
  state.map.geoObjects.add(state.clusterer);
  state.map.events.add("mousedown", onMapMouseDown);
  state.map.events.add("mouseup", onMapMouseUp);
  state.map.events.add("click", onMapClick);
  state.map.events.add("dblclick", finishPolygon);
}

function setDrawMode(mode) {
  if (!state.map) return showStatus("Для выбора области требуется настроенная карта.", true);
  clearArea();
  state.mode = mode;
  state.map.behaviors[mode === "rectangle" ? "disable" : "enable"]("drag");
  byId("rectangle-button").classList.toggle("active", mode === "rectangle");
  byId("polygon-button").classList.toggle("active", mode === "polygon");
  showStatus(mode === "rectangle" ? "Зажмите мышь и протяните прямоугольник." : "Кликайте вершины полигона; двойной клик завершает.");
}

function onMapMouseDown(event) {
  if (state.mode === "rectangle") state.rectangleStart = event.get("coords");
}

function onMapMouseUp(event) {
  if (state.mode !== "rectangle" || !state.rectangleStart) return;
  const finish = event.get("coords");
  const south = Math.min(state.rectangleStart[0], finish[0]);
  const north = Math.max(state.rectangleStart[0], finish[0]);
  const west = Math.min(state.rectangleStart[1], finish[1]);
  const east = Math.max(state.rectangleStart[1], finish[1]);
  setArea({ type: "bbox", coordinates: [west, south, east, north] });
  state.rectangleStart = null;
}

function onMapClick(event) {
  if (state.mode !== "polygon") return;
  const [lat, lon] = event.get("coords");
  state.polygonPoints.push([lon, lat]);
  drawPolygonPreview();
}

function finishPolygon(event) {
  if (state.mode !== "polygon" || state.polygonPoints.length < 3) return;
  event.preventDefault();
  const coordinates = [...state.polygonPoints, state.polygonPoints[0]];
  setArea({ type: "polygon", coordinates });
}

function setArea(area) {
  clearAreaObject();
  state.area = area;
  state.mode = null;
  byId("rectangle-button").classList.remove("active");
  byId("polygon-button").classList.remove("active");
  if (area.type === "bbox") {
    const [west, south, east, north] = area.coordinates;
    state.areaObject = new ymaps.Rectangle([[south, west], [north, east]], {}, areaStyle());
  } else {
    state.areaObject = new ymaps.Polygon([area.coordinates.map(([lon, lat]) => [lat, lon])], {}, areaStyle());
  }
  state.map.geoObjects.add(state.areaObject);
  state.map.behaviors.enable("drag");
  showStatus("Область поиска выбрана.");
}

function drawPolygonPreview() {
  clearAreaObject();
  if (state.polygonPoints.length < 2) return;
  state.areaObject = new ymaps.Polyline(state.polygonPoints.map(([lon, lat]) => [lat, lon]), {}, areaStyle());
  state.map.geoObjects.add(state.areaObject);
}

function areaStyle() {
  return { strokeColor: "#2563eb", strokeWidth: 3, fillColor: "#2563eb22" };
}

function clearAreaObject() {
  if (state.map && state.areaObject) state.map.geoObjects.remove(state.areaObject);
  state.areaObject = null;
}

function clearArea() {
  clearAreaObject();
  state.area = null;
  state.mode = null;
  state.polygonPoints = [];
  state.rectangleStart = null;
  if (state.map) state.map.behaviors.enable("drag");
  byId("rectangle-button").classList.remove("active");
  byId("polygon-button").classList.remove("active");
}

async function startJob() {
  const query = byId("query").value.trim();
  if (!query) return showStatus("Введите поисковый запрос.", true);
  if (!state.area) return showStatus("Выберите область поиска на карте.", true);
  resetResults();
  try {
    const job = await fetchJson("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, area: state.area, params: collectParams() }),
    });
    state.jobId = job.id;
    byId("start-button").disabled = true;
    byId("stop-button").disabled = false;
    pollJob();
  } catch (error) {
    showStatus(error.message, true);
  }
}

function collectParams() {
  const values = {};
  document.querySelectorAll("[data-param]").forEach((input) => {
    values[input.dataset.param] = input.type === "checkbox" ? input.checked : input.type === "number" ? Number(input.value) : input.value;
  });
  return values;
}

async function pollJob() {
  clearTimeout(state.pollTimer);
  if (!state.jobId) return;
  try {
    const [job, page] = await Promise.all([
      fetchJson(`/api/jobs/${state.jobId}`),
      fetchJson(`/api/jobs/${state.jobId}/results?limit=1000`),
    ]);
    renderJob(job);
    renderResults(page.items);
    if (["queued", "running", "stopping"].includes(job.status)) {
      state.pollTimer = setTimeout(pollJob, 1000);
    } else {
      byId("start-button").disabled = false;
      byId("stop-button").disabled = true;
    }
  } catch (error) {
    showStatus(error.message, true);
    state.pollTimer = setTimeout(pollJob, 2000);
  }
}

function renderJob(job) {
  byId("progress").value = job.progress;
  byId("progress-text").textContent = `${job.progress}% · ${job.message || job.status}`;
  byId("found-count").textContent = String(job.found);
  showStatus(job.error || job.message, job.status === "failed");
}

function renderResults(items) {
  for (const company of items) {
    const key = company.dedupe_key || company.yandex_id || company.url || `${company.name}-${company.address}`;
    if (state.resultIds.has(key)) continue;
    state.resultIds.add(key);
    const row = document.createElement("tr");
    row.innerHTML = `<td>${escapeHtml(company.name || "")}</td><td>${escapeHtml(company.address || "")}</td><td>${escapeHtml(formatPhones(company.phones))}</td><td>${escapeHtml(company.rating || "")}</td>`;
    byId("results-body").append(row);
    addMarker(company);
  }
}

function addMarker(company) {
  if (!state.clusterer || company.latitude == null || company.longitude == null) return;
  const marker = new ymaps.Placemark([company.latitude, company.longitude], {
    balloonContentHeader: escapeHtml(company.name || ""),
    balloonContentBody: `${escapeHtml(company.address || "")}<br>${escapeHtml(formatPhones(company.phones))}`,
  });
  state.clusterer.add(marker);
}

function resetResults() {
  state.resultIds.clear();
  byId("results-body").textContent = "";
  byId("found-count").textContent = "0";
  byId("progress").value = 0;
  if (state.clusterer) state.clusterer.removeAll();
}

async function stopJob() {
  if (!state.jobId) return;
  await fetchJson(`/api/jobs/${state.jobId}/stop`, { method: "POST" });
  pollJob();
}

function exportResults(format) {
  if (!state.jobId) return showStatus("Сначала запустите задачу.", true);
  window.location.href = `/api/jobs/${state.jobId}/export?format=${format}`;
}

function formatPhones(phones) {
  if (Array.isArray(phones)) return phones.join(", ");
  return phones || "";
}

function showMapPlaceholder(message) {
  byId("map-placeholder").hidden = false;
  byId("map-placeholder-message").textContent = message;
}

function showStatus(message, error = false) {
  const status = byId("status-message");
  status.textContent = message || "";
  status.classList.toggle("error", error);
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || `Ошибка HTTP ${response.status}`);
  return body;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character]);
}
