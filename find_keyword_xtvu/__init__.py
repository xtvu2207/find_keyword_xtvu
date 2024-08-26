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
            
            user_input = input("Do you want to update the library? Type 1 for Yes and 0 for No: ")
            if user_input == '1':
                print(f"Uninstalling the old version of {library_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", library_name, "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"Installing the new version of {library_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", library_name + "==" + latest_version], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            else:
                print(f"No update will be performed for {library_name}. Current version is {installed_version}.")

    except requests.RequestException:
        print("Failed to fetch library details from PyPI.")
    except subprocess.CalledProcessError as e:
        print("Failed to install or uninstall the library. Please check the permissions and the library name.")

library_name = 'find_keyword_xtvu'
check_and_update_library(library_name)
