"""
WSGI config for centroestetico project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

#import os

#from django.core.wsgi import get_wsgi_application

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'centroestetico.settings')

#application = get_wsgi_application()

import os
import sys

path = '/home/gerart674/aplicacioncitaspladsh'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'centroestetico.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()