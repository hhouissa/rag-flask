
---

## **📄 check_requirements.py**
```python
import sys
import importlib.metadata
import re

def get_package_name_from_requirement(req):
    """Extract package name from requirement string, handling version specifiers."""
    # Remove version specifiers (=, ==, >=, <=, >, <, ~=, !=)
    package_name = re.split(r'[<>=!~]', req)[0].strip()
    return package_name

def check_requirements(requirements_file):
    try:
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print("Installed packages from requirements.txt:")
        print("-" * 50)
        
        for req in requirements:
            try:
                package_name = get_package_name_from_requirement(req)
                if package_name:  # Skip empty lines
                    version = importlib.metadata.version(package_name)
                    print(f"{package_name}: {version}")
            except importlib.metadata.PackageNotFoundError:
                package_name = get_package_name_from_requirement(req)
                print(f"{package_name}: NOT INSTALLED")
            except Exception as e:
                package_name = get_package_name_from_requirement(req)
                print(f"{package_name}: ERROR - {str(e)}")
                
    except FileNotFoundError:
        print(f"Error: {requirements_file} not found")
    except Exception as e:
        print(f"Error reading requirements file: {str(e)}")

if __name__ == "__main__":
    requirements_file = "requirements.txt"
    if len(sys.argv) > 1:
        requirements_file = sys.argv[1]
    check_requirements(requirements_file)
