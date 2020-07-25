from bottle import default_app
app = default_app()

from .main import *
from .wiki import *
from .article import *
from .media import *
