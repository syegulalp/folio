from bottle import (
    template,
    route,
    redirect,
    request,
)

from models import (
    Article,
    Wiki,
    Author,
    Tag,
    Metadata,
)

from peewee import SQL

from .decorators import *
from .wiki import wiki_home
from .media import image_search

from utils import Message, Error, Unsafe

import datetime


@route(f"{Wiki.PATH}/article")
@wiki_env
def articles(wiki: Wiki, user: Author):
    return wiki_home(wiki, user)


@route(f"{Wiki.PATH}{Article.PATH}")
@article_env
def article_display_(wiki: Wiki, user: Author, article: Article):
    return article_display(wiki, user, article)


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
            title=request.forms.article_title, content=request.forms.article_content,
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
        return redirect(f"{wiki.link}/new?title={Wiki.title_to_url(article.title)}")

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

        action = request.forms.save

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

        article_content = request.forms.article_content
        article_title = request.forms.article_title

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
            "includes/modal_search.tpl",
            url=f"{article.link}/insert-image",
            search_results=image_search(wiki, None),
        ),
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", method="POST")
@article_env
def modal_insert_image_search(wiki: Wiki, user: Author, article: Article):

    search = request.forms.search_query
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
    search = request.forms.search_query
    return search_results(wiki, search)


@route(f"{Wiki.PATH}{Article.PATH}/add-tag", method="POST")
@article_env
def modal_add_tag(wiki: Wiki, user: Author, article: Article):
    tag = request.forms.tag
    article.add_tag(tag)
    wiki.invalidate_cache()
    return existing_tags(article)


@route(f"{Wiki.PATH}{Article.PATH}/remove-tag", method="POST")
@article_env
def modal_remove_tag(wiki: Wiki, user: Author, article: Article):
    tag = request.forms.tag
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

    key = request.forms.key
    if key:
        value = request.forms.value
        article.set_metadata(key, value)

    delete = request.forms.delete
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
            url=f"{article.link}/insert-link",
            search_results=link_search(wiki, None),
            alt_input=("Text for link", "link_text"),
        ),
        footer="",
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-link", method="POST")
@article_env
def modal_insert_link_search_post(wiki: Wiki, user: Author, article: Article):

    search = request.forms.search_query
    return link_search(wiki, search)
