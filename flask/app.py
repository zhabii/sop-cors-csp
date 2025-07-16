from flask import Flask, render_template, request, Response
from datetime import datetime
import json

app = Flask(__name__)
hits = 0

@app.route('/')
def root():
    global hits
    hits += 1

    ip = request.remote_addr
    ref = request.headers.get('Referer', '—')
    ua = request.headers.get('User-Agent', '—')
    time = datetime.now().isoformat()

    with open("log.txt", "a") as f:
        f.write(f"[{time}] {ip} | {ref} | {ua}\n")

    with open("log.txt", "r") as f:
        lines = f.readlines()[-30:]

    return render_template("index.html", count=hits, lines=lines)


@app.route("/csp-report", methods=['POST', 'GET'])
def csp_report():
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True) or {}
        time_str = datetime.now().isoformat()
        log_entry = f"[{time_str}] | {json.dumps(data)}\n"

        with open("csp.log", "a") as f:
            f.write(log_entry)

        return '', 204

    try:
        with open("csp.log", "r") as f:
            return "<br>".join(f.readlines()[-30:])
    except FileNotFoundError:
        return "empty log"

    
@app.route("/csp")
def csp():
    return render_template("csp.html")

   


