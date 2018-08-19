function showhideStatus(id) {
	var style = document.getElementById('status_' + id).style;
	style.display = style.display === 'block' ? 'none' : 'block';
}

function start() {
    window.history.pushState({}, document.title, '/');
    // Re-render history every 80ms, should be ok on mobile device?
    setInterval(render, 80);
}

function updateHeartRate() {
    document.getElementById('heart_rate').innerText = document.getElementById('heart_rate_slider').value
}

function render() {
    now = moment();
    format_history('state_history', window.state_history, now);
    format_history('heart_rate_history', window.heart_rate_history, now);
}

function format_history(id, hist, now) {
    el = document.getElementById(id);
    el.innerText = hist.map(function(entry) {
        t = moment.utc(entry[0]);
        ts = t.local().format('MM/DD hh:mm:ss.SSS');
        diff = moment.duration(now.diff(t));
        diffs = diff.hours().toString().padStart(2, '0') + ':'
            + diff.minutes().toString().padStart(2, '0') + ':'
            + diff.seconds().toString().padStart(2, '0') + '.'
            + diff.milliseconds().toString().padStart(3, '0');
        v = entry[1];

        return ts + ' (' + diffs + ' ago): ' + v;
    }).join('\n');
}