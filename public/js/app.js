import { db } from "./firebase-config.js";

import {
  doc,
  getDoc,
  setDoc
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js";

console.log("APP JS v12000 loaded");

const DEFAULT_WATCH = [
  "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN",
  "TSLA", "AMD", "NFLX", "BTC-USD", "ETH-USD", "SOL-USD"
];

const els = {
  watchlist: document.getElementById("watchlist"),
  searchInput: document.getElementById("searchInput"),
  searchBtn: document.getElementById("searchBtn"),
  symbolTitle: document.getElementById("symbolTitle"),
  assetName: document.getElementById("assetName"),
  dataSource: document.getElementById("dataSource"),
  mainPrice: document.getElementById("mainPrice"),
  mainChange: document.getElementById("mainChange"),
  marketState: document.getElementById("marketState"),
  aiScore: document.getElementById("aiScore"),
  aiSummary: document.getElementById("aiSummary"),
  signalGrid: document.getElementById("signalGrid"),
  strongestSignal: document.getElementById("strongestSignal"),
  weakestSignal: document.getElementById("weakestSignal"),
  aiDisclaimer: document.getElementById("aiDisclaimer"),
  detailsGrid: document.getElementById("detailsGrid"),
  newsList: document.getElementById("newsList")
};

let activeSymbol = "AAPL";
let activeRange = "1D";
let userWatchlist = [...DEFAULT_WATCH];

function currentUser() {
  return window.CHARTIX_USER || null;
}

function getLocalGuestList() {
  try {
    const raw = localStorage.getItem("chartix_guest_watchlist");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length ? parsed : [...DEFAULT_WATCH];
  } catch {
    return [...DEFAULT_WATCH];
  }
}

function saveLocalGuestList() {
  localStorage.setItem("chartix_guest_watchlist", JSON.stringify(userWatchlist));
}

function getUserWatchDoc() {
  const user = currentUser();
  if (!user) return null;
  return doc(db, "watchlists", user.uid);
}

async function loadUserWatchlist() {
  const user = currentUser();

  if (!user) {
    userWatchlist = getLocalGuestList();
    return;
  }

  try {
    const ref = getUserWatchDoc();
    const snap = await getDoc(ref);

    if (snap.exists()) {
      const data = snap.data();
      userWatchlist = Array.isArray(data.symbols) && data.symbols.length
        ? data.symbols
        : [...DEFAULT_WATCH];
    } else {
      userWatchlist = [...DEFAULT_WATCH];
      await saveUserWatchlist();
    }
  } catch (err) {
    console.error(err);
    userWatchlist = getLocalGuestList();
  }
}

async function saveUserWatchlist() {
  const user = currentUser();

  if (!user) {
    saveLocalGuestList();
    return;
  }

  const ref = getUserWatchDoc();

  await setDoc(ref, {
    email: user.email || "",
    symbols: userWatchlist,
    updatedAt: new Date().toISOString()
  });
}

async function addToWatchlist(symbol) {
  symbol = String(symbol || "").trim().toUpperCase();
  if (!symbol) return;

  if (!userWatchlist.includes(symbol)) {
    userWatchlist.unshift(symbol);
    await saveUserWatchlist();
  }

  renderWatchlist(symbol);
}

async function removeFromWatchlist(symbol) {
  userWatchlist = userWatchlist.filter(s => s !== symbol);
  await saveUserWatchlist();
  renderWatchlist(activeSymbol);
}

function priceOnly(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";

  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function money(currency, value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";

  return `${currency || "USD"} ${n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function compact(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  if (Math.abs(n) >= 1e12) return (n / 1e12).toFixed(2) + "T";
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(2) + "K";
  return n.toFixed(2);
}

function signed(value) {
  const n = Number(value || 0);
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}`;
}

function pct(value) {
  const n = Number(value || 0);
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function renderWatchlist(active) {
  const user = currentUser();

  els.watchlist.innerHTML = `
    <div style="display:flex;gap:8px;margin-bottom:12px;">
      <input
        id="newWatchSymbol"
        placeholder="Add symbol..."
        style="flex:1;padding:11px;border-radius:12px;border:1px solid #263149;background:#151d2e;color:white;outline:none;"
      />
      <button
        id="addWatchBtn"
        style="padding:11px 14px;border:0;border-radius:12px;background:#7c3cff;color:white;font-weight:900;cursor:pointer;"
      >+</button>
    </div>

    <div style="font-size:12px;color:#a8b1c4;margin-bottom:12px;">
      ${user ? "Saved for: " + (user.email || user.uid) : "Guest watchlist. Login to sync."}
    </div>

    ${userWatchlist.map(symbol => `
      <button class="watch-item ${symbol === active ? "active" : ""}" data-symbol="${symbol}">
        <strong>${symbol}</strong>
        <span style="display:flex;gap:10px;align-items:center;">
          <b class="remove-watch" data-remove="${symbol}" style="color:#ff4d5a;">×</b>
          <span>›</span>
        </span>
      </button>
    `).join("")}
  `;

  document.querySelectorAll(".watch-item").forEach(button => {
    button.addEventListener("click", e => {
      if (e.target.classList.contains("remove-watch")) return;
      load(button.dataset.symbol);
    });
  });

  document.querySelectorAll(".remove-watch").forEach(button => {
    button.addEventListener("click", async e => {
      e.stopPropagation();
      await removeFromWatchlist(button.dataset.remove);
    });
  });

  document.getElementById("addWatchBtn").addEventListener("click", async () => {
    const input = document.getElementById("newWatchSymbol");
    await addToWatchlist(input.value);
    input.value = "";
  });

  document.getElementById("newWatchSymbol").addEventListener("keydown", async e => {
    if (e.key === "Enter") {
      await addToWatchlist(e.target.value);
      e.target.value = "";
    }
  });
}

function renderSignals(signals) {
  els.signalGrid.innerHTML = signals.map(signal => `
    <div class="signal ${signal.status}">
      <small>${signal.name}</small>
      <strong>${signal.value}</strong>
      <p>${signal.text}</p>
    </div>
  `).join("");
}

function renderDetails(details, analysis, quote) {
  const rows = [
    ["Symbol", details.symbol],
    ["Type", details.assetType],
    ["Sector", details.sector],
    ["Data Source", details.source],
    ["Market Cap", details.marketCap ? compact(details.marketCap) : "-"],
    ["Volume", compact(details.volume)],
    ["52W High", money(quote.currency, details.high52)],
    ["52W Low", money(quote.currency, details.low52)],
    ["Support", money(quote.currency, analysis.support)],
    ["Resistance", money(quote.currency, analysis.resistance)],
    ["SMA20", money(quote.currency, analysis.sma20)],
    ["SMA50", money(quote.currency, analysis.sma50)],
    ["SMA200", money(quote.currency, analysis.sma200)]
  ];

  els.detailsGrid.innerHTML = rows.map(([label, value]) => `
    <div class="detail-row">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("");
}

function renderNews(news) {
  els.newsList.innerHTML = news.map(item => `
    <a class="news-item" href="${item.url}" target="_blank" rel="noreferrer">
      <strong>${item.title}</strong>
      <small>${item.source} • ${item.time}</small>
    </a>
  `).join("");
}

function renderYahooStyleTop(quote) {
  const currency = quote.currency || "USD";

  els.mainPrice.innerHTML = `
    <div style="font-size:26px;line-height:1;color:#fff;margin-bottom:6px;">
      ${currency}
    </div>
    <div>${priceOnly(quote.price)}</div>
  `;

  els.mainChange.classList.toggle("negative", Number(quote.changePercent) < 0);
  els.mainChange.textContent = `${signed(quote.change)} (${pct(quote.changePercent)})`;

  let afterHtml = "";

  if (quote.afterPrice !== null && quote.afterPrice !== undefined) {
    const afterNegative = Number(quote.afterChangePercent) < 0;

    afterHtml = `
      <div style="margin-top:14px;font-size:18px;color:#a8b1c4;">
        <strong style="color:#fff;">${priceOnly(quote.afterPrice)}</strong>
        <span style="color:${afterNegative ? "#ff4d5a" : "#00ff9d"};font-weight:900;">
          ${signed(quote.afterChange)} (${pct(quote.afterChangePercent)})
        </span>
        <div style="font-size:14px;margin-top:4px;">After Hours</div>
      </div>
    `;
  }

  els.marketState.innerHTML = `
    <div style="color:#a8b1c4;font-size:14px;margin-top:8px;">
      At close • ${quote.lastUpdate || "-"}
    </div>
    ${afterHtml}
  `;
}

async function load(symbol) {
  symbol = String(symbol || "").trim().toUpperCase();
  if (!symbol) return;

  try {
    activeSymbol = symbol;
    renderWatchlist(symbol);

    els.symbolTitle.textContent = symbol;
    els.assetName.textContent = "Loading...";
    els.dataSource.textContent = "Source: -";
    els.mainPrice.textContent = "-";
    els.mainChange.textContent = "-";
    els.marketState.textContent = "-";
    els.aiSummary.textContent = "Preparing AI analysis...";

    const data = await window.API.details(symbol, activeRange);

    const quote = data.quote;
    const details = data.details;
    const analysis = data.analysis;

    els.symbolTitle.textContent = quote.symbol;
    els.assetName.textContent = quote.name || details.name;
    els.dataSource.textContent = `Source: ${quote.source} • ${data.history?.rangeLabel || activeRange}`;

    renderYahooStyleTop(quote);

    if (window.drawChart) {
      window.drawChart(data.history.candles);
    } else {
      drawChart(data.history.candles);
    }

    els.aiScore.textContent = `Score: ${analysis.score}/100`;
    els.aiSummary.textContent = analysis.summary;
    els.strongestSignal.textContent = `${analysis.strongest.name}: ${analysis.strongest.text}`;
    els.weakestSignal.textContent = `${analysis.weakest.name}: ${analysis.weakest.text}`;
    els.aiDisclaimer.textContent = analysis.disclaimer;

    renderSignals(analysis.signals);
    renderDetails(details, analysis, quote);
    renderNews(data.news);
  } catch (err) {
    console.error(err);
    alert("Data could not be loaded: Data source did not respond.");
  }
}

window.refreshUserWatchlist = async function () {
  await loadUserWatchlist();
  renderWatchlist(activeSymbol || "AAPL");
};

function hideConsent() {
  const overlay = document.getElementById("consentOverlay");
  const box = document.getElementById("cookieBox");

  if (overlay) overlay.style.display = "none";
  if (box) box.style.display = "none";
}

const acceptCookie = document.getElementById("acceptCookie");

if (acceptCookie) {
  acceptCookie.addEventListener("click", () => {
    hideConsent();
  });
}

els.searchBtn.addEventListener("click", async () => {
  const symbol = els.searchInput.value;
  await addToWatchlist(symbol);
  load(symbol);
});

els.searchInput.addEventListener("keydown", async event => {
  if (event.key === "Enter") {
    const symbol = els.searchInput.value;
    await addToWatchlist(symbol);
    load(symbol);
  }
});

document.querySelectorAll(".range").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".range").forEach(b => {
      b.classList.remove("active");
    });

    button.classList.add("active");
    activeRange = button.dataset.range || "1D";
    load(activeSymbol);
  });
});

await loadUserWatchlist();
renderWatchlist("AAPL");
load("AAPL");