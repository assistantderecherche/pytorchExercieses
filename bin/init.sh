#!/bin/bash
#
# should be called as bin/init.sh
#

deactivate > /dev/null 2>&1

#
# venv will be named '.<the name you provide or nothing>venv'
#
if [[ $1 ]];
then
	venv_name=$1
else
	venv_name=""
fi

python3 -m venv ./.${venv_name}venv
source ./.${venv_name}venv/bin/activate
pip install -r requirements_${venv_name}.txt
pip install --upgrade pip
