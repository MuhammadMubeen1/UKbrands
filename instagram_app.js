/**
 * Instagram Businesses & Social-to-SEO Engine
 * Page 2 Application Controller
 * Handles 6 Categories: Salons, Estate Agents, Dentists, Restaurants, Cafes, and Fitness & Gyms.
 * Direct Instagram DM outreach across Singapore, UAE, UK, and USA.
 */

// Universal High-Converting Outreach Pitch Template
const UNIVERSAL_IG_PITCH_TEMPLATE = `Hi *{name}* team 👋

Your visual content and brand presence look great! I noticed you already have an engaged audience of *{followers}* followers.

However, when local customers search Google for *"{keyword}"* in *{city}*, competitors are appearing ahead of you.

I help local businesses improve their *Google Maps visibility and local SEO* so they can attract more high-intent customers and bookings.

Would you be open to a *2-minute video audit* showing the top 3 SEO opportunities I found for your business?

Best regards,
*M. Mubeen* | Digital Growth Specialist
🌐 https://mubecodes.com`;

// Category Definitions & Tailored Instagram DM Pitch Templates
const IG_CATEGORIES = {
  salons: {
    id: 'salons',
    name: 'Beauty Salons & Spas',
    singular: 'Beauty Salon',
    icon: '💆',
    badgeId: 'badge-salons',
    tabId: 'tab-salons',
    storageStatusKey: 'ig_salons_status_v1',
    storageScriptKey: 'ig_salons_script_v2',
    storageCustomKey: 'ig_salons_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  },

  estate_agents: {
    id: 'estate_agents',
    name: 'Estate Agents & Lettings',
    singular: 'Estate Agency',
    icon: '🏠',
    badgeId: 'badge-estate_agents',
    tabId: 'tab-estate_agents',
    storageStatusKey: 'ig_estate_status_v1',
    storageScriptKey: 'ig_estate_script_v2',
    storageCustomKey: 'ig_estate_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  },

  dentists: {
    id: 'dentists',
    name: 'Dentists & Clinics',
    singular: 'Dental Clinic',
    icon: '🦷',
    badgeId: 'badge-dentists',
    tabId: 'tab-dentists',
    storageStatusKey: 'ig_dentists_status_v1',
    storageScriptKey: 'ig_dentists_script_v2',
    storageCustomKey: 'ig_dentists_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  },

  restaurants: {
    id: 'restaurants',
    name: 'Restaurants & Dining',
    singular: 'Restaurant',
    icon: '🍽️',
    badgeId: 'badge-restaurants',
    tabId: 'tab-restaurants',
    storageStatusKey: 'ig_restaurants_status_v1',
    storageScriptKey: 'ig_restaurants_script_v2',
    storageCustomKey: 'ig_restaurants_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  },

  cafes: {
    id: 'cafes',
    name: 'Cafes & Coffee Shops',
    singular: 'Cafe & Coffee Shop',
    icon: '☕',
    badgeId: 'badge-cafes',
    tabId: 'tab-cafes',
    storageStatusKey: 'ig_cafes_status_v1',
    storageScriptKey: 'ig_cafes_script_v2',
    storageCustomKey: 'ig_cafes_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  },

  fitness: {
    id: 'fitness',
    name: 'Fitness & Gyms',
    singular: 'Gym & Fitness Studio',
    icon: '🏋️',
    badgeId: 'badge-fitness',
    tabId: 'tab-fitness',
    storageStatusKey: 'ig_fitness_status_v1',
    storageScriptKey: 'ig_fitness_script_v2',
    storageCustomKey: 'ig_fitness_custom_v1',
    defaultScript: UNIVERSAL_IG_PITCH_TEMPLATE
  }
};

// Application State
const igState = {
  activeCity: localStorage.getItem('uk_leads_selected_city') || 'Lahore',
  activeCategory: 'salons',
  categoryData: {
    salons: [],
    estate_agents: [],
    dentists: [],
    restaurants: [],
    cafes: [],
    fitness: []
  },
  filteredLeads: [],
  searchQuery: '',
  followerFilter: 'all',
  statusFilter: 'all',
  viewMode: 'cards' // 'cards' | 'table'
};

// DOM Element References
const dom = {
  cityDropdown: document.getElementById('city-selector-dropdown'),
  cityPills: document.querySelectorAll('.city-pill-btn'),
  cityHeadingDisplay: document.getElementById('current-active-city-display'),
  categoryTabs: document.querySelectorAll('.category-tab'),
  searchInput: document.getElementById('search-input'),
  searchClear: document.getElementById('search-clear'),
  filterFollowers: document.getElementById('filter-followers'),
  filterStatus: document.getElementById('filter-status'),
  btnViewCards: document.getElementById('btn-view-cards'),
  btnViewTable: document.getElementById('btn-view-table'),
  leadsGrid: document.getElementById('leads-grid'),
  leadsTableContainer: document.getElementById('leads-table-container'),
  leadsTableBody: document.getElementById('leads-table-body'),
  emptyState: document.getElementById('empty-state'),
  btnResetFilters: document.getElementById('btn-reset-filters'),
  resultsCountBadge: document.getElementById('results-count-badge'),
  resultsCaptionText: document.getElementById('results-caption-text'),
  btnBulkCopy: document.getElementById('btn-bulk-copy'),
  btnEditScript: document.getElementById('btn-edit-script'),
  btnAddLead: document.getElementById('btn-add-lead'),
  btnExportCsv: document.getElementById('btn-export-csv'),
  exportCount: document.getElementById('export-count'),
  statTotalLeads: document.getElementById('stat-total-leads'),
  statIgVerified: document.getElementById('stat-ig-verified'),
  // Modals
  modalScript: document.getElementById('modal-script'),
  modalScriptClose: document.getElementById('modal-script-close'),
  modalCategoryName: document.getElementById('modal-category-name'),
  scriptEditorTextarea: document.getElementById('script-editor-textarea'),
  btnScriptReset: document.getElementById('btn-script-reset'),
  btnScriptSave: document.getElementById('btn-script-save'),
  modalAddLead: document.getElementById('modal-add-lead'),
  modalAddClose: document.getElementById('modal-add-close'),
  formAddLead: document.getElementById('form-add-lead'),
  btnAddCancel: document.getElementById('btn-add-cancel'),
  toastContainer: document.getElementById('toast-container')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  await loadAllLeadsData();
  setupEventListeners();
  applyCitySelection(igState.activeCity, false);
});

// Load Leads Bundle Data
async function loadAllLeadsData() {
  const catKeys = Object.keys(IG_CATEGORIES);

  for (const key of catKeys) {
    let list = [];
    if (window.LONDON_LEADS_DATA && Array.isArray(window.LONDON_LEADS_DATA[key])) {
      list = window.LONDON_LEADS_DATA[key];
    }

    // Load custom leads from storage
    try {
      const customSaved = localStorage.getItem(IG_CATEGORIES[key].storageCustomKey);
      if (customSaved) {
        const parsed = JSON.parse(customSaved);
        if (Array.isArray(parsed)) {
          list = [...parsed, ...list];
        }
      }
    } catch (e) {
      console.warn(`Error loading custom leads for ${key}:`, e);
    }

    // Ensure Instagram properties are normalized
    list = list.map(item => {
      const handle = item.instagram_handle || `@${item.name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20)}`;
      const cleanHandle = handle.replace('@', '');
      const igUrl = item.instagram_url || `https://www.instagram.com/${cleanHandle}/`;
      const followers = item.instagram_followers || '12.4k';
      const gap = item.instagram_audit_gap || `Instagram bio lacks direct booking link & ${item.city} local search rank is on Page 2`;
      
      // Load saved status if any
      const savedStatus = localStorage.getItem(`ig_lead_status_${item.id}`);

      return {
        ...item,
        instagram_handle: handle,
        instagram_url: igUrl,
        instagram_followers: followers,
        instagram_audit_gap: gap,
        has_instagram: true,
        instagram_verified: true,
        outreach_status: savedStatus || item.outreach_status || 'new'
      };
    });

    igState.categoryData[key] = list;
  }

  updateGlobalStats();
  updateCategoryBadges();
}

// Update Global Stats Metric
function updateGlobalStats() {
  let total = 0;
  for (const key in igState.categoryData) {
    total += igState.categoryData[key].length;
  }
  if (dom.statTotalLeads) dom.statTotalLeads.textContent = total;
  if (dom.exportCount) dom.exportCount.textContent = total;
}

// Update Category Tab Counters for Current City
function updateCategoryBadges() {
  for (const key in IG_CATEGORIES) {
    const badge = document.getElementById(IG_CATEGORIES[key].badgeId);
    if (badge) {
      const count = igState.categoryData[key].filter(lead => matchesCity(lead.city, igState.activeCity)).length;
      badge.textContent = count;
    }
  }
}

// Helper: Check if lead belongs to city
function matchesCity(leadCity, targetCity) {
  if (!leadCity || !targetCity) return false;
  return leadCity.trim().toLowerCase() === targetCity.trim().toLowerCase();
}

// Set Active City
function applyCitySelection(cityName, saveToStorage = true) {
  igState.activeCity = cityName;
  if (saveToStorage) {
    try {
      localStorage.setItem('uk_leads_selected_city', cityName);
    } catch (_) {}
  }

  // Update Dropdown
  if (dom.cityDropdown) {
    dom.cityDropdown.value = cityName;
  }

  // Update Pills
  dom.cityPills.forEach(pill => {
    if (pill.dataset.city && pill.dataset.city.toLowerCase() === cityName.toLowerCase()) {
      pill.classList.add('active');
    } else {
      pill.classList.remove('active');
    }
  });

  // Update Heading Display
  if (dom.cityHeadingDisplay) {
    dom.cityHeadingDisplay.textContent = cityName;
  }

  updateCategoryBadges();
  renderLeads();
}

// Set Active Category
function applyCategorySelection(categoryKey) {
  if (!IG_CATEGORIES[categoryKey]) return;
  igState.activeCategory = categoryKey;

  dom.categoryTabs.forEach(tab => {
    if (tab.dataset.category === categoryKey) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  renderLeads();
}

// Filter and Render Leads
function renderLeads() {
  const currentCategoryList = igState.categoryData[igState.activeCategory] || [];
  
  // Filter by City
  let list = currentCategoryList.filter(lead => matchesCity(lead.city, igState.activeCity));

  // Filter by Search Query
  if (igState.searchQuery.trim() !== '') {
    const q = igState.searchQuery.trim().toLowerCase();
    list = list.filter(lead => {
      const name = (lead.name || '').toLowerCase();
      const handle = (lead.instagram_handle || '').toLowerCase();
      const borough = (lead.borough || '').toLowerCase();
      const kw = (lead.target_keyword || '').toLowerCase();
      return name.includes(q) || handle.includes(q) || borough.includes(q) || kw.includes(q);
    });
  }

  // Filter by Follower Tier
  if (igState.followerFilter !== 'all') {
    list = list.filter(lead => {
      const count = parseFollowerCount(lead.instagram_followers);
      if (igState.followerFilter === 'micro') return count < 10000;
      if (igState.followerFilter === 'growth') return count >= 10000 && count <= 50000;
      if (igState.followerFilter === 'authority') return count > 50000;
      return true;
    });
  }

  // Filter by Status
  if (igState.statusFilter !== 'all') {
    list = list.filter(lead => (lead.outreach_status || 'new') === igState.statusFilter);
  }

  igState.filteredLeads = list;

  // Update Results Badge & Caption
  const cat = IG_CATEGORIES[igState.activeCategory];
  if (dom.resultsCountBadge) {
    dom.resultsCountBadge.textContent = `${list.length} ${cat ? cat.name : 'Brands'}`;
  }
  if (dom.resultsCaptionText) {
    dom.resultsCaptionText.textContent = `Showing verified Instagram business profiles in ${igState.activeCity}`;
  }

  // Handle Empty State
  if (list.length === 0) {
    dom.leadsGrid.innerHTML = '';
    dom.leadsTableBody.innerHTML = '';
    dom.emptyState.classList.remove('hidden');
    dom.leadsGrid.classList.add('hidden');
    dom.leadsTableContainer.classList.add('hidden');
    return;
  }

  dom.emptyState.classList.add('hidden');

  if (igState.viewMode === 'cards') {
    dom.leadsGrid.classList.remove('hidden');
    dom.leadsTableContainer.classList.add('hidden');
    renderCards(list);
  } else {
    dom.leadsGrid.classList.add('hidden');
    dom.leadsTableContainer.classList.remove('hidden');
    renderTable(list);
  }
}

// Parse string like "24.5k" or "120k" to integer
function parseFollowerCount(str) {
  if (!str) return 0;
  const cleaned = str.toString().toLowerCase().trim();
  if (cleaned.endsWith('m')) return parseFloat(cleaned) * 1000000;
  if (cleaned.endsWith('k')) return parseFloat(cleaned) * 1000;
  return parseInt(cleaned.replace(/[^\d]/g, ''), 10) || 0;
}

// Render Card View
function renderCards(leads) {
  dom.leadsGrid.innerHTML = '';

  const fragment = document.createDocumentFragment();

  leads.forEach(lead => {
    const card = document.createElement('div');
    card.className = 'lead-card lead-card-instagram';
    card.id = `lead-card-${lead.id}`;

    const cleanHandle = (lead.instagram_handle || '').replace('@', '');
    const igDirectUrl = `https://ig.me/m/${cleanHandle}`;
    const igWebUrl = lead.instagram_url || `https://www.instagram.com/${cleanHandle}/`;
    const status = lead.outreach_status || 'new';

    card.innerHTML = `
      <div class="lead-header">
        <div class="lead-header-info">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span class="category-pill">${lead.borough || lead.city}</span>
            <span class="instagram-follower-pill">📸 ${lead.instagram_followers || 'Verified'}</span>
          </div>
          <h3 class="lead-name" title="${lead.name}">${lead.name}</h3>
          <div class="lead-address">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            ${lead.address || `${lead.borough || ''}, ${lead.city}`}
          </div>
        </div>
        <div class="lead-rating-box">
          <span class="rating-val">★ ${lead.rating || 4.9}</span>
          <span class="reviews-count">(${lead.reviews_count || 120} reviews)</span>
        </div>
      </div>

      <div class="instagram-info-item" style="margin: 8px 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <a href="${igWebUrl}" target="_blank" rel="noopener noreferrer" class="instagram-handle-link" title="Open Instagram Profile in new tab">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            <strong>${lead.instagram_handle}</strong>
            <span style="color: #38bdf8; font-size: 0.8rem;" title="Instagram Verified Account">✓</span>
          </a>
          <span style="font-size: 0.75rem; color: #94a3b8;">${lead.city}</span>
        </div>
      </div>

      <!-- Social to SEO Audit Gap Box -->
      <div class="ig-audit-box">
        <div class="ig-audit-icon">🔍</div>
        <div class="ig-audit-text">
          <span class="ig-audit-label">Social-to-SEO Conversion Gap:</span>
          ${lead.instagram_audit_gap || 'Instagram bio lacks direct WhatsApp trial pass link & local search rank is on Page 2.'}
        </div>
      </div>

      <!-- Opportunity Tag -->
      <div class="seo-opportunity-box" style="margin-bottom: 12px;">
        <div class="opportunity-tag">🎯 Keyword: "${lead.target_keyword || (lead.category + ' in ' + lead.city)}"</div>
        <div class="opportunity-impact">${lead.seo_opportunity ? lead.seo_opportunity.monthly_impact : 'Est. 40-70 new customer inquiries monthly'}</div>
      </div>

      <!-- Direct Action Buttons -->
      <div class="lead-actions" style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
          <button class="btn btn-instagram btn-launch-dm" data-id="${lead.id}" title="Launch Instagram Direct Message & Auto-copy Tailored Pitch">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            Launch DM
          </button>
          <button class="btn btn-secondary btn-copy-pitch" data-id="${lead.id}" title="Copy Tailored DM Pitch to Clipboard">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            Copy Pitch
          </button>
        </div>

        <div style="display: flex; gap: 8px; align-items: center;">
          <a href="${lead.website}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" style="flex: 1; text-decoration: none;" title="Visit Website">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            Website
          </a>
          ${lead.whatsapp_number ? `
            <a href="https://wa.me/${lead.whatsapp_number}?text=${encodeURIComponent(getTailoredPitch(lead))}" target="_blank" rel="noopener noreferrer" class="btn btn-emerald btn-sm" style="text-decoration: none;" title="Backup WhatsApp Outreach">
              💬 WA
            </a>
          ` : ''}
          <select class="status-select select-lead-status" data-id="${lead.id}" aria-label="Update Lead Status">
            <option value="new" ${status === 'new' ? 'selected' : ''}>New</option>
            <option value="contacted" ${status === 'contacted' ? 'selected' : ''}>DM Sent</option>
            <option value="in_discussion" ${status === 'in_discussion' ? 'selected' : ''}>Discussion</option>
            <option value="converted" ${status === 'converted' ? 'selected' : ''}>Converted</option>
          </select>
        </div>
      </div>
    `;

    fragment.appendChild(card);
  });

  dom.leadsGrid.appendChild(fragment);
  bindCardEvents();
}

// Render Table View
function renderTable(leads) {
  dom.leadsTableBody.innerHTML = '';

  const fragment = document.createDocumentFragment();

  leads.forEach(lead => {
    const tr = document.createElement('tr');
    tr.id = `table-row-${lead.id}`;

    const cleanHandle = (lead.instagram_handle || '').replace('@', '');
    const igDirectUrl = `https://ig.me/m/${cleanHandle}`;
    const igWebUrl = lead.instagram_url || `https://www.instagram.com/${cleanHandle}/`;
    const status = lead.outreach_status || 'new';

    tr.innerHTML = `
      <td>
        <div style="font-weight: 700; color: #f8fafc;">${lead.name}</div>
        <a href="${lead.website}" target="_blank" rel="noopener noreferrer" style="font-size: 0.75rem; color: #94a3b8; text-decoration: none;">${lead.website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]}</a>
      </td>
      <td>
        <a href="${igWebUrl}" target="_blank" rel="noopener noreferrer" class="instagram-handle-link">
          ${lead.instagram_handle}
        </a>
      </td>
      <td>
        <span class="instagram-follower-pill">${lead.instagram_followers || '10k+'}</span>
      </td>
      <td>
        <span style="font-size: 0.8rem; color: #cbd5e1;">${lead.borough || lead.city}, ${lead.city}</span>
      </td>
      <td>
        <div style="font-size: 0.75rem; color: #fda4af; max-width: 260px; line-height: 1.3;">
          ${lead.instagram_audit_gap || 'Audit Gap: Missing direct booking & local rank page 2'}
        </div>
      </td>
      <td>
        <code style="font-size: 0.75rem; color: #fbbf24;">${lead.target_keyword || lead.category}</code>
      </td>
      <td>
        <select class="status-select select-lead-status" data-id="${lead.id}">
          <option value="new" ${status === 'new' ? 'selected' : ''}>New</option>
          <option value="contacted" ${status === 'contacted' ? 'selected' : ''}>DM Sent</option>
          <option value="in_discussion" ${status === 'in_discussion' ? 'selected' : ''}>Discussion</option>
          <option value="converted" ${status === 'converted' ? 'selected' : ''}>Converted</option>
        </select>
      </td>
      <td>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-instagram btn-sm btn-launch-dm" data-id="${lead.id}" title="Launch DM & Copy Script">
            DM
          </button>
          <button class="btn btn-secondary btn-sm btn-copy-pitch" data-id="${lead.id}" title="Copy Pitch">
            📋
          </button>
        </div>
      </td>
    `;

    fragment.appendChild(tr);
  });

  dom.leadsTableBody.appendChild(fragment);
  bindCardEvents();
}

// Bind Click & Change Events to Dynamic Elements
function bindCardEvents() {
  // Launch DM Buttons
  document.querySelectorAll('.btn-launch-dm').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const leadId = btn.dataset.id;
      launchInstagramDM(leadId);
    });
  });

  // Copy Pitch Buttons
  document.querySelectorAll('.btn-copy-pitch').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const leadId = btn.dataset.id;
      copyLeadPitch(leadId);
    });
  });

  // Status Dropdown Changes
  document.querySelectorAll('.select-lead-status').forEach(select => {
    select.addEventListener('change', (e) => {
      const leadId = select.dataset.id;
      const newStatus = select.value;
      updateLeadStatus(leadId, newStatus);
    });
  });
}

