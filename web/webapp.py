from flask import Flask, redirect, request, render_template, send_from_directory
from context import get_context
from api import start, stop, fr0stlevel
from mq import mq_start


app = Flask(__name__)


@app.route('/', methods=['GET'])
def landing_page():
    context = get_context()

    if 'success' in request.args:
        context['alert_success'] = request.args['success']
    if 'error' in request.args:
        context['alert_error'] = request.args['error']

    return render_template('landing_page.html', **context)


@app.route('/static/<path:path>', methods=['GET'])
def send_static(path):
    return send_from_directory('static', path)


@app.route('/fonts/<path:path>', methods=['GET'])
def send_fonts(path):
    return send_from_directory('fonts', path)


@app.route('/api/start/<path:path>', methods=['POST'])
def api_start(path):
    return redirect_with_alert(start(path))


@app.route('/api/stop/<path:path>', methods=['POST'])
def api_stop(path):
    return redirect_with_alert(stop(path))


@app.route('/api/fr0stlevel/<path:path>', methods=['POST'])
def api_fr0stlevel(path):
    return redirect_with_alert(fr0stlevel(path))


def redirect_with_alert(result):
    success, message = result
    alert_type = 'success' if success else 'error'
    return redirect('/?' + alert_type + '=' + message)


if __name__ == "__main__":
    mq_start()
    app.run(debug=True, host='0.0.0.0', port=8080)
