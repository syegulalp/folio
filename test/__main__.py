import unittest
from pathlib import Path

# TODO: need image tests


class TestRendering(unittest.TestCase):
    def setUp(self):
        self.models = models
        self.author = self.models.Author.select().get()

        self.wiki = self.models.Wiki(
            title="New test wiki",
            description="Wiki created for testing.",
            author=self.author,
        )
        self.wiki.save()

        self.article = self.models.Article(
            wiki=self.wiki,
            title="Test data article",
            content="",
            author=self.author,
        )
        self.article.save()

        with open(Path("test", "data", "source.md")) as f:
            self.article.content = f.read()
        self.article.save()

        self.include_article = self.models.Article(
            wiki=self.wiki,
            title="Include article",
            content="""$$[Include article with metadata.]$$

**Formatted content.**""",
            author=self.author,
        )
        self.include_article.save()
        self.include_article.add_tag("@test")
        self.include_article.update_autogen_metadata()

        # TODO: add some media for testing, too

    def test_article_all_inclusive(self):
        self.maxDiff = None
        content = self.article.formatted
        # with open(Path("test", "data", "output.html"), "w", encoding="utf8") as f:
        #     f.write(content)
        with open(Path("test", "data", "output.html"), encoding="utf8") as f:
            output = f.read()
        self.assertEqual(
            content,
            output,
        )

    def _make_article(self, article_title):
        article = self.models.Article(
            wiki=self.wiki,
            title=article_title,
            content="",
            author=self.author,
        )
        article.save()
        return article

    def test_article_delete(self):
        article_title = "Test article for deletion"
        tag_title = "Frumblebrumble"

        test_article = self._make_article(article_title)
        self.assertEqual(self.wiki.article_exists(article_title), True)

        test_article.add_tag(tag_title)
        self.assertEqual(self.wiki.tag_exists(tag_title), True)

        test_article.set_metadata("Foo", "Bar")
        self.assertEqual(test_article.get_metadata("Foo"), "Bar")

        # TODO: have a master delete override that handles all this

        test_article.clear_tags()
        self.assertEqual(self.wiki.tag_exists(tag_title), False)

        test_article.clear_metadata()
        self.assertEqual(test_article.get_metadata("Foo"), None)

        test_article.delete_instance(recursive=True)
        self.assertEqual(
            self.wiki.articles.where(
                self.models.Article.title == article_title
            ).count(),
            0,
        )

    def test_url_conversions(self):
        base = self.models.BaseModel

        self.assertEqual(
            base.title_to_url("Title_with_underscores"),
            "Title%5fwith%5funderscores",
        )

        self.assertEqual(
            base.url_to_title("Title%5fwith%5funderscores"),
            "Title_with_underscores",
        )

        self.assertEqual(
            base.title_to_url("Title_with_underscores and spaces"),
            "Title%5fwith%5funderscores_and_spaces",
        )

        self.assertEqual(
            base.url_to_title("Title%5fwith%5funderscores_and_spaces"),
            "Title_with_underscores and spaces",
        )

        self.assertEqual(
            base.title_to_url('"Title_with_quotes_and_underscores"'),
            "%22Title%5fwith%5fquotes%5fand%5funderscores%22",
        )

        self.assertEqual(
            base.url_to_title("%22Title%5fwith%5fquotes%5fand%5funderscores%22"),
            '"Title_with_quotes_and_underscores"',
        )

        self.assertEqual(
            base.title_to_url('"Title with quotes"'), "%22Title_with_quotes%22"
        )

        self.assertEqual(
            base.url_to_title("%22Title_with_quotes%22"), '"Title with quotes"'
        )

        self.assertEqual(
            base.title_to_url("Fall Of The Hammer / Original Version"),
            "Fall_Of_The_Hammer_%2f_Original_Version",
        )
        self.assertEqual(
            base.url_to_title("Fall_Of_The_Hammer_%2f_Original_Version"),
            "Fall Of The Hammer / Original Version",
        )
        self.assertEqual(base.file_to_url("myfile_01 ext.jpg"), "myfile_01%20ext.jpg")
        self.assertEqual(base.url_to_file("myfile_01%20ext.jpg"), "myfile_01 ext.jpg")

    def test_article_exists(self):
        self.assertTrue(self.wiki.article_exists("Test data article"))
        self.assertFalse(self.wiki.article_exists("Nonexistent article"))

    def test_tag_exists(self):
        self.article.add_tag("Foobletzky")
        self.assertTrue(self.wiki.tag_exists("Foobletzky"))
        self.assertFalse(self.wiki.tag_exists("Veeblefetzer"))
        self.article.remove_tag("Foobletzky")
        self.assertFalse(self.wiki.tag_exists("Foobletzky"))

    def test_wiki_has_name_collision(self):
        new_wiki = self.models.Wiki(title="New test wiki", description="")
        self.assertTrue(new_wiki.has_name_collision())
        new_wiki.title = "Non-colliding test wiki"
        self.assertFalse(new_wiki.has_name_collision())

    def test_wiki_link(self):
        self.assertEqual(self.wiki.link, "/wiki/New_test_wiki")

    def test_wiki_new_page_link(self):
        self.assertEqual(self.wiki.new_page_link, "/wiki/New_test_wiki/new")

    def test_wiki_edit_link(self):
        self.assertEqual(self.wiki.edit_link, "/wiki/New_test_wiki/edit")

    def test_wiki_search_link(self):
        self.assertEqual(self.wiki.search_link, "/wiki/New_test_wiki/search")

    def test_wiki_upload_link(self):
        self.assertEqual(self.wiki.upload_link, "/wiki/New_test_wiki/upload")

    def test_wiki_media_link(self):
        self.assertEqual(self.wiki.media_link, "/wiki/New_test_wiki/media")

    def test_default_wiki(self):
        new_wiki = self.models.Wiki.default()
        self.assertEqual(new_wiki.title, "Untitled Wiki")
        self.assertEqual(new_wiki.description, "Replace this with your description.")


if __name__ == "__main__":
    import sys, os

    sys.path.insert(0, "folio")
    sys.path.insert(0, Path("test", "data").absolute())

    import models as m

    global models
    models = m
    models.create_db()

    try:
        unittest.main(failfast=True)
    except:
        pass

    # teardown
    models.db.close()
    os.remove(Path("test", "data", "wiki.db"))
    os.rmdir(Path("test", "data", "1"))
