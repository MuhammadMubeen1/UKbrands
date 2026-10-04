const LIVE_SITE = "https://muhammadmubeen1.github.io/UKbrands/";

const PITCH = `Hi *{name}* team 👋

I found your Google listing and noticed you don’t have a website, so I designed a quick demo for you:

🌐 {site}

If you’re interested, I can create a *fully customized website + mobile booking app* where customers can easily book appointments online 📱, along with *Local SEO* to help you rank higher than competitors and get more customers.

Interested? I’d be happy to discuss it.

Best regards,  
*M. Mubeen* | Digital Growth Specialist  
🌐 https://mubecodes.com`;

const CATS = {
  salons: "Beauty Salons",
  estate_agents: "Real Estate",
  aesthetic: "Aesthetic Clinics",
  fitness: "Fitness",
  restaurants: "Restaurants",
  dentists: "Dentists"
};

const state = {
  city: "London",
  category: "salons",
  data: window.PAKISTAN_NO_WEBSITE_LEADS || {}
};

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function cityLeads(city, cat) {
  return (state.data[cat] || []).filter(l => l.city === city && l.whatsapp_live_verified === true && !l.has_website);
}

function viewPitchUrl(lead) {
  const id = String(lead.id || "").replace(/^l(?=lon-)/, "");
  return LIVE_SITE + "p.html?id=" + encodeURIComponent(id);
}

function viewSiteUrl(lead) {
  const id = String(lead.id || "").replace(/^l(?=lon-)/, "");
  return LIVE_SITE + "w.html?id=" + encodeURIComponent(id);
}

function fillPitch(lead, siteValue) {
  return PITCH
    .replace(/\{name\}/g, lead.name || "there")
    .replace(/\{city\}/g, lead.city || state.city)
    .replace(/\{borough\}/g, lead.borough || lead.city || state.city)
    .replace(/\{keyword\}/g, lead.target_keyword || `${CATS[state.category]} in ${lead.city}`)
    .replace(/\{site\}/g, siteValue);
}

function pitchFor(lead) {
  return fillPitch(lead, viewSiteUrl(lead));
}

function pitchPreviewHtml(lead) {
  return escapeHtml(pitchFor(lead))
    .replace(/\*([^*]+)\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>")
    .replace(/https:\/\/[^\s<]+/g, (u) => `<a class="pitch-brand-link" href="${u}" target="_blank" rel="noopener">${u}</a>`);
}

function waUrl(lead) {
  const phone = String(lead.whatsapp_number || "").replace(/[^\d]/g, "");
  const text = encodeURIComponent(pitchFor(lead));
  return `https://api.whatsapp.com/send?phone=${phone}&text=${text}`;
}

function updateBadges() {
  Object.keys(CATS).forEach(cat => {
    const el = document.getElementById(`badge-${cat}`);
    if (el) el.textContent = cityLeads(state.city, cat).length;
  });
  ["Lahore", "Karachi", "Islamabad", "Dubai", "London", "New York"].forEach(city => {
    const total = Object.keys(CATS).reduce((n, cat) => n + cityLeads(city, cat).length, 0);
    const el = document.getElementById(`counter-city-${city.toLowerCase().replace(/\s+/g, "-")}`);
    if (el) el.textContent = total;
  });
}

function render() {
  const list = cityLeads(state.city, state.category);
  document.getElementById("title-city-name").textContent = state.city;
  document.getElementById("results-count").textContent = list.length;
  document.getElementById("results-city").textContent = state.city;
  document.getElementById("results-category").textContent = CATS[state.category];
  document.getElementById("export-count").textContent = list.length;
  const previewLead = list[0] || {
    name: "your brand",
    city: state.city,
    borough: state.city,
    id: "preview"
  };
  document.getElementById("banner-pitch-preview").innerHTML = pitchPreviewHtml(previewLead);
  const sendWa = document.getElementById("banner-send-wa");
  if (sendWa) {
    sendWa.href = list.length ? waUrl(previewLead) : "#";
    sendWa.style.display = list.length ? "inline-flex" : "none";
  }

  const grid = document.getElementById("leads-grid");
  const empty = document.getElementById("empty-state");
  if (!list.length) {
    grid.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  grid.innerHTML = list.map(lead => `
    <article class="salon-card">
      <div class="card-header-row">
        <h3>${escapeHtml(lead.name)}</h3>
        <span class="badge badge-emerald">Live WhatsApp · No website</span>
      </div>
      <p class="card-info-list">📍 ${escapeHtml(lead.address || lead.city)} · ${escapeHtml(lead.category)}</p>
      <p class="card-info-list">💬 ${escapeHtml(lead.whatsapp_display)} · Meta: ${escapeHtml(lead.whatsapp_account_name || "Registered")}</p>
      <p class="card-info-list">${escapeHtml((lead.seo_opportunity && lead.seo_opportunity.audit) || "")}</p>
      <div class="pitch-mini">
        <span class="pitch-mini-label">Message template</span>
        <a class="pitch-demo-btn" href="${escapeHtml(viewSiteUrl(lead))}" target="_blank" rel="noopener">VIEW DEMO WEBSITE</a>
      </div>
      <div class="card-action-row">
        <a class="btn btn-whatsapp" href="${waUrl(lead)}" target="_blank" rel="noopener">Share on WhatsApp</a>
        <a class="btn btn-primary" href="${escapeHtml(viewSiteUrl(lead))}" target="_blank" rel="noopener">VIEW DEMO WEBSITE</a>
        <a class="btn btn-secondary" href="${escapeHtml(lead.google_maps_url)}" target="_blank" rel="noopener">Google Maps</a>
      </div>
    </article>
  `).join("");
}

function exportCsv() {
  const list = cityLeads(state.city, state.category);
  const rows = [["Name", "City", "Area", "Category", "WhatsApp", "Account", "Maps"]];
  list.forEach(l => rows.push([
    l.name, l.city, l.borough, l.category, l.whatsapp_display, l.whatsapp_account_name || "", l.google_maps_url
  ]));
  const csv = rows.map(r => r.map(c => `"${String(c || "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `pakistan_no_website_${state.city.toLowerCase()}_${state.category}.csv`;
  a.click();
}

function richestCategory(city) {
  let best = "restaurants";
  let max = -1;
  Object.keys(CATS).forEach(cat => {
    const n = cityLeads(city, cat).length;
    if (n > max) {
      max = n;
      best = cat;
    }
  });
  return best;
}

function setCategory(cat) {
  state.category = cat;
  document.querySelectorAll(".category-tab").forEach(b => b.classList.toggle("active", b.dataset.category === cat));
}

function init() {
  updateBadges();
  setCategory(richestCategory(state.city));
  document.querySelectorAll(".city-pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      state.city = btn.dataset.city;
      document.querySelectorAll(".city-pill-btn").forEach(b => b.classList.toggle("active", b === btn));
      setCategory(richestCategory(state.city));
      updateBadges();
      render();
    });
  });
  document.querySelectorAll(".category-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      state.category = btn.dataset.category;
      document.querySelectorAll(".category-tab").forEach(b => b.classList.toggle("active", b === btn));
      render();
    });
  });
  document.getElementById("btn-export-csv").addEventListener("click", exportCsv);
  render();
}

document.addEventListener("DOMContentLoaded", init);
