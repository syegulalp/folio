from bottle import template, error, request, redirect

from models import Article, Wiki, Author, Media, Tag, TagAssociation

from utils import Error, Unsafe

from math import ceil
from urllib.parse import urlencode
import time

blank_wiki = Wiki()

default_headers = {
    "Expires": "-1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache, no-store, must-revalidate",
}


class LocalException(Exception):
    pass


def get_user() -> Author:
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


@error(404)
def error_404(error):
    return home_page_render([Error(f"Page or wiki not found: {Unsafe(request.path)}")])


def home_page_render(wikis=None, messages=[]):
    return template(
        "home.tpl",
        wikis=wikis,
        articles=(
            Article.select()
            .where(
                Article.draft_of.is_null(),
                Article.revision_of.is_null(),
            )
            .order_by(Article.last_edited.desc())
            .limit(25)
        ),
        page_title="Folio (Homepage)",
        messages=messages,
        wiki=blank_wiki,
    )


items_on_page = 12


def paginator(media: Media):
    search = request.params.get("search")
    if search == "":
        search = None
    if search:
        media = media.where(Media.file_path.contains(search))
    else:
        search = ""

    page = int(request.params.get("p", 1))

    last = ceil(media.count() / items_on_page)

    if page == -1 or page > last:
        page = last

    previous_page = max(page - 1, 1)
    next_page = min(page + 1, last)

    media = media.paginate(page, items_on_page)

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
            if not Wiki.export_mode:
                return redirect(article.link)

    if article.id is None:
        try:
            tagged_as_form = wiki.articles_tagged_with("@form")
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
        style=wiki.stylesheet(),
    )

    if article.id:
        Wiki.article_cache[article.id] = result

    return result
