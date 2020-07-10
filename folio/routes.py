from bottle import (
    template,
    route,
    default_app,
    static_file,
    response,
    redirect,
    error,
    request,
    HTTPError,
)

app = default_app()

from models import (
    Article,
    ArticleIndex,
    Wiki,
    Author,
    Tag,
    TagAssociation,
    Media,
    Metadata,
    ARTICLE_TIME_FORMAT,
    re,
    db,
)

from __main__ import config
from utils import Message, Error, Unsafe

from peewee import fn, SQL

from pathlib import Path
from typing import Any, Union
from email import utils as email_utils
from urllib.parse import urlencode
from math import ceil

import urllib
import datetime
import os
import time


default_headers = {
    "Expires": "-1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache, no-store, must-revalidate",
}

blank_wiki = Wiki()


class LocalException(Exception):
    pass


######################################################################
# Decorators
######################################################################


def get_user()->Author:
    return Author.get(Author.name == "Admin")


def get_wiki(wiki_title) -> Wiki:
    while Wiki.export_mode:
        time.sleep(0.1)
    try:
        wiki = Wiki.get(Wiki.title == Wiki.url_to_title(wiki_title))
    except Wiki.DoesNotExist as e:
        raise e

    if wiki.sidebar_cache is None:
        Wiki._sidebar_cache[wiki.id] = template("includes/sidebar.tpl", wiki=wiki)
    return wiki


def user_env(func):
    def wrapper(*a, **ka):
        user = get_user()
        return func(user, *a, **ka)

    return wrapper


def wiki_env(func):
    def wrapper(wiki_title: str, *a, **ka):
        user = get_user()
        try:
            wiki = get_wiki(wiki_title)
        except Wiki.DoesNotExist:
            return home_page_render([Error(f'Wiki "{Unsafe(wiki_title)}" not found')])
        return func(wiki, user, *a, **ka)

    return wrapper


def media_env(func):
    def wrapper(wiki_title: str, media_filename: str, *a, **ka):
        user = get_user()
        wiki = get_wiki(wiki_title)
        try:
            media = wiki.media.where(
                Media.file_path == Wiki.url_to_file(media_filename)
            ).get()
        except Media.DoesNotExist:
            media, pagination = paginator(wiki.media_alpha)
            return template(
                "wiki_media.tpl",
                wiki=wiki,
                media=media,
                messages=[Error(f'Media "{Unsafe(media_filename)}" not found')],
                paginator=pagination,
            )
        return func(wiki, user, media, *a, **ka)

    return wrapper


def article_env(func):
    def wrapper(wiki_title: str, article_title: str, *a, **ka):
        user = get_user()
        wiki = get_wiki(wiki_title)

        # NOTE: there may be circumstances where we want to return a blank article, but there may be others when we want to fail, so we may want to push that off to the wrapped function

        try:
            article = wiki.articles.where(
                Article.title == Article.url_to_title(article_title),
                Article.revision_of.is_null(),
            ).get()
        except Article.DoesNotExist:
            article = Article(
                wiki=wiki, title=Article.url_to_title(article_title), author=user
            )
        return func(wiki, user, article, *a, **ka)

    wrapper.__wrapped__ = func
    return wrapper


######################################################################
# Top-level paths
######################################################################


@error(404)
def error_404(error):
    return home_page_render([Error(f"Page or wiki not found: {Unsafe(request.path)}")])


def home_page_render(messages=[]):

    return template(
        "home.tpl",
        wikis=Wiki.select().order_by(Wiki.title.asc()),
        articles=(
            Article.select()
            .where(Article.draft_of.is_null(), Article.revision_of.is_null(),)
            .order_by(Article.last_edited.desc())
            .limit(25)
        ),
        page_title="Folio (Homepage)",
        messages=messages,
        wiki=blank_wiki,
    )


@route("/")
def main_route():
    return home_page_render()


route("/wiki")(main_route)


@route("/new")
@user_env
def new_wiki(user: Author):
    wiki = Wiki(title="", description="",)
    return template("wiki_new.tpl", wiki=wiki, user=user, page_title=f"Create new wiki")


@route("/new", method="POST")
@user_env
def new_wiki_save(user: Author):

    wiki_title = request.forms.get("wiki_title", "")
    wiki_description = request.forms.get("wiki_description", "")
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


# ######################################################################
# # Wiki paths
# ######################################################################


@route(f"{Wiki.PATH}")
@wiki_env
def wiki_home(wiki: Wiki, user: Author):
    return article_display.__wrapped__(wiki, user, wiki.main_article)