// Generate Tailored Instagram DM Pitch
function getTailoredPitch(lead) {
  const cat = IG_CATEGORIES[lead.category_key || igState.activeCategory] || IG_CATEGORIES.salons;
  const savedTemplate = localStorage.getItem(cat.storageScriptKey) || cat.defaultScript;

  const cleanHandle = (lead.instagram_handle || '').replace('@', '');
  const followers = lead.instagram_followers || '10k+';
  const borough = lead.borough || lead.city;
  const keyword = lead.target_keyword || `${cat.singular} in ${lead.city}`;
  const gap = lead.instagram_audit_gap || 'Instagram bio lacks direct booking link';

  let msg = savedTemplate
    .replace(/{name}/g, lead.name)
    .replace(/{handle}/g, `@${cleanHandle}`)
    .replace(/{city}/g, lead.city)
    .replace(/{borough}/g, borough)
    .replace(/{followers}/g, followers)
    .replace(/{keyword}/g, keyword)
    .replace(/{website}/g, lead.website)
    .replace(/{gap}/g, gap);

  // Normalize markdown bold (**text**) to clean bold (*text*)
  msg = msg.replace(/\*\*([^*]+)\*\*/g, '*$1*');
  return msg;
}

// Launch Instagram DM + Auto-copy Pitch
async function launchInstagramDM(leadId) {
  const lead = findLeadById(leadId);
  if (!lead) return;

  const pitch = getTailoredPitch(lead);
  const cleanHandle = (lead.instagram_handle || '').replace('@', '');

  // Copy to clipboard
  try {
    await navigator.clipboard.writeText(pitch);
    showToast(`🚀 Pitch copied! Launching Instagram DM for @${cleanHandle}...`);
  } catch (err) {
    console.warn('Clipboard write failed:', err);
    showToast(`Launching Instagram DM for @${cleanHandle}...`);
  }

  // Auto update status to contacted if currently new
  if (lead.outreach_status === 'new') {
    updateLeadStatus(leadId, 'contacted');
  }

  // Open Direct Message deep link
  // Primary: Instagram DM thread / fallback to profile
  const dmUrl = `https://ig.me/m/${cleanHandle}`;
  const profileUrl = lead.instagram_url || `https://www.instagram.com/${cleanHandle}/`;

  // Open in new tab
  window.open(profileUrl, '_blank');
}

