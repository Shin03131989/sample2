/* global Chart */

let priceChart = null;
let lastAnalysis = null;

// ── Utility ──────────────────────────────────────────────────────────────────

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "コピー済み ✓";
    btn.disabled = true;
    setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 1500);
  });
}

function fmt(n, currency = "JPY") {
  if (n == null) return "—";
  if (currency === "USD") return `$${Number(n).toFixed(2)}`;
  return `¥${Number(n).toLocaleString("ja-JP")}`;
}

function setLoading(show) {
  document.getElementById("loadingSpinner").style.display = show ? "flex" : "none";
  document.getElementById("submitBtn").disabled = show;
}

// ── Price Analysis ────────────────────────────────────────────────────────────

function renderAnalysis(analysis) {
  lastAnalysis = analysis;

  const section = document.getElementById("priceSection");
  section.innerHTML = "";

  const usd_to_jpy = analysis.usd_to_jpy || 150;

  // eBay block
  const ebay = analysis.ebay || {};
  section.appendChild(buildPlatformStats(
    "eBay（過去90日 実売価格）",
    "badge-ebay",
    ebay.configured,
    ebay.error,
    ebay.usd,
    "USD",
    ebay.jpy,
    ebay.total_count,
    `${ebay.period_days || 90}日間 / 取得件数`,
  ));

  // Yahoo block
  const yahoo = analysis.yahoo || {};
  section.appendChild(buildPlatformStats(
    "Yahooショッピング（現在出品価格）",
    "badge-yahuoku",
    yahoo.configured,
    yahoo.error,
    yahoo.stats,
    "JPY",
    null,
    yahoo.stats ? yahoo.stats.count : 0,
    yahoo.note || "",
  ));

  // Price chart
  if ((ebay.prices_chart || []).length || (yahoo.prices_chart || []).length) {
    const chartWrap = document.createElement("div");
    chartWrap.className = "card mb-3";
    chartWrap.innerHTML = `<div class="card-header">価格分布</div>
      <div class="card-body"><div class="chart-container"><canvas id="priceCanvas"></canvas></div></div>`;
    section.appendChild(chartWrap);

    requestAnimationFrame(() => buildChart(ebay.prices_chart || [], yahoo.prices_chart || [], usd_to_jpy));
  }

  // Recommendations
  const rec = analysis.recommendations;
  if (rec) {
    section.appendChild(buildRecommendations(rec, usd_to_jpy));
  }
}

function buildPlatformStats(title, badgeClass, configured, error, statsUSD, currency, statsJPY, count, note) {
  const card = document.createElement("div");
  card.className = "card mb-3";

  const statusHtml = configured
    ? '<span class="api-status ok">API 接続済み</span>'
    : '<span class="api-status off">API 未設定（.envを確認）</span>';

  if (!configured || error) {
    card.innerHTML = `
      <div class="card-header d-flex justify-content-between align-items-center">
        <span><span class="platform-badge ${badgeClass}">&nbsp;</span>${title}</span>
        ${statusHtml}
      </div>
      <div class="card-body text-muted small">
        ${error ? `<div class="alert alert-warning py-2">${error}</div>` : ""}
        <p>APIキーを設定すると実際の相場データを取得できます。</p>
      </div>`;
    return card;
  }

  const s = statsUSD || {};
  const j = statsJPY || {};

  const rows = [
    ["件数", count != null ? `${Number(count).toLocaleString()} 件` : "—"],
    ["最安値", currency === "USD" ? `${fmt(s.min, "USD")} (${fmt(s.min * (j.min ? j.min / s.min : 150), "JPY")})` : fmt(s.min, "JPY")],
    ["最高値", currency === "USD" ? `${fmt(s.max, "USD")} (${fmt(s.max * (j.max ? j.max / s.max : 150), "JPY")})` : fmt(s.max, "JPY")],
    ["平均値", currency === "USD" ? `${fmt(s.mean, "USD")} (${fmt(s.mean * 150, "JPY")})` : fmt(s.mean, "JPY")],
    ["中央値", currency === "USD" ? `${fmt(s.median, "USD")} (${fmt(s.median * 150, "JPY")})` : fmt(s.median, "JPY")],
  ];

  const rowsHtml = rows.map(([l, v]) => `<tr><th class="text-muted fw-normal">${l}</th><td class="fw-semibold">${v}</td></tr>`).join("");
  const noteHtml = note ? `<p class="text-muted small mb-0 mt-2">${note}</p>` : "";

  card.innerHTML = `
    <div class="card-header d-flex justify-content-between align-items-center">
      <span><span class="platform-badge ${badgeClass}">&nbsp;</span>${title}</span>
      ${statusHtml}
    </div>
    <div class="card-body">
      <table class="table table-sm mb-0">${rowsHtml}</table>
      ${noteHtml}
    </div>`;
  return card;
}

