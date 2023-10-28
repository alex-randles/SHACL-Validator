import json
import os
import random
import string
import urllib.parse
from flask import Flask, render_template, request, flash, redirect, session
from werkzeug.utils import secure_filename
import morph_kgc
import rdflib
import pyshacl


# definition of web application
app = Flask(__name__)
app.config['SECRET_KEY'] = "x633UE2xYRC"
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['FILE_COUNT'] = 0


def get_session_id():
    if "uid" not in session.keys():
        uid = ''.join(random.choices(string.ascii_lowercase, k=10))
        session['uid'] = uid
        return uid
    else:
        return session.get("uid")


# the main endpoint for the interface
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        session["count"] = 0
        # make uploads directory if not exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        # returns the initial view displayed
        return render_template(
            "index.html",
            open=open,
        )
    else:
        # if session.get("uid") is None:
        #     uid = ''.join(random.choices(string.ascii_lowercase, k=10))
        #     session['uid'] = uid
        # session_id = session.get("uid")
        # upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        # if not os.path.exists(upload_folder):
        #     os.makedirs(upload_folder)
        # session["upload_folder"] = upload_folder
        # exit()
        # returns the result page of the mapping process
        mapping_file = request.files.get("mapping-file")
        mapping_filename = secure_filename(mapping_file.filename)
        print(mapping_filename)
        # check mapping is uploaded and is a turtle file
        if mapping_filename == '':
            flash('Please upload a Mapping File!')
            return redirect(request.url)
        if not mapping_filename.endswith(".ttl"):
            flash('Mapping file must be a Turtle file (.ttl)')
            return redirect(request.url)
        mapping_file_path = os.path.join(app.config['UPLOAD_FOLDER'], mapping_filename)
        # check for two files with same name uploaded at same time
        if os.path.exists(mapping_file_path):
            # file_count = g.get("file_count", 0)
            file_count = app.config['FILE_COUNT']
            mapping_filename = f"{mapping_filename.split('.')[0]}-{file_count}.ttl"
            mapping_file_path = os.path.join(app.config['UPLOAD_FOLDER'], mapping_filename)
            app.config['FILE_COUNT'] = file_count + 1
        # save the mapping uploaded
        mapping_file.save(mapping_file_path)
        files = request.files.getlist("source-data")
        source_files = []
        # save each source file uploaded
        for file in files:
            source_filename = file.filename
            if source_filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], source_filename))
                source_files.append(source_filename)
        # execute the mapping and retrieve RDF data and any error messages
        mapping_result = execute_mapping(mapping_filename)
        # compare the source files defined in mapping to uploaded files
        rdf_generated = mapping_result.get("rdf_data")
        mapping_error = mapping_result.get("error_message")
        file_errors = []
        if mapping_error:
            file_errors = compare_mapping_sources(mapping_filename, source_files)
        print(f"RDF Generated: \n {rdf_generated}")
        print(f"Mapping Engine Error: \n {mapping_error}")
        # remove the files from server
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], mapping_filename))
        for file in source_files:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
        # check if any source files defined in mapping were not uploaded
        if file_errors:
            # join returned list of source files not uploaded and create a HTML list to display
            file_listing = "<ul>"
            for file_name in file_errors:
                file_listing += f"<li> {file_name} </li>"
            file_listing += "</ul>"
            file_error_message = f"The following source file(s) were not uploaded: {file_listing}"
            flash(file_error_message)
            return redirect(request.referrer)
        if mapping_error:
            # output any error messages generated by the mapping engine
            flash(mapping_error)
            return redirect(request.referrer)
        print(f"Count: {session.get('count')}")
        return render_template("results.html",
                               rdf_generated=rdf_generated)


def compare_mapping_sources(mapping_filename, uploaded_sources):
    # compares each mapping source to uploaded source files
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], mapping_filename)
    file_error_message = []
    try:
        mapping_graph = rdflib.Graph().parse(file_path, format="ttl")
        query = """
        PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
        SELECT DISTINCT ?sourceName
        WHERE { 
            ?subject rml:source ?sourceName . 
            FILTER(isLiteral(?sourceName)) 
        }
        """
        query_results = mapping_graph.query(query)
        source_names = []
        # store source names retrieved from SPARQL query
        for row in query_results:
            current_source = str(row.get("sourceName"))
            source_names.append(current_source)
        # compare sources from query result to uploaded files
        for source in source_names:
            if source not in uploaded_sources:
                file_error_message.append(source)
        return file_error_message
    except Exception as e:
        return file_error_message


