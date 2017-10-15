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

	def __init__(self, author, name, branch):
		self.author = author
		self.name = name
		self.branch = branch
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

#############################
# Language-Specific Parsers #
#############################

def parse_c_sharp(code):
	a = [] # Class decs
	b = [] # Class refs
	c = [] # Func decs
	d = [] # Func refs
	return (a, b, c, d)

###################
# Persistent Data #
###################

repo_map = {} # (repo_path, repo_name, repo_branch) -> file_map
code_map = {} # (repo_path, repo_name, repo_branch) -> file_id -> ([class decs], [class refs], [func decs], [func refs])

language_map = {
	'.cs': parse_c_sharp,
	'.py': parse_c_sharp
}

ext_whitelist = set()
ext_blacklist = set()

def init_file_map(repo_author, repo_name, repo_branch):
	repo_map[(repo_author, repo_name, repo_branch)] = FileMap(repo_author, repo_name, repo_branch)
	code_map[(repo_author, repo_name, repo_branch)] = {}
	file_map = repo_map[(repo_author, repo_name, repo_branch)]
	analysis_map = code_map[(repo_author, repo_name, repo_branch)]

	# Get list of file paths in a directory
	def get_list(html):
		ret_list = []
		soup = BeautifulSoup(html, 'html.parser')
		for link in soup.find_all('a'):
			linkparent = link.parent
			if (linkparent.name == 'span' and linkparent.parent.name == 'td'):
				link_list = link.get('href')
				if '/commit/' not in link_list:
					ret_list.append(link_list)
		return ret_list

	# Checks to see if a blob file is a code file
	def check_file_content(ext, html):
		if ext in ext_whitelist:
			return True
		if ext in ext_blacklist:
			return False
		soup = BeautifulSoup(html, 'html.parser')
		for item in soup.find_all('div', class_='blob-wrapper data type-text'):
			ext_blacklist.add(ext)
			return False
		ext_whitelist.add(ext)
		return True

	# Attempt to analyze the contents of a code file and add them to the code map
	def analyze_content(path, ext, file_id):
		content = requests.get(('https://raw.githubusercontent.com' + path).replace('/blob', '')).text
		analysis_map[file_id] = language_map[ext](content)

	# Recurse through the tree, saving files as persistent data
	def github_dfs(path):
		base = 'https://github.com'
		html = requests.get(base + path).text
		if '/tree/' in path:
			for child in get_list(html):
				github_dfs(child)
		else:
			ext = '.' + path.rsplit('.', 1)[-1]
			if check_file_content(ext, html):
				folder, name = path.rsplit('/', 1)
				file_id = file_map.add_file(folder, name)
				if ext in language_map:
					analyze_content(path, ext, file_id)

	path = '/' + repo_author + '/' + repo_name + '/tree/' + repo_branch
	github_dfs(path)

	# Create links using code analysis
	for source_id, source_analysis in analysis_map.items():
		for class_dec in source_analysis[0]:
			for ref_id, ref_analysis in analysis_map.items():
				if source_id == ref_id:
					continue
				if class_dec in ref_analysis[1]:
					edge = (ref_id, source_id)
					if edge not in file_map.edges:
						file_map.edges.append(edge)
	for source_id, source_analysis in analysis_map.items():
		for func_dec in source_analysis[2]:
			for ref_id, ref_analysis in analysis_map.items():
				if source_id == ref_id:
					continue
				if func_dec in ref_analysis[3]:
					edge = (ref_id, source_id)
					if edge not in file_map.edges:
						file_map.edges.append(edge)

def get_file_map(repo_author, repo_name, repo_branch):
	repo = (repo_author, repo_name, repo_branch)
	if not repo in repo_map:
		init_file_map(repo_author, repo_name, repo_branch)
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

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>')
def get_repo(repo_author, repo_name, repo_branch):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	
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

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/file', methods=['POST'])
def add_file(repo_author, repo_name, repo_branch):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	file_info = request.json
	file_map.add_file(file_info['path'], file_info['name'])
	return json.dumps({'success': True})

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/file', methods=['DELETE'])
def remove_file(repo_author, repo_name, repo_branch):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	file_info = request.json
	file_map.remove_file(file_info['file_id'])
	return json.dumps({'success': True})

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/edge', methods=['POST'])
def add_edge(repo_author, repo_name, repo_branch):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	edge = request.json
	edge = (edge['source'], edge['target'])
	if not file_map.get_file(edge[0]) or not file_map.get_file(edge[1]):
		return json.dumps({'success': False})

	if edge in file_map.edges:
		return json.dumps({'success': False})
	file_map.edges.append(edge)
	return json.dumps({'success': True})

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/edge', methods=['DELETE'])
def remove_edge(repo_author, repo_name, repo_branch):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	edge = request.json
	file_map.edges.remove((edge['source'], edge['target']))
	return json.dumps({'success': True})

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/file/<file_id>/tag/<tag>', methods=['PUT'])
def set_file_tag(repo_author, repo_name, repo_branch, file_id, tag):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	file = file_map.get_file(int(file_id))
	if not file:
		return json.dumps({'success': False})

	file.tag = tag
	return json.dumps({'success': True})

@app.route('/api/<repo_author>/<repo_name>/<repo_branch>/tag/<tag>/color/<color_hex>', methods=['PUT'])
def set_tag_color(repo_author, repo_name, repo_branch, tag, color_hex):
	file_map = get_file_map(repo_author, repo_name, repo_branch)
	file_map.tag_colors[tag] = Color(color_hex)
	return json.dumps({'success': True})

if __name__ == "__main__":
	app.run(debug=True)