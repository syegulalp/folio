from pixie_web import (
    route,
    RouteType,
    Template,
    Request,
    Response,
    run,
    static_file,
    simple_response,
    Unsafe,
    redirect,
    server,
    WebException,
)
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
import asyncio
import urllib
import datetime
import os
import time

from email import utils as email_utils

from __main__ import config
from utils import Message, Error
from peewee import fn, SQL
from pathlib import Path
from typing import Union
from urllib.parse import urlencode

home_template = Template(file="home.html")
blank_template = Template(file="blank.html")
article_template = Template(file="article.html")
wiki_edit_template = Template(file="wiki_edit.html")
wiki_clone_template = Template(file="wiki_clone.html")
article_edit_template = Template(file="article_edit.html")
article_preview_template = Template(file="includes/article_core.html")
article_history_template = Template(file="article_history.html")
wiki_tags_template = Template(file="wiki_tags.html")
wiki_pages_template = Template(file="wiki_pages.html")
wiki_search_template = Template(file="wiki_search.html")
wiki_media_template = Template(file="wiki_media.html")
wiki_media_edit_template = Template(file="wiki_media_edit.html")
modal_template = Template(file="includes/modal.html")
modal_search_template = Template(file="includes/modal_search.html")
modal_metadata_template = Template(file="includes/modal_metadata.html")
sidebar_template = Template(file="includes/sidebar.html")

default_headers = {
    "Expires": "-1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache, no-store, must-revalidate",
}


class LocalException(Exception):
    pass


######################################################################
# Decorators
######################################################################


def get_user():
    return Author.get(Author.name == "Admin")


def transaction(func):
    def wrapper(*a, **ka):
        with db.atomic():
            result = func(*a, **ka)
        return result

    return wrapper


def get_wiki(wiki_title):
    try:
        wiki = Wiki.get(Wiki.title == Wiki.url_to_title(wiki_title))
    except Wiki.DoesNotExist:
        raise WebException(
            home_page_render([Error(f'Wiki "{Unsafe(wiki_title)}" not found')])
        )

    if wiki.sidebar_cache is None:
        Wiki._sidebar_cache[wiki.id] = sidebar_template.render(wiki=wiki)
    return wiki


def user_env(func):
    def wrapper(env: Request, *a, **ka):
        user = get_user()
        return func(env, user, *a, **ka)

    return wrapper


def wiki_env(func):
    def wrapper(env: Request, wiki_title: str, *a, **ka):
        user = get_user()
        wiki = get_wiki(wiki_title)
        return func(env, wiki, user, *a, **ka)

    return wrapper


def media_env(func):
    def wrapper(env: Request, wiki_title: str, media_filename: str, *a, **ka):
        user = get_user()
        wiki = get_wiki(wiki_title)
        try:
            media = wiki.media.where(
                Media.file_path == Wiki.url_to_file(media_filename)
            ).get()
        except Media.DoesNotExist:
            response = Response(
                wiki_media_template.render(
                    wiki=wiki,
                    media=wiki.media_alpha,
                    messages=[Error(f'Media "{Unsafe(media_filename)}" not found')],
                ),
                headers=default_headers,
            )
            raise WebException(response)
        return func(env, wiki, user, media, *a, **ka)

    return wrapper


def article_env(func):
    def wrapper(env: Request, wiki_title: str, article_title: str, *a, **ka):
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
        return func(env, wiki, user, article, *a, **ka)

    wrapper.__wrapped__ = func
    return wrapper


######################################################################
# Top-level paths
######################################################################


def error_404(env: Request):
    return home_page_render([Error(f'Page or wiki "{Unsafe(env.path)}" not found')])


server.error_404 = error_404  # type: ignore


@route("/", RouteType.asnc_local)
async def main_route(env: Request):
    return home_page_render()


route("/wiki", RouteType.asnc_local)(main_route)


@route("/new", RouteType.asnc_local)
async def new_wiki(env: Request):
    user = Author.get(Author.name == "Admin")
    wiki = Wiki(title="", description="",)
    return Response(
        wiki_edit_template.render(wiki=wiki, user=user, page_title=f"Create new wiki")
    )