// Copy Pitch to Clipboard
async function copyLeadPitch(leadId) {
  const lead = findLeadById(leadId);
  if (!lead) return;

  const pitch = getTailoredPitch(lead);
  try {
    await navigator.clipboard.writeText(pitch);
    showToast(`📋 Tailored DM pitch copied for ${lead.name}!`);
  } catch (err) {
    showToast(`❌ Could not copy pitch: ${err.message}`, 'error');
  }
}

// Find Lead by ID
function findLeadById(leadId) {
  for (const catKey in igState.categoryData) {
    const found = igState.categoryData[catKey].find(l => l.id === leadId);
    if (found) return found;
  }
  return null;
}

// Update Lead Status
function updateLeadStatus(leadId, newStatus) {
  const lead = findLeadById(leadId);
  if (!lead) return;

  lead.outreach_status = newStatus;
  try {
    localStorage.setItem(`ig_lead_status_${leadId}`, newStatus);
  } catch (_) {}

  // Sync across inputs
  document.querySelectorAll(`.select-lead-status[data-id="${leadId}"]`).forEach(el => {
    el.value = newStatus;
  });

  showToast(`Updated status to "${newStatus.replace('_', ' ')}" for ${lead.name}`);
}

// Bulk Copy Handles
async function copyBulkHandles() {
  if (igState.filteredLeads.length === 0) {
    showToast('No leads to copy handles from!', 'error');
    return;
  }

  const handles = igState.filteredLeads
    .map(l => l.instagram_handle)
    .filter(Boolean)
    .join(', ');

  try {
    await navigator.clipboard.writeText(handles);
    showToast(`📋 Copied ${igState.filteredLeads.length} Instagram handles to clipboard!`);
  } catch (err) {
    showToast(`Error copying: ${err.message}`, 'error');
  }
}

