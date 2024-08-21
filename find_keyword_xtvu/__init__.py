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
            print(f"A new version of {library_name} is available: {installed_version} -> {latest_version}")
            print(f"Updating {library_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", library_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            importlib.invalidate_caches()
            importlib.reload(pkg_resources)
            new_installed_version = pkg_resources.get_distribution(library_name).version
            if "ipykernel" in sys.modules or "IPython" in sys.modules:
                from IPython.display import display, HTML
                display(HTML(f"<div style='color: red; font-weight: bold;'>Update completed. Please restart the kernel to apply the new version of {library_name}.</div>"))
            else:
                print(f"Update completed. The current version of {library_name} is {new_installed_version}.")
                subprocess.check_call([sys.executable] + sys.argv)
                sys.exit(0)

    except requests.RequestException:
        pass

library_name = 'find_keyword_xtvu'
check_and_update_library(library_name)

from .core import find_keyword_xtvu

__all__ = ["find_keyword_xtvu"]
