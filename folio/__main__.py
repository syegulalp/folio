# cover img: https://unsplash.com/photos/Y7d265_7i08

import sys, os

sys.path.insert(0, "folio")

import regex as re

import bottle
bottle.TEMPLATE_PATH.insert(0, "folio/templates")
bottle.re = re

import peewee
peewee.re = re

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

import config # type: ignore

debug = getattr(config, "DEBUG", False) or args.debug
launch_browser = getattr(config, "LAUNCH_BROWSER", None) or args.browser
config.DATA_PATH = config_path

port = getattr(config, "PORT", 6171)

bottle.DEBUG = debug


if __name__ == "__main__":

    if INIT:
        import models

        models.create_db()

    import routes

    img_paths = getattr(config, "IMG_PATHS", None)
    if img_paths:

        from bottle import static_file, route

        for alias, img_path in img_paths:

            @route(f"{routes.Wiki.PATH}/media/{alias}/<file_name>",)
            def media_files(wiki_title, file_name):
                return static_file(routes.Wiki.url_to_file(file_name), root=img_path)

    import settings

    if launch_browser:
        import webbrowser

        webbrowser.open(f"http://localhost:{port}")
    print(
        f'{settings.PRODUCT} running on port {port}\nNavigate to "/quit" in browser to shut down'
    )
    
    from wsgiref.simple_server import make_server, WSGIServer
    from socketserver import ThreadingMixIn

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): 
        pass

    import utils    

    with make_server('0.0.0.0', port, routes.app, ThreadingWSGIServer) as httpd:
        utils.server = httpd
        httpd.serve_forever()