@route(f"{Wiki.PATH}/export")
@wiki_env
def wiki_export(wiki: Wiki, user: Author):

    import os, glob, shutil

    export_path = Path(config.DATA_PATH, "export", wiki.title_to_url(wiki.title))
    if not export_path.exists():
        os.makedirs(export_path)

    article_path = Path(export_path, "article")
    if not article_path.exists():
        article_path.mkdir()

    static_path = Path(export_path, "static")
    if not static_path.exists():
        static_path.mkdir()

    media_path = Path(export_path, "media")
    if not media_path.exists():
        media_path.mkdir()

    for f in glob.glob(f"{os.getcwd()}\\folio\\static\\*.*"):
        shutil.copy(f, static_path)

    for m in wiki.media:
        shutil.copy(m.file_path_, media_path)

    # TODO: make a context mgr
    Wiki.export_mode = True

    wiki.invalidate_cache()

    for article in wiki.articles_nondraft_only:
        article_text = article_display.__wrapped__(wiki, user, article)
        article_text = article_text.body

        with open(
            Path(article_path, wiki.title_to_url(article.title) + ".html"),
            "w",
            encoding="utf-8",
        ) as export_file:
            export_file.write(article_text)

    wiki.invalidate_cache()

    Wiki.export_mode = False

    with open(Path(article_path, ".htaccess"), "w") as htf:
        htf.write("DirectoryIndex Contents.html")

    redirect = """
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="refresh" content="0; url='article'" />
  </head>
  <body>
    <p>Please follow <a href="article">this link</a>.</p>
  </body>
</html>"""

    with open(Path(export_path, "index.html"), "w") as rdf:
        rdf.write(redirect)

    return "ok"


@route(f"{Wiki.PATH}/edit", method=("GET", "POST"))
@wiki_env
def wiki_settings_edit(wiki: Wiki, user: Author):
    action = None
    error = None
    original_wiki = wiki

    if request.method == "POST":

        wiki_new_title = request.forms.get("wiki_title", "")
        wiki_new_description = request.forms.get("wiki_description", "")

        if wiki_new_title == "":
            error = Error("Wiki title cannot be blank.")

        if wiki_new_title != wiki.title:
            wiki.title = wiki_new_title
            if wiki.has_name_collision():
                error = Error(
                    f'Sorry, a wiki with the name "{Unsafe(wiki_new_title)}" already exists. Choose another name.'
                )

        if wiki_new_description != wiki.description:
            wiki.description = wiki_new_description

        action = request.forms.get("save", None)

        if error is None:
            wiki.save()
            wiki.invalidate_cache()
            if action == "quit":
                return redirect(wiki.link)
            if action == "save":
                return redirect(wiki.edit_link)
        else:
            original_wiki = Wiki.get(Wiki.id == wiki.id)

    return template(
        "wiki_edit.tpl",
        wiki=wiki,
        user=user,
        page_title=f"Edit wiki settings ({wiki.title})",
        messages=[error] if error else None,
        original_wiki=original_wiki,
    )


@route(f"{Wiki.PATH}/clone")
@wiki_env
def clone_wiki(wiki: Wiki, user: Author):

    return template(
        "wiki_clone.tpl",
        wiki=wiki,
        user=user,
        page_title=f"Create new wiki from existing wiki",
    )


@route(f"{Wiki.PATH}/clone", method="POST")
@wiki_env
def clone_wiki_confirm(wiki: Wiki, user: Author):

    new_wiki = Wiki.new_wiki(
        f"New wiki created from {wiki.title}", "", user, empty=True
    )

    # TODO: move to models

    for article in wiki.template:
        if article.has_tag("@asis") or article.has_tag("@form"):
            # copy article text
            article_content = article.content
        else:
            # copy only autogen metadata
            article_content = []
            matches = article.metadata_all_re.finditer(article.content)
            for match in matches:
                article_content.append(match[0])
            article_content = "\n".join(article_content)

        new_article = Article(
            wiki=new_wiki, author=user, title=article.title, content=article_content
        )
        new_article.save()

        # FIXME: I thought article.tags gave us tags, not associations

        for tag in article.tags:
            new_article.add_tag(tag.tag.title)

        for metadata in article.metadata_not_autogen:
            new_article.set_metadata(metadata.key, metadata.value)

        new_article.update_index()
        new_article.update_links()
        new_article.update_autogen_metadata()

        if article.has_tag("@form"):
            make_auto = new_article.get_metadata("@make-auto")
            if make_auto:
                new_article.make_from_form(make_auto)

        default = new_article.get_metadata("@default")
        if default:
            new_article.content += default
            new_article.save()

    new_wiki.invalidate_cache()

    return redirect(new_wiki.edit_link)


@route(f"{Wiki.PATH}/delete")
@wiki_env
def wiki_delete(wiki: Wiki, user: Author):

    warning = f'Wiki "{Unsafe(wiki.title)}" is going to be deleted! Deleted wikis are GONE FOREVER.'

    return template(
        "article.tpl",
        articles=[wiki.main_article,],
        wiki=wiki,
        messages=[Message(warning, yes=wiki.delete_confirm_link, no=wiki.link,)],
    )


@route(f"{Wiki.PATH}/delete/<delete_key>")
@wiki_env
def wiki_delete_confirm(wiki: Wiki, user: Author, delete_key: str):
    wiki_title = wiki.title
    wiki.delete_()
    confirmation = f'Wiki "{Unsafe(wiki_title)}" has been deleted.'
    return home_page_render([Message(confirmation)])


