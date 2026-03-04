// Initialize Map
const map = L.map('map', {
    zoomControl: false // Move zoom control
}).setView([49.25, -123.1], 10);

L.control.zoom({ position: 'topright' }).addTo(map);

// Add sleek dark theme map tiles (CartoDB Dark Matter)
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// App State
let clients = [];
let markers = [];
let pendingCorrelation = [];
let isCorrelating = false;

// DOM Elements
const clientListEl = document.getElementById('clientList');
const identifiedCountEl = document.getElementById('identifiedCount');
const pendingCountEl = document.getElementById('pendingCount');
const searchInput = document.getElementById('searchInput');

// Load Data
async function loadData() {
    try {
        const response = await fetch('correlated_nearby.json');
        const data = await response.json();
        clients = data.clients.map((c, index) => {
            const hasCandidates = c.candidates && c.candidates.length > 0;
            let defaultIndex = 0;

            if (hasCandidates) {
                // Find first candidate that isn't a generic location/address
                const isGeneric = (cat) => {
                    if (!cat) return true;
                    const genericLabels = ['premise', 'street address', 'route', 'intersection', 'subpremise', 'neighborhood'];
                    return genericLabels.includes(cat.toLowerCase());
                };

                const nonGenericIndex = c.candidates.findIndex(cand => !isGeneric(cand.category) && cand.name !== 'Unknown');
                if (nonGenericIndex !== -1) {
                    defaultIndex = nonGenericIndex;
                }
            }

            const primary = hasCandidates ? c.candidates[defaultIndex] : c;
            const isUnknown = primary.name === 'Unknown' || !primary.name;

            return {
                id: index,
                ...c,
                selectedIndex: defaultIndex,
                identified: !isUnknown,
                businessName: isUnknown ? 'Unknown Business' : primary.name,
                address: primary.address || c.address || 'Unresolved Location',
                category: primary.category || c.category || 'misc',
                maps_uri: primary.maps_uri || c.maps_uri || ''
            };
        });

        document.querySelector('header p span').textContent = clients.length;

        initMapMarkers();
        updateStats();
        renderSidebar();
    } catch (error) {
        console.error("Failed to load correlated_nearby.json:", error);
        clientListEl.innerHTML = '<div style="padding:20px; text-align:center; color: #ef4444;">Error loading json. Did you run the python script?</div>';
    }
}

// Markers
function initMapMarkers() {
    clients.forEach(client => {
        const icon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="pin ${client.identified ? 'identified' : ''}" id="pin-${client.id}"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
        });

        const marker = L.marker([client.lat, client.lon], { icon }).addTo(map);

        marker.on('click', () => {
            selectClient(client.id);
        });

        markers[client.id] = marker;
    });

    // Fit bounds
    if (clients.length > 0) {
        const group = new L.featureGroup(Object.values(markers));
        map.fitBounds(group.getBounds(), { padding: [50, 50] });
    }
}

// Sidebar Rendering
function renderSidebar(filterText = '') {
    clientListEl.innerHTML = '';

    const filteredClients = clients.filter(c =>
        c.businessName.toLowerCase().includes(filterText.toLowerCase()) ||
        c.address.toLowerCase().includes(filterText.toLowerCase())
    );

    filteredClients.forEach((client, idx) => {
        const card = document.createElement('div');
        card.className = `client-card ${client.identified ? 'identified' : ''}`;
        card.id = `card-${client.id}`;
        card.style.animationDelay = `${idx * 0.05}s`;

        const badgeClass = client.identified ? 'status-badge identified' : 'status-badge';
        const badgeText = client.identified ? 'Identified' : 'Pending';

        let extraHtml = '';
        if (client.identified) {
            extraHtml = `
                <div class="coords" style="margin-top:8px;">Category: ${client.category}</div>
                <div class="coords" style="margin-top:4px;"><a href="${client.maps_uri}" target="_blank" style="color:#60a5fa; text-decoration:none;">View on Google Maps</a></div>
            `;
        } else {
            extraHtml = `<div class="coords" style="margin-top:8px; color:#ef4444;">Could not resolve Place ID</div>`;
        }

        let candidateSelectHtml = '';
        if (client.candidates && client.candidates.length > 1) {
            candidateSelectHtml = `
                <div style="margin-top: 12px;">
                    <select class="candidate-select" data-client-id="${client.id}" onclick="event.stopPropagation()">
                        ${client.candidates.map((cand, i) =>
                `<option value="${i}" ${i === client.selectedIndex ? 'selected' : ''}>
                                ${cand.name} (${cand.category}) - ${cand.distance !== undefined ? cand.distance : '0'}m
                            </option>`
            ).join('')}
                    </select>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="card-header">
                <span class="coords">${client.lat.toFixed(4)}, ${client.lon.toFixed(4)}</span>
                <span class="${badgeClass}">${badgeText}</span>
            </div>
            <div class="business-name" id="name-${client.id}">${client.businessName}</div>
            <div class="address" id="addr-${client.id}">${client.address}</div>
            ${extraHtml}
            ${candidateSelectHtml}
        `;

        card.addEventListener('click', () => selectClient(client.id));
        clientListEl.appendChild(card);
    });

    document.querySelectorAll('.candidate-select').forEach(select => {
        select.addEventListener('change', (e) => {
            const clientId = parseInt(e.target.dataset.clientId);
            const candidateIndex = parseInt(e.target.value);
            updateClientCandidate(clientId, candidateIndex);
        });
    });
}

// Interaction
function selectClient(id) {
    // Reset active states
    document.querySelectorAll('.client-card').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.pin').forEach(el => el.classList.remove('active'));

    // Set active
    const card = document.getElementById(`card-${id}`);
    if (card) {
        card.classList.add('active');
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    const pin = document.getElementById(`pin-${id}`);
    if (pin) pin.classList.add('active');

    // Pan map
    map.setView([clients[id].lat, clients[id].lon], 16, { animate: true, duration: 1 });
}

function updateClientCandidate(clientId, candidateIndex) {
    const client = clients.find(c => c.id === clientId);
    if (!client || !client.candidates) return;

    client.selectedIndex = candidateIndex;
    const cand = client.candidates[candidateIndex];
    const isUnknown = cand.name === 'Unknown' || !cand.name;

    client.identified = !isUnknown;
    client.businessName = isUnknown ? 'Unknown Business' : cand.name;
    client.address = cand.address || client.address || 'Unresolved Location';
    client.category = cand.category || 'misc';
    client.maps_uri = cand.maps_uri || '';

    // Re-render sidebar and update stats
    renderSidebar(searchInput.value);
    updateStats();

    // Update marker
    const pin = document.getElementById(`pin-${clientId}`);
    if (pin) {
        if (client.identified) {
            pin.classList.add('identified');
        } else {
            pin.classList.remove('identified');
        }
    }
}

// Search
searchInput.addEventListener('input', (e) => {
    renderSidebar(e.target.value);
});

function updateStats() {
    const identified = clients.filter(c => c.identified).length;
    identifiedCountEl.textContent = identified;
    pendingCountEl.textContent = clients.length - identified;
}

// Startup
loadData();
