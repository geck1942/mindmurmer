function showhideStatus(id) {
	var style = document.getElementById('status_' + id).style;
	style.display = style.display === 'block' ? 'none' : 'block';
}

function hideAlert(type) {
    for (var e of document.getElementsByClassName('alert-' + type)) {
        e.style.display = 'none';
    }
}
