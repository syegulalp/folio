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
)
from models import (
    Article,
    ArticleIndex,
    Wiki,
    Author,
    Tag,
    TagAssociation,
    Media,
    ARTICLE_TIME_FORMAT,
)
import asyncio
import urllib
import datetime
import os
from __main__ import config
from utils import Message, Error
from peewee import fn, SQL

home_template = Template(file="home.html")
article_template = Template(file="article.html")
wiki_edit_template = Template(file="wiki_edit.html")
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
sidebar_template = Template(file="includes/sidebar.html")

default_headers = {
    "Expires": "-1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache, no-store, must-revalidate",
}

######################################################################
# Decorators
######################################################################

def get_user():
    return Author.get(Author.name == "Admin")

def get_wiki(wiki_title):
    wiki = Wiki.get(Wiki.title == Wiki.url_to_title(wiki_title))
    if Wiki.sidebar_cache.get(wiki.id, None) is None:
        Wiki.sidebar_cache[wiki.id] = (
            sidebar_template.render(wiki=wiki)
        )
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


def article_env(func):
    def wrapper(env: Request, wiki_title: str, article_title: str, *a, **ka):
        user = get_user()
        wiki = get_wiki(wiki_title)
        
        try:
            article = wiki.articles.where(
                Article.title == Article.url_to_title(article_title)
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


@route("/", RouteType.asnc)
async def main_route(env: Request):
    default_article = Article.get(Article.title == "Contents")
    wikis = Wiki.select().order_by(Wiki.title.asc())
    articles = Article.select().order_by(Article.last_edited.desc()).limit(25)
    return Response(
        home_template.render(
            wikis=wikis, page_title="Wiki Server Homepage", articles=articles
        )
    )


route("/wiki", RouteType.asnc)(main_route)


@route("/new", RouteType.asnc)
async def new_wiki(env: Request):
    user = Author.get(Author.name == "Admin")
    wiki = Wiki(title="", description="",)
    return Response(
        wiki_edit_template.render(wiki=wiki, user=user, page_title=f"Create new wiki")
    )


@route("/new", RouteType.asnc, action="POST")
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


@route(f"{Wiki.PATH}", RouteType.asnc)
@wiki_env
async def wiki_home(env: Request, wiki: Wiki, user: Author):
    return Response(
        article_template.render(wiki=wiki, articles=[wiki.main_article], user=user)
    )


@route(f"{Wiki.PATH}/edit", RouteType.asnc, action=("GET", "POST"))
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
            if action == "quit":
                return redirect(wiki.link)
            if action == "save":
                return redirect(wiki.edit_link)
        else:
            original_wiki = Wiki.get(Wiki.id == wiki.id)

    wiki.invalidate_cache()
    
    return Response(
        wiki_edit_template.render(
            wiki=wiki,
            user=user,
            page_title=f"{wiki.title}: Edit settings",
            messages=[error] if error else None,
            original_wiki=original_wiki,
        ),
        headers=default_headers,
    )


######################################################################
# Article paths
######################################################################


@route(f"{Wiki.PATH}/article", RouteType.asnc)
@wiki_env
async def articles(env: Request, wiki: Wiki, user: Author):
    return await wiki_home(env, wiki, user)


@route(f"{Wiki.PATH}{Article.PATH}", RouteType.asnc)
@article_env
async def article_display(env: Request, wiki: Wiki, user: Author, article: Article):
    if article.id is None:
        
        try:
            template_tag = Tag.select(Tag.id).where(Tag.wiki == wiki, Tag.title=='@template')

            tagged_as_template = TagAssociation.select(
                TagAssociation.article
            ).where(
                TagAssociation.tag << template_tag
            )
            
            templates = wiki.articles_alpha.select().where(
                Article.id << tagged_as_template
            )

        except (Tag.DoesNotExist, TagAssociation.DoesNotExist, Article.DoesNotExist) as e:
            templates = ''
        else:            
            if templates.count():
                template_list =['<p>You can also create this article using a template:</p><hr/><ul>']
                for template in templates:
                    template_list.append(f'<li><a href="{article.template_creation_link(template)}">{template.title}</a></li>')
                template_list.append('</ul>')
                templates = ''.join(template_list)
            else:
                templates=''

        article.content = f'This article does not exist. Click the <a class="autogenerate" href="{article.edit_link}">edit link</a> to create this article.{templates}'

    return Response(
        article_template.render(
            articles=[article], page_title=article.title, wiki=wiki
        ),
        headers=default_headers,
    )

@route(f"{Wiki.PATH}{Article.PATH}/new_from_template/<template>", RouteType.asnc)
@article_env
async def article_new_from_template(env: Request, wiki: Wiki, user: Author, article: Article, template: str):
    template_text = wiki.articles.where(Article.title == wiki.url_to_title(template)).get().content

    article.content = template_text
    article.save()

    wiki.invalidate_cache()

    return redirect(article.edit_link)

@route(f"{Wiki.PATH}{Article.PATH}/history", RouteType.asnc)
@article_env
async def article_history(env: Request, wiki: Wiki, user: Author, article: Article):
    return Response(
        article_history_template.render(
            article=article, page_title=article.title, wiki=wiki
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/preview", RouteType.asnc, action=("GET", "POST"))
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


@route(f"{Wiki.PATH}{Article.PATH}/save", RouteType.asnc, action="POST")
async def article_save_ajax(env: Request, wiki_title: str, article_title: str):
    return await article_edit(env, wiki_title, article_title, ajax=True)


@route(f"{Wiki.PATH}{Article.PATH}/edit", RouteType.asnc, action=("GET", "POST"))
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
            article = draft

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

            if action == "exit":
                article.opened_by = None
                article.save()
                wiki.invalidate_cache()
                return redirect(article.link)

            elif action in ("publish", "revise"):
                new_article = article.draft_of

                if action == "revise":
                    revision = Article(
                        wiki=new_article.wiki,
                        title=f"{new_article.title} [{new_article.last_edited.strftime(ARTICLE_TIME_FORMAT)}]",
                        content=new_article.content,
                        author=new_article.author,
                        created=new_article.created,
                        revision_of=new_article,
                    )
                    revision.save()                    
                    #revision.update_index()
                    revision.update_links()                    
                    revision.update_autogen_metadata()
                    revision.copy_tags_from(new_article)

                if article.new_title:
                    new_article.title = article.new_title

                new_article.content = article.content
                new_article.last_edited = article.last_edited
                new_article.save()         
                new_article.update_index()       
                new_article.update_links()
                new_article.update_autogen_metadata()
                new_article.clear_tags()
                new_article.copy_tags_from(article)

                article.clear_tags()
                article.delete_instance(recursive=True)
                wiki.invalidate_cache()
                return redirect(new_article.link)

            elif action == "save":
                article.opened_by = None
                article.save()

                wiki.invalidate_cache()

                if article.draft_of:
                    return redirect(article.draft_of.edit_link)

                return redirect(article.link)
        else:
            original_article = Article.get(Article.id == article.id)

    if ajax:
        if error:
            return simple_response(str(error))
        return simple_response(str(Message("Article successfully saved.")))

    article.content = article.content.replace("&", "&amp;")

    return Response(
        article_edit_template.render(
            article=article,
            page_title=f"Editing: {article.title}",
            wiki=wiki,
            original_article=original_article,
            messages=[error, warning],
            has_error="true" if error else "false",
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/delete", RouteType.asnc)
@article_env
async def article_delete(
    env: Request,
    wiki: Wiki,
    user: Author,
    article: Article):

    warning = f'Article "{Unsafe(article.title)}" is going to be deleted! Deleted articles are GONE FOREVER.'

    if article.revision_of:
        warning += "<hr/>This is an earlier revision of an existing article. Deleting this will remove it from that article's revision history. This is allowed, but NOT RECOMMENDED."

    return Response(
        article_template.render(
            articles=[article],
            page_title=article.title,
            wiki=wiki,
            messages=[
                Message(warning, yes=article.delete_confirm_link, no=article.link,)
            ],
        ),
        headers=default_headers,
    )

@route(f"{Wiki.PATH}{Article.PATH}/discard-draft", RouteType.asnc)
@article_env
async def draft_discard(
    env: Request,
    wiki: Wiki,
    user: Author,
    article: Article):

    if article.id is None:
        return redirect(article.link)

    if article.draft_of is None:
        return redirect(article.link)

    warning = f'"{Unsafe(article.title)}" is going to be discarded.'

    if article.content != article.draft_of.content:

        warning += "<br/>THIS DRAFT HAS MODIFICATIONS THAT WERE NOT SAVED TO THE ARTICLE."

    return Response(
        article_template.render(
            articles=[article],
            page_title=article.title,
            wiki=wiki,
            messages=[
                Message(warning, yes=article.discard_draft_confirm_link, no=article.link,)
            ],
        ),
        headers=default_headers,
    )    

@route(f"{Wiki.PATH}{Article.PATH}/discard-draft/<delete_key>", RouteType.asnc)
@article_env
async def draft_discard_confirm(
    env: Request,
    wiki: Wiki,
    user: Author,
    article: Article,    
    delete_key: str, 
):
    return await article_delete_confirm.__wrapped__(env, wiki, user, article, delete_key, redirect_to=article.draft_of)


@route(f"{Wiki.PATH}{Article.PATH}/delete/<delete_key>", RouteType.asnc)
@article_env
async def article_delete_confirm(
    env: Request,
    wiki: Wiki,
    user: Author,
    article: Article,
    delete_key: str, 
    redirect_to = None
):
    if article.id is None:
        return redirect(wiki.link)

    if article.delete_key != delete_key:
        return redirect(article.link)

    if article.drafts.count():
        draft = article.drafts.get()
        draft.clear_tags()
        draft.delete_instance(recursive=True)
    for revision in article.edits.select():
        revision.clear_tags()
        revision.delete_instance(recursive=True)
    article.clear_tags()
    article.clear_index()
    article.delete_instance(recursive=True)

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


@route(f"{Wiki.PATH}/new", RouteType.asnc, action=("GET", "POST"))
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
            page_title=f"Creating: {new_article.title}",
            wiki=wiki,
            messages=messages,
            has_error="true" if messages else "false",
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/search", RouteType.asnc, action=("GET", "POST"))
@wiki_env
async def wiki_search(env: Request, wiki: Wiki, user: Author):

    search_results = []
    search_query = ""

    if env.verb == "POST":

        search_query = env.form.get("search_query", "")
        if search_query != "":
            search_query_wildcard = search_query

            title_result = (
                Article.select()
                .where(
                    Article.wiki == wiki, Article.title.contains(search_query_wildcard)
                )
                .order_by(SQL("title COLLATE NOCASE"))
            )


            _article_result = (
                ArticleIndex.select(ArticleIndex.rowid)
                .where(
                    ArticleIndex.match(search_query_wildcard+'*')
                )
            )

            article_result = wiki.articles.select().where(Article.id << _article_result).order_by(SQL("title COLLATE NOCASE"))


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
                    title_result,
                ]
            )

            search_results.append(
                [
                    "Article contents",
                    r'<li><a href="{result.link}">{result.title}</a></li>',
                    article_result,
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
            tags=wiki.tags,
            wiki=wiki,
            search_results=search_results,
        ),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/tags", RouteType.asnc)
@wiki_env
async def tags_all(env: Request, wiki: Wiki, user: Author):

    return Response(
        wiki_tags_template.render(tags=wiki.tags_alpha, wiki=wiki),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/upload", RouteType.asnc, action="POST")
@wiki_env
async def upload_to_wiki(env: Request, wiki: Wiki, user: Author):

    for file_name, file_data in env.files.values():
        rename = 1
        dest_file_name = file_name
        while True:
            file_path = os.path.join(wiki.data_path, dest_file_name)
            if os.path.exists(file_path):
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


@route(f"{Wiki.PATH}/tag/<tag_name>", RouteType.asnc)
@wiki_env
async def tag_pages(env: Request, wiki: Wiki, user: Author, tag_name: str):
    tag_name = Wiki.url_to_title(tag_name)
    try:
        tag = Tag.get(Tag.title == tag_name)
        tagged_articles = wiki.articles_tagged_with(tag_name).order_by(
            SQL("title COLLATE NOCASE")
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
        ),
        headers=default_headers,
    )


######################################################################
# Media and static paths
######################################################################


@route("/static/<filename>", RouteType.asnc)
async def static_content(env: Request, filename: str):
    return static_file(filename, path="folio/static")


@route(f"{Wiki.PATH}/media", RouteType.asnc)
@wiki_env
async def wiki_media(env: Request, wiki: Wiki, user: Author):

    return Response(
        wiki_media_template.render(wiki=wiki, media=wiki.media_alpha,),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}/media/<file_name>", RouteType.asnc)
@wiki_env
async def media_file(env: Request, wiki: Wiki, user: Author, file_name: str):

    return static_file(
        Wiki.url_to_file(file_name), path=f"{config.DATA_PATH}/{wiki.id}",
        last_modified=env.headers.get('HTTP_IF_MODIFIED_SINCE',None)
    )


@route(f"{Wiki.PATH}/media/<file_name>/edit", RouteType.asnc)
@wiki_env
async def media_file_edit(env: Request, wiki: Wiki, user: Author, file_name: str):

    try:
        media = (
            Media.select()
            .where(Media.file_path == Wiki.url_to_file(file_name), Media.wiki == wiki)
            .get()
        )
    except Media.DoesNotExist:
        return simple_response("", 404)
        # TODO: proper error

    return Response(
        wiki_media_edit_template.render(wiki=wiki, media=media),
        headers=default_headers,
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", RouteType.asnc, action="GET")
@article_env
async def modal_insert_image(env: Request, wiki: Wiki, user: Author, article: Article):

    return Response(
        modal_template.render(
            title="Insert image into article",
            body=modal_search_template.render(
                url=f"{article.link}/insert-image/", modal_post_enter=""
            ),
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-image", RouteType.asnc, action="POST")
@article_env
async def modal_insert_image_search(
    env: Request, wiki: Wiki, user: Author, article: Article
):

    search = env.form.get("search", None)

    search_results = (
        wiki.media.select()
        .where(
            (Media.file_path.contains(search)) | (Media.description.contains(search))
        )
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

    return Response("".join(results))


def existing_tags(article):
    taglist = [""]
    for tag in article.tags_alpha:
        taglist.append(
            f'<a href="#" onclick="removeTag(this)"; title="Click to remove this tag from this article" class="badge badge-primary">{tag.title}</a> '
        )
    tags = "".join(taglist)
    return tags


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag", RouteType.asnc, action="GET")
@article_env
async def modal_tags(env: Request, wiki: Wiki, user: Author, article: Article):
    tags = existing_tags(article)
    body = modal_search_template.render(
        url=f"{article.link}/insert-tag", modal_post_enter="tagEnter();"
    )
    return Response(
        modal_template.render(
            title="Edit article tags",
            body=f'Existing tags (click to remove):<br/><div id="modal-tag-listing">{tags}</div><hr/>{body}',
            footer="",
        )
    )


@route(f"{Wiki.PATH}{Article.PATH}/insert-tag", RouteType.asnc, action="POST")
@article_env
async def modal_tags_search(env: Request, wiki: Wiki, user: Author, article: Article):
    search = env.form.get("search", None)
    search_results = wiki.tags.select().where(Tag.title.contains(search)).limit(10)
    results = ["<ul>"]
    for result in search_results:
        results.append(
            f'<li><a href="#" onclick="insertTag(this);">{result.title}</li>'
        )
    results.append("</ul>")
    return Response("".join(results))


@route(f"{Wiki.PATH}{Article.PATH}/add-tag", RouteType.asnc, action="POST")
@article_env
async def modal_add_tag(env: Request, wiki: Wiki, user: Author, article: Article):
    tag = env.form.get("tag", None)
    article.add_tag(tag)
    wiki.invalidate_cache()
    return Response(existing_tags(article))


@route(f"{Wiki.PATH}{Article.PATH}/remove-tag", RouteType.asnc, action="POST")
@article_env
async def modal_remove_tag(env: Request, wiki: Wiki, user: Author, article: Article):
    tag = env.form.get("tag", None)
    article.remove_tag(tag)
    wiki.invalidate_cache()
    return Response(existing_tags(article))


@route("/quit", RouteType.sync_nothread)
def quit(*a):
    yield simple_response("You may now close this browser.")
    from models import db

    db.commit()
    db.close()
    import sys

    sys.exit()
