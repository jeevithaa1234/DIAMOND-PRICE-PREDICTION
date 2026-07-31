document.addEventListener("DOMContentLoaded", function () {

    const chartData = document.getElementById("chart-data");

    if (!chartData) return;

    const cutLabels = JSON.parse(chartData.dataset.cutLabels);
    const cutValues = JSON.parse(chartData.dataset.cutValues);

    const colorLabels = JSON.parse(chartData.dataset.colorLabels);
    const colorValues = JSON.parse(chartData.dataset.colorValues);

    const clarityLabels = JSON.parse(chartData.dataset.clarityLabels);
    const clarityValues = JSON.parse(chartData.dataset.clarityValues);

    const cutCanvas = document.getElementById("cutChart");

    if (cutCanvas) {

        new Chart(cutCanvas, {

            type: "bar",

            data: {

                labels: cutLabels,

                datasets: [{

                    label: "Diamond Cut",

                    data: cutValues,

                    backgroundColor: "#38BDF8"

                }]

            }

        });

    }

    const colorCanvas = document.getElementById("colorChart");

    if (colorCanvas) {

        new Chart(colorCanvas, {

            type: "pie",

            data: {

                labels: colorLabels,

                datasets: [{

                    data: colorValues

                }]

            }

        });

    }

    const clarityCanvas = document.getElementById("clarityChart");

    if (clarityCanvas) {

        new Chart(clarityCanvas, {

            type: "doughnut",

            data: {

                labels: clarityLabels,

                datasets: [{

                    data: clarityValues

                }]

            }

        });

    }

});