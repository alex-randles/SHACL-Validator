from flask import Flask, render_template, request
import rdflib
import pyshacl

# definition of web application
app = Flask(__name__)
app.config['SECRET_KEY'] = "x633UE2xYRC"
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['FILE_COUNT'] = 0


# the main endpoint for the interface
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        # returns the initial view displayed
        return render_template(
            "index.html",
            open=open,
        )


def load_rdflib_graph(rdf_string, raw_rdf_data=False, file_format="ttl"):
    # load RDF string or file and capture errors
    try:
        print(f"File format: {file_format}")
        if raw_rdf_data:
            graph = rdflib.Graph().parse(data=rdf_string, format=file_format)
        else:
            graph = rdflib.Graph().parse(source=rdf_string, format=file_format)
        return graph
    except Exception as e:
        print(f"Exception loading graph: {e}")
        return str(e)


def get_graph_format(graph_text):
    # outputs the format of a graph based on common strings used
    file_formats = {
        "xml": ["</rdf:RDF>", "<?xml"],
        "json-ld": ["@id", "@type"],
    }
    for file_format, strings in file_formats.items():
        for value in strings:
            if value in graph_text:
                return file_format
    return "ttl"


@app.route('/execute-shacl-shape', methods=["GET", "POST"])
def execute_shacl_shape():
    if request.method == "POST":
        form_data = request.form
        print(form_data)
        shacl_graph, data_graph, file_format = None, None, "ttl"
        data_graph_text = form_data.get("data-graph-text")
        shacl_graph_text = form_data.get("shacl-graph-text")
        if data_graph_text:
            file_format = get_graph_format(data_graph_text)
            data_graph = load_rdflib_graph(data_graph_text, raw_rdf_data=True, file_format=file_format)
            if isinstance(data_graph, str):
                return {"error_message": data_graph, "error_banner": "Data Graph has Incorrect Syntax!"}
        if shacl_graph_text:
            file_format = get_graph_format(shacl_graph_text)
            shacl_graph = load_rdflib_graph(shacl_graph_text, raw_rdf_data=True, file_format=file_format)
            if isinstance(shacl_graph, str):
                return {"error_message": shacl_graph, "error_banner": "SHACL Graph has Incorrect Syntax!"}
        data_graph_file = request.files.get('data-graph-file')
        if data_graph_file != "undefined" and data_graph_file:
            # print(data_graph_file)
            # if not data_graph_file.filename.endswith((".xml", ".ttl", ".json")):
                # return {"error_message": "Data Graph File must be Turtle (.ttl)", "error_banner": "Incorrect File Type!"}
            # if ".owl" in data_graph_file.filename or ".xml" in data_graph_file.filename:
            #     file_format = "xml"
            file_format = rdflib.util.guess_format(data_graph_file.filename)
            data_graph = load_rdflib_graph(data_graph_file.read().decode("utf-8"), raw_rdf_data=True, file_format=file_format)
            if not data_graph:
                return {"error_message": "Data Graph could not be parsed!"}
        shacl_graph_file = request.files.get('shacl-graph-file')
        if shacl_graph_file != "undefined" and shacl_graph_file:
            # if not shacl_graph_file.filename.endswith(".ttl"):
            #     return {"error_message": "SHACL Graph File must be Turtle (.ttl)"}
            shacl_graph = load_rdflib_graph(shacl_graph_file.read().decode("utf-8"), raw_rdf_data=True)
            if isinstance(shacl_graph, str):
                return {"error_message": shacl_graph, "error_banner": "SHACL Graph has Incorrect Syntax!"}
        data_graph_uri = form_data.get("data-graph-uri")
        shacl_graph_uri = form_data.get("shacl-graph-uri")
        if data_graph_uri:
            file_format = rdflib.util.guess_format(data_graph_uri)
            data_graph = load_rdflib_graph(data_graph_uri, file_format=file_format)
            print(data_graph_uri)
            if not data_graph:
                if "HTTP Error 404" in data_graph:
                    error_banner = "File could not be retrieved!"
                else:
                    error_banner = "SHACL Graph has Incorrect Syntax!"
                return {"error_message": data_graph, "error_banner": error_banner}
        if shacl_graph_uri:
            file_format = rdflib.util.guess_format(shacl_graph_uri)
            shacl_graph = load_rdflib_graph(shacl_graph_uri, file_format=file_format)
            if isinstance(shacl_graph, str):
                if "HTTP Error 404" in shacl_graph:
                    error_banner = "File could not be retrieved!"
                else:
                    error_banner = "SHACL Graph has Incorrect Syntax!"
                return {"error_message": shacl_graph, "error_banner": error_banner}
        if shacl_graph and data_graph:
            print(f'Data graph loaded:\n {data_graph.serialize(format="ttl")}')
            print(f'SHACL graph loaded:\n {shacl_graph.serialize(format="ttl")}')
            shacl_results = pyshacl.validate(data_graph, shacl_graph=shacl_graph)
            conforms, results_graph, results_text = shacl_results
            results_graph = results_graph.serialize(format="ttl")
            results = {
                "conforms": conforms,
                "results_text": results_text,
                "results_graph": results_graph,
            }
            print(f'SHACL validation results: \n {results}')
            return results


@app.errorhandler(Exception)
def error(exception):
    print(exception)
    return render_template("error.html")


if __name__ == '__main__':
    # start the web application
    app.run(debug=True, host="127.0.0.1", port=5000, threaded=True)
