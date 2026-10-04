const LIVE_SITE = "https://muhammadmubeen1.github.io/UKbrands/";

const PITCH = `Hi *{name}* team 👋

I found your Google listing and noticed you don’t have a website, so I designed a quick demo for you:

{site}

If you’re interested, I can create a fully customized website + mobile booking app where customers can easily book appointments online 📱, along with Local SEO to help you rank higher than competitors and get more customers.

Interested? I’d be happy to discuss it.

Best regards,
*M. Mubeen* | Digital Growth Specialist
https://mubecodes.com`;

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

function sitePreviewUrl(lead) {
  const base = new URL("site-preview.html", window.location.href).href.split("#")[0];
  const params = new URLSearchParams({
    name: lead.name || "Your Business",
    city: lead.city || state.city,
    area: lead.borough || lead.city || "",
    cat: lead.category_key || state.category,
    phone: String(lead.whatsapp_number || "").replace(/[^\d]/g, ""),
    maps: lead.google_maps_url || ""
  });
  return `${base}?${params.toString()}`;
}

function shortSiteUrl(lead) {
  const id = lead.id || String(lead.whatsapp_number || "").replace(/[^\d]/g, "");
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
  return fillPitch(lead, lead.name || "your brand");
}

function pitchPreviewHtml(lead) {
  const name = escapeHtml(lead.name || "your brand");
  const url = escapeHtml(shortSiteUrl(lead));
  const link = `<a class="pitch-brand-link" href="${url}" target="_blank" rel="noopener">${name}</a>`;
  return escapeHtml(fillPitch(lead, "%%SITE%%")).replace(/\n/g, "<br>").replace("%%SITE%%", link);
}

function waUrl(lead) {
  const phone = String(lead.whatsapp_number || "").replace(/[^\d]/g, "");
  return `https://wa.me/${phone}?text=${encodeURIComponent(pitchFor(lead))}`;
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
        <h3><a class="pitch-brand-link" href="${escapeHtml(shortSiteUrl(lead))}" target="_blank" rel="noopener">${escapeHtml(lead.name)}</a></h3>
        <span class="badge badge-emerald">Live WhatsApp · No website</span>
      </div>
      <p class="card-info-list">📍 ${escapeHtml(lead.address || lead.city)} · ${escapeHtml(lead.category)}</p>
      <p class="card-info-list">💬 ${escapeHtml(lead.whatsapp_display)} · Meta: ${escapeHtml(lead.whatsapp_account_name || "Registered")}</p>
      <p class="card-info-list">${escapeHtml((lead.seo_opportunity && lead.seo_opportunity.audit) || "")}</p>
      <div class="card-action-row">
        <a class="btn btn-whatsapp" href="${waUrl(lead)}" target="_blank" rel="noopener">WhatsApp Pitch</a>
        <a class="btn btn-primary" href="${escapeHtml(sitePreviewUrl(lead))}" target="_blank" rel="noopener">Website Design</a>
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
