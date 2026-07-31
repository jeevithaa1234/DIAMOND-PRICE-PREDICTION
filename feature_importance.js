document.addEventListener("DOMContentLoaded", function () {

    const featureData = document.getElementById("feature-data");

    if (!featureData) {
        console.error("Feature data element not found.");
        return;
    }

    const labels = JSON.parse(featureData.dataset.labels);
    const values = JSON.parse(featureData.dataset.values);

    const ctx = document.getElementById("importanceChart");

    if (!ctx) {
        console.error("Canvas not found.");
        return;
    }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Feature Importance",
                data: values,
                backgroundColor: "#4facfe",
                borderColor: "#2196f3",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,

            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: "Feature Importance of Diamond Attributes"
                }
            },

            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Importance Score"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Features"
                    }
                }
            }
        }
    });

});