@route(f"{Wiki.PATH}/new", method=("GET", "POST"))
@wiki_env
def article_new(wiki: Wiki, user: Author):

    messages = []
    wiki.invalidate_cache()

    if request.method == "POST":
        article_content = request.forms.get("article_content", None)
        article_title = request.forms.get("article_title", None)
        new_article = Article(
            title=article_title, content=article_content, author=user, wiki=wiki
        )
        if new_article.has_name_collision():
            messages.append(
                Error(
                    f'An article named "{Unsafe(article_title)}" already exists. Choose another name for this article.'
                )
            )
        else:
            new_article.save()
            return redirect(new_article.edit_link)

    else:
        counter = 0

        article_title = Wiki.url_to_title(request.params.get("title", ["Untitled"])[0])

        # TODO: move name making into model

        new_article = Article(title=article_title, content="", author=user, wiki=wiki)

        while True:

            if new_article.has_name_collision():
                counter += 1
                new_article.title = f"Untitled ({counter})"
                continue
            break

    return template(
        "article_edit.tpl",
        article=new_article,
        page_title=f"Creating: {new_article.title} ({wiki.title})",
        wiki=wiki,
        messages=messages,
        has_error="true" if messages else "false",
    )


@route(f"{Wiki.PATH}/replace", method=("GET", "POST"))
@wiki_env
def wiki_replace(wiki: Wiki, user: Author):

    search_query = ""
    replace_query = ""
    result_query = ""
    results = []
    messages = []
    search_results: Any = []
    article_count: int = 0

    if request.method == "POST":
        search_query = request.form.get("search_query", "")
        replace_query = request.form.get("replace_query", "")

        if search_query:

            search_results = (
                wiki.articles.select()
                .where(
                    Article.revision_of.is_null(),
                    Article.content.contains(search_query),
                )
                .order_by(SQL("title COLLATE NOCASE"))
            )
            results = search_results
            result_query = search_query
            article_count = search_results.count()

        if replace_query:

            messages = [
                Message(
                    f"Press [Replace all] to update {article_count} articles.<br>Note that there is no undo for this operation, but every changed article will have a revision saved."
                )
            ]

        if replace_query and request.form.get("replace", ""):

            for result in search_results:
                result.make_revision()
                result.content = result.content.replace(search_query, replace_query)
                result.last_edited = datetime.datetime.now()
                result.save()
                result.update_index()
                result.update_links()
                result.update_autogen_metadata()
            wiki.invalidate_cache()

            search_results = (
                wiki.articles.select()
                .where(
                    Article.revision_of.is_null(),
                    Article.content.contains(replace_query),
                )
                .order_by(SQL("title COLLATE NOCASE"))
            )
            results = search_results
            result_query = replace_query

            article_count = search_results.count()
            messages = [Message(f"{article_count} articles updated.", "success")]

    return template(
        "wiki_replace.tpl",
        search_query=search_query,
        replace_query=replace_query,
        page_title=f"Search ({wiki.title})",
        tags=wiki.tags,
        wiki=wiki,
        search_results=results,
        messages=messages,
        result_query=result_query,
    )


@route(f"{Wiki.PATH}/search", method=("GET", "POST"))
@wiki_env
def wiki_search(wiki: Wiki, user: Author):

    search_results = []
    search_query = ""

    if request.method == "POST":

        search_query = request.form.get("search_query", "")
        if search_query != "":
            search_query_wildcard = search_query

            article_title_result = (
                wiki.articles.select()
                .where(
                    Article.revision_of.is_null(),
                    Article.title.contains(search_query_wildcard),
                )
                .order_by(SQL("title COLLATE NOCASE"))
            )

            _article_contents_result = ArticleIndex.select(ArticleIndex.rowid).where(
                ArticleIndex.match(search_query_wildcard + "*")
            )

            article_contents_result = (
                wiki.articles.select()
                .where(
                    Article.revision_of.is_null(),
                    Article.id << _article_contents_result,
                )
                .order_by(SQL("title COLLATE NOCASE"))
            )

            tag_result = (
                wiki.tags.select()
                .where(Tag.title.contains(search_query_wildcard))
                .order_by(SQL("title COLLATE NOCASE"))
            )

            media_result = (
                wiki.media.select()
                .where(Media.file_path.contains(search_query_wildcard))
                .order_by(SQL("file_path COLLATE NOCASE"))
            )

            search_results.append(
                [
                    "Article titles",
                    r'<li><a href="{result.link}">{result.title}</a></li>',
                    article_title_result,
                ]
            )

            search_results.append(
                [
                    "Article contents",
                    r'<li><a href="{result.link}">{result.title}</a></li>',
                    article_contents_result,
                ]
            )

            search_results.append(
                [
                    "Tag titles",
                    r'<li><a href="{result.link}">{result.title}</a></li>',
                    tag_result,
                ]
            )

            search_results.append(
                [
                    "Media objects",
                    r'<li><a href="{result.edit_link}"><img class="img-fluid img-search-result" src="{result.link}"/> {result.file_path}</a></li>',
                    media_result,
                ]
            )

    return template(
        "wiki_search.tpl",
        search_query=search_query,
        page_title=f"Search ({wiki.title})",
        tags=wiki.tags,
        wiki=wiki,
        search_results=search_results,
    )


