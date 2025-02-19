function searchMovies() {
    const query = document.getElementById('search').value;
    fetch(`https://api.themoviedb.org/3/search/movie?api_key=YOUR_API_KEY&query=${query}`)
        .then(response => response.json())
        .then(data => {
            const movies = data.results;
            const resultsDiv = document.getElementById('movie-results');
            resultsDiv.innerHTML = '';
            movies.forEach(movie => {
                const movieCard = `
                    <div class="movie-card">
                        <img src="https://image.tmdb.org/t/p/w500${movie.poster_path}" alt="${movie.title}">
                        <h2>${movie.title}</h2>
                        <p>${movie.overview}</p>
                    </div>
                `;
                resultsDiv.innerHTML += movieCard;
            });
        });
}

function addToWatchlist(movieId) {
    // Logique pour ajouter le film à la liste
    console.log(`Ajouté à la liste: ${movieId}`);
}

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer la barre de films
    const carousel = document.querySelector('.film-carousel');

    let scrollAmount = 0;
    const scrollInterval = setInterval(function() {
        if (scrollAmount >= carousel.scrollWidth) {
            carousel.scrollLeft = 0;
            scrollAmount = 0;
        } else {
            carousel.scrollLeft += 1; // Change la vitesse du défilement
            scrollAmount += 1;
        }
    }, 15); // Plus la valeur est basse, plus le défilement est rapide
});

