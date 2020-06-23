import datetime
import urllib

import commonmark

parser = commonmark.Parser()
renderer = commonmark.HtmlRenderer()

try:
    import regex as re
except ImportError:
    import re  # type: ignore
import datetime
import config
import os
from hashlib import blake2b

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, RowIDField, SearchField
from peewee import SQL

from settings import defaults

from pathlib import Path

db = SqliteExtDatabase(
    Path(config.DATA_PATH, "wiki.db"),
    pragmas=(("cache_size", -1024 * 64), ("journal_mode", "wal"), ("synchronous", 0)),
)

db.connect()

from playhouse.sqlite_ext import (
    Model,
    TextField,
    DateTimeField,
    ForeignKeyField,
    CharField,
    BooleanField,
    IntegerField,
)

from pixie_web import Unsafe

from html.parser import HTMLParser

ARTICLE_TIME_FORMAT = r"%Y-%m-%d %H:%m:%S"


class DocTagParser(HTMLParser):
    """
    Handles parsing for macro tags in documents.
    """

    def __init__(self, article):
        super().__init__()
        self.query = []
        self.results = []
        self.article = article

    def handle_starttag(self, tag, attrs):
        error = None
        if tag in ("documents", "articles", "items"):
            for k, v in attrs:
                if k == "tag":
                    try:
                        # TODO: this kind of construction happens often enough that we should probably make a special constructor
                        self.query = (
                            self.article.wiki.articles_tagged_with(v)
                            .where(
                                Article.draft_of.is_null(),
                                Article.revision_of.is_null(),
                            )
                            .order_by(SQL("title COLLATE NOCASE"))
                        )
                    except Exception:
                        error = v

            if not self.query:
                self.results.append(
                    f"<inline-error>[No such tag: {error}]</inline-error>"
                )
                return

            for __ in self.query:
                __.formatted
                blurb = __.get_metadata("@blurb")
                blurb = f" -- {blurb}" if blurb else ""
                self.results.append(f"* [[{__.title}]]{blurb}")

        elif tag == "meta":
            for k, v in attrs:
                v = Wiki.html_keysafe_to_title(v)
                if k in ("doc", "article", "item"):
                    try:
                        self.query = self.article.wiki.articles.where(
                            Article.title == v,
                            Article.draft_of.is_null(),
                            Article.revision_of.is_null(),
                        ).get()
                    except Article.DoesNotExist:
                        error = v
                        self.query = None
                elif k in ("key", "key_opt") and not error:
                    if not self.query:
                        self.query = self.article
                    try:
                        self.query = self.query.get_metadata(v)
                    except KeyError:
                        self.query = []
                        if k == "key":
                            error = v
                elif k == "pre":
                    if self.query:
                        self.query = v + self.query
                elif k == "post":
                    if self.query:
                        self.query += v

            if not self.query:
                if error:
                    self.results.append(
                        f"<inline-error>[No such document or tag: {error}]</inline-error>"
                    )
                return

            self.results.append(self.query)

        else:
            self.results.append(f"<inline-error>[No such macro: {tag}]</inline-error>")
            return

    def render(self):
        return "\n".join(self.results)


class BaseModel(Model):
    _config = config

    class ItemInUseError(Exception):
        pass

    class Meta:
        database = db

    @classmethod
    def title_to_html_keysafe(cls, title):
        return title.replace('"', "&quot;")

    @classmethod
    def html_keysafe_to_title(cls, title):
        return title.replace("&quot;", '"')

    @classmethod
    def title_to_url(cls, title):
        anchor = None
        if "#" in title:
            title, anchor = title.split("#", 1)
        title = title.replace(" ", "_")
        title = urllib.parse.quote(title)
        title = title.replace("/", r"%2f")
        if anchor:
            title = title + "#" + anchor
        return title

    @classmethod
    def url_to_title(cls, url):
        anchor = None
        if "#" in url:
            url, anchor = url.split("#", 1)
        title = url.replace(r"_", " ")
        title = urllib.parse.unquote(title)
        if anchor:
            title = title + "#" + anchor
        return title

    @classmethod
    def file_to_url(cls, url):
        title = urllib.parse.quote(url)
        return title

    @classmethod
    def url_to_file(cls, url):
        title = urllib.parse.unquote(url)
        return title

    @property
    def metadata(self):
        return Metadata.select().where(
            Metadata.item == self._meta.table_name, Metadata.item_id == self.id
        )

    @property
    def metadata_autogen(self):
        return self.metadata.where(Metadata.autogen == True)

    @property
    def metadata_not_autogen(self):
        return self.metadata.where(Metadata.autogen == False)

    def get_metadata(self, key=None):
        metadata = self.metadata.select()
        if key:
            try:
                value = metadata.where(Metadata.key == key).get().value
            except Metadata.DoesNotExist:
                return None
            else:
                return value
        return metadata

    def set_metadata(self, key, value):
        try:
            metadata_item = self.metadata.where(Metadata.key == key).get()
        except Metadata.DoesNotExist:
            metadata_item = Metadata(
                item=self._meta.table_name, item_id=self.id, key=key, value=value
            )
        else:
            metadata_item.value = value
        metadata_item.save()

    def delete_metadata(self, key):
        try:
            value = self.metadata.select().where(Metadata.key == key).get()
        except Metadata.DoesNotExist:
            return
        else:
            value.delete_instance()


