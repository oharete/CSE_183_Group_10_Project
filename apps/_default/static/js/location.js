const app = Vue.createApp({
  data() {
    return {
      speciesStats: [], // Stores species stats for the selected region
      topContributors: [], // Stores top contributors for the region
      graphData: [], // Data for the sightings graph
      isLoading: false, // Loading state for region stats
      graphLoading: false, // Loading state for graph data
    };
  },
  methods: {
    fetchRegionStats() {
      const region = JSON.parse(localStorage.getItem('selectedRegion')); // Get region from localStorage
      if (!region) {
        alert("No region selected.");
        return;
      }

      this.isLoading = true; // Set loading state
      axios.post('/api/region_stats', region)
        .then(response => {
          this.speciesStats = Object.entries(response.data.species_stats).map(([name, stats]) => ({
            name,
            sightings: stats.sightings,
            checklists: stats.checklists,
          }));
          this.topContributors = response.data.top_contributors;

          if (this.speciesStats.length === 0 && this.topContributors.length === 0) {
            alert("No data available for the selected region.");
          }
        })
        .catch(error => {
          alert("An error occurred while fetching region stats. Please try again.");
          console.error("Error fetching region stats:", error);
        })
        .finally(() => {
          this.isLoading = false; // Reset loading state
        });
    },
    viewGraph(species) {
      this.graphLoading = true; // Set graph loading state
      axios.get(`/api/species_graph?species=${species}`)
        .then(response => {
          this.graphData = response.data;
          this.renderGraph();
        })
        .catch(error => {
          alert("An error occurred while fetching graph data.");
          console.error("Error fetching graph data:", error);
        })
        .finally(() => {
          this.graphLoading = false; // Reset graph loading state
        });
    },
    renderGraph() {
      const canvas = document.getElementById('sightingsGraph');
      const ctx = canvas.getContext('2d');
      
      // Clear previous graph if any
      if (canvas.chart) {
        canvas.chart.destroy();
      }

      // Render new graph
      canvas.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: this.graphData.map(entry => entry.date),
          datasets: [{
            label: 'Sightings',
            data: this.graphData.map(entry => entry.count),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
            },
          },
        },
      });
    },
    clearGraph() {
      const canvas = document.getElementById('sightingsGraph');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear graph canvas
    },
  },
  mounted() {
    this.fetchRegionStats(); // Fetch region stats on page load
  }
});

app.mount('#app');

