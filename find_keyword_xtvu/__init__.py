import subprocess
import sys
import pkg_resources
import requests
from packaging import version
import importlib

def check_and_update_library(library_name):
    try:
        installed_version = pkg_resources.get_distribution(library_name).version
        pypi_url = f"https://pypi.org/pypi/{library_name}/json"
        response = requests.get(pypi_url)
        response.raise_for_status()
        latest_version = response.json()['info']['version']

        if version.parse(installed_version) < version.parse(latest_version):
            print(f"Une nouvelle version de {library_name} est disponible : {installed_version} -> {latest_version}")
            print(f"Mise à jour de {library_name} en cours...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", library_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            importlib.invalidate_caches()
            importlib.reload(pkg_resources)
            new_installed_version = pkg_resources.get_distribution(library_name).version
            if "ipykernel" in sys.modules or "IPython" in sys.modules:
                from IPython.display import display, HTML
                display(HTML(f"<div style='color: red; font-weight: bold;'>Mise à jour terminée. Veuillez redémarrer le kernel pour appliquer la nouvelle version de {library_name}.</div>"))
            else:
                print(f"Mise à jour terminée. La version actuelle de {library_name} est {new_installed_version}.")
                subprocess.check_call([sys.executable] + sys.argv)
                sys.exit(0)

    except requests.RequestException:
        pass

library_name = 'find_keyword_xtvu'
check_and_update_library(library_name)

from .core import find_keyword_xtvu

__all__ = ["find_keyword_xtvu"]
