function showhideStatus(id) {
	var style = document.getElementById('status_' + id).style;
	style.display = style.display === 'block' ? 'none' : 'block';
}

function removeAlerts() {
    window.history.pushState({}, document.title, '/');
}

function updateHeartRate() {
    document.getElementById('heart_rate').innerText = document.getElementById('heart_rate_slider').value
}