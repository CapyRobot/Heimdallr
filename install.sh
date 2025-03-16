#! /bin/bash

# cd to script directory
cd "$(dirname "$0")"

# create venv if does not exist
if [ ! -d "myenv" ]; then
    python3 -m venv myenv
fi

# setup venv
source myenv/bin/activate
pip install -r requirements.txt
deactivate

# add script to path - override if exists
if [ -f /usr/local/bin/heim ]; then
    sudo rm /usr/local/bin/heim
fi
sudo ln -s $(pwd)/run.sh /usr/local/bin/heim

# add session.sh to path
if [ -f /usr/local/bin/heim_session ]; then
    sudo rm /usr/local/bin/heim_session
fi
sudo ln -s $(pwd)/session.sh /usr/local/bin/heim_session