class Wiki(BaseModel):
    title = TextField(index=True)
    description = TextField()

    _sidebar_cache: dict = {}
    article_cache: dict = {}

    PATH = "/wiki/<wiki_name>"
    METADATA = "wiki"

    export_mode = False

    def delete_(self):
        with db.transaction():

            Metadata.delete().where(
                Metadata.item == "wiki", Metadata.id == self.id,
            )

            for article in self.articles:
                article.delete_()

            for media in self.media:
                media.delete_()

            try:
                # os.remove(os.path.join(self.data_path, "cover.jpg"))
                Path(self.data_path, "cover.jpg").unlink()
            except:
                pass

            os.rmdir(self.data_path)

            self.delete_instance()

    @property
    def sidebar_cache(self):
        return Wiki._sidebar_cache.get(self.id, None)

    def invalidate_cache(self):
        try:
            del Wiki._sidebar_cache[self.id]
        except KeyError:
            pass
        Wiki.article_cache = {}

    @classmethod
    def new_wiki(cls, title, description, author, first_wiki=False, empty=False):
        """
        Create a new wiki with the provided title, description, and author.
        """

        # TODO: perform name collision checks here?

        new_wiki = cls(title=title, description=description)
        new_wiki.save()

        Path(cls._config.DATA_PATH, str(new_wiki.id)).mkdir()

        if first_wiki:
            from init_data import wiki_init

            for title, article in wiki_init.items():
                new_article = Article(
                    title=title,
                    content=article["content"],
                    author=author,
                    wiki=new_wiki,
                )
                new_article.save()
                for tag in article["tags"]:
                    new_article.add_tag(tag)
                new_article.update_index()
                new_article.update_links()
                new_article.update_autogen_metadata()

        else:
            if not empty:
                new_article = Article.default(new_wiki, author)
                new_article.save()

                new_article.add_tag("@template")
                new_article.update_index()
                new_article.update_links()
                new_article.update_autogen_metadata()

        return new_wiki

    def article_exists(self, title):
        """
        Confirm if an article with the same title exists in this wiki.
        """
        try:
            article = self.articles.select().where(Article.title == title).get()
        except Article.DoesNotExist:
            return False
        return True

    def tag_exists(self, tag):
        """
        Confirm if a tag with the given name exists in this wiki.
        """
        try:
            self.tags.select().where(Tag.title == tag).get()
        except Tag.DoesNotExist:
            return False
        return True

    def has_name_collision(self):
        """
        Make sure there is no other wiki with the same name.
        """
        try:
            same_title = (
                Wiki.select().where(Wiki.title == self.title, Wiki.id != self.id).get()
            )
        except Wiki.DoesNotExist:
            return False
        return True

    def remove_wiki(self):
        pass

    @property
    def static_folder_link(self):
        if Wiki.export_mode:
            return f"../static"
        return "/static"

    @property
    def link(self):
        if Wiki.export_mode:
            return f".."
        return f"/wiki/{self.title_to_url(self.title)}"

    @property
    def homepage_link(self):
        if Wiki.export_mode:
            return f"{self.article_root_link}/Contents.html"
        return self.link

    @property
    def server_homepage_link(self):
        if Wiki.export_mode:
            return f"{self.article_root_link}/Contents.html"
        return "/"

    @property
    def article_root_link(self):
        if Wiki.export_mode:
            return "../article"
        return f"{self.link}/article"

    @property
    def tag_root_link(self):
        if Wiki.export_mode:
            return "../tag"
        return f"{self.link}/tag"        

    @property
    def delete_key(self):
        h = blake2b(key=b"key1", digest_size=16)
        h.update(bytes(self.title, "utf8"))
        return h.hexdigest()

    @property
    def delete_link(self):
        return f"{self.link}/delete"

    @property
    def delete_confirm_link(self):
        return f"{self.delete_link}/{self.delete_key}"

    def recent_articles(self):
        return (
            self.articles.where(Article.revision_of.is_null())
            .order_by(Article.last_edited.desc())
            .limit(50)
        )

    @property
    def new_page_link(self):
        return f"{self.link}/new"

    @property
    def edit_link(self):
        return f"{self.link}/edit"

    @property
    def search_link(self):
        return f"{self.link}/search"

    @property
    def upload_link(self):
        return f"{self.link}/upload"

    @property
    def media_link(self):
        return f"{self.link}/media"

    @property
    def media_paste_link(self):
        return f"{self.link}/media-paste"

    @classmethod
    def default(cls):
        return cls(
            title="Untitled Wiki", description="Replace this with your description."
        )

    @property
    def main_article(self):
        return self.articles.where(Article.title == "Contents").get()

    @property
    def data_path(self):
        return str(Path(config.DATA_PATH, str(self.id)))

    @property
    def cover_img(self):
        cover_img_id = self.get_metadata("cover_img")
        if not cover_img_id:
            return f"{self.static_folder_link}/default_cover.jpg"
        return Media.get(Media.id == cover_img_id).link

    @property
    def last_edited(self):
        return self.recent_articles()[0].last_edited.strftime(ARTICLE_TIME_FORMAT)

    def articles_tagged_with(self, tag):
        try:
            tag_q = Tag.get(Tag.title == tag, Tag.wiki == self)
            tag_assoc = TagAssociation.select(TagAssociation.article).where(
                TagAssociation.tag == tag_q
            )
            return self.articles.where(Article.id << tag_assoc).order_by(
                Article.title.asc()
            )
        except Tag.DoesNotExist:
            return []

    @property
    def articles_alpha(self):
        return self.articles.order_by(SQL("title COLLATE NOCASE"))

    @property
    def tags_alpha(self):
        return self.tags.order_by(SQL("title COLLATE NOCASE"))

    @property
    def media_alpha(self):
        return self.media.order_by(SQL("file_path COLLATE NOCASE"))

    @property
    def articles_main_only(self):
        return self.articles_alpha.where(Article.revision_of.is_null())

    @property
    def articles_nondraft_only(self):
        return self.articles_main_only.where(Article.draft_of.is_null())

    @property
    def articles_draft_only(self):
        return self.articles_main_only.where(~Article.draft_of.is_null())

    @property
    def template(self):
        template_articles = []

        articles = self.articles_tagged_with("@template")
        if articles:
            template_articles = articles.where(
                Article.revision_of.is_null(), Article.draft_of.is_null()
            )

        return template_articles


