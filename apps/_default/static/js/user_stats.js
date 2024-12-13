"use strict";

const app = Vue.createApp({
  delimiters: ['[[', ']]'], // Adjusted for compatibility with backend templates
  data() {
    return {
      // User stats data
      searchQuery: "", // User's search input for species
      userStatsData: {
        speciesList: [], // List of species seen by the user
        trends: [], // Bird-watching trends over time
      },
    };
  },
  computed: {
    filteredSpecies() {
      return this.userStatsData.speciesList.filter((species) =>
        species.toLowerCase().includes(this.searchQuery.toLowerCase())
      );
    },
  },
  methods: {
    fetchUserStats() {
      // Fetch species list
      axios
        .get("/api/user_stats/species")
        .then((response) => {
          this.userStatsData.speciesList = response.data.species;
        })
        .catch((error) => {
          console.error("Error fetching user stats (species list):", error);
        });

      // Fetch trends data
      axios
        .get("/api/user_stats/trends")
        .then((response) => {
          this.userStatsData.trends = response.data.trends;
          this.renderChart(); // Render chart after fetching data
        })
        .catch((error) => {
          console.error("Error fetching user stats (trends):", error);
        });
    },
    renderChart() {
      // Render trends chart using Chart.js
      const ctx = document.getElementById("trendChart").getContext("2d");
      const labels = this.userStatsData.trends.map((t) => t.date);
      const counts = this.userStatsData.trends.map((t) => t.count);

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
        },
      });
    },
  },
  mounted() {
    this.fetchUserStats(); // Fetch stats when the app loads
  },
});

app.mount("#app");
