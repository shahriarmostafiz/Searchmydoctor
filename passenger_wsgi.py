import os
import sys

project_home = "/home/picosl/doctor_search"
sys.path.insert(0, project_home)
os.chdir(project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doctor_search.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()