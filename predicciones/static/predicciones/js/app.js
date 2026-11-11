(() => {
  const body = document.body;
  const sidebar = document.getElementById("sidebar");
  const mobileButton = document.getElementById("mobile-menu");
  const isDashboard = body.dataset.dashboard === "true";
  const panels = [...document.querySelectorAll("[data-view-panel]")];
  const navButtons = [...document.querySelectorAll("[data-view-target]")];
  const titles = {
    inicio: "Centro de crecimiento",
    prediccion: "Planificá el próximo mes",
    registros: "Registros mensuales",
    marketing: "Rendimiento de marketing",
    retencion: "Retención de socios",
    finanzas: "Pulso financiero",
    planes: "Planes y cobros",
  };

  function showView(name, updateHash = true) {
    const target = panels.some((panel) => panel.dataset.viewPanel === name) ? name : "inicio";
    panels.forEach((panel) => {
      const active = panel.dataset.viewPanel === target;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    navButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.viewTarget === target));
    const breadcrumb = document.getElementById("breadcrumb-title");
    if (breadcrumb) breadcrumb.textContent = titles[target] || "GymPredictAI";
    if (updateHash && location.hash !== `#${target}`) history.replaceState(null, "", `#${target}`);
    if (sidebar) sidebar.classList.remove("is-open");
    if (mobileButton) mobileButton.setAttribute("aria-expanded", "false");
    requestAnimationFrame(() => renderCharts());
  }

  if (isDashboard && panels.length) {
    const initialView = location.hash.replace("#", "") || body.dataset.initialView || "inicio";
    showView(initialView, false);
    navButtons.forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewTarget)));
    window.addEventListener("hashchange", () => showView(location.hash.replace("#", ""), false));
  }

  if (mobileButton && sidebar) {
    mobileButton.addEventListener("click", () => {
      const open = sidebar.classList.toggle("is-open");
      mobileButton.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("pointerdown", (event) => {
      if (!sidebar.contains(event.target) && !mobileButton.contains(event.target)) {
        sidebar.classList.remove("is-open");
        mobileButton.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll(".toast-close").forEach((button) => button.addEventListener("click", () => button.closest(".toast")?.remove()));

  const launch = document.getElementById("assistant-launch");
  const panel = document.getElementById("assistant-panel");
  const close = document.getElementById("assistant-close");
  const answerBox = document.getElementById("assistant-answer");
  const questionInput = document.getElementById("assistant-question");
  const contextNode = document.getElementById("gym-assistant-data");
  let context = {};
  try { context = contextNode ? (JSON.parse(contextNode.textContent || "{}") || {}) : {}; } catch { context = {}; }

  function openAssistant() {
    if (!panel) return;
    panel.hidden = false;
    questionInput?.focus();
  }
  function closeAssistant() { if (panel) panel.hidden = true; }
  launch?.addEventListener("click", () => panel?.hidden ? openAssistant() : closeAssistant());
  close?.addEventListener("click", closeAssistant);
  document.getElementById("help-open")?.addEventListener("click", openAssistant);

  function answerQuestion(question) {
    const q = question.toLocaleLowerCase("es-AR");
    const months = Number(context.meses || 0);
    let answer;
    if (q.includes("predic") || q.includes("pronost")) {
      answer = months < 12
        ? `Hay ${months} meses cargados. El pronóstico necesita al menos 12; con 24 a 36 períodos se puede observar mejor la estacionalidad.`
        : `Se comparan Random Forest y un promedio reciente-estacional con un backtest cronológico. Para el último período, la tasa de conversión histórica fue ${context.conversion || 0}% y las bajas representaron ${context.tasa_bajas || 0}% de los socios al inicio.`;
    } else if (q.includes("primero") || q.includes("empez")) {
      answer = months < 12
        ? "Empezá revisando que el CSV esté importado y completá los meses faltantes. Cada registro mensual incluye socios, consultas, pruebas, inversión, cuota, altas y bajas."
        : "Primero revisá que el último mes esté completo. Después compará el pronóstico con el promedio reciente-estacional y probá un escenario sin guardar cambios.";
    } else if (q.includes("marketing") || q.includes("campaña") || q.includes("campana")) {
      answer = "El CSV trae inversión publicitaria mensual, pero no alcance por red ni resultados por campaña. En Marketing podés cargar esos datos manualmente para comparar canales; el costo por alta es descriptivo y no prueba causalidad.";
    } else if (q.includes("baja") || q.includes("retenci")) {
      answer = "Retención muestra bajas agregadas divididas por socios al inicio. No identifica personas ni el motivo de cada cancelación. Usalo para detectar meses que conviene revisar.";
    } else if (q.includes("finanza") || q.includes("ingreso")) {
      answer = "El ingreso mensual se estima multiplicando socios activos estimados por la última cuota registrada. No descuenta costos, morosidad ni impuestos; por eso no equivale a ganancia.";
    } else {
      answer = "Puedo explicarte predicciones, registros, marketing, retención o finanzas. También podés abrir una sección desde el menú lateral.";
    }
    if (answerBox) {
      answerBox.textContent = answer;
      answerBox.hidden = false;
    }
    if (questionInput) questionInput.value = question;
  }

  document.querySelectorAll("[data-assistant-question]").forEach((button) => button.addEventListener("click", () => answerQuestion(button.dataset.assistantQuestion || "")));
  document.getElementById("assistant-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const question = questionInput?.value.trim();
    if (question) answerQuestion(question);
  });

  document.querySelectorAll("[data-plan-select]").forEach((button) => button.addEventListener("click", () => {
    const selection = document.getElementById("plan-selection");
    if (!selection) return;
    selection.textContent = `Seleccionaste el plan ${button.dataset.planSelect}. No se inició ningún cobro: falta configurar Mercado Pago.`;
    selection.hidden = false;
    document.querySelectorAll("[data-plan-select]").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
  }));

  const chartDataNode = document.getElementById("gym-chart-data");
  const seasonalNode = document.getElementById("gym-seasonal-data");
  let chartData = { labels: [], altas: [], bajas: [], socios: [], inversion: [] };
  let seasonalData = [];
  try { if (chartDataNode) chartData = JSON.parse(chartDataNode.textContent); } catch { /* el resto del panel sigue disponible */ }
  try { if (seasonalNode) seasonalData = JSON.parse(seasonalNode.textContent); } catch { seasonalData = []; }
  const createdCharts = new WeakMap();

  function chartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#a8aab2", usePointStyle: true, boxWidth: 7, font: { size: 10 } } },
        tooltip: { backgroundColor: "#1b1c20", borderColor: "#3b3c42", borderWidth: 1, titleColor: "#fff", bodyColor: "#d4d5d9", padding: 10 },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#858891", font: { size: 9 } }, border: { display: false } },
        y: { beginAtZero: true, grid: { color: "#ffffff0b" }, ticks: { color: "#858891", precision: 0, font: { size: 9 } }, border: { display: false } },
      },
    };
  }

  function createChart(canvas, config) {
    if (!canvas || canvas.offsetParent === null) return;
    if (window.Chart) {
      if (createdCharts.has(canvas)) { createdCharts.get(canvas).resize(); return; }
      createdCharts.set(canvas, new window.Chart(canvas, config));
      return;
    }
    drawCanvasFallback(canvas, config.data.labels, config.data.datasets);
  }

  function drawCanvasFallback(canvas, labels, datasets) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    const w = rect.width, h = rect.height, pad = { l: 34, r: 12, t: 12, b: 28 };
    const series = datasets.filter((d) => Array.isArray(d.data));
    const max = Math.max(1, ...series.flatMap((d) => d.data.map(Number)));
    ctx.strokeStyle = "rgba(255,255,255,.07)";
    ctx.fillStyle = "#858891";
    ctx.font = "9px Inter, sans-serif";
    for (let i = 0; i < 4; i++) {
      const y = pad.t + (h - pad.t - pad.b) * i / 3;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.fillText(String(Math.round(max * (3 - i) / 3)), 2, y + 3);
    }
    const span = (w - pad.l - pad.r) / Math.max(1, labels.length - 1);
    labels.forEach((label, i) => { if (i % Math.ceil(labels.length / 6) === 0) ctx.fillText(label, pad.l + i * span - 8, h - 7); });
    series.forEach((dataset) => {
      ctx.strokeStyle = dataset.borderColor || dataset.backgroundColor || "#d71920";
      ctx.fillStyle = dataset.backgroundColor || dataset.borderColor || "#d71920";
      ctx.lineWidth = 2;
      ctx.beginPath();
      dataset.data.forEach((value, i) => {
        const x = pad.l + i * span;
        const y = h - pad.b - Number(value) / max * (h - pad.t - pad.b);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
    });
  }

  function renderCharts() {
    if (!isDashboard) return;
    const base = chartOptions();
    createChart(document.getElementById("growth-chart"), {
      type: "bar",
      data: { labels: chartData.labels, datasets: [
        { type: "bar", label: "Altas", data: chartData.altas, backgroundColor: "#d71920bb", borderRadius: 4, maxBarThickness: 18 },
        { type: "bar", label: "Bajas", data: chartData.bajas, backgroundColor: "#f1cb52bb", borderRadius: 4, maxBarThickness: 18 },
        { type: "line", label: "Socios al cierre", data: chartData.socios, borderColor: "#73a7ff", backgroundColor: "#73a7ff", borderWidth: 2, pointRadius: 2, tension: .3, yAxisID: "y" },
      ] }, options: base,
    });
    createChart(document.getElementById("retention-chart"), {
      type: "line",
      data: { labels: chartData.labels, datasets: [
        { label: "Bajas", data: chartData.bajas, borderColor: "#f1cb52", backgroundColor: "#f1cb5220", fill: true, tension: .3, pointRadius: 2 },
        { label: "Socios al cierre", data: chartData.socios, borderColor: "#73a7ff", tension: .3, pointRadius: 2 },
      ] }, options: base,
    });
    createChart(document.getElementById("finance-chart"), {
      type: "bar",
      data: { labels: chartData.labels, datasets: [
        { label: "Inversión publicitaria · ARS", data: chartData.inversion, backgroundColor: "#d71920bb", borderRadius: 4, maxBarThickness: 20 },
      ] }, options: base,
    });
    createChart(document.getElementById("seasonal-chart"), {
      type: "bar",
      data: { labels: seasonalData.map((item) => item.mes.slice(0, 3)), datasets: [
        { label: "Promedio de altas", data: seasonalData.map((item) => item.promedio), backgroundColor: seasonalData.map((item) => item.promedio > 0 && item.promedio >= Math.max(...seasonalData.map((row) => row.promedio)) * .95 ? "#d71920cc" : "#41434b"), borderRadius: 5, maxBarThickness: 25 },
      ] }, options: base,
    });
  }
  window.addEventListener("resize", () => { createdCharts && renderCharts(); });
  if (isDashboard) requestAnimationFrame(renderCharts);
})();
