from bottle import (
    template,
    route,
    redirect,
    request,
)

from models import (
    Article,
    ArticleIndex,
    Wiki,
    Author,
    Tag,
    Media,
)

from .decorators import wiki_env, article_display, home_page_render

from __main__ import config
from utils import Message, Error, Unsafe

from peewee import SQL

from pathlib import Path
from typing import Any

import datetime
import json


@route(f"{Wiki.PATH}")
@wiki_env
def wiki_home(wiki: Wiki, user: Author):
    return article_display(wiki, user, wiki.main_article)


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

    wiki.invalidate_cache()

    Wiki.export_mode = True

    for article in wiki.articles_nondraft_only:
        article_text = article_display(wiki, user, article)

        with open(
            Path(article_path, f"{wiki.title_to_url(article.title)}.html"),
            "w",
            encoding="utf-8",
        ) as export_file:
            export_file.write(article_text)

    Wiki.export_mode = False

    wiki.invalidate_cache()

    with open(Path(article_path, ".htaccess"), "w", encoding="utf8") as htf:
        htf.write("DirectoryIndex Contents.html")

    redirect_txt = """
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="refresh" content="0; url='article'" />
  </head>
  <body>
    <p>Please follow <a href="article">this link</a>.</p>
  </body>
</html>"""

    with open(Path(export_path, "index.html"), "w", encoding="utf8") as rdf:
        rdf.write(redirect_txt)

    return "ok"


@route(f"{Wiki.PATH}/edit", method=("GET", "POST"))
@wiki_env
def wiki_settings_edit(wiki: Wiki, user: Author):
    action = None
    error = None
    original_wiki = wiki

    if request.method == "POST":

        wiki_new_title = request.forms.wiki_title
        wiki_new_description = request.forms.wiki_description

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

        action = request.forms.save

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
        article_content = request.forms.article_content
        article_title = request.forms.article_title
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

        article_title = Wiki.url_to_title(request.params.get("title", "Untitled"))

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
        style=wiki.stylesheet(),
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

        search_query = request.forms.search_query
        replace_query = request.forms.replace_query

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

        if replace_query and request.forms.get("replace", ""):

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


@route(f"{Wiki.PATH}/search2", method=("POST",))
@wiki_env
def wiki_search2(wiki: Wiki, user: Author):

    search_query = request.forms.search
    if search_query == "":
        return ""

    article_title_results = Article.search(wiki.articles, search_query).limit(5)
    media_results = Media.search(wiki.media, search_query).limit(5)
    tag_results = Tag.search(wiki.tags, search_query).limit(5)

    results = []
    for article in article_title_results:
        results.append(
            f'<p>📝<a class="jsnavlink" href="{article.link}">{article.title}</a></p>'
        )
    for media in media_results:
        results.append(
            f'<p>🖼<a class="jsnavlink" href="{media.edit_link}">{media.file_path}</a></p>'
        )
    for tag in tag_results:
        results.append(
            f'<p>🏷<a class="jsnavlink" href="{tag.link}">{tag.title}</a></p>'
        )

    return "".join(results)


@route(f"{Wiki.PATH}/search", method=("GET", "POST"))
@wiki_env
def wiki_search(wiki: Wiki, user: Author):

    search_results = []
    search_query = ""

    if request.method == "POST":

        search_query = request.forms.search_query
        if search_query != "":

            article_title_result = Article.search(wiki.articles, search_query)
            article_contents_result = Article.fulltext_search(wiki.articles, search_query)
            tag_result = Tag.search(wiki.tags, search_query)
            media_result = Media.search(wiki.media, search_query)

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

    result = {
        "link": new_img.edit_link,
        "url": new_img.link,
        "filename": new_img.file_path,
    }

    return json.dumps(result)


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
