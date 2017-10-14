from flask import Flask, render_template, request, json, jsonify, redirect
import json
from colour import Color
import requests
from bs4 import BeautifulSoup

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
        return self.files[file_id] if file_id < len(self.files) else None

    def add_file(self, path, name):
        index = 0
        while index < len(self.files):
            current = self.files[index]
            if current != None and current.path == path and current.name == name:
                return index
            index += 1

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
    branch = 'master'
    repo_map[(repo_author, repo_name)] = FileMap(repo_author, repo_name)

    # define functions
    # return list of file paths in a directory
    def get_list(url) :
        ret_list = []
        response = requests.get(url).text
        soup = BeautifulSoup(response)
        for file_tree in soup.find_all('table', class_='files js-navigation-container js-active-navigation-container') :
            for tbody in file_tree.find_all('tbody') :
                for link in tbody.find_all('a') :
                    link_list = link.get('href')
                    if '/commit/' not in link_list :
                        ret_list.append(link_list)
        return ret_list

    # check if file is legit TODO
    def check_file_content(base, path) :
        response = requests.get(base + path).text
        return True

    # create map by performing dfs search on root Github directory
    def dfs_util(base, path, stack) :
        if '/blob/' in (path) :
            if check_file_content(base, path) :
                sub_path = path.rsplit("/", 1)[0]
                name = path.rsplit("/", 1)[1]
                repo_map[(repo_author, repo_name)].add_file(sub_path, name)
        elif '/tree/' in (path):
            uri = base + path
            dir_list = get_list(uri)
            for item in dir_list :
                stack.append(item)
                dfs_util(base, item, stack)
                stack.pop()

    # create repo_map
    base = "https://github.com"
    path = "/" + repo_author + "/" + repo_name + "/" + "tree/" + branch
    stack = []
    dfs_util(base, path, stack)

def get_file_map(repo_author, repo_name):
    repo = (repo_author, repo_name)
    if not repo in repo_map:
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
    for key, value in file_map.tag_colors.items():
        data['tag_colors'].append({
            'tag': key,
            'color': value.hex_l
        })

    return jsonify(data)

@app.route('/api/<repo_author>/<repo_name>/file', methods=['POST'])
def add_file(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    file_info = request.json
    file_map.add_file(file_info['path'], file_info['name'])
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

@app.route('/api/<repo_author>/<repo_name>/file', methods=['DELETE'])
def remove_file(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    file_info = request.json
    file_map.remove_file(file_info['file_id'])
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

@app.route('/api/<repo_author>/<repo_name>/edge', methods=['POST'])
def add_edge(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    edge = request.json
    if not file_map.get_file(edge['source']) or not file_map.get_file(edge['target']):
        return json.dumps({'success': False}, 400, {'ContentType': 'application/json'})

    file_map.edges.append((edge['source'], edge['target']))
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

@app.route('/api/<repo_author>/<repo_name>/edge', methods=['DELETE'])
def remove_edge(repo_author, repo_name):
    file_map = get_file_map(repo_author, repo_name)
    edge = request.json
    file_map.edges.remove((edge['source'], edge['target']))
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

@app.route('/api/<repo_author>/<repo_name>/file/<file_id>/tag/<tag>', methods=['PUT'])
def set_file_tag(repo_author, repo_name, file_id, tag):
    file_map = get_file_map(repo_author, repo_name)
    file = file_map.get_file(int(file_id))
    if not file:
        return json.dumps({'success': False}, 400, {'ContentType': 'application/json'})

    file.tag = tag
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

@app.route('/api/<repo_author>/<repo_name>/tag/<tag>/color/<color_hex>', methods=['PUT'])
def set_tag_color(repo_author, repo_name, tag, color_hex):
    file_map = get_file_map(repo_author, repo_name)
    file_map.tag_colors[tag] = Color(color_hex)
    return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

if __name__ == "__main__":
    app.run(debug=True)