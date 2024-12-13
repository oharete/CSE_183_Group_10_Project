"use strict";

const app = Vue.createApp({
  delimiters: ["[[", "]]"], // Adjust Vue delimiters for compatibility with backend
  data() {
    return {
      searchQuery: "", // User's search input for species
      selectedSpecies: "", // Currently selected species for trends
      speciesSuggestions: [], // Species suggestions based on search query
      trends: [], // Bird-watching trends over time
    };
  },
  methods: {
    // Fetch species suggestions based on the search query
    fetchSpeciesSuggestions() {
      if (this.searchQuery.trim() === "") {
        this.speciesSuggestions = [];
        return;
      }
      axios
        .get(`/api/user_stats/species?suggest=${encodeURIComponent(this.searchQuery)}`)
        .then((response) => {
          this.speciesSuggestions = response.data.species.map((species) => species.common_name);
        })
        .catch((error) => {
          console.error("Error fetching species suggestions:", error);
        });
    },
    // Set the selected species and fetch trends
    selectSpecies(species) {
      this.selectedSpecies = species;
      this.searchQuery = species; // Update search bar
      this.speciesSuggestions = []; // Clear suggestions dropdown
      this.fetchTrendsForSpecies(); // Fetch trends for the selected species
    },
    // Fetch trends for a specific species
    fetchTrendsForSpecies() {
      if (!this.selectedSpecies) {
        alert("Please select a species.");
        return;
      }

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

      // Destroy any existing chart instance
      if (window.trendChart) {
        window.trendChart.destroy();
      }

      // Create a new chart
      window.trendChart = new Chart(ctx, {
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
    // Clear the selected species
    clearSelection() {
      this.selectedSpecies = "";
      this.searchQuery = "";
      this.speciesSuggestions = [];
      this.trends = [];
      if (window.trendChart) {
        window.trendChart.destroy();
      }
    },
  },
});

app.mount("#app");
