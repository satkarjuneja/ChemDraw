import sys
import os
import json
import subprocess
import re


FORMULA=sys.argv[1]
PNG_PATH=sys.argv[2]
PDB_PATH=sys.argv[3]

pattern=r'[NO]'

if re.search(pattern,FORMULA):
    print("Contains N or O")
    subprocess.run([sys.executable,"Matrix_Generation.py",FORMULA])
else:
    subprocess.run([sys.executable,"Graph_Theory_Approach.py",FORMULA])
    print(PDB_PATH)
subprocess.run(["python", "Depicter.py",PNG_PATH])
subprocess.run(["python","3D_Depicter.py",PDB_PATH])
subprocess.run(["python","templates/PDB_Splitter.py",PDB_PATH])