#!/bin/bash
set -e

if [ "$1" == "jetson" ]; then
    cp .devcontainer/devcontainer-jetson.json .devcontainer/devcontainer.json
    echo "Switched to Jetson GPU devcontainer."
elif [ "$1" == "cpu" ]; then
    git checkout -- .devcontainer/devcontainer.json
    echo "Switched to universal CPU devcontainer."
else
    echo "Usage: $0 [jetson|cpu]"
fi