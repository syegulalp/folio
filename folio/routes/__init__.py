from bottle import default_app
app = default_app()

from .main import *
from .decorators import *
from .article import *
from .media import *
from .wiki import *