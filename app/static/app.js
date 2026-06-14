const state = {
  map: null,
  clusterer: null,
  areaObject: null,
  addressMarker: null,
  area: null,
  mode: null,
  polygonPoints: [],
  rectangleStart: null,
  jobId: null,
  pollTimer: null,
  addressSuggestTimer: null,
  addressSuggestRequest: 0,
  selectedSuggestion: -1,
  resultIds: new Set(),
  totalResults: 0,
  dashboardOpened: false,
};

const byId = (id) => document.getElementById(id);
const hidePlaceholder = () => { const el = byId("map-placeholder"); if (el) { el.hidden = true; el.style.display = "none"; } };

function watchMapReady() {
  try {
    const mapEl = byId("map");
    if (!mapEl) return;
    const obs = new MutationObserver(() => {
      if (mapEl.children.length > 1) { hidePlaceholder(); obs.disconnect(); }
    });
    obs.observe(mapEl, { childList: true });
  } catch {}
}

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
  byId("address-search-button").addEventListener("click", searchAddress);
  byId("address").addEventListener("input", scheduleAddressSuggestions);
  byId("address").addEventListener("keydown", onAddressKeydown);
  byId("address").addEventListener("blur", () => setTimeout(hideAddressSuggestions, 200));
  byId("move-map-button").addEventListener("click", enableMapMovement);
  byId("theme-toggle").addEventListener("click", toggleTheme);
  byId("import-url-button").addEventListener("click", importYandexUrl);
  byId("yandex-url").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); importYandexUrl(); } });
  for (const format of ["json", "csv", "xlsx"]) {
    byId(`export-${format}`).addEventListener("click", () => exportResults(format));
  }
  byId("export-dashboard").addEventListener("click", exportDashboard);
  byId("export-dashboard-html").addEventListener("click", exportDashboardHtml);
}

function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.documentElement.setAttribute("data-theme", "dark");
    byId("theme-toggle").textContent = "\u2600\uFE0F";
  }
}

