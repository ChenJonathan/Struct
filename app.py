from flask import Flask, render_template, request, json, jsonify, redirect
import json
from colour import Color

app = Flask(__name__)

class File:

    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.tag = None

class FileMap:

    def __init__(self, author, name):
        self.author = author
        self.name = name
        self.files = []
        self.edges = []
        self.tag_colors = {}

    def get_file(self, file_id):
        return self.files[file_id]

    def add_file(self, path, name):
        file = File(path, name)
        index = 0
        while index < len(self.files) and self.files[index] != None:
            index += 1
        self.files.insert(index, file)
        return index

    def remove_file(self, file_id):
        self.files[file_id] = None
        for edge in self.edges:
            # TODO improve efficiency
            if edge[0] == file_id or edge[1] == file_id:
                self.edges.remove(edge)

# Map of repos to file map objects
repo_map = {}

def init_file_map(repo_author, repo_name):
    repo_map[(repo_author, repo_name)] = FileMap(repo_author, repo_name)
    # TODO everything

def get_file_map(repo_author, repo_name):
    repo = (repo_author, repo_name)
    if not repo_map.has_key(repo):
        init_file_map(repo_author, repo_name)
    return repo_map[repo]

###########
# Routing #
###########

@app.route('/')
def route_index():
    return render_template('index.html', title='Index')

@app.route('/struct')
def route_struct():
    return render_template('graph.html', title='Struct Graph')

@app.route('/api/<repo_author>/<repo_name>')
def get_repo(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    
    data = {}
    data['author'] = repo_author
    data['name'] = repo_name

    data['files'] = []
    for file_id, file in enumerate(file_map.files):
        if file != None:
            data['files'].append({
                'id': file_id,
                'path': file.path,
                'name': file.name,
                'tag': file.tag
            })

    data['edges'] = []
    for source, target in file_map.edges:
        data['edges'].append({
            'source': source,
            'target': target
        })

    data['tag_colors'] = []
    for key, value in file_map.items():
        data['tag_colors'].append({
            'tag': key,
            'color': value.hex_l
        })

    return jsonify(data)

@app.route('/api/<repo_author>/<repo_name>/file', method='POST')
def add_file(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    file_info = request.json
    file_map.add_file(file_info['path'], file_info['name'])

@app.route('/api/<repo_author>/<repo_name>/file', method='DELETE')
def remove_file(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    file_info = request.json
    file_map.remove_file(file_info['file_id'])

@app.route('/api/<repo_author>/<repo_name>/edge', method='POST')
def add_edge(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    edge = request.json
    file_map.edges.append(edge['source'], edge['target'])

@app.route('/api/<repo_author>/<repo_name>/edge', method='DELETE')
def remove_edge(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    edge = request.json
    file_map.edges.remove(edge['source'], edge['target'])

@app.route('/api/<repo_author>/<repo_name>/file/<file_id>/tag/<tag>', method='PUT')
def set_file_tag(repo_author, repo_name, file_id, tag):
    file_map = get_file_map(repo_author, repo_name)
    file = file_map.get_file(file_id)
    file.tag = tag

@app.route('/api/<repo_author>/<repo_name>/tag/<tag>/color/<color_hex>', method='PUT')
def set_tag_color(repo_author, repo_name, tag, color_hex):
    file_map = get_file_map(repo_author, repo_name)
    file_map.tag_colors[tag] = Color(color_hex)

if __name__ == "__main__":
    app.run(debug=True)