@route(f"{Wiki.PATH}/tags")
@wiki_env
def tags_all(wiki: Wiki, user: Author):

    return template("wiki_tags.tpl", tags=wiki.tags_alpha, wiki=wiki)


@route(f"{Wiki.PATH}/upload", method="POST")
@wiki_env
def upload_to_wiki(wiki: Wiki, user: Author):

    f = request.files["file"]

    rename = 1
    dest_file_name = f.filename
    while True:
        file_path = Path(wiki.data_path, dest_file_name)
        if file_path.exists():
            fn = f.filename.rsplit(".", 1)
            dest_file_name = f"{fn[0]}_{rename}.{fn[1]}"
            rename += 1
        else:
            break

    f.save(str(file_path))
    
    new_img = Media(wiki=wiki, file_path=dest_file_name)
    new_img.save()

    return f"{new_img.link}\n{new_img.edit_link}\n{new_img.file_path}"


@route(f"{Wiki.PATH}/tag/<tag_name>")
@wiki_env
def tag_pages(wiki: Wiki, user: Author, tag_name: str):
    tag_name = Wiki.url_to_title(tag_name)
    try:
        tag = wiki.tags.where(Tag.title == tag_name).get()
        tagged_articles = (
            wiki.articles_tagged_with(tag_name)
            .where(Article.revision_of.is_null())
            .order_by(SQL("title COLLATE NOCASE"))
        )
    except Tag.DoesNotExist:
        tag = Tag(title=tag_name, wiki=wiki)
        tag.id = 0
        tagged_articles = []

    try:
        article_with_tag_name = wiki.articles.where(Article.title == tag_name).get()
    except Article.DoesNotExist:
        article_with_tag_name = None

    return template(
        "wiki_pages.tpl",
        tag=tag,
        articles=tagged_articles,
        article_with_tag_name=article_with_tag_name,
        wiki=wiki,
        page_title=f"Tag: {tag_name} ({wiki.title})",
    )


# ######################################################################
# # Article paths
# ######################################################################


@route(f"{Wiki.PATH}/article")
@wiki_env
def articles(wiki: Wiki, user: Author):
    return wiki_home(wiki, user)


@route(f"{Wiki.PATH}{Article.PATH}")
@article_env
def article_display(wiki: Wiki, user: Author, article: Article):
    try:
        return Wiki.article_cache[article.id]
    except KeyError:
        pass

    redirect_article = article.get_metadata("@redirect")
    if redirect_article:
        try:
            article = Article.get(
                Article.title == redirect_article, Article.wiki == wiki
            )
        except Article.DoesNotExist:
            pass
        else:
            return redirect(article.link)

    if article.id is None:
        try:
            # TODO: replace with common search object
            # articles_tagged_with
            # article searches need to be composable entities
            # something for a later revision

            form_tag = Tag.select(Tag.id).where(Tag.wiki == wiki, Tag.title == "@form")

            tagged_as_form = TagAssociation.select(TagAssociation.article).where(
                TagAssociation.tag << form_tag
            )

            forms = wiki.articles_alpha.select().where(
                Article.id << tagged_as_form,
                Article.draft_of.is_null(),
                Article.revision_of.is_null(),
            )

        except (
            Tag.DoesNotExist,
            TagAssociation.DoesNotExist,
            Article.DoesNotExist,
        ) as e:
            forms_txt_list = ""
        else:
            if forms.count():
                form_list = [
                    "<p>You can also create this article using a form article:</p><hr/><ul>"
                ]
                for form in forms:
                    form_list.append(
                        f'<li><a href="{article.form_creation_link(form)}/{article.title}">{form.title}</a></li>'
                    )
                form_list.append("</ul>")
                forms_txt_list = "".join(form_list)
            else:
                forms_txt_list = ""

        article.content = f'This article does not exist. Click the <a class="autogenerate" href="{article.edit_link}">edit link</a> to create this article.{forms_txt_list}'

    result = template(
        "article.tpl",
        articles=[article],
        page_title=f"{article.title} ({wiki.title})",
        wiki=wiki,
    )

    if article.id:
        Wiki.article_cache[article.id] = result

    return result


def new_article_from_form_core(wiki: Wiki, user: Author, form: str, title: str):
    form_article = wiki.articles.where(Article.title == wiki.url_to_title(form)).get()

    new_article = form_article.make_from_form(wiki.url_to_title(title))
    return redirect(new_article.edit_link)


@route(f"{Wiki.PATH}/new_from_form/<form>")
@wiki_env
def article_new_from_form(wiki: Wiki, user: Author, form: str):
    return new_article_from_form_core(wiki, user, form, "Untitled")


@route(f"{Wiki.PATH}/new_from_form/<form>/<title>")
@wiki_env
def article_new_from_form_with_title(wiki: Wiki, user: Author, form: str, title: str):
    return new_article_from_form_core(wiki, user, form, title)


