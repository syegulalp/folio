import datetime
import urllib
import markdown

try:
    import regex as re
except ImportError:
    import re
import datetime
import config
import os
from hashlib import blake2b

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, RowIDField, SearchField
from peewee import SQL

from settings import defaults

db = SqliteExtDatabase(
    os.path.join(config.DATA_PATH, "wiki.db"),
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
                        self.query = self.article.wiki.articles_tagged_with(v).order_by(
                            SQL("title COLLATE NOCASE")
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
                blurb = __.get_metadata("blurb")
                blurb = f" -- {blurb}" if blurb else ""
                self.results.append(f"* [[{__.title}]]{blurb}")

        elif tag == "meta":
            for k, v in attrs:
                if k in ("doc", "article", "item"):
                    try:
                        self.query = self.article.wiki.articles.where(
                            Article.title == v
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

    class Meta:
        database = db

    @classmethod
    def title_to_url(cls, title):
        title = title.replace(" ", "_")
        title = urllib.parse.quote(title)
        title = title.replace("/", r"%2f")
        return title

    @classmethod
    def url_to_title(cls, url):
        title = url.replace(r"_", " ")
        title = urllib.parse.unquote(title)
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
                item=self._meta.table_name, item_id=self.id, key=key
            )
            metadata_item.save()
        metadata_item.value = value
        metadata_item.save()


class Wiki(BaseModel):
    title = TextField(index=True)
    description = TextField()

    _sidebar_cache: dict = {}
    article_cache: dict = {}

    PATH = "/wiki/<wiki_name>"
    METADATA = "wiki"

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
                os.remove(os.path.join(self.data_path, "cover.jpg"))
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

    def setting(self, key):
        try:
            return self.metadata.where(Metadata.key == key).get().value
        except Metadata.DoesNotExist:
            if key not in defaults:
                return None
            return defaults[key]

    @property
    def settings(self):
        return self.metadata.where(Metadata.key << list(defaults.keys()))

    @classmethod
    def new_wiki(cls, title, description, author, first_wiki=False):
        """
        Create a new wiki with the provided title, description, and author.
        """

        # TODO: perform name collision checks here?

        new_wiki = cls(title=title, description=description)
        new_wiki.save()

        os.mkdir(os.path.join(cls._config.DATA_PATH, str(new_wiki.id)))

        if first_wiki:
            from utils import wiki_init

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
            new_article = Article.default(new_wiki, author)
            new_article.save()

            new_article.add_tag("@meta")
            new_article.update_index()
            new_article.update_links()
            new_article.update_autogen_metadata()

        return new_wiki

    def article_exists(self, title):
        """
        Confirm if an article with the same title exists in this wiki.
        """
        try:
            self.articles.select().where(Article.title == title).get()
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
    def link(self):
        return f"/wiki/{self.title_to_url(self.title)}"

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
        return os.path.join(config.DATA_PATH, str(self.id))

    @property
    def cover_img(self):
        cover_img_file = self.setting("Cover image")
        img_path = os.path.join(self.data_path, cover_img_file)
        if os.path.exists(img_path):
            return f"{self.link}/media/{cover_img_file}"
        return f"/static/default_cover.jpg"

    @property
    def last_edited(self):
        return self.recent_articles()[0].last_edited.strftime(ARTICLE_TIME_FORMAT)

    def articles_tagged_with(self, tag):
        tag_q = Tag.get(Tag.title == tag, Tag.wiki == self)
        tag_assoc = TagAssociation.select(TagAssociation.article).where(
            TagAssociation.tag == tag_q
        )
        return self.articles.where(Article.id << tag_assoc).order_by(
            Article.title.asc()
        )

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
    revision_of = ForeignKeyField("self", null=True, backref="edits")
    new_title = TextField(null=True)

    PATH = "/article/<title>"

    checkbox_re = re.compile(r"\[([xX_ ])\]")
    link_re = re.compile(r"\[\[([^]]*?)\]\]")
    literal_include_re = re.compile(r"\{\{\{([^}]*?)\}\}\}")
    include_re = re.compile(r"\{\{([^}]*?)\}\}")
    function_re = re.compile(r"\<\<[^>]*?\>\>")
    href_re = re.compile(r'(<a .*?)href="([^"]*?)"([^>]*?>)')
    blurb_re = re.compile(r"\<\<\<([^>]*?)\>\>\>")
    media_re = re.compile("!\[([^\]]*?)\]\(([^)]*?)\)")
    strike_re = re.compile(r"\~\~(.*?)\~\~")
    metadata_re = re.compile(r"\$\[(.*?)\]\$\(([^)]*?)\)", re.MULTILINE | re.DOTALL)
    blurb_inline_re = re.compile(r"\$\[(.*?)\]\$", re.MULTILINE | re.DOTALL)

    def clear_metadata(self):
        for metadata in self.metadata_not_autogen:
            metadata.delete_instance()
   
    def copy_metadata_from(self, other):
        for metadata in other.metadata_not_autogen:
            self.set_metadata(metadata.key, metadata.value)

    def clear_index(self):
        ArticleIndex.delete().where(ArticleIndex.rowid == self.id).execute()

    def update_index(self):
        self.clear_index()
        ArticleIndex(rowid=self.id, content=self.content).save()

    def template_creation_link(self, template):
        return f"{self.wiki.link}/new_from_template/{self.title_to_url(template.title)}"

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
    def edits_chrono(self):
        return self.edits.order_by(Article.last_edited.desc())

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
        return f"{self.wiki.link}/article/{self.title_to_url(self.title)}"

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

    def update_links(self):
        article_link_path = f"{self.wiki.link}/article/"
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

    def get_metadata_old(self):
        """
        Extracts only the RAW metadata from an article.
        """
        md = markdown.Markdown(extensions=["markdown.extensions.meta"])
        # content = self.content.split("\n\n")[0]
        md.convert(self.content)
        return md.Meta

    @property
    def formatted(self):
        # content, metadata = self._formatted(self.content)
        # self.metadata = metadata
        # return content
        return self._formatted(self.content)

    def _function_re(self, matchobj):
        query_iter = []
        tag = matchobj.group(0)[1:-1]
        parser = DocTagParser(self)
        parser.feed(tag)
        return parser.render()

    def _article_re(self, matchobj):
        return f"({self.wiki.link}/article/{matchobj.group(1)})"

    def _media_re(self, matchobj):
        url = matchobj.group(2)
        if not url.startswith(("http://", "https://")):
            url = f"{self.wiki.link}/media/{url}"
        return f"![{matchobj.group(1)}]({url})"

    def _href_re(self, matchobj):
        link = matchobj.group(2)
        target = ""

        if link.startswith(f"{self.wiki.link}/article/"):
            link_to_find = link.split(f"{self.wiki.link}/article/")[1]
            link_to_render = link
            link_to_find = self.url_to_title(link_to_find)
            link_test = self.wiki.article_exists(link_to_find)
            link_class = "wiki-link"
        elif link.startswith(f"/tag/"):
            link_to_find = link.split(f"/tag/")[1]
            link_to_render = f"{self.wiki.link}/tag/{link_to_find}"
            link_to_find = self.url_to_title(link_to_find)
            link_test = self.wiki.tag_exists(link_to_find)
            link_class = "wiki-tag-link"
        else:
            link_to_show = self.title_to_url(link)
            link_to_render = f"{self.wiki.link}/article/{link_to_show}"
            link_test = self.wiki.article_exists(link)
            link_class = "wiki-link"

        if link_test:
            link_title = link
        else:
            link_class = "wiki-missing-link"
            link_title = f"{link} (nonexistent article)"

        if link.startswith(("http://", "https://")):
            link_class = "wiki-external-link"
            link_title = link
            link_to_render = link
            target = ' target="_blank"'

        return f'{matchobj.group(1)}title="{Unsafe(link_title)}" class="{link_class}" href="{link_to_render}"{target}{matchobj.group(3)}'

    def _include_re(self, matchobj):
        replace = matchobj.group(0)
        include = matchobj.group(1)
        try:
            article = Article.get(Article.title == include, Article.wiki == self.wiki)
        except Article.DoesNotExist:
            return (
                f"<inline-error>[No such article to include: {include}]</inline-error>"
            )
        return article.formatted

    def _literal_include_re(self, matchobj):
        replace = matchobj.group(0)
        include = matchobj.group(1)
        try:
            article = Article.get(Article.title == include, Article.wiki == self.wiki)
        except Article.DoesNotExist:
            return (
                f"<inline-error>[No such article to include: {include}]</inline-error>"
            )
        return article.content

    def _link_re(self, matchobj):
        link = matchobj.group(1)
        if link.startswith(("http://", "https://")):
            newlink = link
        elif link.startswith("/tag/"):
            link = link.split("/tag/", 1)[1]
            newlink = f"/tag/{self.title_to_url(link)}"
        else:
            newlink = f"{self.wiki.link}/article/{self.title_to_url(link)}"
        return f"[{link}]({newlink})"

    def _blurb_re(self, matchobj):
        return f'[[{matchobj.group(1)}]]<<meta doc="{matchobj.group(1)}" key_opt="blurb" pre=" -- ">>'

    def _strike_re(self, matchobj):
        return f"<strike>{matchobj.group(1)}</strike>"

    def _metadata_re(self, matchobj):
        self.autogen_metadata.append((matchobj.group(2), matchobj.group(1)))
        return matchobj.group(1)

    def _blurb_inline_re(self, matchobj):
        self.autogen_metadata.append(("blurb", matchobj.group(1)))
        return matchobj.group(1)

    def _format_table(self, content):
        table_fmt = []
        is_table = False
        header_row = None
        md_mini = None
        dummy = None

        for _ in content.splitlines():
            if _.startswith("|"):
                if not is_table:
                    is_table = True
                    md_mini = markdown.Markdown()
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
                    table_fmt.append("</tbody></table>")
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
                        f"<{col_type}>{dummy._formatted(cell)[3:-4]}</{col_type}>"
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
            table_fmt.append("</tbody></table>")

        content = "\n".join(table_fmt)

        return content

    def _checkbox_re(self, matchobj):
        if matchobj.group(1) not in " _":
            return '<input type="checkbox" disabled checked />'
        return '<input type="checkbox" disabled/>'

    def _formatted(self, raw_content):
        md = markdown.Markdown()

        self.autogen_metadata = []
        raw_content = self.metadata_re.sub(self._metadata_re, raw_content)

        preformat_content = raw_content.split("```")
        preformatted = False
        output = []

        for section in preformat_content:
            if preformatted:
                output.append("<code><pre>")
                lines = section.split("\n")
                for line in lines:
                    if line:
                        line = (
                            line.replace("<", "&lt;")
                            .replace('"', "&quot;")
                            .replace("\\`", "`")
                        )
                        output.append(line + "\n")
                output.append("</pre></code>")
            else:
                inline_content = section.split("`")
                inline_output = []
                inline_preformat = False
                for content in inline_content:
                    if inline_preformat:
                        content = content.replace("{", "\\{").replace("}", "\\}")
                        inline_output.append(f"`{content}`")
                    else:
                        content = content.replace("\\{", "\\\\{").replace(
                            "\\}", "\\\\}"
                        )

                        # Included items come first
                        content = self.literal_include_re.sub(
                            self._literal_include_re, content
                        )

                        content = self.blurb_re.sub(self._blurb_re, content)
                        content = self.blurb_inline_re.sub(
                            self._blurb_inline_re, content
                        )
                        content = self.function_re.sub(self._function_re, content)

                        # then local post-processing
                        content = self.strike_re.sub(self._strike_re, content)
                        content = self.media_re.sub(self._media_re, content)
                        content = self.link_re.sub(self._link_re, content)
                        content = self._format_table(content)
                        content = self.checkbox_re.sub(self._checkbox_re, content)

                        inline_output.append(content)
                    inline_preformat = not inline_preformat

                content = md.convert("".join(inline_output))

                # Post-rendering processing
                content = self.href_re.sub(self._href_re, content)
                content = self.include_re.sub(self._include_re, content)
                content = (
                    content.replace("\\{", "{").replace("\\}", "}").replace("``", "`")
                )
                content = content.replace(
                    "<img ", '<img loading="lazy" class="img-fluid" '
                )

                output.append(content)

            preformatted = not preformatted

        result = "".join(output)
        # return result, md.Meta
        return result


# class ArticleRevision(Article):
#     revision_of = ForeignKeyField(Article, backref="revisions")


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
        return f"{self.wiki.link}/tag/{self.title}"

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

    @property
    def link(self):
        return f"{self.wiki.link}/media/{self.file_to_url(self.file_path)}"

    @property
    def file_path_(self):
        return os.path.join(self.wiki.data_path, self.file_path)

    @property
    def edit_link(self):
        return f"{self.link}/edit"

    def delete_(self):
        os.remove(self.file_path_)
        self.delete_instance()


class ArticleIndex(FTSModel):
    rowid = RowIDField()
    # title = SearchField()
    content = SearchField()

    class Meta:
        database = db
        options = {"content": Article.content}


def create_db():
    all_tables = [_ for _ in BaseModel.__subclasses__()] + [
        _ for _ in FTSModel.__subclasses__()
    ]
    db.drop_tables(all_tables)
    db.create_tables(all_tables)

    new_admin = Author.default()
    new_admin.save()

    Wiki.new_wiki("Welcome to Folio", "", new_admin, first_wiki=True)

    ArticleIndex.rebuild()
    ArticleIndex.optimize()


def update():
    pass

    # for article in Article.select():
    #     m = article.get_metadata_old()
    #     if m.items():
    #         article.clear_tags()
    #         #print(article.title)
    #         for k, v in m.items():
    #             if k != "tag":
    #                 new_metadata = Metadata(
    #                     item="article",
    #                     item_id=article.id,
    #                     key=k,
    #                     value=v[0],
    #                     autogen=True,
    #                 )
    #                 new_metadata.save()
    #             else:
    #                 article.add_tag(v)

    #         if "\r\n" in article.content:
    #             splitter = "\r\n\r\n"
    #         else:
    #             splitter = "\n\n"
    #         text = article.content.split(splitter, 1)
    #         if len(text) > 1:
    #             text = text[1]
    #         else:
    #             text = ""
    #         article.content = text
    #         article.save()


# update()

# for article in Article.select():
#     article.update_autogen_metadata()


# db.create_tables([ArticleIndex])
# ArticleIndex.rebuild()
# ArticleIndex.optimize()
