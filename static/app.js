// --- GLOBAL VARIABLES ---
let scanning = false;
let debounceTimer;
let html5Scanner = null; // For Html5Qrcode if used later
let isCameraActive = false;

// Product database for local matching
const products = {
    "1001": {"name": "Dairy Milk", "price": 40},
    "1002": {"name": "Coca Cola", "price": 50},
    "1003": {"name": "Maggi Noodles", "price": 20},
    "1004": {"name": "Lay's Chips", "price": 10}
};

document.addEventListener('DOMContentLoaded', () => {
    initBluetooth();
    loadCart();
});

// --- 1. AI PREDICTION ---
function predictNextWord(text) {
    clearTimeout(debounceTimer);
    const predictionBox = document.getElementById('predictionBox');
    const suggestionList = document.getElementById('suggestionList');
    
    if (text.length < 1) {
        predictionBox.style.display = 'none';
        return;
    }

    const localMatch = localProductSearch(text);
    if (localMatch) {
        showPrediction(localMatch);
        return;
    }

    suggestionList.innerHTML = `<div class="prediction-item"><span class="prediction-name">Searching...</span></div>`;
    predictionBox.style.display = 'block';

    debounceTimer = setTimeout(() => {
        fetch('/ollama_predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        })
        .then(response => response.ok ? response.json() : Promise.reject())
        .then(data => {
            if (data.prediction && data.prediction.trim() !== '') showPrediction(data.prediction);
            else showNoPredictions();
        })
        .catch(() => {
            const fallbackMatch = localProductSearch(text);
            if (fallbackMatch) showPrediction(fallbackMatch); else showNoPredictions();
        });
    }, 300);
}

function localProductSearch(text) {
    const textLower = text.toLowerCase();
    for (const product of Object.values(products)) {
        if (product.name.toLowerCase().startsWith(textLower)) return product.name;
        const words = product.name.toLowerCase().split(' ');
        for (const word of words) if (word.startsWith(textLower)) return product.name;
        if (product.name.toLowerCase().includes(textLower)) return product.name;
    }
    return null;
}

function showPrediction(productName) {
    const suggestionList = document.getElementById('suggestionList');
    const predictionBox = document.getElementById('predictionBox');
    let productPrice = '';
    for (const product of Object.values(products)) {
        if (product.name === productName) { productPrice = `₹${product.price}`; break; }
    }
    suggestionList.innerHTML = `<div class="prediction-item" onclick="selectPrediction('${productName}')"><span class="prediction-name">${productName}</span><span class="prediction-price">${productPrice}</span></div>`;
    predictionBox.style.display = 'block';
}

function showNoPredictions() {
    document.getElementById('suggestionList').innerHTML = `<div class="prediction-item"><span class="prediction-name text-muted">Type more letters...</span></div>`;
}

function selectPrediction(productName) {
    sendItem(productName);
    document.getElementById('aiSearch').value = '';
    document.getElementById('predictionBox').style.display = 'none';
}

// --- 2. CAMERA (Quagga) ---
function toggleCamera() {
    let container = document.getElementById('scanner-container');
    if (!scanning) {
        container.style.display = 'block';
        Quagga.init({
            inputStream: { name: "Live", type: "LiveStream", target: container },
            decoder: { readers: ["code_128_reader"] }
        }, () => Quagga.start());
        scanning = true;
    } else {
        Quagga.stop();
        container.style.display = 'none';
        scanning = false;
    }
}
Quagga.onDetected((result) => {
    toggleCamera();
    sendItem(result.codeResult.code);
});

// --- 3. CART & ITEMS ---
function sendItem(code) {
    document.getElementById('aiSearch').value = '';
    document.getElementById('predictionBox').style.display = 'none';
    
    fetch('/scan_barcode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ code: code })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            return fetch('/add_item', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code: code })
            }).then(r => r.json());
        }
        return data;
    })
    .then(data => {
        if (data.success) {
            updateUI(data);
            updateRecommendations(data.recommendations || []);
        } else {
            alert('Product not found!');
        }
    })
    .catch(error => console.error('Error:', error));
}

function changeQty(code, action) {
    fetch('/update_qty', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ code: code, action: action })
    })
    .then(response => response.json())
    .then(data => { if (data.success) updateUI(data); });
}

function updateUI(data) {
    let display = document.getElementById('cartDisplay');
    display.innerHTML = "";
    if (!data.cart || Object.keys(data.cart).length === 0) {
        display.innerHTML = `<p class="text-muted text-center py-4">Cart is empty</p>`;
        document.getElementById('totalAmt').innerText = '0';
        return;
    }
    for (let code in data.cart) {
        let item = data.cart[code];
        display.innerHTML += `
        <div class="d-flex justify-content-between align-items-center mb-3 p-3 bg-white rounded shadow-sm">
            <div><b>${item.name}</b><br><small class="text-muted">₹${item.price} / unit</small></div>
            <div class="qty-box">
                <button class="qty-btn qty-minus" onclick="changeQty('${code}','minus')">−</button>
                <b>${item.qty}</b>
                <button class="qty-btn qty-plus" onclick="changeQty('${code}','plus')">+</button>
            </div>
            <b class="text-success">₹${item.price * item.qty}</b>
        </div>`;
    }
    document.getElementById('totalAmt').innerText = data.total || '0';
}

