from flask import Flask, render_template, request, redirect, session, abort, Response
import subprocess
from flask_sse import sse
import time
import threading
import os
from os import listdir
from os.path import isfile, join
import shutil

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost:6379"
app.register_blueprint(sse, url_prefix='/stream')
processes = []
newthread = None

@app.route('/')
def index():
    if request.remote_addr in [x[0] for x in os.walk(os.path.abspath(__file__).replace(os.path.basename(__file__), ""))]:
        files = [f for f in listdir(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr) if isfile(join(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr, f))]
        if len(files) == 1:
            return redirect("/buildozer")
        if len(files) == 2:
            return redirect("/compile")
    else:
        return render_template('index.html')

@app.route('/buildozer')
def buildozer():
    return render_template("buildozer.html")

def compilelog():
    _id = threading.get_ident()
    time.sleep(1)
    process = subprocess.Popen(
        'tcpdump',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding='utf-8',
        errors='replace'
    )
    with app.app_context():
        sse.publish({"message": "--id "+str(_id)}, type='greeting')
    text = ""
    while True:
        realtime_output = process.stdout.readline()

        if realtime_output == '' and process.poll() is not None:
            break

        if realtime_output:
            text += realtime_output.strip()
            text += "<br>"
            with app.app_context():
              sse.publish({"message": text}, type='greeting')

        pass

        if _id not in processes:
            print("Yeah that's right")
            break

    if _id in processes:
        processes.remove(_id)

@app.route("/compile")
def compile():
    if os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr in [x[0] for x in os.walk(os.path.abspath(__file__).replace(os.path.basename(__file__), ""))]:
        files = [f for f in listdir(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr) if isfile(join(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr, f))]
        if len(files) == 1:
            return redirect("/buildozer")
        if len(files) == 2:
            if len(processes) > 5:
                return "I'm sorry, the server is a tiny bit overloaded, please try compiling your app later, when less people are also compiling their app!"
            else:
                newthread = threading.Thread(target=compilelog)
                newthread.start()
                processes.append(newthread.ident)
                return render_template("compile.html")
    else:
        return redirect("/")
    
@app.route('/', methods=['POST'])
def upload_file():
    if os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr in [x[0] for x in os.walk(os.path.abspath(__file__).replace(os.path.basename(__file__), ""))]:
        files = [f for f in listdir(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr) if isfile(join(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr, f))]
        if len(files) == 1:
            return redirect("/buildozer")
        if len(files) == 2:
            return redirect("/compile")
    else:
        os.mkdir(request.remote_addr)
        uploaded_file = request.files['file']
        if uploaded_file.filename == "main.py":
            if uploaded_file.filename != '':
                uploaded_file.save(fr"{request.remote_addr}\\{uploaded_file.filename}")
            return redirect('/buildozer')
        else:
            abort(415) is None

@app.route('/buildozer', methods=['POST'])
def upload_buildozer():
    if os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr in [x[0] for x in os.walk(os.path.abspath(__file__).replace(os.path.basename(__file__), ""))]:
        files = [f for f in listdir(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr) if isfile(join(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr, f))]
        if len(files) == 1:
            uploaded_file = request.files['file']
            if uploaded_file.filename == "buildozer.spec":
                if uploaded_file.filename != '':
                    uploaded_file.save(fr"{request.remote_addr}\\{uploaded_file.filename}")
                return redirect('/compile')
            else:
                abort(415)
        if len(files) == 2:
            return redirect("/compile")
    else:
        return redirect("/")

@app.route('/erase')
def erase():
    if os.path.exists(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr):
        shutil.rmtree(os.path.abspath(__file__).replace(os.path.basename(__file__), "")+request.remote_addr)
    return redirect("/")

@app.route("/stopthread", methods=["POST"])
def stopthread():
    _id = int(request.args.get("id"))
    if _id in processes:
        if _id is None:
            return abort(400)
        else:
            processes.remove(_id)
            return Response("OK", status=200)
    else:
        return Response("You either tried to made this request yourself, or the program has finished.", status=404)

@app.route("/checkthreads")
def checkthreads():
    return str(len(processes))

app.run()
