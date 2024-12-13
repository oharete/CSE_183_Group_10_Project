"use strict";

const app = Vue.createApp({
  delimiters: ["[[", "]]"], // Adjust Vue delimiters for compatibility with backend
  data() {
    return {
      searchQuery: "", // User's search input for species
      speciesList: [], // List of species fetched from the backend
      trends: [], // Bird-watching trends over time
    };
  },
  computed: {
    // Dynamically filter the species list based on the search query
    filteredSpecies() {
      return this.speciesList.filter((species) =>
        species.toLowerCase().includes(this.searchQuery.toLowerCase())
      );
    },
  },
  methods: {
    // Fetch the list of species the user has seen
    fetchSpeciesList() {
      axios
        .get("/api/user_stats/species")
        .then((response) => {
          this.speciesList = response.data.species || [];
        })
        .catch((error) => {
          console.error("Error fetching species list:", error);
        });
    },
    // Fetch the user's bird-watching trends
    fetchTrends() {
      axios
        .get("/api/user_stats/trends")
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
              label: "Bird Sightings Over Time",
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
    console.log("Vue is mounted!"); // Debugging message
    this.fetchSpeciesList();
    this.fetchTrends();
  },
});

app.mount("#app");