function updateRecommendations(recommendations) {
    const ul = document.getElementById("recommendations");
    ul.innerHTML = "";
    if (!recommendations || recommendations.length === 0) {
        ul.innerHTML = `<li class="list-group-item text-muted">No recommendations available</li>`;
        return;
    }
    recommendations.forEach(item => { ul.innerHTML += `<li class="list-group-item">${item}</li>`; });
}

function loadCart() {
    fetch('/get_cart')
    .then(response => response.json())
    .then(data => { if (data.success) updateUI(data); });
}

// Event Listeners for Search
const aiSearchInput = document.getElementById('aiSearch');
if(aiSearchInput) {
    aiSearchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            const text = this.value.trim();
            if (text) sendItem(text);
        }
    });
    
    document.addEventListener('click', function(event) {
        const predictionBox = document.getElementById('predictionBox');
        if (!aiSearchInput.contains(event.target) && !predictionBox.contains(event.target)) {
            predictionBox.style.display = 'none';
        }
    });
}

// Reset Alert
document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('reset')) {
        alert("✅ Payment Successful! Cart cleared.");
        window.history.replaceState({}, document.title, "/");
    }
});

// --- 4. BLUETOOTH LOGIC ---
function initBluetooth() {
    let bluetoothDevice, commandCharacteristic, isFollowing = false, rssiHistory = [];
    const TROLLEY_SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
    const TROLLEY_COMMAND_UUID = '12345678-1234-5678-1234-56789abcdef1';

    const btnConnect = document.getElementById('btn-connect');
    const btnFollow = document.getElementById('btn-follow');
    const btnStop = document.getElementById('btn-stop');
    const statusText = document.getElementById('bt-status');
    const rssiText = document.getElementById('bt-rssi');
    const modeText = document.getElementById('bt-mode');
    const proximityBar = document.getElementById('proximity-bar');

    if (!btnConnect) return;

    btnConnect.addEventListener('click', async () => {
        if (!navigator.bluetooth) { alert("Web Bluetooth not supported. Use Chrome/Edge."); return; }
        try {
            statusText.textContent = "Searching..."; statusText.className = "badge bg-warning text-dark";
            bluetoothDevice = await navigator.bluetooth.requestDevice({ filters: [{ services: [TROLLEY_SERVICE_UUID] }], optionalServices: [TROLLEY_SERVICE_UUID] });
            bluetoothDevice.addEventListener('gattserverdisconnected', onDisconnected);
            const server = await bluetoothDevice.gatt.connect();
            const service = await server.getPrimaryService(TROLLEY_SERVICE_UUID);
            commandCharacteristic = await service.getCharacteristic(TROLLEY_COMMAND_UUID);
            statusText.textContent = "Connected"; statusText.className = "badge bg-success";
            btnConnect.disabled = true; btnFollow.disabled = false; btnStop.disabled = false;
            monitorRSSI();
        } catch (error) {
            console.error(error);
            if (error.name === 'NotFoundError') alert("No device found. Is ESP32 on?");
            else alert("Error: " + error.message);
            statusText.textContent = "Failed"; statusText.className = "badge bg-danger";
        }
    });

    if(btnFollow) {
        btnFollow.addEventListener('click', () => {
            isFollowing = !isFollowing;
            if (isFollowing) { modeText.textContent = "Following"; btnFollow.textContent = "⏸ Pause"; btnFollow.classList.replace('btn-success', 'btn-warning'); }
            else { modeText.textContent = "Paused"; btnFollow.textContent = "▶ Resume"; btnFollow.classList.replace('btn-warning', 'btn-success'); sendCommand(0x00); }
        });
    }
    if(btnStop) {
        btnStop.addEventListener('click', () => {
            isFollowing = false; modeText.textContent = "Stopped";
            if(btnFollow) { btnFollow.textContent = "▶ Start"; btnFollow.classList.replace('btn-warning', 'btn-success'); }
            sendCommand(0x00);
        });
    }

    async function monitorRSSI() {
        if (!bluetoothDevice || !bluetoothDevice.gatt.connected) return;
        try {
            const rssi = bluetoothDevice.rssi;
            if (rssi !== null && rssiText) {
                rssiText.textContent = rssi + " dBm";
                if (isFollowing) determineMovement(rssi);
                if(proximityBar) { let pct = ((rssi + 100) * 100) / 60; pct = Math.max(0, Math.min(100, pct)); proximityBar.style.width = pct + "%"; }
            }
        } catch (e) {}
        setTimeout(monitorRSSI, 1000);
    }

    function getSmoothedRSSI(newVal) {
        rssiHistory.push(newVal);
        if (rssiHistory.length > 10) rssiHistory.shift();
        return Math.floor(rssiHistory.reduce((a, b) => a + b, 0) / rssiHistory.length);
    }

    function determineMovement(currentRSSI) {
        const smoothed = getSmoothedRSSI(currentRSSI);
        if (smoothed > -60) sendCommand(0x02);
        else if (smoothed > -75) sendCommand(0x01);
        else if (smoothed > -85) sendCommand(0x03);
        else sendCommand(0x00);
    }

    async function sendCommand(byteCode) {
        if (!commandCharacteristic) return;
        try { await commandCharacteristic.writeValue(new Uint8Array([byteCode]).buffer); } catch (e) { onDisconnected(); }
    }

    function onDisconnected() {
        if(statusText) { statusText.textContent = "Disconnected"; statusText.className = "badge bg-danger"; }
        if(btnConnect) btnConnect.disabled = false;
        if(btnFollow) btnFollow.disabled = true;
        if(btnStop) btnStop.disabled = true;
        isFollowing = false;
        if(modeText) modeText.textContent = "Idle";
    }
}