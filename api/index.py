import os
import sys

# Add project root directory to sys.path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atm_system.settings')

from atm_system.wsgi import application

app = application
