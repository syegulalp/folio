# Changelog

## HEAD

### New features

* We're now using Python 3.8 to build the standalone version of the app.
* Slight tweaks to dark mode color theme. The default light mode has also been softened further. Some buttons in dark mode are now more legible.
* You can now modify the CSS styling of a wiki. Simply create articles tagged with `@style`, and the contents of those articles will be inserted into a `<style>` block on article template pages.
* The image gallery layout is now a grid, which looks far better and is easier to navigate.
* The sidebar now lists all articles that have a link to them, but do not yet exist (Articles/Uncreated).
* The sidebar now has a live search box, which will search article, tag, and media object titles as you type, with a limit of five of each kind of object. Article fulltext search is not (yet) supported in this view, but might be at some point. The core of this will eventually be used to rework how the general search view operates, which has not been very useful.

### Bugfixes

* If you have parentheses in an article link, you must escape them with backslashes. E.g., if you have an article named `My Story (So Far)`, the link `[[the story]](My Story (So Far))` will not work. But you can use `[[the story]](My Story \(So Far\))`. We've also added a note about this to the included documentation. Link insertion in a document also obeys this rule; any links inserted with parentheses in the title will be auto-escaped.
* Squashed a minor bug involving a trailing slash in redirection URLs.
* Tables, modals, preformatted text, and a number of other controls were all but unreadable in dark mode. This has been fixed.
* We now use a more precise way to determine if a renamed article is going to create a name collision.
* Sorting for tags failed if the retrieved articles did not have the listed sort key. The default is now that articles with no sort key show up first.
* Fixed an issued where links to external URLs did not render correctly.
* Fixed an issue where backslashes in article titles did not render correctly in links, leading to a dead page.
* Fixed an issue where articles whose titles consisted of a single underscore created issues.
* Fixed an issue where articles with a backslash in the name were not correctly located as an existing article.

## [0.0.7-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.7-alpha)

### New features

