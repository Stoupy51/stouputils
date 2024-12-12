
import shutil
import os

source = os.path.dirname(os.path.realpath(__file__)).replace("\\","/") + "/src/stouputils"
destination = "C:/Users/Alexandre-PC/AppData/Local/Programs/Python/Python310/Lib/site-packages/stouputils"

shutil.rmtree(destination, ignore_errors=True)
shutil.copytree(source, destination)
os.system("clear")
print("\nCopied stouputils to local Python's site-packages\n")

