#!/bin/bash
#
# should be called as bin/jup.sh <venv_name_prefix=...> or bin/jup.sh for "." default
# 	For example via make: make jupenv env_name=gpt4allread
# 	Or using the default venv: make: make jup
#
#
# kill previous versions of jupyter
# might be an overkill :)
#
pkill -f jupyter

if [[ $1 ]];
then
	venv_prefix=${1}
else
	venv_prefix=''
fi

venv_name=.${venv_prefix}venv

echo "===> activating "$venv_name
source ./${venv_name}/bin/activate

rm nohup.out > /dev/null 2>&1
nohup jupyter notebook &
sleep 3
grep Serving nohup.out | sed 's/.*Serving/\t ... Serving/1'
grep http nohup.out | grep token | grep -v App | tail -1 | sed 's/^ */\t ... /g'
