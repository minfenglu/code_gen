import truss
from pathlib import Path
import requests

tr = truss.load("./codellama-7b")
command = tr.docker_build_setup(build_dir=Path("./codellama2"))
print(command)