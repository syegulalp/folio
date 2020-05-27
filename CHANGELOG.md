# Changelog

## HEAD

### New features

* You can now paste images from the clipboard directly into the article editor. The image will be uploaded to the wiki, and an image reference will be inserted at the edit point.

### Bugfixes

* Fixed isses with the paginator and the redirection behavior on deleting an image from the image manager.

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