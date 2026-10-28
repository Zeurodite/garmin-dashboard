"""Lee garmin_data.json y genera dashboard.html (todo local, sin servidor)."""
import json
from pathlib import Path

CARPETA = Path(__file__).parent
datos = json.loads((CARPETA / "garmin_data.json").read_text(encoding="utf-8"))
datos_js = json.dumps(datos).replace("</", "<\\/")

PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mi entrenamiento</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {
    --fondo: #eef1f4;
    --papel: #ffffff;
    --tinta: #15202b;
    --tinta-suave: #5b6773;
    --linea: #d9dfe5;
    --moderada: #6fa8a0;
    --vigorosa: #d1495b;
    --pasos: #2f5d8a;
    --calorias: #e0a030;
    --pulso: #7a4eab;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--fondo); color: var(--tinta);
    font-family: "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
    line-height: 1.5;
  }
  main { max-width: 1040px; margin: 0 auto; padding: 28px 18px 60px; }
  header { display: flex; flex-wrap: wrap; gap: 12px; align-items: end; justify-content: space-between; }
  h1 { margin: 0; font-size: 1.5rem; font-weight: 650; }
  .sub { margin: 2px 0 0; color: var(--tinta-suave); font-size: .9rem; }
  .rango { display: flex; gap: 6px; }
  .rango button {
    font: inherit; font-size: .9rem; padding: 6px 14px; border-radius: 6px;
    border: 1px solid var(--linea); background: var(--papel); color: var(--tinta); cursor: pointer;
  }
  .rango button[aria-pressed="true"] { background: var(--tinta); color: #fff; border-color: var(--tinta); }
  button:focus-visible { outline: 3px solid var(--pasos); outline-offset: 2px; }

  .semana { margin: 26px 0 8px; background: var(--papel); border-radius: 14px; padding: 22px 24px; }
  .semana .num { font-size: 3.4rem; font-weight: 700; line-height: 1; }
  .semana .num small { font-size: 1.2rem; font-weight: 500; color: var(--tinta-suave); }
  .semana p { margin: 6px 0 14px; color: var(--tinta-suave); }
  .barra { height: 14px; border-radius: 7px; background: var(--fondo); overflow: hidden; display: flex; }
  .barra span { display: block; height: 100%; }

  .resumen { display: grid; grid-template-columns: repeat(4, 1fr); margin: 18px 0 8px; }
  .resumen div { padding: 6px 14px; border-left: 3px solid var(--linea); }
  .resumen b { display: block; font-size: 1.5rem; font-weight: 650; }
  .resumen span { color: var(--tinta-suave); font-size: .85rem; }

  .graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
  .grafica { background: var(--papel); border-radius: 14px; padding: 16px 18px 12px; }
  .grafica.ancha { grid-column: 1 / -1; }
  .grafica h2 { margin: 0 0 2px; font-size: 1rem; font-weight: 650; }
  .grafica p { margin: 0 0 8px; color: var(--tinta-suave); font-size: .82rem; }
  .lienzo { position: relative; height: 230px; }
  .vacio { padding: 40px 0; text-align: center; color: var(--tinta-suave); }

  @media (max-width: 760px) {
    .resumen { grid-template-columns: 1fr 1fr; row-gap: 12px; }
    .graficas { grid-template-columns: 1fr; }
    .semana .num { font-size: 2.8rem; }
  }
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Mi entrenamiento</h1>
      <p class="sub" id="periodo"></p>
    </div>
    <div class="rango" role="group" aria-label="Rango de días">
      <button data-r="7" aria-pressed="false">7 días</button>
      <button data-r="30" aria-pressed="true">30 días</button>
      <button data-r="all" aria-pressed="false">Todo</button>
    </div>
  </header>

  <section class="semana" aria-label="Minutos de intensidad de la semana">
    <div class="num"><span id="sem-total">0</span> <small>de 150 min</small></div>
    <p>Minutos de intensidad en los últimos 7 días. Los vigorosos cuentan doble, igual que en Garmin.</p>
    <div class="barra" id="sem-barra"></div>
  </section>

  <section class="resumen" id="resumen"></section>

  <section class="graficas">
    <div class="grafica ancha">
      <h2>Minutos de intensidad por día</h2>
      <p>Moderados y vigorosos, apilados.</p>
      <div class="lienzo"><canvas id="g-intensidad"></canvas></div>
    </div>
    <div class="grafica">
      <h2>Calorías activas</h2>
      <p>Lo que quemaste moviéndote, sin contar el metabolismo basal.</p>
      <div class="lienzo"><canvas id="g-calorias"></canvas></div>
    </div>
    <div class="grafica">
      <h2>Pasos y meta diaria</h2>
      <p>La línea es tu meta de cada día.</p>
      <div class="lienzo"><canvas id="g-pasos"></canvas></div>
    </div>
    <div class="grafica">
      <h2>Pulso en reposo</h2>
      <p>Latidos por minuto. Bajar con el tiempo suele indicar mejor condición.</p>
      <div class="lienzo"><canvas id="g-pulso"></canvas></div>
    </div>
    <div class="grafica">
      <h2>Body Battery</h2>
      <p>Tu nivel más alto y más bajo de cada día.</p>
      <div class="lienzo"><canvas id="g-bateria"></canvas></div>
    </div>
  </section>
</main>

<script>
const DATOS = __DATOS__;
DATOS.sort((a, b) => a.calendar_date.localeCompare(b.calendar_date));

const C = {
  moderada: "#6fa8a0", vigorosa: "#d1495b", pasos: "#2f5d8a",
  calorias: "#e0a030", pulso: "#7a4eab", linea: "#d9dfe5", suave: "#5b6773"
};
let rango = 30;
const graficas = {};

const num = v => (typeof v === "number" ? v : null);
const prom = arr => {
  const v = arr.filter(x => typeof x === "number");
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
};
const fmt = (v, d = 0) => v === null ? "–" : v.toLocaleString("es", { maximumFractionDigits: d });
const fechaCorta = s => {
  const [, m, d] = s.split("-");
  return Number(d) + "/" + Number(m);
};

function filas() {
  return rango === "all" ? DATOS : DATOS.slice(-rango);
}

function dibujar(id, config) {
  if (graficas[id]) graficas[id].destroy();
  config.options = Object.assign({
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { display: config.data.datasets.length > 1,
      labels: { boxWidth: 12, color: C.suave } } },
    scales: {
      x: { grid: { display: false }, ticks: { color: C.suave, maxTicksLimit: 10, maxRotation: 0 } },
      y: { grid: { color: C.linea }, ticks: { color: C.suave }, beginAtZero: true }
    }
  }, config.options || {});
  graficas[id] = new Chart(document.getElementById(id), config);
}

