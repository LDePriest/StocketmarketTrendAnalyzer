let myChart;

async function getStockTrends() {
    const symbols = document.getElementById('symbols').value.split(',').map(s => s.trim());
    const resultsDiv = document.getElementById('results');
    const cpuCoresDiv = document.getElementById('cpu-cores');
    const ctx = document.getElementById('trendChart').getContext('2d');

    resultsDiv.innerHTML = '<p>Loading trends...</p>';

    try {
        const response = await fetch('/get_trends', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbols: symbols })
        });

        const data = await response.json();

        if (data.error) {
            resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }

        const trends = data.trends;
        const predictions = data.predictions;
        const cpuCores = data.cpu_cores;

        // Display CPU cores info
        cpuCoresDiv.innerHTML = `<p>Your computer is using ${cpuCores} physical CPU cores.</p>`;

        resultsDiv.innerHTML = '<h3>Stock Trends and Predictions:</h3>';

        // Create chart data
        const datasets = trends.map((trend, index) => ({
            label: symbols[index] + ' Trend',
            data: trend,
            borderColor: getRandomColor(),
            fill: false,
            tension: 0.3
        }));

        predictions.forEach((prediction, index) => {
            datasets.push({
                label: symbols[index] + ' Prediction',
                data: prediction,
                borderColor: getRandomColor(),
                fill: false,
                borderDash: [5, 5],
                tension: 0.3
            });
        });

        // Clear and render the chart
        if (myChart) {
            myChart.destroy();
        }
        myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: Math.max(...trends.map(t => t.length)) }, (_, i) => `Day ${i + 1}`),
                datasets: datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    zoom: {
                        pan: {
                            enabled: true, // Enable panning
                            mode: 'xy', // Pan in both directions (x and y)
                            threshold: 10, // Optional: increase the pan sensitivity
                            modifierKey: 'alt', // Optional: hold 'alt' key for panning (you can change this if needed)
                        },
                        zoom: {
                            enabled: true, // Enable zooming
                            mode: 'xy', // Zoom in both directions (x and y)
                            wheel: {
                                enabled: true // Allow zooming with the mouse wheel
                            },
                            pinch: {
                                enabled: true // Allow pinch-to-zoom on touch devices
                            },
                            drag: {
                                enabled: false // Disable drag-to-zoom for this setup
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error fetching trends:', error);
        resultsDiv.innerHTML = '<p>Error fetching trends. Please try again later.</p>';
    }
}

// Generate random color for charts
function getRandomColor() {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgb(${r}, ${g}, ${b})`;
}

// Reset zoom function
function resetZoom() {
    if (myChart) {
        myChart.resetZoom();
    }
}
