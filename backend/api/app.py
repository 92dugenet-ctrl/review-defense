"""Compatibility import for the canonical production WSGI application.

The application used to expose a second, legacy HTTP contract here. Keeping
this module as a thin alias avoids breaking imports while ensuring every HTTP
request follows the same production routing boundary in wsgi.py.
"""

from wsgi import app as application

app = application
