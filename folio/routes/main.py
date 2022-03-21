from bottle import (
    template,
    route,
    redirect,
    request,
)

from models import (
    Wiki,
    Author,
    Article,
    System,
    db,
)

from utils import Error, Message, quit_key

from .decorators import user_env, home_page_render


@route("/")
def main_route():
    if "s" in request.params:
        a = Article.select(Article.wiki).distinct().order_by(Article.last_edited.desc())
        wikis = [_.wiki for _ in a]
    else:
        wikis = Wiki.select().order_by(Wiki.title.asc())

    return home_page_render(wikis)


route("/wiki")(main_route)


@route("/wikititles/<title>")
@route("/wikititles/")
def get_titles(title=None):
    wikis = Wiki.select().order_by(Wiki.title.asc())
    if title:
        wikis = wikis.where(Wiki.title.contains(title))
    return template("includes/wiki_listing.tpl", wikis=wikis)


@route("/new")
@user_env
def new_wiki(user: Author):
    wiki = Wiki(title="", description="",)
    return template("wiki_new.tpl", wiki=wiki, user=user, page_title=f"Create new wiki")


@route("/new", method="POST")
@user_env
def new_wiki_save(user: Author):

    wiki_title = request.forms.wiki_title
    wiki_description = request.forms.wiki_description
    wiki = Wiki(title=wiki_title, description=wiki_description)

    error = None

    if wiki_title == "":
        error = "Wiki title cannot be blank."

    if wiki.has_name_collision():
        error = "Sorry, a wiki with this name already exists. Choose another name."

    if error:
        return template(
            "wiki_new.tpl",
            wiki=wiki,
            user=user,
            page_title=f"Create new wiki",
            messages=[Error(error)],
        )

    with db.atomic():
        new_wiki = Wiki.new_wiki(wiki_title, wiki_description, user, first_wiki=False)

    return redirect(new_wiki.link)


@route("/quit")
def quit(*a):

    warning = Message(
        "You are about to shut the wiki down.", yes=f"/quit/{quit_key()}", no="/"
    )
    return template("blank.tpl", wiki=System, messages=[warning], sidebar=False)


@route("/quit/<delete_key>")
def quit_confirm(delete_key: str):

    if delete_key != quit_key():
        return quit()

    yield "You may now close this browser."
    from models import db

    db.close()

    from utils import server

    server.shutdown()
