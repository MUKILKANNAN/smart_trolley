function onScanSuccess(decodedText) {

    fetch("/scan_barcode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: decodedText })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert("Unknown barcode");
            return;
        }

        document.getElementById("lastProduct").innerText = data.product;
        document.getElementById("total").innerText = data.total;

        updateCart(data.cart);
        updateRecommendations(data.recommendations);
    });
}

function updateCart(cart) {
    const ul = document.getElementById("cart");
    ul.innerHTML = "";
    for (let key in cart) {
        let li = document.createElement("li");
        li.textContent = `${cart[key].name} x${cart[key].qty}`;
        ul.appendChild(li);
    }
}

function updateRecommendations(recs) {
    const ul = document.getElementById("recommendations");
    ul.innerHTML = "";

    if (!recs || recs.length === 0) {
        ul.innerHTML = "<li>No recommendations available</li>";
        return;
    }

    recs.forEach(item => {
        let li = document.createElement("li");
        li.textContent = item;
        ul.appendChild(li);
    });
}


// Start camera
let scanner = new Html5Qrcode("reader");
scanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 250 },
    onScanSuccess
);
