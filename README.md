# README

## Usage of this template

Step 1: **ADD DATA FOLDER TO .GITIGNORE**

Intended uses for the data folders:

- source: this will hold the input data for models to be run. Using the `ndr_setup` (etc...)
  functions will populate this folder with the data for the InVEST models.
- intermediate: this should hold meaningful intermediate products from ongoing analyses. These
  should be things that it would be useful to share. 
- final: this should hold the final outputs from the analysis. These will be identified as the key
  results in the project planning.

Workspace vs intermediate:
Use the local workspace for anything you want, plan on copying shareable results to the intermediate
or final folders as appropriate, with appropriate metadata/documentation of their lineage. The
workspace should be considered disposable.

