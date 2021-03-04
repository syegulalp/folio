import sys

config_path = "data"
sys.path.insert(0, config_path)
sys.path.insert(0, "folio")
import config

config.DATA_PATH = config_path

from . import models