def load_rdflib_graph(rdf_string, raw_rdf_data=False, file_format="ttl"):
    try:
        if raw_rdf_data:
            graph = rdflib.Graph().parse(data=rdf_string, format=file_format)
        else:
            graph = rdflib.Graph().parse(source=rdf_string, format=file_format)
        return graph
    except Exception as e:
        print(f"Exception loading graph: {e}")
        return None


@app.route('/execute-shacl-shape', methods=["GET", "POST"])
def execute_shacl_shape():
    if request.method == "POST":
        form_data = request.form
        print(form_data)
        shacl_graph, data_graph, file_format = None, None, "ttl"
        data_graph_text = form_data.get("data-graph-text")
        shacl_graph_text = form_data.get("shacl-graph-text")
        if data_graph_text:
            data_graph = load_rdflib_graph(data_graph_text, raw_rdf_data=True)
            if not data_graph:
                return {"error_message": "Data Graph could not be parsed!"}
        if shacl_graph_text:
            shacl_graph = load_rdflib_graph(shacl_graph_text, raw_rdf_data=True)
            if not shacl_graph:
                return {"error_message": "SHACL Graph could not be parsed!"}

        data_graph_file = request.files.get('data-graph-file')
        if data_graph_file != "undefined":
            print(data_graph_file)
            # if data_graph_file.filename not in [".xml", ".ttl", ".json"]:
            #     return {"error_message": "Data Graph File must be Turtle (.ttl)"}
            # if ".owl" in data_graph_file.filename or ".xml" in data_graph_file.filename:
            #     file_format = "xml"
            file_format = rdflib.util.guess_format(data_graph_file.filename)
            data_graph = load_rdflib_graph(data_graph_file.read().decode("utf-8"), raw_rdf_data=True, file_format=file_format)
            if not data_graph:
                return {"error_message": "Data Graph could not be parsed!"}
        shacl_graph_file = request.files.get('shacl-graph-file')
        if shacl_graph_file:
            if not shacl_graph_file.filename.endswith(".ttl"):
                return {"error_message": "SHACL Graph File must be Turtle (.ttl)"}
            shacl_graph = load_rdflib_graph(shacl_graph_file.read().decode("utf-8"), raw_rdf_data=True)
            if not data_graph:
                return {"error_message": "SHACL Graph could not be parsed!"}
        # exit()

        data_graph_uri = form_data.get("data-graph-uri")
        shacl_graph_uri = form_data.get("shacl-graph-uri")
        if data_graph_uri:
            data_graph = load_rdflib_graph(data_graph_uri)
            if not data_graph:
                return {"error_message": "Data Graph could not be parsed!"}
        if shacl_graph_uri:
            shacl_graph = load_rdflib_graph(shacl_graph_uri)
            if not shacl_graph:
                return {"error_message": "SHACL Graph could not be parsed!"}



        print(data_graph.serialize(format="ttl"))

        if shacl_graph and data_graph:
            shacl_results = pyshacl.validate(data_graph, shacl_graph=shacl_graph)
            conforms, results_graph, results_text = shacl_results
            results_graph = results_graph.serialize(format="ttl")
            results = {
                "conforms": conforms,
                "results_text": results_text,
                "results_graph": results_graph,
            }
            return results
        return "whshs"

# run the uploaded mapping
def execute_mapping(mapping_filename):
    # create the config string and execute the morph kgc engine and save output
    config = f"""
                [DataSource1]
                mappings: {mapping_filename}
             """
    output_file = "output.ttl"
    # change working directory to allow engine to access uploads
    if not os.getcwd().endswith("uploads"):
        os.chdir("uploads")
    results = {}
    # try/catch the execution of the mapping
    try:
        g = morph_kgc.materialize(config)
        session["count"] += 1
        with open(output_file, "w") as f:
            g.serialize(format="turtle", file=f)
            results["rdf_data"] = g.serialize(format="turtle").strip()
    except Exception as e:
        results["error_message"] = str(e)
        print(e)
        # exit()
    if os.getcwd().endswith("uploads"):
        os.chdir("..")
    return results


@app.errorhandler(Exception)
def error(exception):
    print(exception)
    return render_template("error.html")


if __name__ == '__main__':
    # start the web application
    app.run(debug=True, host="127.0.0.1", port=5000, threaded=True)