@route(f"{Wiki.PATH}{Article.PATH}/revision/<revision_id>")
@article_env
def article_revision(wiki: Wiki, user: Author, article: Article, revision_id: str):

    try:
        revision = article.revisions.where(Article.id == int(revision_id)).get()
    except Exception:
        return wiki_home(wiki, user)

    return template(
        "article.tpl",
        articles=[revision],
        page_title=f"{revision.title} ({wiki.title})",
        wiki=wiki,
    )


@route(f"{Wiki.PATH}{Article.PATH}/history")
@article_env
def article_history(wiki: Wiki, user: Author, article: Article):
    return template(
        "article_history.tpl",
        article=article,
        page_title=f"History: {article.title} ({wiki.title})",
        wiki=wiki,
    )


@route(f"{Wiki.PATH}{Article.PATH}/preview", method=("GET", "POST"))
@article_env
def article_preview(wiki: Wiki, user: Author, article: Article):

    if request.method == "POST":
        article = Article(
            title=request.forms.get("article_title", None),
            content=request.forms.get("article_content", None),
        )

    if article.id is None:
        article.content = f'This article does not exist. Click the <a class="autogenerate" href="{article.edit_link}">edit link</a> to create this article.'

    return template(
        "includes/article_core.tpl",
        article=article,
        page_title=article.title,
        wiki=wiki,
    )


@route(f"{Wiki.PATH}{Article.PATH}/save", method="POST")
def article_save_ajax(wiki_title: str, article_title: str):
    return article_edit(wiki_title, article_title, ajax=True)


@route(f"{Wiki.PATH}{Article.PATH}/edit", method=("GET", "POST"))
@article_env
def article_edit(wiki: Wiki, user: Author, article: Article, ajax=False):

    # Redirect to article creation if we try to edit a nonexistent article

    if article.id is None:
        return redirect(f"{wiki.link}/new/?title={Wiki.title_to_url(article.title)}")

    # Redirect to edit link if we visit the draft of the article

    if request.method == "GET":
        if article.draft_of:
            return redirect(article.draft_of.edit_link)

    error = None
    warning = None

    # Create draft if it doesn't exist

    if article.id is not None and not article.draft_of:
        if article.drafts.count():
            article = article.drafts.get()
        else:
            # TODO: check for name collisions
            draft = Article(
                wiki=article.wiki,
                title=f"Draft: {article.title}",
                content=article.content,
                author=article.author,
                created=article.created,
                draft_of=article,
            )
            draft.save()
            draft.update_links()
            draft.update_autogen_metadata()
            draft.copy_tags_from(article)
            draft.copy_metadata_from(article)
            article = draft
            wiki.invalidate_cache()

    original_article = article
    original_id = article.id

    # Check if article opened in edit mode without being formally closed out

    if request.method == "GET":

        if article.opened_by is None:
            article.opened_by = article.author
            article.last_edited = datetime.datetime.now()
            article.save()
        else:
            warning = Message(
                "This article was previously opened for editing without being saved. It may contain unsaved changes elsewhere. Use 'Save and Exit' or 'Quit Editing' to remove this message."
            )

    if request.method == "POST" or ajax is True:

        action = request.forms.get("save", None)

        if action == "quit":
            article.opened_by = None
            article.save()
            article.update_index()
            article.update_autogen_metadata()
            article.update_links()
            wiki.invalidate_cache()
            return redirect(article.link)

        elif action == "discard":
            wiki.invalidate_cache()
            return redirect(article.discard_draft_link)

        article_content = request.forms.get("article_content", None)
        article_title = request.forms.get("article_title", None)

        if article_content != article.content:
            article.content = article_content
            article.last_edited = datetime.datetime.now()

        renamed = False

        if article.new_title is None:
            if article_title != article.draft_of.title:
                article.new_title = article_title
                renamed = True
        else:
            if article_title != article.new_title:
                article.new_title = article_title
                renamed = True

        if renamed:
            if article.has_new_name_collision():
                error = Error(
                    f'An article named "{Unsafe(article_title)}" already exists. Choose another name for this article.'
                )

        if error is None:
            article.save()
            article.update_index()
            article.update_links()
            article.update_autogen_metadata()
            wiki.invalidate_cache()

            if action == "exit":
                article.opened_by = None
                article.save()
                return redirect(article.link)

            elif action in {"publish", "revise"}:
                new_article = article.draft_of

                if action == "revise":
                    new_article.make_revision()

                if article.new_title:
                    new_article.title = article.new_title
                    # Check for rename options here

                new_article.content = article.content
                new_article.last_edited = article.last_edited
                new_article.save()

                new_article.update_index()
                new_article.update_links()
                new_article.clear_metadata()
                new_article.update_autogen_metadata()
                new_article.copy_metadata_from(article)
                new_article.clear_tags()
                new_article.copy_tags_from(article)

                article.delete_()

                return redirect(new_article.link)

            elif action == "save":
                article.opened_by = None
                article.save()

                if article.draft_of:
                    return redirect(article.draft_of.edit_link)

                return redirect(article.link)
        else:
            original_article = Article.get(Article.id == article.id)

    if ajax:
        if error:
            return str(error)
        return str(Message("Article successfully saved.", color="success"))

    article.content = article.content.replace("&", "&amp;")

    return template(
        "article_edit.tpl",
        article=article,
        page_title=f"Editing: {article.title} ({wiki.title})",
        wiki=wiki,
        original_article=original_article,
        messages=[error, warning],
        has_error="true" if error else "false",
    )


