import os
import json
from re import sub
import sys
from pathlib import Path
import subprocess

if __name__ == "__main__":
    if Path("./utils/configs/utils.json").exists:
        print("good")
    else:
        print("bad")
    with open("./utils/configs/utils.json") as f:
        config = json.load(f)
    
    file = Path(sys.argv[1])

    path = Path(__file__).parent / Path(config['binPath']) / file.name
    print(__file__)

    #args = ''
    #for arg in sys.argv[2:]:
    #    args += f'"{arg}" '

    args = [arg.replace('\\\\', '\\') for arg in sys.argv[2:]]
    print(f'Executing program {path} with arguments:\n{args}')
    print(sys.argv[0], sys.argv[1])
#    os.execv(path, sys.argv[1:])
    args = [path]
    for arg in sys.argv[2:]:
        args.append(arg)
    p = subprocess.run(args)
    print(p.returncode)
    print("DONE")

