const app = Vue.createApp({
    data() {
      return {
        speciesStats: [],
        topContributors: [],
        graphData: [],
      };
    },
    methods: {
      fetchRegionStats() {
        const region = JSON.parse(localStorage.getItem('selectedRegion')); // Get region from localStorage
        if (!region) {
          alert("No region selected.");
          return;
        }
  
        axios.post('/api/region_stats', region)
          .then(response => {
            this.speciesStats = Object.entries(response.data.species_stats).map(([name, stats]) => ({
              name,
              sightings: stats.sightings,
              checklists: stats.checklists,
            }));
            this.topContributors = response.data.top_contributors;
          })
          .catch(error => {
            console.error("Error fetching region stats:", error);
          });
      },
      viewGraph(species) {
        axios.get(`/api/species_graph?species=${species}`)
          .then(response => {
            this.graphData = response.data;
            this.renderGraph();
          })
          .catch(error => {
            console.error("Error fetching graph data:", error);
          });
      },
      renderGraph() {
        const ctx = document.getElementById('sightingsGraph').getContext('2d');
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: this.graphData.map(entry => entry.date),
            datasets: [{
              label: 'Sightings',
              data: this.graphData.map(entry => entry.count),
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1
            }]
          }
        });
      }
    },
    mounted() {
      this.fetchRegionStats();
    }
  });
  
  app.mount('#app');
  