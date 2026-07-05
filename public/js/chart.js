window.drawChart = function drawChart(candles) {
  const canvas = document.getElementById("priceChart");
  const wrap = canvas.parentElement;
  const rect = wrap.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.floor(rect.width * dpr);
  canvas.height = Math.floor(430 * dpr);

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const width = rect.width;
  const height = 430;

  ctx.clearRect(0, 0, width, height);

  const clean = (candles || []).filter(c => Number.isFinite(Number(c.close)));

  if (clean.length < 2) {
    ctx.fillStyle = "#a8b1c4";
    ctx.font = "16px Arial";
    ctx.fillText("Not enough chart data.", 24, 42);
    return;
  }

  const closes = clean.map(c => Number(c.close));
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;

  const pad = { top: 24, right: 28, bottom: 34, left: 58 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const x = i => pad.left + (i / (clean.length - 1)) * plotW;
  const y = v => pad.top + (1 - (v - min) / range) * plotH;

  ctx.strokeStyle = "#263149";
  ctx.lineWidth = 1;

  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + (i / 4) * plotH;

    ctx.beginPath();
    ctx.moveTo(pad.left, yy);
    ctx.lineTo(width - pad.right, yy);
    ctx.stroke();

    const label = max - (i / 4) * range;

    ctx.fillStyle = "#a8b1c4";
    ctx.font = "12px Arial";
    ctx.fillText(label.toFixed(2), 8, yy + 4);
  }

  const first = closes[0];
  const last = closes[closes.length - 1];
  const color = last >= first ? "#00ff9d" : "#ff4d5a";

  const grad = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom);
  grad.addColorStop(0, last >= first ? "rgba(0,255,157,.22)" : "rgba(255,77,90,.22)");
  grad.addColorStop(1, "rgba(255,255,255,0)");

  ctx.beginPath();

  clean.forEach((c, i) => {
    const px = x(i);
    const py = y(Number(c.close));

    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });

  ctx.lineTo(x(clean.length - 1), height - pad.bottom);
  ctx.lineTo(x(0), height - pad.bottom);
  ctx.closePath();

  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();

  clean.forEach((c, i) => {
    const px = x(i);
    const py = y(Number(c.close));

    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });

  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.stroke();
};
