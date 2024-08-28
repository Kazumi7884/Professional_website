document.addEventListener('DOMContentLoaded', function() {
    const updateBox = document.querySelector('.update-box');
    
    if (updateBox) {
        fetch('/updates.json')
            .then(response => response.json())
            .then(updates => {
                updateBox.innerHTML = '<h3>What\'s New</h3>';
                updates.sort((a, b) => new Date(b.date) - new Date(a.date));
                updates.slice(0, 3).forEach(update => {
                    updateBox.innerHTML += `
                        <div class="update-item">
                            <a href="${update.url}">${update.title}</a>
                            <span class="update-date">${formatDate(update.date)}</span>
                        </div>
                    `;
                });
            })
            .catch(error => {
                console.error('Error fetching updates:', error);
                updateBox.innerHTML = '<p>Unable to load updates at this time.</p>';
            });
    }
});

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}