@route("/new", RouteType.asnc_local, action="POST")
@transaction
async def new_wiki_save(env: Request):
    author = Author.get(Author.name == "Admin")

    wiki_title = env.form.get("wiki_title", "")
    wiki_description = env.form.get("wiki_description", "")
    wiki = Wiki(title=wiki_title, description=wiki_description)

    error = None

    if wiki_title == "":
        error = "Wiki title cannot be blank."

    if wiki.has_name_collision():
        error = "Sorry, a wiki with this name already exists. Choose another name."

    if error:
        return Response(
            wiki_edit_template.render(
                wiki=wiki,
                author=author,
                page_title=f"Create new wiki",
                messages=[Error(error)],
            )
        )

    wiki = Wiki.new_wiki(wiki_title, wiki_description, author, first_wiki=False)
    return redirect(wiki.link)


######################################################################
# Wiki paths
######################################################################


def home_page_render(messages=[]):
    return Response(
        home_template.render(
            wikis=Wiki.select().order_by(Wiki.title.asc()),
            articles=Article.select().order_by(Article.last_edited.desc()).limit(25),
            page_title="Folio (Homepage)",
            messages=messages,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}", RouteType.asnc_local)
@wiki_env
async def wiki_home(env: Request, wiki: Wiki, user: Author):
    return await article_display.__wrapped__(env, wiki, user, wiki.main_article)


@route(f"{Wiki.PATH}/edit", RouteType.asnc_local, action=("GET", "POST"))
@transaction
@wiki_env
async def wiki_settings_edit(env: Request, wiki: Wiki, user: Author):
    action = None
    error = None
    original_wiki = wiki

    if env.verb == "POST":

        wiki_new_title = env.form.get("wiki_title", "")
        wiki_new_description = env.form.get("wiki_description", "")

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

        action = env.form.get("save", None)

        if error is None:
            wiki.save()
            wiki.invalidate_cache()
            if action == "quit":
                return redirect(wiki.link)
            if action == "save":
                return redirect(wiki.edit_link)
        else:
            original_wiki = Wiki.get(Wiki.id == wiki.id)

    return Response(
        wiki_edit_template.render(
            wiki=wiki,
            user=user,
            page_title=f"Edit settings ({wiki.title})",
            messages=[error] if error else None,
            original_wiki=original_wiki,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/clone", RouteType.asnc_local)
@wiki_env
async def clone_wiki(env: Request, wiki: Wiki, user: Author):

    return Response(
        wiki_clone_template.render(
            wiki=wiki, user=user, page_title=f"Create new wiki from existing wiki"
        )
    )


@route(f"{Wiki.PATH}/clone", RouteType.asnc_local, action="POST")
@transaction
@wiki_env
async def clone_wiki_confirm(env: Request, wiki: Wiki, user: Author):

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


@route(f"{Wiki.PATH}/delete", RouteType.asnc_local)
@wiki_env
async def wiki_delete(env: Request, wiki: Wiki, user: Author):

    warning = f'Wiki "{Unsafe(wiki.title)}" is going to be deleted! Deleted wikis are GONE FOREVER.'

    return Response(
        article_template.render(
            articles=[wiki.main_article,],
            wiki=wiki,
            messages=[Message(warning, yes=wiki.delete_confirm_link, no=wiki.link,)],
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/delete/<delete_key>", RouteType.asnc_local)
@transaction
@wiki_env
async def wiki_delete_confirm(env: Request, wiki: Wiki, user: Author, delete_key: str):
    wiki_title = wiki.title
    wiki.delete_()
    confirmation = f'Wiki "{Unsafe(wiki_title)}" has been deleted.'
    return home_page_render([Message(confirmation)])


@route(f"{Wiki.PATH}/new", RouteType.asnc_local, action=("GET", "POST"))
@transaction
@wiki_env
async def article_new(env: Request, wiki: Wiki, user: Author):

    messages = []
    wiki.invalidate_cache()

    if env.verb == "POST":
        article_content = env.form.get("article_content", None)
        article_title = env.form.get("article_title", None)
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
        article_title = Wiki.url_to_title(env.params.get("title", "Untitled"))

        # TODO: move name making into model

        new_article = Article(title=article_title, content="", author=user, wiki=wiki)

        while True:

            if new_article.has_name_collision():
                counter += 1
                new_article.title = f"Untitled ({counter})"
                continue
            break

    return Response(
        article_edit_template.render(
            article=new_article,
            page_title=f"Creating: {new_article.title} ({wiki.title})",
            wiki=wiki,
            messages=messages,
            has_error="true" if messages else "false",
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/search", RouteType.asnc_local, action=("GET", "POST"))
@transaction
@wiki_env
async def wiki_search(env: Request, wiki: Wiki, user: Author):

    search_results = []
    search_query = ""

    if env.verb == "POST":

        search_query = env.form.get("search_query", "")
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

    return Response(
        wiki_search_template.render(
            search_query=search_query,
            page_title=f"Search ({wiki.title})",
            tags=wiki.tags,
            wiki=wiki,
            search_results=search_results,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/tags", RouteType.asnc_local)
@wiki_env
async def tags_all(env: Request, wiki: Wiki, user: Author):

    return Response(
        wiki_tags_template.render(tags=wiki.tags_alpha, wiki=wiki),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/upload", RouteType.asnc_local, action="POST")
@transaction
@wiki_env
async def upload_to_wiki(env: Request, wiki: Wiki, user: Author):

    for file_name, file_data in env.files.values():
        rename = 1
        dest_file_name = file_name
        while True:
            file_path = Path(wiki.data_path, dest_file_name)
            if file_path.exists():
                fn = file_name.rsplit(".", 1)
                dest_file_name = f"{fn[0]}_{rename}.{fn[1]}"
                rename += 1
            else:
                break

        with open(file_path, "wb") as f:
            f.write(file_data)

        new_img = Media(wiki=wiki, file_path=dest_file_name)
        new_img.save()

    return simple_response("")


@route(f"{Wiki.PATH}/tag/<tag_name>", RouteType.asnc_local)
@wiki_env
async def tag_pages(env: Request, wiki: Wiki, user: Author, tag_name: str):
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

    return Response(
        wiki_pages_template.render(
            tag=tag,
            articles=tagged_articles,
            article_with_tag_name=article_with_tag_name,
            wiki=wiki,
            page_title=f"Tag: {tag_name} ({wiki.title})",
        ),
        headers=default_headers,
    )


######################################################################
# Article paths
######################################################################


@route(f"{Wiki.PATH}/article", RouteType.asnc_local)
@wiki_env
async def articles(env: Request, wiki: Wiki, user: Author):
    return await wiki_home(env, wiki, user)


@route(f"{Wiki.PATH}{Article.PATH}", RouteType.asnc_local)
@article_env
async def article_display(env: Request, wiki: Wiki, user: Author, article: Article):
    try:
        return Response(Wiki.article_cache[article.id], headers=default_headers,)
    except KeyError:
        pass

    if article.id is None:
        try:
            form_tag = Tag.select(Tag.id).where(Tag.wiki == wiki, Tag.title == "@form")

            tagged_as_form = TagAssociation.select(TagAssociation.article).where(
                TagAssociation.tag << form_tag
            )

            forms = wiki.articles_alpha.select().where(Article.id << tagged_as_form)

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

    result = article_template.render(
        articles=[article], page_title=f"{article.title} ({wiki.title})", wiki=wiki
    )

    Wiki.article_cache[article.id] = result

    return Response(result, headers=default_headers,)


@route(f"{Wiki.PATH}/new_from_form/<form>", RouteType.asnc_local)
@transaction
@wiki_env
async def article_new_from_form(env: Request, wiki: Wiki, user: Author, form: str):
    return new_article_from_form_core(env, wiki, user, form, "Untitled")

@route(f"{Wiki.PATH}/new_from_form/<form>/<title>", RouteType.asnc_local)
@transaction
@wiki_env
async def article_new_from_form_with_title(env: Request, wiki: Wiki, user: Author, form: str, title: str):
    return new_article_from_form_core(env, wiki, user, form, title)

def new_article_from_form_core(env: Request, wiki: Wiki, user: Author, form: str, title: str):
    form_article = wiki.articles.where(Article.title == wiki.url_to_title(form)).get()

    new_article = form_article.make_from_form(wiki.url_to_title(title))
    return redirect(new_article.edit_link)    

@route(f"{Wiki.PATH}{Article.PATH}/revision/<revision_id>", RouteType.asnc_local)
@article_env
async def article_revision(
    env: Request, wiki: Wiki, user: Author, article: Article, revision_id: str
):

    try:
        revision = article.revisions.where(Article.id == int(revision_id)).get()
    except Exception:
        return await wiki_home(env, wiki, user)

    return Response(
        article_template.render(
            articles=[revision],
            page_title=f"{revision.title} ({wiki.title})",
            wiki=wiki,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/history", RouteType.asnc_local)
@article_env
async def article_history(env: Request, wiki: Wiki, user: Author, article: Article):
    return Response(
        article_history_template.render(
            article=article,
            page_title=f"History: {article.title} ({wiki.title})",
            wiki=wiki,
        )
    )


@route(
    f"{Wiki.PATH}{Article.PATH}/preview", RouteType.asnc_local, action=("GET", "POST")
)
@article_env
async def article_preview(env: Request, wiki: Wiki, user: Author, article: Article):

    if env.verb == "POST":
        article = Article(
            title=env.form.get("article_title", None),
            content=env.form.get("article_content", None),
        )
        return Response(
            article_preview_template.render(
                article=article, page_title=article.title, wiki=wiki
            )
        )

    # TODO: consolidate error msg with above

    if article.id is None:
        article.content = f'This article does not exist. Click the <a class="autogenerate" href="{article.edit_link}">edit link</a> to create this article.'

    return Response(
        article_preview_template.render(
            article=article, page_title=article.title, wiki=wiki
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/save", RouteType.asnc_local, action="POST")
async def article_save_ajax(env: Request, wiki_title: str, article_title: str):
    return await article_edit(env, wiki_title, article_title, ajax=True)


@route(f"{Wiki.PATH}{Article.PATH}/edit", RouteType.asnc_local, action=("GET", "POST"))
@transaction
@article_env
async def article_edit(
    env: Request, wiki: Wiki, user: Author, article: Article, ajax=False
):

    # Redirect to article creation if we try to edit a nonexistent article

    if article.id is None:
        return redirect(f"{wiki.link}/new/?title={Wiki.title_to_url(article.title)}")

    # Redirect to edit link if we visit the draft of the article

    if env.verb == "GET":
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

    if env.verb == "GET":

        if article.opened_by is None:
            article.opened_by = article.author
            article.last_edited = datetime.datetime.now()
            article.save()
        else:
            warning = Message(
                "This article was previously opened for editing without being saved. It may contain unsaved changes elsewhere. Use 'Save and Exit' or 'Quit Editing' to remove this message."
            )

    if env.verb == "POST" or ajax is True:

        action = env.form.get("save", None)

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

        article_content = env.form.get("article_content", None)
        article_title = env.form.get("article_title", None)

        if article_content != article.content:
            article.content = article_content
            article.last_edited = datetime.datetime.now()

        if (
            article_title != article.draft_of.title
            and article_title != article.new_title
        ):
            article.new_title = article_title
            if article.has_new_name_collision():
                error = Error(
                    f'An article named "{Unsafe(article_title)}" already exists. Choose another name for this article.'
                )
            else:
                if action is None:
                    action = "save"

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

            elif action in ("publish", "revise"):
                new_article = article.draft_of

                if action == "revise":
                    revision = Article(
                        wiki=new_article.wiki,
                        title=new_article.title,
                        # title=f"{new_article.title} [{new_article.last_edited.strftime(ARTICLE_TIME_FORMAT)}]",
                        content=new_article.content,
                        author=new_article.author,
                        created=new_article.created,
                        revision_of=new_article,
                    )
                    revision.save()
                    revision.update_links()
                    revision.update_autogen_metadata()
                    revision.copy_metadata_from(new_article)
                    revision.copy_tags_from(new_article)

                if article.new_title:
                    new_article.title = article.new_title

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
            return simple_response(str(error))
        return simple_response(str(Message("Article successfully saved.", color="success")))

    article.content = article.content.replace("&", "&amp;")

    return Response(
        article_edit_template.render(
            article=article,
            page_title=f"Editing: {article.title} ({wiki.title})",
            wiki=wiki,
            original_article=original_article,
            messages=[error, warning],
            has_error="true" if error else "false",
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/delete", RouteType.asnc_local)
@article_env
async def article_delete(env: Request, wiki: Wiki, user: Author, article: Article):

    warning = f'Article "{Unsafe(article.title)}" is going to be deleted! Deleted articles are GONE FOREVER.'

    if article.revision_of:
        warning += "<hr/>This is an earlier revision of an existing article. Deleting this will remove it from that article's revision history. This is allowed, but NOT RECOMMENDED."

    return Response(
        article_template.render(
            articles=[article],
            page_title=f"Delete: {article.title} ({wiki.title})",
            wiki=wiki,
            messages=[
                Message(warning, yes=article.delete_confirm_link, no=article.link,)
            ],
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/delete/<delete_key>", RouteType.asnc_local)
@article_env
async def article_delete_confirm(
    env: Request,
    wiki: Wiki,
    user: Author,
    article: Article,
    delete_key: str,
    redirect_to=None,
):
    if article.id is None:
        return redirect(wiki.link)

    if article.delete_key != delete_key:
        return redirect(article.link)

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

    return Response(
        article_template.render(
            wiki=wiki,
            articles=[redirect_to],
            messages=[Error(f'Article "{Unsafe(article.title)}" has been deleted.')],
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/discard-draft", RouteType.asnc_local)
@transaction
@article_env
async def draft_discard(env: Request, wiki: Wiki, user: Author, article: Article):

    if article.id is None:
        return redirect(article.link)

    if article.draft_of is None:
        return redirect(article.link)

    warning = f'"{Unsafe(article.title)}" is going to be discarded.'

    if article.content != article.draft_of.content:

        warning += (
            "<br/>THIS DRAFT HAS MODIFICATIONS THAT WERE NOT SAVED TO THE ARTICLE."
        )

    return Response(
        article_template.render(
            articles=[article],
            page_title=f"Discard draft: {article.title} ({wiki.title})",
            wiki=wiki,
            messages=[
                Message(
                    warning, yes=article.discard_draft_confirm_link, no=article.link,
                )
            ],
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/discard-draft/<delete_key>", RouteType.asnc_local)
@article_env
async def draft_discard_confirm(
    env: Request, wiki: Wiki, user: Author, article: Article, delete_key: str,
):
    return await article_delete_confirm.__wrapped__(
        env, wiki, user, article, delete_key, redirect_to=article.draft_of
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", RouteType.asnc_local, action="GET")
@article_env
async def modal_insert_image(env: Request, wiki: Wiki, user: Author, article: Article):

    return Response(
        modal_template.render(
            title="Insert image into article",
            body=modal_search_template.render(
                url=f"{article.link}/insert-image/",
                modal_post_enter="",
                search_results=image_search(wiki, None),
            ),
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", RouteType.asnc_local, action="POST")
@article_env
async def modal_insert_image_search(
    env: Request, wiki: Wiki, user: Author, article: Article
):

    search = env.form.get("search_query", None)
    return Response(image_search(wiki, search))


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


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag", RouteType.asnc_local, action="GET")
@article_env
async def modal_tags(env: Request, wiki: Wiki, user: Author, article: Article):
    tags = existing_tags(article)
    body = modal_search_template.render(
        url=f"{article.link}/insert-tag",
        modal_post_enter="tagEnter();",
        search_results=search_results(wiki, None),
    )
    return Response(
        modal_template.render(
            title="Edit article tags",
            body=f'Existing tags (click to remove):<br/><div id="modal-tag-listing">{tags}</div><hr/>{body}',
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag", RouteType.asnc_local, action="POST")
@article_env
async def modal_tags_search(env: Request, wiki: Wiki, user: Author, article: Article):
    search = env.form.get("search_query", None)
    return Response(search_results(wiki, search))


@route(f"{Wiki.PATH}{Article.PATH}/add-tag", RouteType.asnc_local, action="POST")
@article_env
async def modal_add_tag(env: Request, wiki: Wiki, user: Author, article: Article):
    tag = env.form.get("tag", None)
    article.add_tag(tag)
    wiki.invalidate_cache()
    return Response(existing_tags(article))


@route(f"{Wiki.PATH}{Article.PATH}/remove-tag", RouteType.asnc_local, action="POST")
@article_env
async def modal_remove_tag(env: Request, wiki: Wiki, user: Author, article: Article):
    tag = env.form.get("tag", None)
    article.remove_tag(tag)
    wiki.invalidate_cache()
    return Response(existing_tags(article))


@route(f"{Wiki.PATH}{Article.PATH}/edit-metadata", RouteType.asnc_local, action="GET")
@article_env
async def modal_edit_metadata(env: Request, wiki: Wiki, user: Author, article: Article):
    return Response(
        modal_template.render(
            title="Edit article metadata",
            body=modal_metadata_template.render(
                url=f"{article.link}/edit-metadata",
                article=article,
                modal_post_enter="",
            ),
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/edit-metadata", RouteType.asnc_local, action="POST")
@transaction
@article_env
async def modal_edit_metadata_post(
    env: Request, wiki: Wiki, user: Author, article: Article
):

    key = env.form.get("key", None)
    if key:
        value = env.form.get("value", None)
        article.set_metadata(key, value)

    delete = env.form.get("delete", None)
    if delete:
        try:
            delete_instance = article.metadata.where(Metadata.id == delete).get()
            delete_instance.delete_instance()
        except Metadata.DoesNotExist:
            pass

    return Response(
        modal_metadata_template.render(
            url=f"{article.link}/edit-metadata", article=article, modal_post_enter=""
        )
    )


def link_search(wiki, search):
    if search is None or search == "":
        search_results = (
            wiki.articles.select().order_by(SQL("title COLLATE NOCASE")).limit(10)
        )
    else:
        search_results = (
            wiki.articles.select()
            .where(Article.title.contains(search))
            .order_by(SQL("title COLLATE NOCASE"))
            .limit(10)
        )

    results = ['<ul class="list-unstyled">']
    for result in search_results:
        link = f'<li><a onclick="insertLink(this);" href="#">{result.title}</a></li>'
        results.append(link)

    return "".join(results)


@route(f"{Wiki.PATH}{Article.PATH}/insert-link", RouteType.asnc_local, action="GET")
@article_env
async def modal_insert_link_search(
    env: Request, wiki: Wiki, user: Author, article: Article
):

    return Response(
        modal_template.render(
            title="Insert link into article",
            body=modal_search_template.render(
                url=f"{article.link}/insert-link/",
                modal_post_enter="",
                search_results=link_search(wiki, None),
                alt_input=("Text for link", "link_text"),
            ),
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-link", RouteType.asnc_local, action="POST")
@article_env
async def modal_insert_link_search_post(
    env: Request, wiki: Wiki, user: Author, article: Article
):

    search = env.form.get("search_query", None)
    return Response(link_search(wiki, search))


@route("/quit", RouteType.sync_nothread)
def quit(*a):
    yield simple_response("You may now close this browser.")
    from models import db

    db.commit()
    db.close()
    import sys

    sys.exit()


######################################################################
# Media and static paths
######################################################################


@route("/static/<filename>", RouteType.asnc_local)
async def static_content(env: Request, filename: str):
    return static_file(filename, path="folio/static")

from math import ceil

def paginator(env: Request, media: Media):
    search = env.params.get("search", [None])[0]
    if search:
        media = media.where(Media.file_path.contains(search))
    else:
        search = ""

    page = int(env.params.get("p", [1])[0])

    last = ceil(media.count()/5)

    if page == -1 or page > last:
        page = last

    previous_page = max(page - 1, 1)
    next_page = min(page + 1, last)

    media = media.paginate(page, 5)

    first_url = urlencode({"p": 1, "search": search})
    previous_url = urlencode({"p": previous_page, "search": search})
    next_url = urlencode({"p": next_page, "search": search})
    last_url = urlencode({"p": -1, "search": search})

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


@route(f"{Wiki.PATH}/media", RouteType.asnc_local)
@wiki_env
async def wiki_media(env: Request, wiki: Wiki, user: Author):

    media, pagination = paginator(env, wiki.media_alpha)

    return Response(
        wiki_media_template.render(
            wiki=wiki,
            media=media,
            page_title=f"Media ({wiki.title})",
            paginator=pagination,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/media-paste", RouteType.asnc_local, action="POST")
@wiki_env
async def wiki_media_paste(env: Request, wiki: Wiki, user: Author):

    paste_file = env.files.get("file")
    if not paste_file:
        return simple_response("", code="500")

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

    return simple_response(f"{new_image.link}\n{new_image.edit_link}\n![]({new_image.file_path})")


@route(f"{Wiki.PATH}/media/<file_name>", RouteType.asnc_local)
@wiki_env
async def media_file(env: Request, wiki: Wiki, user: Author, file_name: str):

    return static_file(
        Wiki.url_to_file(file_name),
        path=f"{config.DATA_PATH}/{wiki.id}",
        last_modified=env.headers.get("HTTP_IF_MODIFIED_SINCE", None),
    )


@route(f"{Wiki.PATH}/media/<file_name>/edit", RouteType.asnc_local)
@media_env
async def media_file_edit(env: Request, wiki: Wiki, user: Author, media: Media):

    return Response(
        wiki_media_edit_template.render(
            wiki=wiki, media=media, page_title=f"File {media.file_path} ({wiki.title})"
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/media/<file_name>/edit", RouteType.asnc_local, action="POST")
@transaction
@media_env
async def media_file_edit_post(env: Request, wiki: Wiki, user: Author, media: Media):

    note: Union[Error, Message, None] = None

    filename_body, filename_ext = media.file_path.rsplit(".", 1)
    new_filename_body = env.form.get("media-filename")

    if env.form.get("select", None):
        wiki.set_metadata("cover_img", media.id)
        wiki.invalidate_cache()

    elif env.form.get("save", None) and new_filename_body != filename_body:

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


    return Response(
        wiki_media_edit_template.render(wiki=wiki, media=media, messages=[note]),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/media/<file_name>/delete", RouteType.asnc_local)
@media_env
async def media_file_delete(env: Request, wiki: Wiki, user: Author, media: Media):

    warning = f'Media "{Unsafe(media.file_path)}" is going to be deleted! Deleted media are GONE FOREVER.'

    cover_media_id = wiki.get_metadata("cover_img")

    if cover_media_id and int(cover_media_id) == media.id:

        warning += f"<hr>Also note: This media is in use as the cover image for this wiki. Deleting it will cause the cover image to revert to the default."

    if media.in_articles.count():
        warning += f"<hr>Also note: This media is in use in {media.in_articles.count()} articles. Deleting it will NOT remove references to the image from those articles, but will leave broken links."

    return Response(
        wiki_media_edit_template.render(
            wiki=wiki,
            media=media,
            messages=[
                Message(warning, yes=media.delete_confirm_link, no=media.edit_link,)
            ],
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/media/<file_name>/delete/<delete_key>", RouteType.asnc_local)
@transaction
@media_env
async def media_file_delete_confirm(
    env: Request, wiki: Wiki, user: Author, media: Media, delete_key: str
):

    cover_media_id = wiki.get_metadata("cover_img")
    if cover_media_id and int(cover_media_id) == media.id:
        wiki.delete_metadata("cover_img")

    media.delete_()

    wiki.invalidate_cache()

    media_list, pagination = paginator(env, wiki.media_alpha)

    return Response(
        blank_template.render(
            wiki=wiki,
            messages=[Error(f'<p>Media item "{Unsafe(media.file_path)}" has been deleted.</p><p><a href="{wiki.media_link}">Return to the media manager</a></p>')],
        )
    )


# For now, a dummy response until we can come up with an actual favicon.


@route(f"/favicon.ico", RouteType.asnc_local)
async def favicon(env: Request):
    date = email_utils.formatdate(time.time(), usegmt=True)
    return simple_response(
        b"",
        headers={
            "Cache-Control": f"private, max-age=38400",
            "Last-Modified": date,
            "Date": date,
        },
    )


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
