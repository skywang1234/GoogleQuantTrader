async function fetchImage() {
    try {
        // Trigger chart generation
        await fetch('/generate_macd_chart', { method: 'POST' });

        let response = await fetch('/get_price_image');
        let result = await response.json();
        let expectedMinLength = 40000;
        if (result.image.length < expectedMinLength) {
            console.warn('Received short Base64 string for price image, retrying...');
            return fetchImage();
        }
        
        let priceImage = document.getElementById('priceImage');
        console.log('Price image Base64 length:', result.image.length);
        priceImage.onload = () => {
            console.log('Price image loaded successfully');
        };
        priceImage.src = 'data:image/jpeg;base64,' + result.image;

        response = await fetch('/get_oscillator_image');
        result = await response.json();

        if (result.image.length < expectedMinLength) {
            console.warn('Received short Base64 string for oscillator image, retrying...');
            return fetchImage();
        }

        let oscillatorImage = document.getElementById('oscillatorImage');
        console.log('Oscillator image Base64 length:', result.image.length);
        oscillatorImage.onload = () => {
            console.log('Oscillator image loaded successfully');
        };
        oscillatorImage.src = 'data:image/jpeg;base64,' + result.image;
        fetchProfit();
    } catch (error) {
        console.error('Error fetching images:', error);
    }
}

async function fetchRSIImage() {
    try {
        // Trigger RSI chart generation
        await fetch('/generate_rsi_chart', { method: 'POST' });

        let response = await fetch('/get_rsi_price_image');
        let result = await response.json();

        let expectedMinLength = 40000;
        if (result.image.length < expectedMinLength) {
            console.warn('Received short Base64 string for RSI price image, retrying...');
            return fetchRSIImage();
        }

        let rsiPriceImage = document.getElementById('rsiPriceImage');
        console.log('RSI Price image Base64 length:', result.image.length);
        rsiPriceImage.onload = () => {
            console.log('RSI Price image loaded successfully');
        };
        rsiPriceImage.src = 'data:image/jpeg;base64,' + result.image;

        response = await fetch('/get_rsi_image');
        result = await response.json();
        let rsiImage = document.getElementById('rsiImage');
        console.log('RSI image Base64 length:', result.image.length);
        rsiImage.onload = () => {
            console.log('RSI image loaded successfully');
        };
        rsiImage.src = 'data:image/jpeg;base64,' + result.image;
        fetchProfit();
    } catch (error) {
        console.error('Error fetching RSI images:', error);
    }
}

async function fetchProfit() {
    try {
        let response = await fetch('/get_profit');
        let result = await response.json();
        cumulativeProfit = result.cumulative_profit;
        cumulativeRSIProfit = result.cumulative_rsi_profit;

        document.getElementById('cumulative-profit').textContent = `MACD Cumulative Profit: ${cumulativeProfit}`;
        document.getElementById('cumulative-rsi-profit').textContent = `RSI Cumulative Profit: ${cumulativeRSIProfit}`;
    } catch (error) {
        console.error('Error fetching profit data:', error);
    }
}

// Fetch image initially
fetchImage();
setTimeout(fetchRSIImage, 100);

// Fetch every 60 minutes with delays between each fetch
setInterval(fetchImage, 3600000);
setInterval(() => setTimeout(fetchRSIImage, 100), 3600000);