@route(f"{Wiki.PATH}{Article.PATH}/delete")
@article_env
def article_delete(wiki: Wiki, user: Author, article: Article):

    warning = f'Article "{Unsafe(article.title)}" is going to be deleted! Deleted articles are GONE FOREVER.'

    if article.revision_of:
        warning += "<hr/>This is an earlier revision of an existing article. Deleting this will remove it from that article's revision history. This is allowed, but NOT RECOMMENDED."

    return template(
        "article.tpl",
        articles=[article],
        page_title=f"Delete: {article.title} ({wiki.title})",
        wiki=wiki,
        messages=[Message(warning, yes=article.delete_confirm_link, no=article.link,)],
    )


@route(f"{Wiki.PATH}{Article.PATH}/delete/<delete_key>")
@article_env
def article_delete_confirm(
    wiki: Wiki, user: Author, article: Article, delete_key: str, redirect_to=None,
):
    if article.id is None:
        return redirect(wiki.link)

    if article.delete_key != delete_key:
        return redirect(article.link)

    # TODO: this stuff should be in the delete_instance method

    if article.drafts.count():
        draft = article.drafts.get()
        draft.delete_()
    for revision in article.revisions.select():
        revision.delete_()
    article.delete_()

    # TODO: Move tag-clearing / orphan-check operations to override of delete_instance for article?

    wiki.invalidate_cache()

    if redirect_to is None:
        redirect_to = wiki.main_article

    return template(
        "article.tpl",
        wiki=wiki,
        articles=[redirect_to],
        messages=[Error(f'Article "{Unsafe(article.title)}" has been deleted.')],
    )


@route(f"{Wiki.PATH}{Article.PATH}/discard-draft")
@article_env
def draft_discard(wiki: Wiki, user: Author, article: Article):

    if article.id is None:
        return redirect(article.link)

    if article.draft_of is None:
        return redirect(article.link)

    warning = f'"{Unsafe(article.title)}" is going to be discarded.'

    if article.content != article.draft_of.content:

        warning += (
            "<br/>THIS DRAFT HAS MODIFICATIONS THAT WERE NOT SAVED TO THE ARTICLE."
        )

    return template(
        "article.tpl",
        articles=[article],
        page_title=f"Discard draft: {article.title} ({wiki.title})",
        wiki=wiki,
        messages=[
            Message(warning, yes=article.discard_draft_confirm_link, no=article.link,)
        ],
    )


