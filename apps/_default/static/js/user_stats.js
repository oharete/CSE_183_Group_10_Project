"use strict";

const app = Vue.createApp({
  delimiters: ["[[", "]]"], // Adjust Vue delimiters for compatibility with backend
  data() {
    return {
      searchQuery: "", // User's search input for species
      selectedSpecies: "", // Selected species for trends
      speciesList: [], // List of species fetched from the backend
      trends: [], // Bird-watching trends over time
    };
  },
  methods: {
    // Fetch trends for a specific species
    fetchTrendsForSpecies() {
      if (!this.searchQuery) {
        alert("Please enter a species name.");
        return;
      }
      this.selectedSpecies = this.searchQuery;

      axios
        .get(`/api/user_stats/trends?species=${encodeURIComponent(this.selectedSpecies)}`)
        .then((response) => {
          this.trends = response.data.trends || [];
          this.renderChart(); // Render the trends chart after data is fetched
        })
        .catch((error) => {
          console.error("Error fetching trends data:", error);
        });
    },
    // Render the trends chart using Chart.js
    renderChart() {
      const ctx = document.getElementById("trendChart").getContext("2d");
      const labels = this.trends.map((t) => t.date);
      const counts = this.trends.map((t) => t.count);

      new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: `Trends for ${this.selectedSpecies}`,
              data: counts,
              borderColor: "rgba(75, 192, 192, 1)",
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            x: {
              title: {
                display: true,
                text: "Date",
              },
            },
            y: {
              title: {
                display: true,
                text: "Sightings",
              },
            },
          },
        },
      });
    },
  },
  mounted() {
    console.log("Vue app is mounted!");
  },
});

app.mount("#app");