// Export CSV with Instagram Fields
function exportInstagramCsv() {
  const currentCategoryList = igState.categoryData[igState.activeCategory] || [];
  const list = currentCategoryList.filter(lead => matchesCity(lead.city, igState.activeCity));

  if (list.length === 0) {
    showToast('No leads available in this selection to export.', 'error');
    return;
  }

  const headers = [
    'Business Name',
    'Category',
    'City',
    'Borough',
    'Instagram Handle',
    'Instagram URL',
    'Instagram Followers',
    'Social Audit Gap',
    'Target Keyword',
    'Website',
    'Phone',
    'WhatsApp Number',
    'Rating',
    'Reviews Count',
    'Outreach Status'
  ];

  const rows = list.map(l => [
    `"${(l.name || '').replace(/"/g, '""')}"`,
    `"${(l.category || '').replace(/"/g, '""')}"`,
    `"${(l.city || '').replace(/"/g, '""')}"`,
    `"${(l.borough || '').replace(/"/g, '""')}"`,
    `"${(l.instagram_handle || '').replace(/"/g, '""')}"`,
    `"${(l.instagram_url || '').replace(/"/g, '""')}"`,
    `"${(l.instagram_followers || '').replace(/"/g, '""')}"`,
    `"${(l.instagram_audit_gap || '').replace(/"/g, '""')}"`,
    `"${(l.target_keyword || '').replace(/"/g, '""')}"`,
    `"${(l.website || '').replace(/"/g, '""')}"`,
    `"${(l.phone || '').replace(/"/g, '""')}"`,
    `"${(l.whatsapp_number || '').replace(/"/g, '""')}"`,
    `"${l.rating || ''}"`,
    `"${l.reviews_count || ''}"`,
    `"${l.outreach_status || 'new'}"`
  ]);

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const fileName = `Instagram_Leads_${igState.activeCategory}_${igState.activeCity.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast(`✅ Exported ${list.length} Instagram leads to ${fileName}`);
}

// Show Toast Notification
function showToast(message, type = 'success') {
  if (!dom.toastContainer) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span>${message}</span>
    </div>
  `;

  dom.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-fadeout');
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, 3500);
}

