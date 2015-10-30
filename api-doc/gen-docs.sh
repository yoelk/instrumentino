#!/bin/bash

thisScriptName="gen-docs.sh"
thisProjectVersion="2"
thisReleaseVersion="1"

regenDocs=0

##########
# Initialization 
##########
# Handle paths. Auto-determine as much as possible
# http://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html
docHomeDir="${PWD%*/}" # docHomeDir = <project home>/api-docs
projectHomeDir="$(dirname $docHomeDir)"
projectName="${projectHomeDir##*/}"
docSourceDir="$docHomeDir/source" # Where all the Sphinx rst files are

# For now, only continue if this script is in the current dir (so auto determined patchs will be correct)
# TO DO: Get rid of this requirement?
count=`ls "$docHomeDir" | grep -c "$thisScriptName"`
if [ "$count" = 0 ]; then
  echo "Error: Execute the script only in the the <project>/api-docs directory. Exiting"
  exit
fi

# Handle args
if [ "$1" = "r" ]; then
  regenDocs=1
fi

##########
# Generate documentation
##########
if [ "$regenDocs" = "1" ]; then
  # Note: When this runs, if the project already has been generated it will not 
  # allow you to overwrite existing files. You cannot pass *all* parameters needed. 
  # Just accept all defaults to questions asked. 
  echo "##################################################"
  echo "#     DEBUG: Autodocumentation configuration     #"
  echo "##################################################"
  echo "Project Name: $projectName"
  echo "Project Version: $thisProjectVersion"
  echo "Project Release Version: $thisReleaseVersion"
  echo "Documentation Home Dir: $docHomeDir"
  
  #mkdir $docSourceDir

  sphinx-quickstart --project="$projectName" --author="The $projectName team" -v $thisProjectVersion --release $thisReleaseVersion --ext-autodoc --batchfile --makefile "$docSourceDir"
  
  exit
fi

cd "$docSourceDir"
make clean
sphinx-apidoc -F -o "$docSourceDir" "$projectHomeDir"
make html
cd "$docHomeDir"

echo "##################################################"
echo "#     DEBUG: Autodocumentation configuration     #"
echo "##################################################"
echo "Project Home Directory: $projectHomeDir"
echo "Project Name: $projectName"
echo "Project Version: $thisProjectVersion"
echo "Project Release Version: $thisReleaseVersion"
echo "Documentation Source Files Directory: $docSourceDir"
