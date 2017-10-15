from flask import Flask, render_template, request, json, jsonify, redirect
import json
from colour import Color
import requests
from bs4 import BeautifulSoup
import re

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

def parse_python(code):
    class_decs = set() # Class decs
    class_refs = set() # Class refs
    func_decs = set() # Func decs
    func_refs = set() # Func refs
    for name in re.findall("class .* *:", code) :
    	class_decs.add(re.search("(?<=class )(.*)[^ :]", name).group().strip())
	for name in re.findall("import *.*", code) :
		item = re.search("(?<=import ).*", name).group()
		for i in item.split(',') :
			class_refs.add(i.strip())
    for name in re.findall("def .*\(.*\) *:", code) :
    	func_decs.add(re.search("(?<=def )(.*)(?=\()", name).group().strip())
    # TODO func_refs can use improvement
    for name in re.findall("\..* *\(.*\)", code) :
    	func_refs.add(re.search("(?<=\.)(.*)(?=\()", name).group().strip())
    return (class_decs, class_refs, func_decs, func_refs)

def parse_java(code):
    class_decs = set() # Class decs
    class_refs = set() # Class refs
    func_decs = set() # Func decs
    func_refs = set() # Func refs
    for name in re.findall("class.*", code) :
    	class_decs.add(name.split()[1].strip())
    for name in re.findall("new .*", code) :
    	class_refs.add(re.search("(?<=new )(.*?)((?=\()|(?=\[)|(?=\{)|(?=\.))", name).group().strip())
    for name in re.findall("(public|private)(.*?\(.*? .*\))", code) :
    	name = re.search("(.*)(?=\()", ''.join(name)).group().strip()
    	func_decs.add(name.split()[-1])
    for name in re.findall("\..* *\(.*\)", code) :
    	func_refs.add(re.search("(?<=\.)(.*?)(?=\()", name).group().strip())
    return(class_decs, class_refs, func_decs, func_refs)

def parse_javascript(code):
    class_decs = set() # Class decs
    class_refs = set() # Class refs
    func_decs = set() # Func decs
    func_refs = set() # Func refs

    for name in re.findall("function *.*\(.*\)", code) :
    	reply = re.search("(?<=function )(.*?)(?=\()", name)
    	if (reply) :
    		func_decs.add(reply.group().strip())
    for name in re.findall("\..* *\(.*\)", code) :
    	func_refs.add(re.search("(?<=\.)(.*?)(?=\()", name).group().strip())
    for i in func_refs :
    	print(i)

    return(class_decs, class_refs, func_decs, func_refs)

###################
# Persistent Data #
###################

repo_map = {} # (repo_path, repo_name, repo_branch) -> file_map
code_map = {} # (repo_path, repo_name, repo_branch) -> file_id -> ([class decs], [class refs], [func decs], [func refs])

language_map = {
	'.java': parse_java,
	'.py': parse_python,
	'.js': parse_javascript
}

ext_whitelist = set()
ext_blacklist = set()

