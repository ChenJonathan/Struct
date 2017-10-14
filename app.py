from flask import Flask, render_template, request, json, jsonify, redirect
import json

app = Flask(__name__)

@app.route("/")
def index():
	#username = str(request.form["user"])
	#password= str(request.form['password'])
    return render_template('index.html', title="Index")

if __name__ == "__main__":
    app.run(debug=True)