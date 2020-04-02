# cover img: https://unsplash.com/photos/Y7d265_7i08

import sys, os

sys.path.insert(0, "src")

config_path = "data"

INIT = False

import argparse

parser = argparse.ArgumentParser(description="Launch wiki.")
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="Debug mode. Supersedes existing settings in config file.",
)

parser.add_argument(
    "-b",
    "--browser",
    action="store_true",
    default=True,
    help="Launch browser and open wiki at startup.",
)

parser.add_argument(
    "-bn",
    "--nobrowser",
    action="store_false",
    dest="browser",
    help="Don't launch browser at startup.",
)


parser.add_argument(
    "-p",
    "--path",
    dest="config_path",
    action="store",
    default=config_path,
    nargs="?",
    help=f"Set configuration path (default is {config_path}'). If not found, it will be created and populated with a default config file.",
)

args = parser.parse_args()
config_path = args.config_path or config_path

if not os.path.exists(config_path):
    INIT = True
    os.mkdir(config_path)
    with open(os.path.join(config_path, "config.py"), "w") as f:
        f.write(f"LAUNCH_BROWSER=True\nDEBUG=False")

sys.path.insert(0, config_path)

import config

debug = getattr(config, "DEBUG", None) or args.debug
launch_browser = getattr(config, "LAUNCH_BROWSER", None) or args.browser
config.DATA_PATH = config_path

port = getattr(config, "PORT", 6171)

import pixie_web

pixie_web.DEBUG = debug
pixie_web.TEMPLATE_PATH = "folio/templates"

if __name__ == "__main__":

    if INIT:
        import models

        models.create_db()

    import routes

    if launch_browser:
        import webbrowser

        webbrowser.open(f"http://localhost:{port}")

    routes.run(host="0.0.0.0", port=port, workers=None)