function semana() {
  const ult = DATOS.slice(-7);
  const mod = ult.reduce((a, d) => a + (d.moderate_intensity_minutes || 0), 0);
  const vig = ult.reduce((a, d) => a + (d.vigorous_intensity_minutes || 0), 0) * 2;
  const total = mod + vig;
  document.getElementById("sem-total").textContent = fmt(total);
  const escala = Math.max(150, total);
  document.getElementById("sem-barra").innerHTML =
    `<span style="width:${mod / escala * 100}%;background:${C.moderada}" title="Moderados: ${mod} min"></span>` +
    `<span style="width:${vig / escala * 100}%;background:${C.vigorosa}" title="Vigorosos (x2): ${vig} min"></span>`;
}

function resumen(f) {
  const cumplidos = f.filter(d => d.total_steps != null && d.daily_step_goal != null
    && d.total_steps >= d.daily_step_goal).length;
  const items = [
    [fmt(prom(f.map(d => d.total_steps))), "pasos al día, en promedio"],
    [fmt(prom(f.map(d => d.active_kilocalories))), "kcal activas al día"],
    [fmt(prom(f.map(d => d.resting_heart_rate))), "pulso en reposo promedio"],
    [cumplidos + " de " + f.length, "días con la meta de pasos cumplida"]
  ];
  document.getElementById("resumen").innerHTML =
    items.map(([n, t]) => `<div><b>${n}</b><span>${t}</span></div>`).join("");
}