function buildChart(ebayUSD, yahooJPY, rate) {
  const ctx = document.getElementById("priceCanvas");
  if (!ctx) return;

  if (priceChart) { priceChart.destroy(); priceChart = null; }

  const datasets = [];
  if (ebayUSD.length) {
    datasets.push({
      label: `eBay 実売価格 (¥, @${rate})`,
      data: ebayUSD.map(p => +(p * rate).toFixed(0)),
      backgroundColor: "rgba(0,100,210,.6)",
      borderColor: "rgba(0,100,210,1)",
      borderWidth: 1,
    });
  }
  if (yahooJPY.length) {
    datasets.push({
      label: "Yahoo 出品価格 (¥)",
      data: yahooJPY.map(p => +p.toFixed(0)),
      backgroundColor: "rgba(230,0,51,.4)",
      borderColor: "rgba(230,0,51,1)",
      borderWidth: 1,
    });
  }

  priceChart = new Chart(ctx, {
    type: "bar",
    data: { labels: datasets[0]?.data.map((_, i) => i + 1) || [], datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" }, tooltip: {
        callbacks: { label: ctx => `¥${Number(ctx.parsed.y).toLocaleString()}` }
      }},
      scales: {
        y: { ticks: { callback: v => `¥${Number(v).toLocaleString()}` } },
        x: { display: false },
      },
    },
  });
}

function buildRecommendations(rec, usd_to_jpy) {
  const wrap = document.createElement("div");
  wrap.className = "card mb-3";
  wrap.innerHTML = `<div class="card-header">推奨価格（相場中央値ベース）</div><div class="card-body" id="recBody"></div>`;

  const body = wrap.querySelector("#recBody");

  const platforms = [
    {
      key: "yahuoku",
      label: "ヤフオク!",
      cssClass: "yahuoku",
      price: fmt(rec.yahuoku?.suggested, "JPY"),
      net: `手数料後 約 ${fmt(rec.yahuoku?.net, "JPY")}`,
      note: rec.yahuoku?.fee_note || "",
    },
    {
      key: "yahoo_flea",
      label: "ヤフーフリマ",
      cssClass: "flea",
      price: fmt(rec.yahoo_flea?.suggested, "JPY"),
      net: `手数料後 約 ${fmt(rec.yahoo_flea?.net, "JPY")}`,
      note: rec.yahoo_flea?.fee_note || "",
    },
    {
      key: "ebay",
      label: "eBay",
      cssClass: "ebay",
      price: `${fmt(rec.ebay?.suggested_usd, "USD")} (${fmt(rec.ebay?.suggested_jpy, "JPY")})`,
      net: `手数料後 約 ${fmt(rec.ebay?.net_usd, "USD")}`,
      note: rec.ebay?.fee_note || "",
    },
  ];

  platforms.forEach(p => {
    const div = document.createElement("div");
    div.className = `rec-card ${p.cssClass}`;
    div.innerHTML = `
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <div class="fw-semibold mb-1">${p.label}</div>
          <div class="rec-price">${p.price}</div>
          <div class="rec-net">${p.net}</div>
          <div class="text-muted" style="font-size:.75rem">${p.note}</div>
        </div>
      </div>`;
    body.appendChild(div);
  });

  // Condition table
  if (rec.condition_adjustments) {
    const condLabels = {
      new: "新品・未使用",
      like_new: "未使用に近い",
      very_good: "美品",
      good: "良品",
      acceptable: "ジャンク",
    };
    let tableHtml = `<h6 class="mt-3">コンディション別目安価格</h6>
      <table class="table table-sm table-bordered">
        <thead><tr><th>コンディション</th><th>ヤフオク / フリマ</th><th>eBay (USD)</th></tr></thead><tbody>`;
    Object.entries(rec.condition_adjustments).forEach(([key, v]) => {
      tableHtml += `<tr><td>${condLabels[key] || key}</td><td>${fmt(v.yahuoku, "JPY")}</td><td>${fmt(v.ebay_usd, "USD")}</td></tr>`;
    });
    tableHtml += "</tbody></table>";
    const div = document.createElement("div");
    div.innerHTML = tableHtml;
    body.appendChild(div);
  }

  return wrap;
}

// ── Titles ────────────────────────────────────────────────────────────────────

