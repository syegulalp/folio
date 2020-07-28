wiki_init = {
"Contents": {
   "tags": ['@template'],
   "content": """# $[Welcome to Folio!]$

This wiki has been automatically generated with your new Folio install. It contains some basic details about how to use Folio.

If you just want to jump in, the [[Quick Start]] article has basic instructions.

* <<<What's a wiki?>>>
* <<<Editor>>>
* <<<Wiki formatting>>>
* <<<Tags>>>
* <<<Linking>>>
* <<<Image management>>>
* <<<Includes>>>
* <<<Metadata>>>
* <<<Macros>>>
* <<<Forms and templates>>>"""},
"Editor": {
   "tags": ['@template'],
   "content": """$$[The tool used to create and edit wiki articles.]$$

The editor for Folio lets you edit, save drafts of changes, and publish changes to articles in a Folio wiki.

# Starting a new article

When you click on the <span class="oi oi-file"></span> icon in the sidebar to open a new, blank article, the new article is by default named **Untitled.** Ideally, you should change the name before doing anything else (although you can change the name at any time). Type the new name in the title bar and press the <button type="button" class="btn btn-sm btn-success">Save and create article</button> button, or press the Enter key while the title bar is in focus.

Once you've done this, the new article will be officially created, and you'll see the full range of editing options. Not all of the editing options are available before you save a new article for the first time.

If you click <button type="button" class="btn btn-sm btn-warning">Quit creating article</button> before saving the article, the new article won't be created and you'll be returned to the wiki's default page.

# Drafts and editing

To edit an existing article, click the <span class="oi oi-pencil"></span> icon at the top right of the article. This opens the article for editing.

* [[Learn how to insert formatting into articles with the Markdown format.]](Wiki formatting)

When you open an existing article for editing, or save a newly created one for editing, you'll be editing a *draft copy* of the article -- a clone of the original.

The draft copy is where all changes to an article are saved until you're satisfied with them.  Any changes you make to the article text aren't saved to the draft until you hit the <button type="button" class="btn btn-sm btn-success">Save</button> button.

You can also press **Ctrl-S** when the editor has focus to save the document.

When you hit <button type="button" class="btn btn-sm btn-primary">Publish</button> , the changes in your draft are copied into the original article, and the draft is removed. To start editing a new draft, just click the <span class="oi oi-pencil"></span> icon for the article once again.

If you click <button type="button" class="btn btn-sm btn-info">Save and exit</button> , the changes to the draft are saved, and you'll leave the editor, but the changes from the draft won't be published. The draft will still be available for editing later.

If you want to publish a draft to an article but keep a "snapshot" of its state before the draft, click <button type="button" class="btn btn-sm btn-dark">Version</button> instead of <button type="button" class="btn btn-sm btn-primary">Publish</button>. This will save a copy of the article's state to its history, which you can then browse by way of the <span class="oi oi-calendar"></span> icon at the top of the article.

If you change the name of a draft article, you *must* save changes to the draft before doing anything else, including publishing the article.

# The toolbar

Above the editor pane is a list of icons, called the **toolbar**, that provides shortcuts to common actions.

## Preview

The **Preview** button <span class="oi button-oi oi-eye"></span> opens and closes a pane to the right of the editor that shows what your article looks like when it's published. To update the preview, hit <button type="button" class="btn btn-sm btn-success">Save</button> (or **Ctrl-S**).

You can also toggle the preview by pressing **Ctrl-P** when the editor is in focus.

## Bold

The **Bold** button <span class="oi button-oi oi-bold"></span> adds Markdown bolding, or two asterisks, to either side of the currently selected text.

You can also add bolding to a selection by pressing **Ctrl-B** when the editor is in focus.

## Italic

The **Italic** button <span class="oi button-oi oi-italic"></span> adds Markdown italicizing, or one asterisk, to either side of the currently selected text.

You can also add italicizing to a selection by pressing **Ctrl-I** when the editor is in focus.

## Add link

The **Add link** button <span class="oi button-oi oi-link-intact"></span> lets you take the currently selected text and wrap it in a link to an article. You can type to search the name of the article you want to link to, then either click the article name or press **Enter** to use the topmost listed link.

If no text is selected, a direct link to the article under its name will be inserted at the cursor.

You can also add a link by pressing **Ctrl-L** when the editor is in focus.

* [Learn more about linking, including showing images and linking to external sites.](Linking)

## Add media

To upload media to the wiki -- generally, an image file -- simply drag and drop the media file anywhere in the browser. The uploaded media will show in the wiki's media manager, available from the <span title="See wiki media" class="oi oi-image"></span> icon in the right-hand column.

You can then insert the image in the editor by clicking the **Insert media** button <span class="oi button-oi oi-image"></span> in the editor toolbar. Type the name of a file to search for it, and either click the name of the image or press Enter to select the topmost item displayed.

* [[Learn more about managing images in Folio.]](Image management)

## Add/edit metadata

*Metadata* are key/value pairs associated with objects in Folio. To edit the metadata for an article, click the **Edit article metadata** button <span class="oi button-oi oi-info"></span> in the editor's toolbar.

When you add a metadata element, the key *must* be a single word -- no spaces, but underscores are OK. The value can be any text.

Note that any metadata changes are saved first to an article draft, and only to the actual article after it's published.

* [Learn more about metadata.](Metadata)

## Add tags

To add or change *tags* for an article, click the **Edit tags** <span class="oi button-oi oi-tags"></span> button in the editor toolbar.

Note that any tag changes are saved first to an article draft, and only to the actual article after it's published.

* [Learn more about tagging.](Tags)"""},
"Forms and templates": {
   "tags": ['@template'],
   "content": """$$[How to use articles and wikis as the basis for more articles and other wikis.]$$

Forms and templates let you use Folio articles, or entire Folio wikis, as the basis for a new article or a new wiki.

# Forms

A **form** is any Folio article [tagged](Tags) with the special system tag `@form`. When you apply this tag, the rendered article will appear with a button:

<button type="button" class="btn btn-sm btn-success">Create new article from this form article</button>

Click this button and you'll create a new article from the text of the form article.

# Templates

If you tag pages in a Folio wiki with the system tag `@template`, you can use those pages as the basis for a newly created wiki.

Once you tag one or more pages in a wiki with `@template`, go to the wiki's settings and click:

<button type="button" class="btn btn-sm btn-secondary">Create a new wiki using this one as a template</button>

You'll be presented with a list of all the articles that will be used to create the new wiki. Click <button type="button" class="btn btn-sm btn-success">Create the new wiki</button> and you'll be taken to the settings page for the new wiki.

# Special tags for templates

## `@template`

All pages tagged with `@template` will be created in the new wiki. However, *only the page's metadata (such as its blurb)* will be copied to the new wiki, not the article text. This way, you can use the *structure* of a wiki, rather than its actual *contents*, as the basis for the new wiki.

## `@asis`

if you want to have a `@template` page copy its full text as-is, including metadata references, just add the `@asis` tag to a `@template` page.

## `@make-auto`

If you have a `@form` page tagged as `@template`, it will also be copied into the new wiki. But if you also want to have a new page automatically generated in the wiki from that form, you can add a metadata entry to the article with the key `@make-auto` and the value being the name of the newly created article from the form.

# Special metadata for templates

## `@default`

If you have an article with a metadata entry (not a tag) named `@default`, the value of that entry will be used to populate the newly created article. This is useful if you want to have boilerplate text in an article when a wiki is newly created, but don't want to make that article into a form. This works with metadata added through the metadata editor, and with [autogenerated metadata](Metadata) using the `$[ ]$` and `$$[ ]$$` tags."""},
"Image management": {
   "tags": ['@template'],
   "content": """$$[How to upload images into a wiki and display them in articles.]$$

You can upload images into a wiki and insert them into articles.

To upload an image to a wiki, simply drag and drop the image anywhere into the browser. The image will be uploaded and made available in the wiki's image manager, available from the media icon <span title="See wiki media" class="oi oi-image"></span> in the sidebar.

To insert an image in an article, click the "Image" <span class="oi button-oi oi-image"></span> icon in the editor's toolbar. You can also insert an image reference manually by using the format `![](filename.jpg)`.

# The media manager

Click the media icon <span title="See wiki media" class="oi oi-image"></span> in the sidebar for a wiki to see all the media uploaded to that wiki. From there you can click on an image to see its details and make changes, such as renaming the file.

If you change the filename of an image, all references to that file are automatically updated throughout the wiki.

If you click the button <button type="button" class="btn btn-sm btn-info">Use this image as the wiki's cover image</button> , the image in question will be used as the image that shows in the wiki's sidebar and in its entry on the Folio homepage."""},
"Includes": {
   "tags": ['@template'],
   "content": """$$[How to place the contents of one article within another.]$$

To include the rendered contents of one document inside another, place the name of the document in double curly braces.

`{{Pastries}}` would include the contents of the document named `Pastries`.

To show curly braces as-is, escape them with slashes: `\{\{` and `\}\}` yields \{\{ and \}\}."""},
"Linking": {
   "tags": ['@template'],
   "content": """$$[How to generate links between articles and to external content.]$$

# Simple links

To link to a document in the wiki, surround its name with double square brackets.

`[[Wiki formatting]]` - [[Wiki formatting]]

To type double or single square brackets as-is, escape them with backslashes.

`\[\[` and `\]\]` yields \[\[ and \]\].

# Named links

To link to an article but show a different text in the link, use Markdown-style links with a double bracket.

`[[Link to "Linking"]](Linking)` - [Link to "Linking"](Linking)

# Linking to an external URL

To link to an external URL, use the link format but with *single* brackets (basically, the original Markdown link format):

`[Link to Google](https://google.com)` - [Link to Google](https://google.com)

> **Note:** If you use an external URL link to reference a local article, the link *may* work as expected, but only if the link is a *single word*. E.g., `[Link to "Linking"](Linking)` will work, but `[Link to "Image management"](Image management)` will not. So in general, use `[[]]` to *unambiguously* link to articles.

# Linking to a tag

To link to a *tag*, use `/tag/tag_name` as your target.

`[[/tag/@template]]` - [[/tag/@template]]

You can also use the named link format on a tag link:

`[[@template tag]](/tag/@template)` - [[@template tag]](/tag/@template)

# Link to document with blurb autogeneration

To link to a document and automatically provide its blurb (if it has one), use triple angle brackets.

`<<<Wiki formatting>>>`

This is basically shorthand for:  

`[[Wiki formatting]] <<meta doc="Wiki formatting" key="@blurb" pre="--">>`

# Linking to an image

To link to an image in the wiki's [[image manager]](Image management), use Markdown's image format, with the name of the image:

`![](picture.jpg)`

To have a picture serve as a link, just wrap it in the link:

`[![](picture.jpg)](https://link.to)`

`[[![](picture.jpg)]](Wiki article)`"""},
"Macros": {
   "tags": ['@template'],
   "content": """$$[ Special in-article commands for extended formatting.]$$

**Macros** allow parts of articles to be included in other articles. Macros look like XML tags, but use double angle brackets.

# `documents|articles|items`

Use `documents` (`articles` and `items` are synonyms) to generate a list of all articles in the wiki that match certain parameters.


`<<documents|articles|items tag="tagname" sort="sortkey">>`

* `tag`: Match any articles that have the following tag. Use multiple `tag` items to match against multiple tags.  `<<items tag="Fiction">>` would insert a list of all articles with the tag `Fiction`.
* `sort`: Sort the matched items by way of a specified metadata key. For instance, `sort="alphakey"` would look for metadata on each article under the name `alphakey`, and sort the articles using the value under that key.

# `meta`

Extracts a given piece of metadata from a specific article with a specific metadata key. If no document is specified, the current document is used.


`<<meta doc|article|item="name" key|key_opt="key_name" pre="pre_text" post="post_text">>`

* `doc` / `article` / `item`: Find the article that matches this name. If no such article is found, an error is thrown.
* `key`: Extract the metadata that matches this key. If no such key is found, an error will be thrown.
* `key_opt`: Same as `key` except that if the key isn't found, no error is thrown.
* `pre` / `post`: Automatically insert a specified text either before (`pre`) or after (`post`) the metadata. The `<<<`/`>>>` [linking function](Linking) uses `pre` internally to place a dash between the article title and its extracted blurb.

# Common macro recipes

* `<<items tag="Places">>` -- Display all documents (items) tagged with `Places`, in alpha sort, with blurbs if available."""},
"Metadata": {
   "tags": ['@template'],
   "content": """$$[Sidecar data for articles.]$$

Every object in a Folio wiki can have *metadata* associated with it. Metadata consists of key-value pairs that you can add to, edit, or remove from wiki objects.

To edit the metadata for an article, click the **Edit article metadata** button <span class="oi button-oi oi-info"></span> in the editor's toolbar.

When you add a metadata element, the key *must* be a single word -- no spaces, but underscores are OK. The value can be any text.

Note that any metadata changes are saved first to an article draft, and only to the actual article after it's published.

# Auto-generated metadata

Some articles will have metadata automatically generated based on the contents. For instance, if you use the `$[` and `]$` tags to delineate a block of text, that text will automatically be added to the article's metadata with the key `@blurb`. (The `@` in front of a metadata key indicates it's intended to be handled as special system-level metadata.)


`$[This will show up as metadata in an article with the key "@blurb", with the text remaining in the article.]$`

If you want to use a custom key, you can do so:


`$[This will show up as metadata in an article with the tag "custom_key", with the text remaining in the article.]``$(custom_key)`


If you don't want to keep the value text in the document, but only add the metadata, use `$$[` and `]$$`.


`$$[This text will be added with the key "@blurb", but will not appear in the published document.]$$`


`$$[This text will be added with the key "custom_key", but will not appear in the published document.]$$(custom_key)`

# System metadata

Folio recognizes some metadata keys as having special properties.

## `@default`

If you have an article with a metadata entry (not a tag) named `@default`, the value of that entry will be used to populate the newly created article. This is useful if you want to have boilerplate text in an article when a wiki is newly created, but don't want to make that article into a form. This works with metadata added through the metadata editor, and with [autogenerated metadata](Metadata) using the `$[ ]$` and `$$[ ]$$` tags.

## `@hide-title`

Articles with a metadata entry named `@hide-title` will not show the title or tags of the article when being browsed. This is useful if you want to have, for instance, a splash welcome page where you want more control over the elements at the top of the page. Note that if you do this, the edit control for the page will not be available, but you can always go to the `/edit` URL for that page to open the editor."""},
"Quick Start": {
   "tags": [],
   "content": """# What's a wiki?

<small>(If you already know what a wiki is, go ahead and skip this part.)</small>

A *wiki* is a system for storing and interlinking web documents, using a text format that makes writing and editing documents easy and fast.  [Wikipedia](https://www.wikipedia.org) popularized the concept of the wiki, and many other projects -- not just wiki sites, but the underlying wiki *software* -- have taken inspiration from the same idea.

Folio is a wiki you can use for anything from simple to-do lists to organizing all the details that go into a large creative project. Unlike Wikipedia, though, it's meant to be used by a single person at a time. But it has many of the same features, as you'll see in this document.

* [Learn more about wikis and their concepts.](What's a wiki?)

# Creating a new, blank wiki

To get started with a new wiki with nothing in it, click on the home <span title="Wiki server homepage" class="oi oi-home"></span> icon on the sidebar at right. (You'll want to Ctrl-click the icon to open the new article in a new tab, so you don't close these instructions.) That takes you to the homepage for your Folio installation.

From there, click <button type="button" class="btn btn-sm btn-success">Create a new wiki</button> to create a new wiki. You'll need to pick a name for it and an optional description. 

Press <button type="button" class="btn btn-sm btn-success">Save</button> to create your new wiki. You'll be automatically taken to its homepage.

# Creating a basic wiki article

To create a new article, click on the new article <span class="oi oi-file"></span> icon in the sidebar at right. (You'll want to Ctrl-click the icon to open the new article in a new tab, so you don't close these instructions.)

Type a title in the top bar, then click the <button type="button" class="btn btn-sm btn-success">Save and create article</button> button. This creates the article with a blank body. You can always change the article name later.

Next, type some text in the editor pane. Use plain text, and separate paragraphs with double line breaks. If you want to add formatting, you can do that, but we'll go into that later.

When you want to save your progress, click the <button type="button" class="btn btn-sm btn-success">Save</button> button. *The draft copy of an article is always separate from its finished copy,* so you can edit any article without worrying about wrecking what's already in it.

When you're done, click the <button type="button" class="btn btn-sm btn-primary">Publish</button> button. The article will then be saved and displayed. To edit the article again, click the <span class="oi oi-pencil"></span> icon to the right of the article title.

* [Learn more about the editor and how it works.](Editor)
* [Learn how to insert formatting into articles with the Markdown format.](Wiki formatting)

# Linking

When you've created more than one article, you typically want to link to one from the other. The easiest way to do this is to type the name of the article surrounded by a double pair of square brackets. If you have an article named "Storyline", you'd make a link by typing `[[Storyline]]`.

If you want to link to an article, but you want to use a different text in the link than the article name, use the Markdown format for links: the text in square brackets, followed immediately by the link in parenthesis. For instance, `[This is my storyline](Storyline)` would link to the article **Storyline** with the link text *This is my storyline*.

You can also click the "Link" icon <span class="oi button-oi oi-link-intact"></span> above the editor to insert a link to an article. Type the name of an article -- it'll search as you type -- and then press `Enter` to add the topmost entry in the list.

* [Learn more about linking, including showing images and linking to external sites.](Linking)

# Images

You can upload images into a wiki and insert them into articles.

To upload an image to a wiki, simply drag and drop the image anywhere into the browser. The image will be uploaded and made available in the wiki's image manager, available from the <span title="See wiki media" class="oi oi-image"></span> icon in the sidebar.

To insert an image in an article, click the "Image" <span class="oi button-oi oi-image"></span> icon in the editor's toolbar. You can also insert an image reference manually by using the format `![](filename.jpg)`.

* [Learn more about images and image management.](Image management)

# Tags

Sometimes you want to associate additional information with articles other than its title and text. For this, you can add **tags**.

To add tags to an article, click on the "Tag" <span class="oi button-oi oi-tag"></span> icon in the row of icons above the article editor. Type the tag you want to add in the provided box.

If a tag already exists that has a name with a close match for something you're typing, you'll see suggestions pop up in the box below. You can click on one of those suggestions to add the tag to the article, or hit `Enter` to select the topmost suggestion.

(Hint: If you type something and hit `Shift-Enter`, it'll be inserted as a tag as-is, without selecting a suggestion.)

All tags for all articles can be accessed by way of the **Tags** tab in the sidebar at right.

* [Learn more about tagging.](Tags)

# Metadata

Metadata lets you store key-value information with articles. To edit the metadata for an article, click the **Edit article metadata** button <span class="oi button-oi oi-info"></span> in the editor's toolbar.

* [Learn more about metadata.](Metadata)

# Includes and macros

You can include one or more articles inside another article. To do this, simply type the name of the article in double curly braces. `{{Characters}}` would include the entire article named **Characters**.

If you need for some reason to include the *original, unformatted* text of the article, use *triple* curly braces (e.g., `{{{Characters}}}`). (Note that the source text will be rendered once it's included; this is just if you need, for instance, to include a document that's just a fragment.)

You can also use **macros**, or special wiki commands, to extract parts of articles or their metadata and include them in other articles.

* [Learn more about includes.](Includes)
* [Learn more about macros.](Macros)"""},
"Tags": {
   "tags": ['@template'],
   "content": """$$[Ways to categorize and group articles.]$$

**Tags** allow you to group articles together in categories.

Tag names can be any *plain* text. Markdown and HTML aren't rendered in tags.

When you add a tag to an article (see [using the editor](Editor) for more details on how to do that), it appears at the top of the published article. Clicking on the tag name shows you all other articles with the same tag.

You can also see a list of tags in the **Tags** tab in the sidebar.

To link to a *tag*, use `/tag/tag_name` as your target.

`[[/tag/@template]]` - [[/tag/@template]]

# Special `@` tags

Tag names beginning with an `@` are used for tags that have system functions.

* `@template`: Used to tag articles that are part of a wiki's basic structure. When a blank wiki is created from an existing wiki as a template, all articles tagged `@template` are created automatically in the new wiki (although by default only their titles and metadata are copied).
* `@form`: Used to tag articles that can be used as a blank form for other articles in the same wiki. For instance, a blank character sheet could be tagged `@form`.
* `@asis`: Used to tag articles that are to be copied with their full text when used with `@template`. See [[Forms and templates]] for more information."""},
"What's a wiki?": {
   "tags": ['@template'],
   "content": """$$[A quick introduction to wikis, and why to use them for creative projects.]$$

A *wiki* is a system for storing and interlinking web documents, using a text format that makes writing and editing documents easy and fast.  [Wikipedia](https://www.wikipedia.org) popularized the concept of the wiki, and many other projects -- not just wiki sites, but the underlying wiki *software* -- have taken inspiration from the same idea.

Folio is a wiki you can use for anything from simple to-do lists to organizing all the details that go into a large creative project. Unlike Wikipedia, though, it's meant to be used by a single person at a time. But it has many of the same features, as you'll see in this document.

# Wikis vs. "flat-file" editing

If you take notes on paper, or in a word processing program -- Notepad, Word, etc. -- one of the problems you may run into is how to organize everything. Putting everything in a single, large document is unwieldy, since it's hard to refer elegantly to one piece of information from multiple places. Breaking everything across multiple documents just creates a new kind of unwieldy. The problem is even worse when you're dealing with "freeform" data, or data that has no inherent organization. 

A wiki provides a better paradigm for holding and organizing freeform data. You can write things down first, and then gradually impose structure on your data as you go along. Documents can be [linked](Linking) between each other freely, as with web pages (since they *are* web pages!), and can be [tagged](Tagging and metadata) to give them organization and structure. What's more, once you find a structure you're comfortable with, you can turn that structure into a template you can use for future projects that have the same basic outlines."""},
"Wiki formatting": {
   "tags": ['@template'],
   "content": """$$[How articles are written and marked up.]$$

Folio uses the [CommonMark formatting system](https://spec.commonmark.org/), with a few changes. If you're already familiar with CommonMark or its ancestor Markdown, you should be able to use most of its functionality.

For your convenience, here's a quick rundown of how to add all the formatting supported.

Note that *formatting only applies to article **contents**.* Article *titles* cannot be formatted.

# Inline formatting

*Italics*: `*Italics*`

**Bold**: `**Bold**`

***Italic and bold***: `***Italic and bold***`

~~Strikethrough~~: `~~Strikethrough~~`

# Links

{{Linking}}

# Literal formatting

Use backticks to fence off inline literals. 

```
Inline literal `[[test]]`
```

Inline literal `[[test]]`

Use three backticks to fence off block literals.

```
\`\`\`
[[block]] {{literal}}
\`\`\`
```

# Block formatting

Outline-level headers are preceded by one to five `#` symbols:

# Heading 1

`# Heading 1`

## Heading 2

`## Heading 2`

### Heading 3

`### Heading 3`

#### Heading 4

`#### Heading 4`

##### Heading 5

`##### Heading 5`

For blockquotes, start a line with a greater-than sign.

`> Blockquoted text.`

> Blockquoted text.

You can also nest blockquotes.

`>> Nested quote.`

>> Nested quote.

# Lists

Create bulleted lists by starting a line with an asterisk:

```
* Bullet item.
* Another bullet item.
```

* Bullet item.
* Another bullet item.

Start the list with a number to make it a numbered list.

```
1. Bullet item.
* Another bullet item.
```

1. Bullet item.
* Another bullet item.

Indent items four spaces to create subheadings.

```
* Main item.
    * Indented item.
* Another main item.
```

* Main item.
    * Indented item.
* Another main item.

"""},
}