#!/bin/bash
pyinstaller --collect-submodules skimage --collect-submodules sklearn --add-data "./:arthropod_describer/" --add-data "tools/:tools" --add-data "resources:resources" --noconfirm app.py