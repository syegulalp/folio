from bottle import (
    template,
    route,
    static_file,
    request,
    HTTPError,
)


from models import (
    Wiki,
    Author,
    Media,
    re,
)

from .decorators import *

# from __main__ import config
from data import config
from utils import Message, Error, Unsafe

from peewee import SQL

from pathlib import Path
from typing import Union

import json


@route("/static/<filename>")
def static_content(filename: str):
    return static_file(filename, "folio/static")


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
    file_data = request.files["file"]

    if not file_data:
        return HTTPError(500)

    file_id = 0

    while True:
        filename = f"{wiki.title}_{file_id}.png"
        if not Path(wiki.data_path, filename).exists():
            break
        file_id += 1

    file_data.save(str(Path(wiki.data_path, filename)))

    new_image = Media(
        wiki=wiki,
        file_path=filename,
    )
    new_image.save()

    result = {
        "url": new_image.link,
        "link": new_image.edit_link,
        "filename": new_image.file_path,
    }

    return json.dumps(result)


@route(f"{Wiki.PATH}/media/<file_name>")
@wiki_env
def media_file(wiki: Wiki, user: Author, file_name: str):
    return static_file(
        Wiki.url_to_file(file_name),
        f"{config.DATA_PATH}/{wiki.id}",
    )


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
    new_filename_body = request.forms.get("media-filename")

    if request.forms.get("select", None):
        wiki.set_metadata("cover_img", media.id)
        wiki.invalidate_cache()

    elif request.forms.get("save", None) and new_filename_body != filename_body:
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
                    replacement_src,
                    r"![\1](" + new_filename + r")",
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
        messages=[
            Message(
                warning,
                yes=media.delete_confirm_link,
                no=media.edit_link,
            )
        ],
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