class Author(BaseModel):
    name = TextField()

    @classmethod
    def default(cls):
        return cls(name="Admin")


class Article(BaseModel):

    wiki = ForeignKeyField(Wiki, backref="articles")
    title = TextField(index=True)
    content = TextField(null=True)
    rendered_content = TextField(null=True)
    author = ForeignKeyField(Author, backref="articles")
    created = DateTimeField(default=datetime.datetime.now)
    last_edited = DateTimeField(default=datetime.datetime.now, index=True)
    content_type = TextField(default="text/markdown", index=True)
    opened_by = ForeignKeyField(Author, backref="opened_articles", null=True)
    draft_of = ForeignKeyField("self", null=True, backref="drafts")
    revision_of = ForeignKeyField("self", null=True, backref="revisions")
    new_title = TextField(null=True)

    PATH = "/article/<title>"

    # HTML not handled by Markdown directly
    checkbox_re = re.compile(r"\[([xX_ ])\]")
    strike_re = re.compile(r"\~\~(.*?)\~\~")

    # Folio custom functions: inline
    link_re = re.compile(r"\[\[(.*?)\]\]")
    wikilink_re = re.compile(r"\[\[(.*?)\]\](?:\((.*?)\))?")    
    literal_include_re = re.compile(r"\{\{\{(.*?)\}\}\}")
    include_re = re.compile(r"\{\{(.*?)\}\}")
    function_re = re.compile(r"\<\<[^>]*?\>\>")
    blurb_re = re.compile(r"\<\<\<(.*?)\>\>\>")
    media_re = re.compile(r"!\[([^\]]*?)\]\(([^)]*?)\)")
    
    # Folio custom functions: block
    metadata_re = re.compile(
        r"(\$\[(.*?)\]\$)+(\(([^)]*?)\))?", re.MULTILINE | re.DOTALL
    )
    metadata_cleared_re = re.compile(
        r"(\$\$\[(.*?)\]\$\$)+(\(([^)]*?)\))?", re.MULTILINE | re.DOTALL
    )
    metadata_all_re = re.compile(
        r"(\${1,2}\[(.*?)\]\${1,2})+(\(([^)]*?)\))?", re.MULTILINE | re.DOTALL
    )

    # Everything else
    href_re = re.compile(r'(<a .*?)href="([^"]*?)"([^>]*?>)')
    
    # Not deleting these yet as they may be useful later
    # linkh_re = re.compile(r'(<link .*?)href="([^"]*?)"([^>]*?>)')
    # imgtag_re = re.compile(r'(<img .*?)src="([^"]*?)"([^>]*?>)')
    # script_re = re.compile(r'(<script .*?)src="([^"]*?)"([^>]*?>)')

    literal_block_re = re.compile(r"(```)")
    literal_inline_re = re.compile(r"(`)")

    def make_revision(self):
        revision = Article(
            wiki=self.wiki,
            title=self.title,
            content=self.content,
            author=self.author,
            created=self.created,
            revision_of=self,
        )
        revision.save()
        revision.update_links()
        revision.update_autogen_metadata()
        revision.copy_metadata_from(self)
        revision.copy_tags_from(self)

        return revision

    def replace_text(self, re_to_find, new_text):
        if self.opened_by:
            raise self.ItemInUseError()

        self.content = re_to_find.sub(new_text, self.content)
        self.save()

    @property
    def id_link(self):
        return f"{self.revision_of.link}/revision/{self.id}"

    def copy_metadata_from(self, other):
        for metadata in other.metadata_not_autogen:
            self.set_metadata(metadata.key, metadata.value)

    def clear_index(self):
        ArticleIndex.delete().where(ArticleIndex.rowid == self.id).execute()

    def update_index(self):
        self.clear_index()
        ArticleIndex(rowid=self.id, content=self.content).save()

    def form_creation_link(self, form):
        return f"{self.wiki.link}/new_from_form/{self.title_to_url(form.title)}"

    def make_from_form(self, new_title):
        new_form_article = Article(
            title=new_title, content=self.content, author=self.author, wiki=self.wiki
        )
        new_form_article.save()

        for tag in self.tags:
            if tag.tag.title not in ("@form", "@template"):
                new_form_article.add_tag(tag.tag.title)

        for metadata in self.metadata_not_autogen:
            new_form_article.set_metadata(metadata.key, metadata.value)

        new_form_article.update_index()
        new_form_article.update_links()
        new_form_article.update_autogen_metadata()
        new_form_article.wiki.invalidate_cache()

        return new_form_article

    def update_autogen_metadata(self):
        if getattr(self, "autogen_metadata", None) is None:
            _ = self.formatted
        for _ in self.metadata.where(Metadata.autogen == True):
            _.delete_instance()
        for key, value in self.autogen_metadata:
            new_metadata = Metadata(
                item="article", item_id=self.id, key=key, value=value, autogen=True
            )
            new_metadata.save()

    @property
    def tags_alpha(self):
        t1 = self.tags.select(TagAssociation.tag)
        return Tag.select().where(Tag.id << t1).order_by(SQL("title COLLATE NOCASE"))

    def has_tag(self, tag_name):
        try:
            return self.tags_alpha.where(Tag.title == tag_name).get()
        except Tag.DoesNotExist:
            return None

    def add_tag(self, tag_title):
        try:
            tag_to_add = self.wiki.tags.where(Tag.title == tag_title).get()
        except Tag.DoesNotExist:
            tag_to_add = Tag(title=tag_title, wiki=self.wiki)
            tag_to_add.save()
        try:
            tag_association = (
                TagAssociation.select()
                .where(TagAssociation.tag == tag_to_add, TagAssociation.article == self)
                .get()
            )
        except TagAssociation.DoesNotExist:
            tag_association = TagAssociation(tag=tag_to_add, article=self)
            tag_association.save()
        return tag_association

    def remove_tag(self, tag_title):
        try:
            tag_to_remove = self.wiki.tags.where(Tag.title == tag_title).get()
        except Tag.DoesNotExist:
            return False
        try:
            tag_assoc_to_remove = self.tags.where(
                TagAssociation.tag == tag_to_remove
            ).get()
        except TagAssociation.DoesNotExist:
            return False

        tag_assoc_to_remove.delete_instance()

        for _ in Tag.orphans():
            _.delete_instance()

        return True

    def has_name_collision(self):
        """
        Make sure there is no other article with the same name in this article's wiki.
        """
        try:
            same_title = self.wiki.articles.where(
                Article.title == self.title, Article.id != self.id
            ).get()
        except Article.DoesNotExist:
            return False
        return True

    def has_new_name_collision(self):
        """
        Make sure there is no other article with the same name in this article's wiki.
        """
        try:
            same_title = self.wiki.articles.where(
                Article.title == self.new_title,
                Article.id != self.draft_of.id,
                Article.id != self.id,
            ).get()
        except Article.DoesNotExist:
            return False
        return True

    @property
    def exists_as_tag(self):
        try:
            tag = self.wiki.tags.where(Tag.title == self.title).get()
        except Tag.DoesNotExist:
            return None
        else:
            return tag

    @classmethod
    def default(cls, wiki, author):
        return cls(
            wiki=wiki,
            title="Contents",
            content="""$[This is the first article in your new wiki. By default it is named **Contents**.]$""",
            author=author,
        )

    @property
    def revisions_chrono(self):
        return self.revisions.order_by(Article.last_edited.desc())

    @property
    def short_date(self):
        return self.last_edited.strftime(r"%Y-%m-%d")

    @property
    def formatted_date(self):
        return self.last_edited.strftime(r"%Y-%m-%d %H:%M:%S")

    @classmethod
    def get_by_title(cls, title):
        # FIXME
        title = urllib.parse.unquote(title)
        return cls.get(cls.title == title)

    def exists(self, title):
        return Article.get(Article.title == title, Article.wiki == self.wiki)

    @property
    def link(self):
        if Wiki.export_mode:
            article_title = self.title_to_url(self.title).replace("%", "%25")
            return f"{self.wiki.article_root_link}/{article_title}.html"
        return f"{self.wiki.article_root_link}/{self.title_to_url(self.title)}"

    @property
    def edit_link(self):
        return f"{self.link}/edit"

    @property
    def history_link(self):
        return f"{self.link}/history"

    @property
    def delete_link(self):
        if self.draft_of:
            article = self.draft_of
        else:
            article = self
        return f"{article.link}/delete"

    @property
    def delete_confirm_link(self):
        return f"{self.link}/delete/{self.delete_key}"

    @property
    def discard_draft_link(self):
        return f"{self.link}/discard-draft"

    @property
    def discard_draft_confirm_link(self):
        return f"{self.link}/discard-draft/{self.delete_key}"

    @property
    def delete_key(self):
        # FIXME: use a sitewide key
        h = blake2b(key=b"key1", digest_size=16)
        h.update(bytes(self.title, "utf8"))
        return h.hexdigest()

    def delete_(self):
        with db.atomic():
            self.clear_index()
            self.clear_metadata()
            self.clear_tags()
            self.clear_links()
            self.delete_instance(recursive=True)

    def clear_metadata(self):
        for _ in self.metadata:
            _.delete_instance()

    def clear_tags(self):
        for tag in self.tags:
            tag.delete_instance()

        for _ in Tag.orphans():
            _.delete_instance()

    def copy_tags_from(self, other):
        for tag_assoc in other.tags:
            self.add_tag(tag_assoc.tag.title)

    def clear_links(self):
        ArticleLinks.delete().where(ArticleLinks.article == self).execute()
        MediaLinks.delete().where(MediaLinks.article == self).execute()

    def update_links(self):
        article_link_path = self.wiki.article_root_link
        self.clear_links()

        for _ in self.href_re.finditer(self.formatted):
            link_item = _.group(2)
            if link_item.startswith(article_link_path):
                link_extracted = Wiki.url_to_title(link_item.rsplit("/", 1)[1])
                new_link = ArticleLinks(article=self)
                if self.wiki.article_exists(link_extracted):
                    new_link.valid_link = (
                        Article.select(Article.id)
                        .where(
                            Article.title == link_extracted, Article.wiki == self.wiki
                        )
                        .get()
                    )
                else:
                    new_link.link = link_extracted
                new_link.save()

        for _ in self.media_re.finditer(self.content):
            try:
                media = Media.get(
                    Media.wiki == self.wiki, Media.file_path == _.group(2)
                )
            except Media.DoesNotExist:
                continue

            new_link = MediaLinks(media=media, article=self)

            new_link.save()

    @property
    def formatted(self):
        return self._formatted(self.content)

    def _function_re(self, matchobj):
        query_iter = []
        tag = matchobj.group(0)[1:-1]
        parser = DocTagParser(self)
        parser.feed(tag)
        return parser.render()

    def _article_re(self, matchobj):
        return f"({self.wiki.article_root_link}/{matchobj.group(1)})"

    def _media_re(self, matchobj):
        url = matchobj.group(2)
        if not url.startswith(("http://", "https://")):
            url = f"{self.wiki.link}/media/{self.wiki.file_to_url(url)}"
        return f"![{matchobj.group(1)}]({url})"

    def _href_re(self, matchobj):
        link = matchobj.group(2)
        target = ""
        export_mode_extension = ".html" if Wiki.export_mode else ""

        # Article-internal anchors are a special case
        if link.startswith("#"):
            link_title = link
            link_test = link
            link_class = "wiki-link"
            link_to_render = link
            valid_title = link
        elif link.startswith(f"{self.wiki.article_root_link}/"):
            link_to_find = link.split(f"{self.wiki.article_root_link}/")[1]
            link_to_render = link
            link_to_find = self.url_to_title(link_to_find)
            link_test = self.wiki.article_exists(link_to_find)
            link_class = "wiki-link"
            valid_title = link_to_find
        elif link.startswith(f"{self.wiki.link}/new_from_form/"):
            link_to_find = link.split(f"{self.wiki.link}/new_from_form/")[1]
            link_to_render = link
            link_class = "wiki-link"
            link_with_opt_name = link_to_find.split("/", 1)
            if len(link_with_opt_name) > 1:
                link_to_find = self.url_to_title(link_with_opt_name[0])
            else:
                link_to_find = self.url_to_title(link_to_find)
            link_test = self.wiki.article_exists(link_to_find)
            valid_title = link_to_find
        elif link.startswith(f"{self.wiki.tag_root_link}"):
            link_to_find = link.split(f"/tag/")[1]
            link_to_render = f"{self.wiki.tag_root_link}/{link_to_find}"
            link_to_find = self.url_to_title(link_to_find)
            link_test = self.wiki.tag_exists(link_to_find)
            valid_title = link_to_find
            link_class = "wiki-tag-link"
        else:
            link_to_show = self.title_to_url(link)
            link_to_render = f"{self.wiki.article_root_link}/{link_to_show}"
            link_test = self.wiki.article_exists(link)
            link_class = "wiki-link"
            valid_title = link

        if link_test:
            link_title = valid_title
        else:
            link_class = "wiki-missing-link"
            link_title = f"{link} (nonexistent article)"

        if link.startswith(("http://", "https://")):
            link_class = "wiki-external-link"
            link_title = link
            link_to_render = link
            target = ' target="_blank"'

        if Wiki.export_mode:
            link_to_render = link_to_render.replace("%", "%25")

        link_title = link_title.replace('"', r"\"")

        return f'{matchobj.group(1)}title="{link_title}" class="{link_class}" href="{link_to_render}{export_mode_extension}"{target}{matchobj.group(3)}'

    def _include_re(self, matchobj):
        replace = matchobj.group(0)
        include = matchobj.group(1)
        try:
            article = Article.get(Article.title == include, Article.wiki == self.wiki)
        except Article.DoesNotExist:
            return (
                f"<inline-error>[No such article to include: {include}]</inline-error>"
            )
        return article.content

    def _wikilink_bare_re(self, matchobj):
        return self._wikilink_re(matchobj, False)

    def _wikilink_re(self, matchobj, use_name=True):
        source_name = matchobj.group(1)
        source_link = matchobj.group(2)
        
        if not source_link:
            if use_name:
                return matchobj[0]
            else:
                source_link = matchobj.group(1)
            
        if source_link.startswith("/tag/"):
            newlink = source_link.split("/tag/",1)[1]
            newlink = f"{self.wiki.tag_root_link}/{self.title_to_url(newlink)}"
        else:
            newlink = f"{self.wiki.article_root_link}/{self.title_to_url(source_link)}"

        final_link = f"[{source_name}]({newlink})"

        return final_link
        

    def _blurb_re(self, matchobj):
        Wiki.title_to_url
        return f'[[{matchobj.group(1)}]]<<meta doc="{Wiki.title_to_html_keysafe(matchobj.group(1))}" key_opt="@blurb" pre=" -- ">>'

    def _strike_re(self, matchobj):
        return f"<strike>{matchobj.group(1)}</strike>"

    def _metadata_re(self, matchobj, cleared=False):
        append = matchobj.group(4) if matchobj.group(4) else "@blurb"
        self.autogen_metadata.append((append, matchobj.group(2)))
        return "" if cleared else matchobj.group(2)

    def _metadata_cleared_re(self, matchobj):
        return self._metadata_re(matchobj, True)

    def _format_table(self, content):
        table_fmt = []
        is_table = False
        header_row = None
        md_mini = None
        dummy = None

        for _ in content.splitlines(True):
            if _.startswith("|"):
                if not is_table:
                    is_table = True
                    dummy = Article(
                        title="", content="", author=self.author, wiki=self.wiki
                    )
                    if _.startswith("|!"):
                        header_row = True
                        _ = "|" + _[2:]
                    table_fmt.append(
                        '<table class="table table-striped table-bordered table-hover table-sm">'
                    )
                    if header_row:
                        table_fmt.append('<thead class="thead-light">')
                    else:
                        table_fmt.append("<tbody>")
            else:
                if is_table:
                    is_table = False
                    table_fmt.append("</tbody></table>\n\n")
                table_fmt.append(_)
                continue

            if is_table:
                if header_row:
                    col_type = "th"
                else:
                    col_type = "td"
                line = _.split("|")[1:-1]
                table_line = "".join(
                    ["<tr>"]
                    + [
                        f"<{col_type}>{dummy._formatted(cell)[3:-5]}</{col_type}>"
                        for cell in line
                    ]
                    + ["</tr>"]
                )
                table_fmt.append(table_line)
                if header_row:
                    table_fmt.append("</thead><tbody>")
                    header_row = None
                    md_mini = None
            else:
                table_fmt.append(_)

        if is_table:
            is_table = False
            table_fmt.append("</tbody></table>\n\n")

        content = "".join(table_fmt)

        return content

    def _checkbox_re(self, matchobj):
        if matchobj.group(1) not in " _":
            return '<input type="checkbox" disabled checked />'
        return '<input type="checkbox" disabled/>'

    def _content_regions(self, raw_content, fn):
        preformat_content = self.literal_block_re.split(raw_content)
        skip = False

        for index, region in enumerate(preformat_content):
            if self.literal_block_re.match(region):
                skip = not skip
            if skip:
                continue

            inlines = self.literal_inline_re.split(region)
            inline_skip = False

            for inline_index, inline in enumerate(inlines):
                if self.literal_inline_re.match(inline):
                    inline_skip = not inline_skip
                if inline_skip:
                    continue

                inline = fn(inline)

                inlines[inline_index] = inline

            region = "".join(inlines)

            preformat_content[index] = region

        raw_content = "".join(preformat_content)

        return raw_content

    def _inline_format(self, inline):
        inline = self.include_re.sub(self._include_re, inline)
        inline = self.metadata_cleared_re.sub(self._metadata_cleared_re, inline)
        inline = self.metadata_re.sub(self._metadata_re, inline)
        inline = self.blurb_re.sub(self._blurb_re, inline)
        inline = self.function_re.sub(self._function_re, inline)
        inline = self._format_table(inline)
        inline = self.wikilink_re.sub(self._wikilink_re, inline)
        inline = self.wikilink_re.sub(self._wikilink_bare_re, inline)
        inline = self.media_re.sub(self._media_re, inline)
        inline = self.strike_re.sub(self._strike_re, inline)
        inline = self.checkbox_re.sub(self._checkbox_re, inline)
        return inline

    def _formatted(self, raw_content):

        self.autogen_metadata = []

        raw_content = self._content_regions(raw_content, self._inline_format)

        ast = parser.parse(raw_content)
        html = renderer.render(ast)

        html = self.href_re.sub(self._href_re, html)
        html = html.replace("<img ", '<img class="img-fluid" ')

        return html

    def rename_inbound_links(self, old_name, new_name):
        """
        - get all articles that link to this one
        - iterate through each's regions
        - replace matching links
        """