function renderTitles(titles) {
  const section = document.getElementById("titlesSection");
  section.innerHTML = "";

  const platforms = [
    { key: "yahuoku",    label: "ヤフオク!", badge: "badge-yahuoku" },
    { key: "yahoo_flea", label: "ヤフーフリマ", badge: "badge-flea" },
    { key: "ebay",       label: "eBay",    badge: "badge-ebay" },
  ];

  platforms.forEach(p => {
    const t = titles[p.key] || {};
    const isOver = !t.is_valid;
    const lengthClass = isOver ? "title-length over" : "title-length";
    const lengthText = `${t.length} / ${t.max_length} 文字${isOver ? " ⚠ 上限超過" : ""}`;

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.innerHTML = `
      <div class="card-header d-flex justify-content-between align-items-center">
        <span><span class="platform-badge ${p.badge}">${p.label}</span>タイトル</span>
        <button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copyText(${JSON.stringify(t.title)}, this)">コピー</button>
      </div>
      <div class="card-body">
        <div class="title-display mb-1">${escHtml(t.title)}</div>
        <div class="${lengthClass}">${lengthText}</div>
      </div>`;
    section.appendChild(card);
  });
}

// ── Listing Descriptions ──────────────────────────────────────────────────────

function renderListings(listings) {
  const section = document.getElementById("listingsSection");
  section.innerHTML = "";

  const platforms = [
    { key: "yahuoku",    label: "ヤフオク!", badge: "badge-yahuoku" },
    { key: "yahoo_flea", label: "ヤフーフリマ", badge: "badge-flea" },
    { key: "ebay",       label: "eBay（HTML）", badge: "badge-ebay", isHtml: true },
  ];

  platforms.forEach(p => {
    const listing = listings[p.key] || {};
    const desc = listing.description || "";
    const tips = listing.tips || [];

    const tipsHtml = tips.length
      ? `<h6 class="mt-3">出品のコツ</h6><ul class="tip-list">${tips.map(t => `<li>${escHtml(t)}</li>`).join("")}</ul>`
      : "";

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.innerHTML = `
      <div class="card-header d-flex justify-content-between align-items-center">
        <span><span class="platform-badge ${p.badge}">${p.label}</span>出品詳細</span>
        <div class="d-flex gap-2">
          ${p.isHtml ? `<button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copyText(${JSON.stringify(desc)}, this)">HTMLコピー</button>` : ""}
          <button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copyText(${JSON.stringify(p.isHtml ? stripTags(desc) : desc)}, this)">テキストコピー</button>
        </div>
      </div>
      <div class="card-body">
        <div class="desc-box${p.isHtml ? " html-mode" : ""}">${p.isHtml ? desc : escHtml(desc)}</div>
        ${tipsHtml}
      </div>`;
    section.appendChild(card);
  });
}

// ── Main Form Handler ─────────────────────────────────────────────────────────

document.getElementById("listingForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  setLoading(true);
  document.getElementById("results").classList.remove("show");

  const payload = {
    keyword:    document.getElementById("keyword").value.trim(),
    brand:      document.getElementById("brand").value.trim(),
    model:      document.getElementById("model").value.trim(),
    condition:  document.getElementById("condition").value,
    category:   document.getElementById("category").value,
    description:document.getElementById("description").value.trim(),
    features:   document.getElementById("features").value.trim(),
    accessories:document.getElementById("accessories").value.trim(),
    defects:    document.getElementById("defects").value.trim(),
    usd_to_jpy: parseFloat(document.getElementById("usdToJpy").value) || 150,
  };

  try {
    // Run price analysis and listing generation in parallel
    const [analyzeRes, generateRes] = await Promise.all([
      fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
      fetch("/api/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
    ]);

    const analyzeData = await analyzeRes.json();
    const generateData = await generateRes.json();

    if (analyzeData.success) {
      renderAnalysis(analyzeData.analysis);
    } else {
      document.getElementById("priceSection").innerHTML =
        `<div class="alert alert-danger">${analyzeData.error}</div>`;
    }

    if (generateData.success) {
      renderTitles(generateData.titles);
      // Pass price analysis to listing descriptions (already embedded in generate response)
      renderListings(generateData.listings);
    } else {
      document.getElementById("titlesSection").innerHTML =
        `<div class="alert alert-danger">${generateData.error}</div>`;
    }

    document.getElementById("results").classList.add("show");
    document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    alert("エラーが発生しました: " + err.message);
  } finally {
    setLoading(false);
  }
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function stripTags(html) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || "";
}
