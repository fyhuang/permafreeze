from flask import Flask

PORT = 47568

app = Flask(__name__)

@app.route('/')
def handle_index():
    pass

def start():
    app.run(port=PORT)
