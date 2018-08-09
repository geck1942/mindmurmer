from flask import Flask, render_template, send_from_directory


app = Flask(__name__)


@app.route("/")
def landing_page():
    context = {
        'test': "value",
        'test2': "value2",
        'items': ["a", "b", "c", "d", "e", "f"]
    }
    return render_template('landing_page.html', **context)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/fonts/<path:path>')
def send_fonts(path):
    return send_from_directory('fonts', path)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