def init_file_map(repo_author, repo_name, repo_branch):
	repo_map[(repo_author, repo_name, repo_branch)] = FileMap(repo_author, repo_name, repo_branch)
	code_map[(repo_author, repo_name, repo_branch)] = {}

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
		analysis = language_map[ext](content)
		code_map[(repo_author, repo_name, repo_branch)][file_id] = analysis

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
				file_id = repo_map[(repo_author, repo_name, repo_branch)].add_file(folder, name)
				if ext in language_map:
					analyze_content(path, ext, file_id)

	path = '/' + repo_author + '/' + repo_name + '/tree/' + repo_branch
	#github_dfs(path)
	parse_javascript("""(function(){
    'use strict';

    // saving constants
    var VERSION = '1.0';
    var ORIGINAL = window.Class;

    // creating global class variable
    var Class = window.Class = function (obj) {
        obj = obj || {};
        // call initialize if given
        var constructor = function () {
            return (this.initialize) ? this.initialize.apply(this, arguments) : self;
        };
        // adds implement to the class itself
        if(obj.implement) {
            var self = window === this ? copy(constructor.prototype) : this;
            var imp = obj.implement;
            remove(obj, 'implement');
            obj = extend(obj, implement(imp));
        }
        // assign prototypes
        constructor.prototype = copy(obj);
        // assign correct constructor for correct instanceof comparison
        constructor.constructor = constructor;
        // save initial object as parent so it can be called by this.parent
        constructor._parent = copy(obj);
        // attaching class properties to constructor
        for(var i = 0, values = ['extend', 'implement', 'getOptions', 'setOptions']; i < values.length; i++) {
            constructor[values[i]] = Class[values[i]];
        }

        return constructor;
    };

    // adding class method extend
    Class.extend = function (obj) {
        var self = this;
        // check if implement is passed through extend
        if(obj.implement) {
            this.prototype = extend(this.prototype, implement(obj.implement));
            // remove implement from obj
            remove(obj, 'implement');
        }
        // check if we should invoke parent when its called within a method
        for(var key in obj) {
            obj[key] = typeof obj[key] === 'function' && /parent/.test(obj[key].toString()) ? (function (method, name) {
                return function () {
                    this.parent = self._parent[name];
                    return method.apply(this, arguments);
                };
            })(obj[key], key) : obj[key]
        }
        // assign new parent
        this._parent = extend(this._parent, obj, true);
        // assign new prototype
        this.prototype = extend(this.prototype, obj);
        // return the class if its assigned
        return this;
    };

    // adding class method implement
    Class.implement = function (array) {
        return this.prototype = extend(this.prototype, implement(array));
    };

    // gets options from constructor
    Class.getOptions = function () {
        return this.prototype.options || {};
    };

    // sets options for constructor
    Class.setOptions = function (options) {
        return this.prototype.options = extend(this.prototype.options, options);
    };

    // preventing conflicts
    Class.noConflict = function () {
        // reassign original Class obj to window
        window.Class = ORIGINAL;
        return Class;
    };

    // returns current running version
    Class.version = VERSION;

    // helper for assigning methods to a new prototype
    function copy(obj) {
        var F = function () {};
            F.prototype = obj.prototype || obj;
        return new F();
    }

    // insures the removal of a given method name
    function remove(obj , name, safe){
        // if save is active we need to copy all attributes over.
        if(safe) {
            var safeObj = {};
            for(var key in obj) {
                if(key !== name) safeObj[key] = obj[key];
            }
        } else {
            delete obj[name];
        }
        return safeObj || obj;
    }

    // helper for merging two object with each other
    function extend(oldObj, newObj, preserve) {
        // failsave if something goes wrong
        if(!oldObj || !newObj) return oldObj || newObj || {};

        // make sure we work with copies
        oldObj = copy(oldObj);
        newObj = copy(newObj);

        for(var key in newObj) {
            if(Object.prototype.toString.call(newObj[key]) === '[object Object]') {
                extend(oldObj[key], newObj[key]);
            } else {
                // if preserve is set to true oldObj will not be overwritten by newObj if
                // oldObj has already a method key
                oldObj[key] = (preserve && oldObj[key]) ? oldObj[key] : newObj[key];
            }
        }

        return oldObj;
    }

    // helper for implementing other classes or objects
    function implement(array) {
        var collection = {};

        for(var i = 0; i < array.length; i++) {
            // check if a class is implemented and save its prototype
            if(typeof(array[i]) === 'function') array[i] = array[i].prototype;

            // safely remove initialize
            var safe = remove(array[i], 'initialize', true);

            // we use implement again if array has the apropriate methiod, otherwise we extend
            if(safe.implement) {
                collection = implement(safe.implement);
            } else {
                collection = extend(collection, safe);
            }
        }

        return collection;
    }

})();""")
	# TODO create links using analysis

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
	print('Map ' + str(file_map))
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
	print('Request ' + str(request.json))
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