@route(f"{Wiki.PATH}{Article.PATH}/discard-draft/<delete_key>")
@article_env
def draft_discard_confirm(
    wiki: Wiki, user: Author, article: Article, delete_key: str,
):
    return article_delete_confirm.__wrapped__(
        wiki, user, article, delete_key, redirect_to=article.draft_of
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image")
@article_env
def modal_insert_image(wiki: Wiki, user: Author, article: Article):

    return template(
        "includes/modal.tpl",
        title="Insert image into article",
        body=template(
            "modal_search.tpl",
            url=f"{article.link}/insert-image/",
            search_results=image_search(wiki, None),
        ),
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", method="POST")
@article_env
def modal_insert_image_search(wiki: Wiki, user: Author, article: Article):

    search = request.forms.get("search_query", None)
    return image_search(wiki, search)


def existing_tags(article):
    taglist = [""]
    for tag in article.tags_alpha:
        taglist.append(
            f'<a href="#" onclick="removeTag(this)"; title="Click to remove this tag from this article" class="badge badge-primary">{tag.title}</a> '
        )
    tags = "".join(taglist)
    return tags


def search_results(wiki, search):
    if search is None or search == "":
        search_results = (
            wiki.tags.select().order_by(SQL("title COLLATE NOCASE")).limit(100)
        )
    else:
        search_results = (
            wiki.tags.select()
            .where(Tag.title.contains(search))
            .order_by(SQL("title COLLATE NOCASE"))
            .limit(10)
        )
    results = ["<ul>"]
    for result in search_results:
        results.append(
            f'<li><a href="#" onclick="insertTag(this);">{result.title}</li>'
        )
    results.append("</ul>")
    return "".join(results)


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag")
@article_env
def modal_tags(wiki: Wiki, user: Author, article: Article):
    tags = existing_tags(article)
    body = template(
        "includes/modal_tag_search.tpl",
        url=f"{article.link}/insert-tag",
        search_results=search_results(wiki, None),
    )

    return template(
        "includes/modal.tpl",
        title="Edit article tags",
        body=f'Existing tags (click to remove):<br/><div id="modal-tag-listing">{tags}</div><hr/>{body}',
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag", method="POST")
@article_env
def modal_tags_search(wiki: Wiki, user: Author, article: Article):
    search = request.forms.get("search_query", None)
    return search_results(wiki, search)


@route(f"{Wiki.PATH}{Article.PATH}/add-tag", method="POST")
@article_env
def modal_add_tag(wiki: Wiki, user: Author, article: Article):
    tag = request.forms.get("tag", None)
    article.add_tag(tag)
    wiki.invalidate_cache()
    return existing_tags(article)


@route(f"{Wiki.PATH}{Article.PATH}/remove-tag", action="POST")
@article_env
def modal_remove_tag(wiki: Wiki, user: Author, article: Article):
    tag = request.forms.get("tag", None)
    article.remove_tag(tag)
    wiki.invalidate_cache()
    return existing_tags(article)


@route(f"{Wiki.PATH}{Article.PATH}/edit-metadata")
@article_env
def modal_edit_metadata(wiki: Wiki, user: Author, article: Article):
    return template(
        "includes/modal.tpl",
        title="Edit article metadata",
        body=template(
            "includes/modal_metadata.tpl",
            url=f"{article.link}/edit-metadata",
            article=article,
        ),
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/edit-metadata", method="POST")
@article_env
def modal_edit_metadata_post(wiki: Wiki, user: Author, article: Article):

    key = request.forms.get("key", None)
    if key:
        value = request.forms.get("value", None)
        article.set_metadata(key, value)

    delete = request.forms.get("delete", None)
    if delete:
        try:
            delete_instance = article.metadata.where(Metadata.id == delete).get()
            delete_instance.delete_instance()
        except Metadata.DoesNotExist:
            pass

    return template(
        "includes/modal_metadata.tpl",
        url=f"{article.link}/edit-metadata",
        article=article,
    )


def link_search(wiki, search):
    search_results = wiki.articles.select().where(
        Article.draft_of.is_null(), Article.revision_of.is_null()
    )

    if search:
        search_results = search_results.where(Article.title.contains(search))

    search_results = search_results.order_by(SQL("title COLLATE NOCASE")).limit(10)

    results = ['<ul class="list-unstyled">']
    for result in search_results:
        link = f'<li><a onclick="insertLinkFromList(this);" href="#">{result.title}</a></li>'
        results.append(link)

    return "".join(results)


@route(f"{Wiki.PATH}{Article.PATH}/insert-link")
@article_env
def modal_insert_link_search(wiki: Wiki, user: Author, article: Article):

    return template(
        "includes/modal.tpl",
        title="Insert link into article",
        body=template(
            "includes/modal_search.tpl",
            url=f"{article.link}/insert-link/",
            search_results=link_search(wiki, None),
            alt_input=("Text for link", "link_text"),
        ),
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-link", method="POST")
@article_env
def modal_insert_link_search_post(wiki: Wiki, user: Author, article: Article):

    search = request.forms.get("search_query", None)
    return link_search(wiki, search)


@route("/quit")
def quit(*a):
    yield "You may now close this browser."
    from models import db

    db.commit()
    db.close()

    import sys

    sys.stderr.close()


# ######################################################################
# # Media and static paths
# ######################################################################


@route("/static/<filename>")
def static_content(filename: str):
    return static_file(filename, "folio/static")


def paginator(media: Media):
    search = request.params.get("search", [None])[0]
    if search:
        media = media.where(Media.file_path.contains(search))
    else:
        search = ""

    page = int(request.params.get("p", [1])[0])

    last = ceil(media.count() / 5)

    if page == -1 or page > last:
        page = last

    previous_page = max(page - 1, 1)
    next_page = min(page + 1, last)

    media = media.paginate(page, 5)

    first_url = urlencode({"p": 1, "search": search})
    previous_url = urlencode({"p": previous_page, "search": search})
    next_url = urlencode({"p": next_page, "search": search})
    last_url = urlencode({"p": -1, "search": search})

    # TODO: replace with template

    pagination = f"""
    <div class="btn-group btn-group-sm" role="group">
    <a class="btn btn-info" role="button" href="?{first_url}">First</a>
    <a class="btn btn-info" role="button" href="?{previous_url}">Previous</a>
    <a class="btn btn-secondary" role="button" href="#">{page}/{last}</a>
    <a class="btn btn-info" role="button" href="?{next_url}">Next</a>
    <a <a class="btn btn-info" role="button" href="?{last_url}">Last</a>
    </div>
    """

    return media, pagination


@route(f"{Wiki.PATH}/media")
@wiki_env
def wiki_media(wiki: Wiki, user: Author):

    media, pagination = paginator(wiki.media_alpha)

    return template(
        "wiki_media.tpl",
        wiki=wiki,
        media=media,
        page_title=f"Media ({wiki.title})",
        paginator=pagination,
    )


@route(f"{Wiki.PATH}/media-paste", method="POST")
@wiki_env
def wiki_media_paste(wiki: Wiki, user: Author):

    paste_file = request.files.get("file")
    if not paste_file:
        return HTTPError(500)

    file_data = paste_file[1]
    file_id = 0

    while True:
        filename = f"{wiki.title}_{file_id}.png"
        if not Path(wiki.data_path, filename).exists():
            break
        file_id += 1

    with open(Path(wiki.data_path, filename), "wb") as f:
        f.write(file_data)

    new_image = Media(wiki=wiki, file_path=filename,)
    new_image.save()

    return f"{new_image.link}\n{new_image.edit_link}\n![]({new_image.file_path})"


@route(f"{Wiki.PATH}/media/<file_name>")
@wiki_env
def media_file(wiki: Wiki, user: Author, file_name: str):
    return static_file(Wiki.url_to_file(file_name), f"{config.DATA_PATH}/{wiki.id}",)


@route(f"{Wiki.PATH}/media/<media_filename>/edit")
@media_env
def media_file_edit(wiki: Wiki, user: Author, media: Media):

    return template(
        "wiki_media_edit.tpl",
        wiki=wiki,
        media=media,
        page_title=f"File {media.file_path} ({wiki.title})",
    )


@route(f"{Wiki.PATH}/media/<media_filename>/edit", method="POST")
@media_env
def media_file_edit_post(wiki: Wiki, user: Author, media: Media):

    note: Union[Error, Message, None] = None

    filename_body, filename_ext = media.file_path.rsplit(".", 1)
    new_filename_body = request.form.get("media-filename")

    if request.form.get("select", None):
        wiki.set_metadata("cover_img", media.id)
        wiki.invalidate_cache()

    elif request.form.get("save", None) and new_filename_body != filename_body:

        new_filename = new_filename_body + "." + filename_ext

        try:

            if Media.exists(new_filename, wiki):
                note = Error(
                    f'Filename "{Unsafe(new_filename)}" already exists. Use another filename.'
                )

                raise LocalException()

            # TODO: use transaction/rollback for one-pass rename

            for ref in media.in_articles:
                if ref.article.opened_by:
                    note = Error(
                        f'Media "{Unsafe(new_filename)}" is referenced in article "{Unsafe(ref.article.title)}", which is open for editing. Save the article before renaming the image.'
                    )
                    raise LocalException()

            old_filename = media.file_path

            new_path = Path(media.wiki.data_path, new_filename)
            Path(media.file_path_).rename(new_path)

            media.file_path = new_filename
            media.save()

            # TODO: don't replace if we don't pass the option

            replacement_src = re.compile(
                r"!\[([^\]]*?)\]\((" + re.escape(old_filename) + r")\)"
            )

            for ref in media.in_articles:
                ref.article.replace_text(
                    replacement_src, r"![\1](" + new_filename + r")",
                )

            wiki.invalidate_cache()

            note = Message(
                f'Filename "{Unsafe(old_filename)}" successfully renamed to "{Unsafe(new_filename)}".'
            )

        except LocalException:
            pass

    return template("wiki_media_edit.tpl", wiki=wiki, media=media, messages=[note])


@route(f"{Wiki.PATH}/media/<media_filename>/delete")
@media_env
def media_file_delete(wiki: Wiki, user: Author, media: Media):

    warning = f'Media "{Unsafe(media.file_path)}" is going to be deleted! Deleted media are GONE FOREVER.'

    cover_media_id = wiki.get_metadata("cover_img")

    if cover_media_id and int(cover_media_id) == media.id:

        warning += f"<hr>Also note: This media is in use as the cover image for this wiki. Deleting it will cause the cover image to revert to the default."

    if media.in_articles.count():
        warning += f"<hr>Also note: This media is in use in {media.in_articles.count()} articles. Deleting it will NOT remove references to the image from those articles, but will leave broken links."

    return template(
        "wiki_media_edit.tpl",
        wiki=wiki,
        media=media,
        messages=[Message(warning, yes=media.delete_confirm_link, no=media.edit_link,)],
    )


@route(f"{Wiki.PATH}/media/<media_filename>/delete/<delete_key>")
@media_env
def media_file_delete_confirm(wiki: Wiki, user: Author, media: Media, delete_key: str):

    cover_media_id = wiki.get_metadata("cover_img")
    if cover_media_id and int(cover_media_id) == media.id:
        wiki.delete_metadata("cover_img")

    media.delete_()

    wiki.invalidate_cache()

    media_list, pagination = paginator(wiki.media_alpha)

    return template(
        "blank.tpl",
        wiki=wiki,
        messages=[
            Error(
                f'<p>Media item "{Unsafe(media.file_path)}" has been deleted.</p><p><a href="{wiki.media_link}">Return to the media manager</a></p>'
            )
        ],
    )


# For now, a dummy response until we can come up with an actual favicon.


@route(f"/favicon.ico")
def favicon():
    return b""


def image_search(wiki, search):
    if search is None or search == "":
        search_results = (
            wiki.media.select().order_by(SQL("file_path COLLATE NOCASE")).limit(10)
        )
    else:
        search_results = (
            wiki.media.select()
            .where(
                (Media.file_path.contains(search))
                | (Media.description.contains(search))
            )
            .order_by(SQL("file_path COLLATE NOCASE"))
            .limit(10)
        )

    results = ['<ul class="list-unstyled">']
    for result in search_results:
        link = (
            f'<a href="#" data-url="{result.file_path}" onclick="insertImage(this);">'
        )
        results.append(
            f'<li class="media">{link}<img class="img-fluid align-self-start mr-3" src="{result.link}"></a><div class="media-body">{link}{result.file_path}</a></li>'
        )
    results.append("</ul>")

    return "".join(results)
