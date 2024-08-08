let cumulativeProfit;
let cumulativeRSIProfit;

async function fetchImage() {
    let response = await fetch('/get_price_image');
    let result = await response.json();
    document.getElementById('priceImage').src = 'data:image/png;base64,' + result.image;
    response = await fetch('/get_oscillator_image');
    result = await response.json();
    document.getElementById('oscillatorImage').src = 'data:image/png;base64,' + result.image;
}

async function fetchRSIImage() {
    let response = await fetch('/get_rsi_price_image');
    let result = await response.json();
    document.getElementById('rsiPriceImage').src = 'data:image/png;base64,' + result.image;
    response = await fetch('/get_rsi_image');
    result = await response.json();
    document.getElementById('rsiImage').src = 'data:image/png;base64,' + result.image;
}

async function fetchProfit() {
    let response = await fetch('/get_profit');
    let result = await response.json();
    cumulativeProfit = result.cumulative_profit;
    cumulativeRSIProfit = result.cumulative_rsi_profit;

    document.getElementById('cumulative-profit').textContent = `Cumulative Profit: ${cumulativeProfit}`;
    document.getElementById('cumulative-rsi-profit').textContent = `RSI Cumulative Profit: ${cumulativeRSIProfit}`;
}

// Fetch image initially 
fetchImage();
fetchRSIImage();
fetchProfit();

//Reload to ensure graphs are loaded
setTimeout(fetchImage, 1000);
setTimeout(fetchRSIImage, 1000);
setTimeout(fetchProfit, 1000);

//Fetch every 10 mins
setInterval(fetchProfit, 600000)
setInterval(fetchRSIImage, 600000);
setInterval(fetchImage, 600000);