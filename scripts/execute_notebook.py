from pathlib import Path
import nbformat
from nbclient import NotebookClient
root=Path(__file__).resolve().parents[1]
p=root/"notebooks/01_implementacao_explicada.ipynb"
nb=nbformat.read(p,as_version=4)
NotebookClient(nb,timeout=180,kernel_name="python3",resources={"metadata":{"path":str(root)}}).execute()
nbformat.write(nb,p)
print("Notebook executado sem erros")
