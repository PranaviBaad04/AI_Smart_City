// static/js/map.js

let smartCityMap;
let mapMarkers = [];

// Initialize Map
function initSmartCityMap(containerId, centerLat = 40.7128, centerLng = -74.0060, zoom = 13) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // CartoDB Positron (Bright, sleek, gray map tile layer)
    const mapTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    });

    smartCityMap = L.map(containerId, {
        center: [centerLat, centerLng],
        zoom: zoom,
        layers: [mapTiles]
    });

    return smartCityMap;
}

// Clear all active markers
function clearMapMarkers() {
    mapMarkers.forEach(marker => {
        smartCityMap.removeLayer(marker);
    });
    mapMarkers = [];
}

// Add Custom Marker
function addCityMarker(lat, lng, popupContent, iconType = 'info') {
    if (!smartCityMap) return;

    // Custom glowing color indicators matching roles/categories
    let markerColor = '#2563eb'; // blue default
    if (iconType === 'traffic-high') markerColor = '#ef4444'; // Red
    else if (iconType === 'traffic-med') markerColor = '#f59e0b'; // Amber
    else if (iconType === 'traffic-low') markerColor = '#10b981'; // Green
    else if (iconType === 'pollution-high') markerColor = '#7f1d1d'; // Dark Red
    else if (iconType === 'pollution-med') markerColor = '#b45309'; // Gold
    else if (iconType === 'service-outage') markerColor = '#9333ea'; // Purple
    else if (iconType === 'report-pending') markerColor = '#dc2626'; // Coral Red
    else if (iconType === 'report-progress') markerColor = '#d97706'; // Orange
    else if (iconType === 'report-resolved') markerColor = '#16a34a'; // Grass Green

    // CSS styled circular glowing marker
    const customHtml = `
        <div style="
            background-color: ${markerColor};
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 10px ${markerColor}, 0 0 4px rgba(0,0,0,0.5);
            animation: pulse 2.5s infinite;
        "></div>
    `;

    const customIcon = L.divIcon({
        html: customHtml,
        className: 'custom-leaflet-icon',
        iconSize: [14, 14],
        iconAnchor: [7, 7]
    });

    const marker = L.marker([lat, lng], { icon: customIcon })
        .addTo(smartCityMap)
        .bindPopup(popupContent);
        
    mapMarkers.push(marker);
    return marker;
}

// Set up Map click handler to select coordinates (Citizen Report Page)
function enableMapCoordinatePicker(inputFieldId, indicatorTextId) {
    if (!smartCityMap) return;

    let tempPickerMarker = null;

    smartCityMap.on('click', (e) => {
        const lat = e.latlng.lat.toFixed(6);
        const lng = e.latlng.lng.toFixed(6);
        
        // Remove previous temporary picker marker
        if (tempPickerMarker) {
            smartCityMap.removeLayer(tempPickerMarker);
        }

        // Add temporary target marker
        const pickerHtml = `
            <div style="
                background-color: #2563eb;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 0 12px #2563eb;
            "></div>
        `;
        const pickerIcon = L.divIcon({
            html: pickerHtml,
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        });

        tempPickerMarker = L.marker([lat, lng], { icon: pickerIcon }).addTo(smartCityMap);
        
        // Populate inputs
        const targetInput = document.getElementById(inputFieldId);
        const targetText = document.getElementById(indicatorTextId);
        
        if (targetInput) {
            // Reverse geocode simulation or direct coordinates input
            // Format: "lat,lng,Address Name"
            targetInput.value = `${lat},${lng},Custom Map Marker Sector`;
        }
        
        if (targetText) {
            targetText.innerHTML = `Selected Coordinate: <strong style="color: #2563eb;">${lat}, ${lng}</strong> (Metroville District)`;
        }
    });
}