function toggleTheme() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  if (isDark) {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("theme", "light");
    byId("theme-toggle").textContent = "\uD83C\uDF19";
  } else {
    document.documentElement.setAttribute("data-theme", "dark");
    localStorage.setItem("theme", "dark");
    byId("theme-toggle").textContent = "\u2600\uFE0F";
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
  watchMapReady();
  const config = await fetchJson(`/api/config?t=${Date.now()}`, { cache: "no-store" });
  if (!config.map_enabled) {
    hidePlaceholder();
    showMapPlaceholder("Yandex API-ключ не настроен. Получите ключ на developer.tech.yandex.ru");
    return;
  }
  const script = document.createElement("script");
  let mapReady = false;
  const fallbackTimer = setTimeout(() => {
    if (!mapReady) {
      hidePlaceholder();
      showMapPlaceholder("Yandex Maps не загрузился. Проверьте ключ и подключение.");
    }
  }, 12000);
  script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(config.yandex_maps_api_key)}&lang=ru_RU`;
  script.onload = () => {
    if (typeof ymaps === "undefined") {
      clearTimeout(fallbackTimer);
      hidePlaceholder();
      showMapPlaceholder("Yandex Maps API недоступен.");
      return;
    }
    let readyFired = false;
    const tryCreateMap = () => {
      if (readyFired) return;
      if (typeof ymaps !== "undefined" && typeof ymaps.Map === "function") {
        readyFired = true;
        clearTimeout(fallbackTimer);
        mapReady = true;
        hidePlaceholder();
        createMap();
      }
    };
    const readyTimer = setTimeout(tryCreateMap, 2000);
    ymaps.ready(() => {
      if (readyFired) return;
      readyFired = true;
      clearTimeout(readyTimer);
      clearTimeout(fallbackTimer);
      mapReady = true;
      hidePlaceholder();
      createMap();
    }, () => {
      setTimeout(tryCreateMap, 500);
    });
  };
  script.onerror = () => {
    clearTimeout(fallbackTimer);
    hidePlaceholder();
    showMapPlaceholder("Не удалось загрузить Yandex Maps API. Проверьте подключение.");
  };
  document.head.append(script);
}

function createMap() {
  hidePlaceholder();
  try {
    state.map = new ymaps.Map("map", { center: [55.751244, 37.618423], zoom: 10, controls: ["zoomControl", "geolocationControl"] });
    state.map.behaviors.enable(["drag", "scrollZoom", "dblClickZoom", "multiTouch"]);
    state.clusterer = new ymaps.Clusterer({ preset: "islands#blueClusterIcons", groupByCoordinates: false });
    state.map.geoObjects.add(state.clusterer);
    state.map.events.add("mousedown", onMapMouseDown);
    state.map.events.add("mouseup", onMapMouseUp);
    state.map.events.add("click", onMapClick);
    state.map.events.add("dblclick", finishPolygon);
  } catch (e) {
    console.error("Yandex Map init failed:", e);
    showMapPlaceholder("Yandex Maps не смог создать карту.");
  }
}

function eventCoordinates(event) {
  return event.get("coords");
}

function setDrawMode(mode) {
  if (!state.map) return showStatus("Для выбора области требуется настроенная карта.", true);
  clearArea();
  state.mode = mode;
  setMapDragging(mode !== "rectangle");
  byId("move-map-button").classList.remove("active");
  byId("rectangle-button").classList.toggle("active", mode === "rectangle");
  byId("polygon-button").classList.toggle("active", mode === "polygon");
  showStatus(mode === "rectangle" ? "Зажмите мышь и протяните прямоугольник." : "Кликайте вершины полигона; двойной клик завершает.");
}

function onMapMouseDown(event) {
  if (state.mode === "rectangle") state.rectangleStart = eventCoordinates(event);
}

function onMapMouseUp(event) {
  if (state.mode !== "rectangle" || !state.rectangleStart) return;
  const finish = eventCoordinates(event);
  const south = Math.min(state.rectangleStart[0], finish[0]);
  const north = Math.max(state.rectangleStart[0], finish[0]);
  const west = Math.min(state.rectangleStart[1], finish[1]);
  const east = Math.max(state.rectangleStart[1], finish[1]);
  setArea({ type: "bbox", coordinates: [west, south, east, north] });
  state.rectangleStart = null;
}

function onMapClick(event) {
  if (state.mode !== "polygon") return;
  const [lat, lon] = eventCoordinates(event);
  state.polygonPoints.push([lon, lat]);
  drawPolygonPreview();
}

function finishPolygon(event) {
  if (state.mode !== "polygon" || state.polygonPoints.length < 3) return;
  if (event.preventDefault) event.preventDefault();
  if (event.originalEvent?.preventDefault) event.originalEvent.preventDefault();
  const coordinates = [...state.polygonPoints, state.polygonPoints[0]];
  setArea({ type: "polygon", coordinates });
}

function setArea(area) {
  clearAreaObject();
  state.area = area;
  state.mode = null;
  byId("rectangle-button").classList.remove("active");
  byId("polygon-button").classList.remove("active");
  byId("move-map-button").classList.add("active");
  if (area.type === "bbox") {
    const [west, south, east, north] = area.coordinates;
    state.areaObject = new ymaps.Rectangle([[south, west], [north, east]], {}, areaStyle());
  } else {
    state.areaObject = new ymaps.Polygon([area.coordinates.map(([lon, lat]) => [lat, lon])], {}, areaStyle());
  }
  state.map.geoObjects.add(state.areaObject);
  setMapDragging(true);
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
  if (state.map && state.areaObject) {
    state.map.geoObjects.remove(state.areaObject);
  }
  state.areaObject = null;
}

function clearArea() {
  clearAreaObject();
  state.area = null;
  state.mode = null;
  state.polygonPoints = [];
  state.rectangleStart = null;
  setMapDragging(true);
  byId("move-map-button").classList.add("active");
  byId("rectangle-button").classList.remove("active");
  byId("polygon-button").classList.remove("active");
}

function enableMapMovement() {
  if (!state.map) return showStatus("Карта ещё не загружена.", true);
  state.mode = null;
  state.polygonPoints = [];
  state.rectangleStart = null;
  setMapDragging(true);
  byId("move-map-button").classList.add("active");
  byId("rectangle-button").classList.remove("active");
  byId("polygon-button").classList.remove("active");
  showStatus("Режим перемещения карты включён.");
}

function setMapDragging(enabled) {
  if (!state.map) return;
  state.map.behaviors[enabled ? "enable" : "disable"]("drag");
  if (enabled) state.map.behaviors.enable(["scrollZoom", "dblClickZoom", "multiTouch"]);
}

async function searchAddress() {
  const address = byId("address").value.trim();
  if (!address) return showStatus("Введите адрес для поиска на карте.", true);
  if (!state.map) return showStatus("Для поиска адреса требуется работающая карта.", true);
  showStatus("Ищу адрес...");
  try {
    const item = await fetchJson(`/api/geocode?address=${encodeURIComponent(address)}`);
    const coordinates = [item.latitude, item.longitude];
    const addressLine = item.address;
    state.map.setCenter(coordinates, 16, { duration: 300 });
    if (state.addressMarker) state.map.geoObjects.remove(state.addressMarker);
    state.addressMarker = new ymaps.Placemark(coordinates, { balloonContentHeader: escapeHtml(addressLine) }, { preset: "islands#redIcon" });
    state.map.geoObjects.add(state.addressMarker);
    enableMapMovement();
    hideAddressSuggestions();
    showStatus(`Адрес найден: ${addressLine}`);
  } catch (error) {
    showStatus(`Не удалось найти адрес: ${error.message || error}`, true);
  }
}

function scheduleAddressSuggestions() {
  clearTimeout(state.addressSuggestTimer);
  const address = byId("address").value.trim();
  state.selectedSuggestion = -1;
  if (address.length < 2) return hideAddressSuggestions();
  state.addressSuggestTimer = setTimeout(() => loadAddressSuggestions(address), 250);
}

async function loadAddressSuggestions(address) {
  const requestId = ++state.addressSuggestRequest;
  try {
    const items = await fetchJson(`/api/geocode/suggest?address=${encodeURIComponent(address)}`);
    if (requestId !== state.addressSuggestRequest || byId("address").value.trim() !== address) return;
    renderAddressSuggestions(items, address);
  } catch {
    if (requestId === state.addressSuggestRequest) hideAddressSuggestions();
  }
}

function onAddressKeydown(event) {
  const list = byId("address-suggestions");
  const items = list.querySelectorAll(".address-suggestion");
  if (list.hidden || items.length === 0) {
    if (event.key === "Enter") { event.preventDefault(); searchAddress(); }
    if (event.key === "Escape") hideAddressSuggestions();
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.selectedSuggestion = Math.min(state.selectedSuggestion + 1, items.length - 1);
    highlightSuggestion(items);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    state.selectedSuggestion = Math.max(state.selectedSuggestion - 1, 0);
    highlightSuggestion(items);
  } else if (event.key === "Enter") {
    event.preventDefault();
    if (state.selectedSuggestion >= 0 && state.selectedSuggestion < items.length) {
      items[state.selectedSuggestion].click();
    } else {
      hideAddressSuggestions();
      searchAddress();
    }
  } else if (event.key === "Escape") {
    hideAddressSuggestions();
  }
}

function highlightSuggestion(items) {
  items.forEach((el, i) => {
    el.classList.toggle("active", i === state.selectedSuggestion);
    if (i === state.selectedSuggestion) el.scrollIntoView({ block: "nearest" });
  });
}

function renderAddressSuggestions(items, query) {
  const list = byId("address-suggestions");
  list.textContent = "";
  state.selectedSuggestion = -1;
  const q = query.toLowerCase();
  for (const item of items) {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "address-suggestion";
    option.setAttribute("role", "option");
    const name = item.name || item.address;
    const desc = item.description || "";
    if (name.toLowerCase().includes(q)) {
      const idx = name.toLowerCase().indexOf(q);
      option.innerHTML =
        escapeHtml(name.slice(0, idx)) +
        "<b>" + escapeHtml(name.slice(idx, idx + q.length)) + "</b>" +
        escapeHtml(name.slice(idx + q.length));
    } else {
      option.textContent = name;
    }
    if (desc) {
      const sub = document.createElement("span");
      sub.className = "suggestion-desc";
      sub.textContent = desc;
      option.append(sub);
    }
    option.addEventListener("mousedown", (e) => {
      e.preventDefault();
      byId("address").value = name;
      hideAddressSuggestions();
      searchAddress();
    });
    list.append(option);
  }
  list.hidden = items.length === 0;
  byId("address").setAttribute("aria-expanded", String(items.length > 0));
}

function hideAddressSuggestions() {
  const list = byId("address-suggestions");
  list.hidden = true;
  list.textContent = "";
  byId("address").setAttribute("aria-expanded", "false");
}

function importYandexUrl() {
  const raw = byId("yandex-url").value.trim();
  if (!raw) return showStatus("Вставьте ссылку с Яндекс Карт.", true);
  let url;
  try { url = new URL(raw); } catch { return showStatus("Некорректный URL.", true); }
  const params = url.searchParams;
  let text = params.get("text") || params.get("pt") || "";
  if (!text) {
    const pathMatch = url.pathname.match(/\/search\/([^/]+)/);
    if (pathMatch) text = decodeURIComponent(pathMatch[1]);
  }
  const ll = params.get("ll");
  const spn = params.get("spn") || params.get("sspn");
  const z = parseFloat(params.get("z")) || 12;
  if (!ll) return showStatus("В ссылке нет координат (параметр ll).", true);
  const [lon, lat] = ll.split(",").map(Number);
  if (isNaN(lon) || isNaN(lat)) return showStatus("Некорректные координаты в ll.", true);
  if (text) byId("query").value = text;
  let bbox;
  if (spn) {
    const [dx, dy] = spn.split(",").map(Number);
    if (!isNaN(dx) && !isNaN(dy)) {
      bbox = { type: "bbox", coordinates: [lon - dx / 2, lat - dy / 2, lon + dx / 2, lat + dy / 2] };
    }
  }
  if (!bbox) {
    const factor = 0.02 * Math.pow(2, 12 - z);
    bbox = { type: "bbox", coordinates: [lon - factor, lat - factor, lon + factor, lat + factor] };
  }
  setArea(bbox);
  if (state.map) state.map.setCenter([lat, lon], z, { duration: 300 });
  showStatus(`Импортировано: "${text}" — область установлена.`);
}

async function startJob() {
  const query = byId("query").value.trim();
  if (!query) return showStatus("Введите поисковый запрос.", true);
  if (!state.area) {
    const visibleArea = currentMapArea();
    if (!visibleArea) return showStatus("Карта ещё не готова.", true);
    setArea(visibleArea);
  }
  resetResults();
  byId("start-button").disabled = true;
  showStatus("Создаю задачу и запускаю фоновый парсер...");
  try {
    const job = await fetchJson("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, area: state.area, params: collectParams() }),
    });
    state.jobId = job.id;
    byId("stop-button").disabled = false;
    renderJob(job);
    pollJob();
  } catch (error) {
    byId("start-button").disabled = false;
    showStatus(error.message, true);
  }
}

function currentMapArea() {
  if (!state.map) return { type: "bbox", coordinates: [37.5, 55.7, 37.8, 55.8] };
  try {
    const bounds = state.map.getBounds();
    return { type: "bbox", coordinates: [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]] };
  } catch {
    return { type: "bbox", coordinates: [37.5, 55.7, 37.8, 55.8] };
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
      if (job.status === "completed" && job.found > 0 && !state.dashboardOpened) {
        state.dashboardOpened = true;
        window.location.href = `/api/jobs/${state.jobId}/dashboard.html`;
      }
    }
  } catch (error) {
    showStatus(error.message, true);
    state.pollTimer = setTimeout(pollJob, 2000);
  }
}

function renderJob(job) {
  const progress = byId("progress");
  progress.style.width = `${job.progress}%`;
  progress.classList.toggle("indeterminate", job.status === "running" && job.progress === 0);
  byId("progress-text").textContent = `${job.progress}% · ${job.message || job.status}`;
  byId("found-count").textContent = `Найдено: ${job.found}`;
  showStatus(job.error || job.message, job.status === "failed");
}

function renderResults(items) {
  for (let i = 0; i < items.length; i++) {
    const company = items[i];
    const key = company.dedupe_key || company.yandex_id || company.url || `${company.name}-${company.address}`;
    if (state.resultIds.has(key)) continue;
    state.resultIds.add(key);
    const row = document.createElement("tr");
    row.style.cursor = "pointer";
    row.title = "Нажмите для просмотра деталей";
    row.innerHTML = `<td>${escapeHtml(company.name || "")}</td><td>${escapeHtml(company.address || "")}</td><td>${escapeHtml(formatPhones(company.phones))}</td><td>${escapeHtml(company.rating || "")}</td>`;
    const bizIndex = state.totalResults;
    state.totalResults++;
    row.addEventListener("click", () => {
      if (state.jobId) window.open(`/business/${state.jobId}/${bizIndex}`, "_blank");
    });
    row.addEventListener("mouseenter", () => row.style.background = "#f0f7ff");
    row.addEventListener("mouseleave", () => row.style.background = "");
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
  state.totalResults = 0;
  state.dashboardOpened = false;
  byId("results-body").textContent = "";
  byId("found-count").textContent = "Найдено: 0";
  byId("progress").style.width = "0%";
  byId("progress").classList.remove("indeterminate");
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

function exportDashboard() {
  if (!state.jobId) return showStatus("Сначала запустите задачу.", true);
  window.location.href = `/api/jobs/${state.jobId}/dashboard`;
}

function exportDashboardHtml() {
  if (!state.jobId) return showStatus("Сначала запустите задачу.", true);
  window.open(`/api/jobs/${state.jobId}/dashboard.html`, "_blank");
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