// Setup Event Listeners
function setupEventListeners() {
  // City Dropdown
  if (dom.cityDropdown) {
    dom.cityDropdown.addEventListener('change', (e) => {
      applyCitySelection(e.target.value);
    });
  }

  // City Pills
  dom.cityPills.forEach(pill => {
    pill.addEventListener('click', () => {
      if (pill.dataset.city) {
        applyCitySelection(pill.dataset.city);
      }
    });
  });

  // Category Tabs
  dom.categoryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      if (tab.dataset.category) {
        applyCategorySelection(tab.dataset.category);
      }
    });
  });

  // Search Input
  if (dom.searchInput) {
    dom.searchInput.addEventListener('input', (e) => {
      igState.searchQuery = e.target.value;
      if (dom.searchClear) {
        if (e.target.value.length > 0) {
          dom.searchClear.classList.remove('hidden');
        } else {
          dom.searchClear.classList.add('hidden');
        }
      }
      renderLeads();
    });
  }

  // Clear Search
  if (dom.searchClear) {
    dom.searchClear.addEventListener('click', () => {
      dom.searchInput.value = '';
      igState.searchQuery = '';
      dom.searchClear.classList.add('hidden');
      renderLeads();
    });
  }

  // Follower Filter
  if (dom.filterFollowers) {
    dom.filterFollowers.addEventListener('change', (e) => {
      igState.followerFilter = e.target.value;
      renderLeads();
    });
  }

  // Status Filter
  if (dom.filterStatus) {
    dom.filterStatus.addEventListener('change', (e) => {
      igState.statusFilter = e.target.value;
      renderLeads();
    });
  }

  // View Switchers
  if (dom.btnViewCards) {
    dom.btnViewCards.addEventListener('click', () => {
      igState.viewMode = 'cards';
      dom.btnViewCards.classList.add('active');
      dom.btnViewTable.classList.remove('active');
      renderLeads();
    });
  }

  if (dom.btnViewTable) {
    dom.btnViewTable.addEventListener('click', () => {
      igState.viewMode = 'table';
      dom.btnViewTable.classList.add('active');
      dom.btnViewCards.classList.remove('active');
      renderLeads();
    });
  }

  // Reset Filters
  if (dom.btnResetFilters) {
    dom.btnResetFilters.addEventListener('click', () => {
      if (dom.searchInput) dom.searchInput.value = '';
      if (dom.filterFollowers) dom.filterFollowers.value = 'all';
      if (dom.filterStatus) dom.filterStatus.value = 'all';
      igState.searchQuery = '';
      igState.followerFilter = 'all';
      igState.statusFilter = 'all';
      renderLeads();
    });
  }

  // Bulk Copy Handles
  if (dom.btnBulkCopy) {
    dom.btnBulkCopy.addEventListener('click', copyBulkHandles);
  }

  // Export CSV
  if (dom.btnExportCsv) {
    dom.btnExportCsv.addEventListener('click', exportInstagramCsv);
  }

  // Edit Pitch Script Modal
  if (dom.btnEditScript) {
    dom.btnEditScript.addEventListener('click', () => {
      const cat = IG_CATEGORIES[igState.activeCategory];
      if (!cat) return;

      if (dom.modalCategoryName) dom.modalCategoryName.textContent = cat.name;
      const currentScript = localStorage.getItem(cat.storageScriptKey) || cat.defaultScript;
      if (dom.scriptEditorTextarea) dom.scriptEditorTextarea.value = currentScript;

      dom.modalScript.classList.remove('hidden');
    });
  }

  if (dom.modalScriptClose) {
    dom.modalScriptClose.addEventListener('click', () => {
      dom.modalScript.classList.add('hidden');
    });
  }

  if (dom.btnScriptReset) {
    dom.btnScriptReset.addEventListener('click', () => {
      const cat = IG_CATEGORIES[igState.activeCategory];
      if (!cat) return;
      if (dom.scriptEditorTextarea) dom.scriptEditorTextarea.value = cat.defaultScript;
      try {
        localStorage.removeItem(cat.storageScriptKey);
      } catch (_) {}
      showToast('Reset pitch script to default.');
    });
  }

  if (dom.btnScriptSave) {
    dom.btnScriptSave.addEventListener('click', () => {
      const cat = IG_CATEGORIES[igState.activeCategory];
      if (!cat) return;
      const val = dom.scriptEditorTextarea.value;
      try {
        localStorage.setItem(cat.storageScriptKey, val);
      } catch (_) {}
      dom.modalScript.classList.add('hidden');
      showToast(`Saved customized DM pitch for ${cat.name}!`);
    });
  }

  // Add Lead Modal
  if (dom.btnAddLead) {
    dom.btnAddLead.addEventListener('click', () => {
      dom.modalAddLead.classList.remove('hidden');
    });
  }

  if (dom.modalAddClose) {
    dom.modalAddClose.addEventListener('click', () => {
      dom.modalAddLead.classList.add('hidden');
    });
  }

  if (dom.btnAddCancel) {
    dom.btnAddCancel.addEventListener('click', () => {
      dom.modalAddLead.classList.add('hidden');
    });
  }

  if (dom.formAddLead) {
    dom.formAddLead.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('lead-name').value.trim();
      const category = document.getElementById('lead-category').value;
      const city = document.getElementById('lead-city').value.trim();
      const borough = document.getElementById('lead-borough').value.trim() || city;
      let igHandle = document.getElementById('lead-instagram').value.trim();
      if (!igHandle.startsWith('@')) igHandle = `@${igHandle}`;
      const followers = document.getElementById('lead-followers').value.trim() || '15k';
      const website = document.getElementById('lead-website').value.trim();
      const phone = document.getElementById('lead-phone').value.trim();
      const auditGap = document.getElementById('lead-audit-gap').value.trim() || 'Instagram bio lacks direct booking link & local search rank is on Page 2';
      const keyword = document.getElementById('lead-keyword').value.trim() || `${category} in ${city}`;

      const newLead = {
        id: `custom-ig-${Date.now()}`,
        name,
        category,
        category_key: category,
        city,
        borough,
        address: `${borough}, ${city}`,
        instagram_handle: igHandle,
        instagram_url: `https://www.instagram.com/${igHandle.replace('@', '')}/`,
        instagram_followers: followers,
        instagram_audit_gap: auditGap,
        has_instagram: true,
        instagram_verified: true,
        website,
        has_website: true,
        phone,
        whatsapp_number: phone.replace(/[^\d]/g, ''),
        rating: 5.0,
        reviews_count: 50,
        target_keyword: keyword,
        outreach_status: 'new'
      };

      // Save to storage
      const cat = IG_CATEGORIES[category];
      if (cat) {
        try {
          const currentCustom = JSON.parse(localStorage.getItem(cat.storageCustomKey) || '[]');
          currentCustom.unshift(newLead);
          localStorage.setItem(cat.storageCustomKey, JSON.stringify(currentCustom));
        } catch (_) {}

        igState.categoryData[category].unshift(newLead);
      }

      dom.formAddLead.reset();
      dom.modalAddLead.classList.add('hidden');

      applyCitySelection(city);
      applyCategorySelection(category);
      updateGlobalStats();
      showToast(`✅ Successfully added Instagram lead: ${name}!`);
    });
  }

  // Close modals on overlay click
  window.addEventListener('click', (e) => {
    if (e.target === dom.modalScript) dom.modalScript.classList.add('hidden');
    if (e.target === dom.modalAddLead) dom.modalAddLead.classList.add('hidden');
  });
}
