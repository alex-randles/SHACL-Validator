# SHACL-Validator
An interface which allows SHACL constraints to be executed on associated data graphs and validation results output.

## Online Version 
An online version of the application is available at the following link: https://shacl-validator.adaptcentre.ie/

## Local Version
### Installation Guide
The following sections cover the installation and running of the application. The application requires `python 3.10` or greater to run.
### Downloading Source Code 
The following command can be used to download this repository: `git clone https://github.com/alex-randles/SHACL-Validator.git`

Alternatively, you can download a ZIP file containing the code here: (https://github.com/alex-randles/SHACL-Validator/archive/refs/heads/main.zip)
### Requirements 
The `requirements.txt` file contains the three packages which are required to run the application. 
* [Flask](https://pythonbasics.org/what-is-flask-python/): Responsible for hosting the web application. 
* [RDFLib](https://rdflib.readthedocs.io/en/stable/): Responsible for loading the generated RDF graph. 
* [pySHACL](https://pypi.org/project/pyshacl/): Responsible for executing the SHACL Constraints. 

The packages can be installed using the following command: `pip3 install -r requirements.txt` 
### Running the Application
The application can be started using the following command: `python3 main.py`

The interface of the application will run on localhost port 5000 by default [127.0.0.1:5000](http://127.0.0.1:5000).

The port can be configured on line 129 of `main.py` by changing the respective variable `app.run(debug=True, host="127.0.0.1", port=5000, threaded=True)`

### Sample Graphs 
Sample SHACL constraints and Data Graphs can be found in the [./sample-graphs](./sample-graphs) directory. 

Make sure to provide the links for **GitHub [Raw Content](https://docs.github.com/en/enterprise-cloud@latest/repositories/working-with-files/using-files/viewing-a-file)** when providing a file path for a graph.

### Video Demonstration
A video demonstration of the application can be found here: https://drive.google.com/file/d/1p-0GlLAd1tWJ3y8K4fLZ2VAIxGQltbpA