function render() {
  const f = filas();
  const etiquetas = f.map(d => fechaCorta(d.calendar_date));
  document.getElementById("periodo").textContent = f.length
    ? `${f[0].calendar_date} a ${f[f.length - 1].calendar_date} · ${f.length} días`
    : "Sin datos";
  semana();
  resumen(f);

  dibujar("g-intensidad", { type: "bar", data: { labels: etiquetas, datasets: [
    { label: "Moderados", data: f.map(d => num(d.moderate_intensity_minutes)), backgroundColor: C.moderada },
    { label: "Vigorosos", data: f.map(d => num(d.vigorous_intensity_minutes)), backgroundColor: C.vigorosa }
  ] }, options: { scales: {
    x: { stacked: true, grid: { display: false }, ticks: { color: C.suave, maxTicksLimit: 10, maxRotation: 0 } },
    y: { stacked: true, grid: { color: C.linea }, ticks: { color: C.suave }, beginAtZero: true }
  } } });

  dibujar("g-calorias", { type: "bar", data: { labels: etiquetas, datasets: [
    { label: "kcal activas", data: f.map(d => num(d.active_kilocalories)), backgroundColor: C.calorias }
  ] } });

  dibujar("g-pasos", { type: "bar", data: { labels: etiquetas, datasets: [
    { label: "Pasos", data: f.map(d => num(d.total_steps)), backgroundColor: C.pasos, order: 2 },
    { label: "Meta", type: "line", data: f.map(d => num(d.daily_step_goal)), borderColor: "#15202b",
      borderWidth: 1.5, borderDash: [5, 4], pointRadius: 0, stepped: true, order: 1 }
  ] } });

  dibujar("g-pulso", { type: "line", data: { labels: etiquetas, datasets: [
    { label: "Pulso en reposo", data: f.map(d => num(d.resting_heart_rate)), borderColor: C.pulso,
      backgroundColor: C.pulso, borderWidth: 2, pointRadius: 2, tension: .25, spanGaps: true }
  ] }, options: { scales: {
    x: { grid: { display: false }, ticks: { color: C.suave, maxTicksLimit: 10, maxRotation: 0 } },
    y: { grid: { color: C.linea }, ticks: { color: C.suave }, beginAtZero: false }
  } } });

  dibujar("g-bateria", { type: "line", data: { labels: etiquetas, datasets: [
    { label: "Más alto", data: f.map(d => num(d.body_battery_highest_value)), borderColor: C.moderada,
      backgroundColor: C.moderada, borderWidth: 2, pointRadius: 2, tension: .25, spanGaps: true },
    { label: "Más bajo", data: f.map(d => num(d.body_battery_lowest_value)), borderColor: C.vigorosa,
      backgroundColor: C.vigorosa, borderWidth: 2, pointRadius: 2, tension: .25, spanGaps: true }
  ] }, options: { scales: {
    x: { grid: { display: false }, ticks: { color: C.suave, maxTicksLimit: 10, maxRotation: 0 } },
    y: { grid: { color: C.linea }, ticks: { color: C.suave }, min: 0, max: 100 }
  } } });
}

document.querySelectorAll(".rango button").forEach(b => {
  b.addEventListener("click", () => {
    rango = b.dataset.r === "all" ? "all" : Number(b.dataset.r);
    document.querySelectorAll(".rango button").forEach(x =>
      x.setAttribute("aria-pressed", String(x === b)));
    render();
  });
});

if (DATOS.length) render();
else document.querySelector("main").insertAdjacentHTML("beforeend",
  '<p class="vacio">garmin_data.json no tiene días. Corre download.py otra vez.</p>');
</script>
</body>
</html>
"""

salida = CARPETA / "dashboard.html"
salida.write_text(PLANTILLA.replace("__DATOS__", datos_js), encoding="utf-8")
print(f"Listo: {salida.name} con {len(datos)} días. Ábrelo con doble clic.")
