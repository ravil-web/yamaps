const state = {
  map: null,
  mapProvider: null,
  clusterer: null,
  areaObject: null,
  addressMarker: null,
  resultMarkers: [],
  area: null,
  mode: null,
  polygonPoints: [],
  rectangleStart: null,
  jobId: null,
  pollTimer: null,
  addressSuggestTimer: null,
  addressSuggestRequest: 0,
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
  byId("address-search-button").addEventListener("click", searchAddress);
  byId("address").addEventListener("input", scheduleAddressSuggestions);
  byId("address").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchAddress();
    } else if (event.key === "Escape") {
      hideAddressSuggestions();
    }
  });
  byId("address").addEventListener("blur", () => setTimeout(hideAddressSuggestions, 150));
  byId("move-map-button").addEventListener("click", enableMapMovement);
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
  const config = await fetchJson(`/api/config?t=${Date.now()}`, { cache: "no-store" });
  if (!config.map_enabled) {
    await initializeFallbackMap("Yandex API-ключ не настроен. Включена резервная OpenStreetMap.");
    return;
  }
  const script = document.createElement("script");
  const fallbackTimer = setTimeout(() => {
    const hasMapTiles = byId("map").querySelectorAll("img").length > 0;
    if (!hasMapTiles) initializeFallbackMap("Yandex Maps не загрузил карту. Включена резервная OpenStreetMap.");
  }, 4500);
  script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(config.yandex_maps_api_key)}&lang=ru_RU`;
  script.onload = () => {
    if (typeof ymaps === "undefined") {
      clearTimeout(fallbackTimer);
      initializeFallbackMap("Yandex Maps отклонил ключ. Включена резервная OpenStreetMap.");
      return;
    }
    ymaps.ready(() => {
      clearTimeout(fallbackTimer);
      createMap();
    }, () => {
      clearTimeout(fallbackTimer);
      initializeFallbackMap("Yandex Maps отклонил ключ. Включена резервная OpenStreetMap.");
    });
  };
  script.onerror = () => {
    clearTimeout(fallbackTimer);
    initializeFallbackMap("Yandex Maps недоступен. Включена резервная OpenStreetMap.");
  };
  document.head.append(script);
}

function createMap() {
  byId("map-placeholder").hidden = true;
  state.map = new ymaps.Map("map", { center: [55.751244, 37.618423], zoom: 10, controls: ["zoomControl", "geolocationControl"] });
  state.mapProvider = "yandex";
  state.map.behaviors.enable(["drag", "scrollZoom", "dblClickZoom", "multiTouch"]);
  state.clusterer = new ymaps.Clusterer({ preset: "islands#blueClusterIcons", groupByCoordinates: false });
  state.map.geoObjects.add(state.clusterer);
  state.map.events.add("mousedown", onMapMouseDown);
  state.map.events.add("mouseup", onMapMouseUp);
  state.map.events.add("click", onMapClick);
  state.map.events.add("dblclick", finishPolygon);
  setTimeout(() => {
    if (state.mapProvider === "yandex" && byId("map").querySelectorAll("img").length === 0) {
      initializeFallbackMap("Yandex Maps отклонил ключ. Включена резервная OpenStreetMap.");
    }
  }, 2500);
}

async function initializeFallbackMap(message) {
  try {
    if (state.mapProvider === "leaflet") return;
    if (state.mapProvider === "yandex" && state.map?.destroy) state.map.destroy();
    if (!document.querySelector('link[data-leaflet]')) {
      const style = document.createElement("link");
      style.rel = "stylesheet";
      style.href = "/static/vendor/leaflet/leaflet.css";
      style.dataset.leaflet = "true";
      document.head.append(style);
    }
    if (typeof L === "undefined") {
      await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "/static/vendor/leaflet/leaflet.js";
        script.onload = resolve;
        script.onerror = reject;
        document.head.append(script);
      });
    }
    byId("map-placeholder").hidden = true;
    byId("map").textContent = "";
    state.mapProvider = "leaflet";
    state.map = L.map("map", { doubleClickZoom: false }).setView([55.751244, 37.618423], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap",
    }).addTo(state.map);
    state.clusterer = L.layerGroup().addTo(state.map);
    state.map.on("mousedown", onMapMouseDown);
    state.map.on("mouseup", onMapMouseUp);
    state.map.on("click", onMapClick);
    state.map.on("dblclick", finishPolygon);
    showStatus(message);
  } catch {
    showMapPlaceholder("Не удалось загрузить ни Yandex Maps, ни резервную OpenStreetMap. Проверьте подключение.");
  }
}

function eventCoordinates(event) {
  if (state.mapProvider === "leaflet") return [event.latlng.lat, event.latlng.lng];
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
    state.areaObject = state.mapProvider === "leaflet"
      ? L.rectangle([[south, west], [north, east]], leafletAreaStyle())
      : new ymaps.Rectangle([[south, west], [north, east]], {}, areaStyle());
  } else {
    state.areaObject = state.mapProvider === "leaflet"
      ? L.polygon(area.coordinates.map(([lon, lat]) => [lat, lon]), leafletAreaStyle())
      : new ymaps.Polygon([area.coordinates.map(([lon, lat]) => [lat, lon])], {}, areaStyle());
  }
  addMapObject(state.areaObject);
  setMapDragging(true);
  showStatus("Область поиска выбрана.");
}

function drawPolygonPreview() {
  clearAreaObject();
  if (state.polygonPoints.length < 2) return;
  state.areaObject = state.mapProvider === "leaflet"
    ? L.polyline(state.polygonPoints.map(([lon, lat]) => [lat, lon]), leafletAreaStyle())
    : new ymaps.Polyline(state.polygonPoints.map(([lon, lat]) => [lat, lon]), {}, areaStyle());
  addMapObject(state.areaObject);
}

function areaStyle() {
  return { strokeColor: "#2563eb", strokeWidth: 3, fillColor: "#2563eb22" };
}

function leafletAreaStyle() {
  return { color: "#2563eb", weight: 3, fillColor: "#2563eb", fillOpacity: 0.15 };
}

function addMapObject(object) {
  if (state.mapProvider === "leaflet") object.addTo(state.map);
  else state.map.geoObjects.add(object);
}

function clearAreaObject() {
  if (state.map && state.areaObject) {
    if (state.mapProvider === "leaflet") state.map.removeLayer(state.areaObject);
    else state.map.geoObjects.remove(state.areaObject);
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
  if (state.mapProvider === "leaflet") {
    state.map.dragging[enabled ? "enable" : "disable"]();
    state.map.scrollWheelZoom.enable();
  } else {
    state.map.behaviors[enabled ? "enable" : "disable"]("drag");
    if (enabled) state.map.behaviors.enable(["scrollZoom", "dblClickZoom", "multiTouch"]);
  }
}

async function searchAddress() {
  const address = byId("address").value.trim();
  if (!address) return showStatus("Введите адрес для поиска на карте.", true);
  if (!state.map) return showStatus("Для поиска адреса требуется работающая карта.", true);
  showStatus("Ищу адрес...");
  try {
    let coordinates;
    let addressLine;
    if (state.mapProvider === "leaflet") {
      const item = await fetchJson(`/api/geocode?address=${encodeURIComponent(address)}`);
      coordinates = [item.latitude, item.longitude];
      addressLine = item.address;
      state.map.setView(coordinates, 16);
      if (state.addressMarker) state.map.removeLayer(state.addressMarker);
      state.addressMarker = L.marker(coordinates).bindPopup(escapeHtml(addressLine)).addTo(state.map).openPopup();
    } else {
      const result = await ymaps.geocode(address, { results: 1 });
      const object = result.geoObjects.get(0);
      if (!object) return showStatus("Адрес не найден.", true);
      coordinates = object.geometry.getCoordinates();
      addressLine = object.getAddressLine() || address;
      state.map.setCenter(coordinates, 16, { duration: 300 });
      if (state.addressMarker) state.map.geoObjects.remove(state.addressMarker);
      state.addressMarker = new ymaps.Placemark(coordinates, { balloonContentHeader: escapeHtml(addressLine) }, { preset: "islands#redIcon" });
      state.map.geoObjects.add(state.addressMarker);
    }
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
  if (address.length < 3) return hideAddressSuggestions();
  state.addressSuggestTimer = setTimeout(() => loadAddressSuggestions(address), 300);
}

async function loadAddressSuggestions(address) {
  const requestId = ++state.addressSuggestRequest;
  try {
    const items = await fetchJson(`/api/geocode/suggest?address=${encodeURIComponent(address)}`);
    if (requestId !== state.addressSuggestRequest || byId("address").value.trim() !== address) return;
    renderAddressSuggestions(items);
  } catch {
    if (requestId === state.addressSuggestRequest) hideAddressSuggestions();
  }
}

function renderAddressSuggestions(items) {
  const list = byId("address-suggestions");
  list.textContent = "";
  for (const item of items) {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "address-suggestion";
    option.setAttribute("role", "option");
    option.textContent = item.address;
    option.addEventListener("click", () => {
      byId("address").value = item.address;
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

async function startJob() {
  const query = byId("query").value.trim();
  if (!query) return showStatus("Введите поисковый запрос.", true);
  if (!state.area) {
    const visibleArea = currentMapArea();
    if (!visibleArea) return showStatus("Карта ещё не готова. Дождитесь загрузки и повторите запуск.", true);
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
  if (!state.map) return null;
  if (state.mapProvider === "leaflet") {
    const bounds = state.map.getBounds();
    return {
      type: "bbox",
      coordinates: [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()],
    };
  }
  const bounds = state.map.getBounds();
  return {
    type: "bbox",
    coordinates: [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]],
  };
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
  const progress = byId("progress");
  progress.style.width = `${job.progress}%`;
  progress.classList.toggle("indeterminate", job.status === "running" && job.progress === 0);
  byId("progress-text").textContent = `${job.progress}% · ${job.message || job.status}`;
  byId("found-count").textContent = `Найдено: ${job.found}`;
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
  if (state.mapProvider === "leaflet") {
    const marker = L.marker([company.latitude, company.longitude])
      .bindPopup(`<strong>${escapeHtml(company.name || "")}</strong><br>${escapeHtml(company.address || "")}<br>${escapeHtml(formatPhones(company.phones))}`);
    state.clusterer.addLayer(marker);
    state.resultMarkers.push(marker);
    return;
  }
  const marker = new ymaps.Placemark([company.latitude, company.longitude], {
    balloonContentHeader: escapeHtml(company.name || ""),
    balloonContentBody: `${escapeHtml(company.address || "")}<br>${escapeHtml(formatPhones(company.phones))}`,
  });
  state.clusterer.add(marker);
}

function resetResults() {
  state.resultIds.clear();
  byId("results-body").textContent = "";
  byId("found-count").textContent = "Найдено: 0";
  byId("progress").style.width = "0%";
  byId("progress").classList.remove("indeterminate");
  if (state.clusterer) {
    if (state.mapProvider === "leaflet") state.clusterer.clearLayers();
    else state.clusterer.removeAll();
  }
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
