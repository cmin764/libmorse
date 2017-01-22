@echo off


pip install -Ur requirements.txt

python setup.py install
python bin\morseus include etc res
