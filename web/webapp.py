from flask import Flask, redirect, request, render_template, send_from_directory
from rabbit_controller import RabbitController
from api import API
from bus import Bus
from context import Context
from runner import Runner
from status import Status


rabbit = RabbitController('localhost', 5672, 'guest', 'guest', '/')
bus = Bus(rabbit)
runner = Runner()
api = API(bus, runner)
status = Status()
context = Context(bus, status)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def landing_page():
    ctx = context.fetch()

    if 'success' in request.args:
        ctx['alert_success'] = request.args['success']
    if 'error' in request.args:
        ctx['alert_error'] = request.args['error']

    return render_template('landing_page.html', **ctx)


@app.route('/static/<path:path>', methods=['GET'])
def send_static(path):
    """ Static serving for static directory """
    return send_from_directory('static', path)


@app.route('/fonts/<path:path>', methods=['GET'])
def send_fonts(path):
    """ Static serving for fonts directory """
    return send_from_directory('fonts', path)


@app.route('/api/run/<path:path>', methods=['POST'])
def api_run(path):
    return redirect_with_alert(api.run(path))


@app.route('/api/fr0stlevel/<path:path>', methods=['POST'])
def api_fr0stlevel(path):
    return redirect_with_alert(api.fr0stlevel(path))


def redirect_with_alert(result):
    success, message = result
    alert_type = 'success' if success else 'error'
    return redirect('/?' + alert_type + '=' + message)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
