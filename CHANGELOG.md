# Changelog

## ??

**This version has a breaking schema from the previous versions.**

### New features

* Media can now be deleted from the media gallery for a wiki.
* Media can be renamed, with each article that uses the media automatically renaming its references as well.
* You can select a given image from the media gallery as the cover image for a wiki. Go to the image's edit page and select "Use this image as the wiki's cover image."
* Error pages for wikis, media, etc. not found are much cleaner now.

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