* We have switched to using [Bottle](https://bottlepy.org) as our web framework. This was a major rip-and-replace operation, but it was worth it: maintaining our own little web framework was too much hassle for too little payoff.
* The drag-and-drop file uploader now has a progress report for batch uploads, and shows all uploaded files.
* Dragging and dropping a file into an open editor will insert a reference to the file at the cursor point.
* An experimental new feature allows you to navigate from the sidebar without forcing a reload of the page. This way you can quickly flick through multiple entries in the sidebar without distraction.
* The internal webserver is now multithreaded.
* When unsaved changes are present in a page, the page's Save button will glow red.
* The default theme is a softer white that's less hard on the eyes.
* There is now an experimental "dark mode" available, part of a more general feature to allow custom CSS. To enable it, edit the `config.py` file in your Folio installation's `data` directory and add the line `CSS = ["wiki-dark.css"]`. (It will eventually be possible to further customize CSS on a wiki-level basis by way of configuration articles inside the database.)

### Bugfixes

* Some templates that were supposed to display at fixed width were not; this has been corrected.
* Javascript and CSS now load with hints that indicate the version number, so that upgrades across versions do not cause cached resources to be loaded.
* The drag-and-drop uploader now reports back errors on multiple file uploads.
* Obsolete information about the use of backticks to fence off literals has been removed from the included docs.

### Known bugs

* Parens in the name of an identifier for a link break the link. E.g., if you have an article named `My Story (So Far)`, the link `[[the story]](My Story (So Far))` will not work.

## [0.0.6-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.6-alpha)

**This is the last pre-alpha release.** The next release will be a proper beta, with all changes to the database schema tracked and versioned to allow proper migrations between schemas.

### New features

* We've switched to using the `commonmark` parser for the project. This ensures a greater degree of consistency in the parser, since it uses the CommonMark specification. Any Folio-specific changes we provide to Markdown can be handled more readily this way.
* Because we changed to `commonmark`, there's been one significant change to the syntax from previous versions. You *must* use double bracket links (`[[Link text]](Article name)`) to create links to wiki articles (as opposed to external URLs). You *can* use single bracket links (`[Link text](Article name)`) to refer to local wiki articles, but *only* if the article name is a *single word*. Therefore, to avoid any ambiguities, use the double-bracket link format for wiki articles, and the single-bracket link format for external URLs.
* You can now paste images from the clipboard directly into the article editor. The image will be uploaded to the wiki, and an image reference will be inserted at the edit point.
* Images dragged and dropped, or pasted, will have thumbnails show up in a modal on the page.
* The system metadata entries, `@default` and `@hide-title`, are now fully documented.
* Wikis now have a rudimentary search-and-replace functionality. It is not yet exposed through a menu option, but it's available by going to a wiki's search page and replacing `/search` with `/replace` in the address bar. You can perform case-sensitive search-and-replace operations on article texts. Altered articles automatically have a revision saved. It does not work on any other content, such as article titles, tags, image names, etc. **This is an experimental feature which can result in data loss, so use it with caution.**
* The literal-include feature, which used triple curly braces to include the source of a document, has been removed. Its behavior essentially overlapped with the regular include feature anyway.
* The `articles` macro now includes a `sort` parameter, which allows matched articles to be sorted according to the value of the metadata element specified in `sort`. Details on how to use `sort` have been added to the `Macros` article in the built-in documentation.
* Layout tweaks. The maximum width for the main display is 1024px.

### Bugfixes

* Paginator and redirection behavior on deleting an image from the image manager previously failed under certain circumstances.
* "Image not found" page in the image manager now renders correctly.
* The link inserter in the article editor now works properly once again when you press Shift-Enter to manually add a link definition.
* The drag-and-drop message popup now clears its contents properly.
* When viewing a draft of an article with a different title from the original, the changed name is now seen.
  
### Known bugs

* If a multiple drag-and-drop image upload batch fails, it only displays an error message and no details about which uploads specifically failed.

## [0.0.5-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.5-alpha)

### New features

* You can now drag and drop multiple images to upload. (The upload note does not yet single them out individually; this is coming later.)
* Image upload dates and times are now recorded.
* Template creation now allows `@default`-tagged autogen metadata to populate articles with text, without having to make them into form articles.
* The media browser is now paginated.
* The "article not found" page will now pass along the title of the article you were looking for as a parameter to any form pages you might want to create an article with.

### Bugfixes

* Some issues with how text rendered in tables has been fixed.
* Fixed issue where drafts and revisions incorrectly showed up in `documents` macro results.
* Error messages in the editor weren't being thrown if a save action was attempted when the server had stopped running.

## [0.0.4-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.4-alpha)

**This version has a breaking schema from the previous versions.**

### New features

* The first full version of Folio's internal documentation is complete. When you launch Folio for the first time, it'll create a new wiki with instructions pre-loaded into it.
* You can now create new wikis using existing ones as templates.
* You can now use the `$$[ ]$$` tags to specify auto-generated metadata that is not shown in the underlying article text.
* The link insert function in the editor now lets you specify what text to use when you insert the link. By default the text is the topmost item in the link search box.
* Links now respect anchors. For instance, `[[A link#An anchor]]` will link to the anchor `An anchor` on the article named `A link`.

### Bugfixes

* A bug involving newly created pages not saving correctly when the title wasn't modified was fixed.
* Search results for articles mistakenly showed revisions as well as current articles. (An option to search revisions as well as current versions of articles will come later.)
* Many inconsistencies with how literals were handled have been fixed.

## [0.0.3-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.3-alpha)

**This version has a breaking schema from the previous versions.**

### New features

* Media can now be deleted from the media gallery for a wiki.
* Media can be renamed, with each article that uses the media automatically renaming its references as well.
* You can select a given image from the media gallery as the cover image for a wiki. Go to the image's edit page and select "Use this image as the wiki's cover image."
* Error pages for wikis, media, etc. not found are much cleaner now.
* Titles for many pages are more explicit.
* Deleting an image used as the cover image for a wiki will generate a warning.
* Editor automatically assumes focus when entering article edit mode.
* Adding a link when text is selected automatically uses the selected text as the text for the link.

### Bugfixes

* When a tag page has no article associated with it, the "create page" link sometimes created a new page in the wrong wiki.

## [0.0.2.1-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.2.1-alpha)

### Bugfixes

* Article revisions are now accessed by way of an ID-based URL. This way revisions of an article with an earlier name can be accessed without any trickery in the name field. (Revisions to articles also no longer have a date stamp automatically added to the name.)
* Tag listings now show only main articles, not revisions of articles as well.

## [0.0.2-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.2-alpha)

### New features

* Ctrl-Shift-F takes you to the Search screen when not editing an article.
* Added a simple caching system for article texts. This speeds up things somewhat with wikis that are mainly being browsed. (We already have a sidebar caching system, which provided some speedup, but this enhances that further.)
* Link insert button in article editor. (Hotkey: Ctrl-L when editor is in focus.)
* Metadata editor for articles.
* Tag and image chooser in editor now show default choices instead of requiring you to type to show anything.
* Bold/ital command buttons in editor.
* Wikis can now be deleted.

### Bugfixes

* Metadata wasn't extracted properly from mixed formatted/unformatted content
* Reloading delete-confirmation page sometimes destroyed data.
* Metadata didn't migrate properly between drafts and published articles.

## [0.0.1-alpha](https://github.com/syegulalp/folio/releases/tag/0.0.1-alpha)

Initial release.