class Metadata(BaseModel):
    item = CharField(index=True, null=False)
    item_id = IntegerField(index=True, null=False)
    key = CharField(index=True)
    value = TextField()
    autogen = BooleanField(default=False)


class Tag(BaseModel):
    title = TextField()
    wiki = ForeignKeyField(Wiki, backref="tags")

    @property
    def link(self):
        return f"{self.wiki.tag_root_link}/{self.title}"

    @property
    def as_article(self):
        return Article(title=self.title, wiki=self.wiki, author=Author(""))

    @property
    def article_exists(self):
        try:
            article = self.wiki.articles.where(Article.title == self.title).get()
        except Article.DoesNotExist:
            return None
        else:
            return article

    @classmethod
    def orphans(cls):
        return cls.select().where(
            cls.id.not_in(TagAssociation.select(TagAssociation.tag))
        )


class TagAssociation(BaseModel):
    tag = ForeignKeyField(Tag, backref="articles")
    article = ForeignKeyField(Article, backref="tags")


class ArticleLinks(BaseModel):
    article = ForeignKeyField(Article, backref="ext_links")
    valid_link = ForeignKeyField(Article, backref="linked_from", null=True)
    link = TextField(null=True)


class Media(BaseModel):
    wiki = ForeignKeyField(Wiki, backref="media")
    file_path = TextField()
    description = TextField(null=True)
    date_uploaded = DateTimeField(default=datetime.datetime.now)

    @classmethod
    def exists(cls, file_path, wiki):
        try:
            cls.select().where(cls.file_path == file_path, cls.wiki == wiki).get()
        except cls.DoesNotExist:
            return False
        return True

    @property
    def in_articles(self):
        return self.article_refs.select(MediaLinks.article)

    @property
    def link(self):
        return f"{self.wiki.link}/media/{self.file_to_url(self.file_path)}"

    @property
    def file_path_(self):
        return str(Path(self.wiki.data_path, self.file_path))

    @property
    def edit_link(self):
        return f"{self.link}/edit"

    @property
    def delete_link(self):
        return f"{self.link}/delete"

    @property
    def delete_confirm_link(self):
        return f"{self.delete_link}/{self.delete_key}"

    @property
    def delete_key(self):
        h = blake2b(key=b"key1", digest_size=16)
        h.update(bytes(self.file_path, "utf8"))
        return h.hexdigest()

    def delete_(self):
        os.remove(self.file_path_)
        self.delete_instance()

    def rename_inbound_links(self, old_name, new_name):
        """
        - get all articles that link to this
        - iterate through each's regions
        - replace matching links
        """

class MediaLinks(BaseModel):
    media = ForeignKeyField(Media, backref="article_refs")
    article = ForeignKeyField(Article, backref="media_refs")


class ArticleIndex(FTSModel):
    rowid = RowIDField()
    content = SearchField()

    class Meta:
        database = db
        options = {"content": Article.content}


System = Wiki()
System.id = 0


def create_db():
    all_tables = [_ for _ in BaseModel.__subclasses__()] + [
        _ for _ in FTSModel.__subclasses__()
    ]
    db.drop_tables(all_tables)
    db.create_tables(all_tables)

    new_admin = Author.default()
    new_admin.save()

    from settings import DB_SCHEMA

    metadata = System.set_metadata("schema", DB_SCHEMA)

    Wiki.new_wiki(
        "Welcome to Folio",
        "Introduction and documentation for your personal wiki.",
        new_admin,
        first_wiki=True,
    )

    ArticleIndex.rebuild()
    ArticleIndex.optimize()
