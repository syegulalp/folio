wiki_init = {
"Contents": {
   "tags": ['@meta'],
   "content": """Welcome to Folio!

This wiki has been automatically generated with your new Folio install. It contains some basic details about how to use Folio.

* [Quickstart](Quick Start) instructions. (*Not complete yet but readable*)
* Learn about [wiki formatting](Wiki formatting). """},
"Editor": {
   "tags": ['@meta'],
   "content": """The editor for Folio lets you edit, save drafts of changes, and publish changes to articles in a Folio wiki.

# Starting a new article

When you click on the <span class="oi oi-file"></span> icon in the sidebar to open a new, blank article, it is by default named **Untitled.** Ideally, you should change the name before doing anything else (although you can change the name at any time). Type the new name in the title bar and press the <button type="button" class="btn btn-sm btn-success">Save and create article</button> button, or press the Enter key while the title bar is in focus.

Once you've done this, the new article will be officially created, and you'll see the full range of editing options. Not all of the editing options are available before you save a new article for the first time.

If you click <button type="button" class="btn btn-sm btn-warning">Quit creating article</button> before saving the article, the new article won't be created and you'll be returned to the wiki's default page.

# Drafts and editing

To edit an existing article, click the <span class="oi oi-pencil"></span> icon at the top right of the article. This opens the article for editing.



* [Learn how to insert formatting into articles with the Markdown format.](Wiki formatting)

When you open an existing article for editing, or save a newly created one for editing, you'll be editing a *draft copy* of the article -- a clone of the original.

The draft copy is where all changes to an article are saved until you're satisfied with them.  Any changes you make to the article text aren't saved to the draft until you hit the <button type="button" class="btn btn-sm btn-success">Save</button> button.

You can also press **Ctrl-S** when the editor has focus to save the document.

When you hit <button type="button" class="btn btn-sm btn-primary">Publish</button> , the changes in your draft are copied into the original article, and the draft is removed. To start editing a new draft, just click the <span class="oi oi-pencil"></span> icon for the article once again.

If you click <button type="button" class="btn btn-sm btn-info">Save and exit</button> , the changes to the draft are saved, and you'll leave the editor, but the changes from the draft won't be published. The draft will still be available for editing later.

If you want to publish a draft to an article but keep a "snapshot" of its state before the draft, click <button type="button" class="btn btn-sm btn-dark">Version</button> instead of <button type="button" class="btn btn-sm btn-primary">Publish</button>. This will save a copy of the article's state to its history, which you can then browse by way of the <span class="oi oi-calendar"></span> icon at the top of the article.

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

* [Learn more about managing images in Folio.](Image management)

## Add/edit metadata

*Metadata* are key/value pairs associated with objects in Folio. To edit the metadata for an article, click the **Edit article metadata** button <span class="oi button-oi oi-info"></span> in the editor's toolbar.

When you add a metadata element, the key *must* be a single word -- no spaces, but underscores are OK. The value can be any text.

Note that any metadata changes are saved first to an article draft, and only to the actual article after it's published.

* [Learn more about metadata.](Metadata)

## Add tags

To add or change *tags* for an article, click the **Edit tags** <span class="oi button-oi oi-tags"></span> button in the editor toolbar.

Note that any tag changes are saved first to an article draft, and only to the actual article after it's published.

* [Learn more about tagging.](Tags)"""},
"Quick Start": {
   "tags": [],
   "content": """# What's a wiki?

<small>(If you already know what a wiki is, go ahead and skip this part.)</small>

A *wiki* is a system for storing and interlinking web documents, using a text format that makes writing and editing documents easy and fast.  [Wikipedia](https://www.wikipedia.org) popularized the concept of the wiki, and many other projects -- not just wiki sites, but the underlying wiki *software* -- have taken inspiration from the same idea.

Folio is a wiki you can use for anything from simple to-do lists to organizing all the details that go into a large creative project. Unlike Wikipedia, though, it's meant to be used by a single person at a time. But it has many of the same features, as you'll see in this document.

# Creating a basic wiki article

To create a new article, click on the <span class="oi oi-file"></span> icon in the sidebar at right. (You'll want to Ctrl-click the icon to open the new article in a new tab, so you don't close these instructions.)

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

You can upload images into a wiki and insert them inline. To upload an image to a wiki, simply drag and drop the image anywhere into the browser. The image will be uploaded and made available in the wiki's image manager, available from the <span title="See wiki media" class="oi oi-image"></span> icon in the sidebar.

To insert an image in an article, click the "Image" <span class="oi button-oi oi-image"></span> icon in the editor's toolbar. You can also insert an image reference manually by using the format `![](<Name of image file>)`.

* [Learn more about managing images in Folio.](Image management)

# Tags

Sometimes you want to associate additional information with articles other than its title and text. For this, you can add **tags**.

To add tags to an article, click on the "Tag" <span class="oi button-oi oi-tag"></span> icon in the row of icons above the article editor. Type the tag you want to add in the provided box.

If a tag already exists that has a name with a close match for something you're typing, you'll see suggestions pop up in the box below. You can click on one of those suggestions to add the tag to the article, or hit `Enter` to select the topmost suggestion.

(Hint: If you type something and hit `Shift-Enter`, it'll be inserted as a tag as-is, without selecting a suggestion.)

All tags for all articles can be accessed by way of the **Tags** tab in the sidebar at right.

* [Learn more about metadata.](Metadata)
* [Learn more about tagging.](Tags)

# Includes and macros

You can include one or more articles inside another article. To do this, simply type the name of the article in double curly braces. `{{Characters}}` would include the entire article named **Characters**.

If you need for some reason to include the *original, unformatted* text of the article, use *triple* curly braces (e.g., `{{{Characters}}}`). (Note that the source text will be rendered once it's included; this is just if you need, for instance, to include a document that's just a fragment.)

You can also use **macros**, or special wiki commands, to extract parts of articles or their metadata and include them in other articles.

* [Learn more about includes.](Includes)
* [Learn more about macros.](Macros)"""},
"Wiki formatting": {
   "tags": [],
   "content": """$[How to format wiki pages.]$(blurb)

This wiki uses the Markdown formatting system, with a few changes. If you're already familiar with Markdown, you should be able to use most of its functionality, but for your convenience here's a rundown of how to add all the formatting supported.

Note that *formatting only applies to article contents.* Article titles cannot be formatted.

# Inline formatting

*Italics*: `*Italics*`

**Bold**: `**Bold**`

***Italic and bold***: `***Italic and bold***`

# Links

## Simple links

To link to a document in the wiki, surround its name with double square brackets.

[[Wiki formatting]] - `[[Wiki formatting]]`

To type double square brackets as-is, escape them with backslashes.

`\[\[` and `\]\]` yields \[\[ and \]\].

## Named links

To make a link but show a different text, use Markdown-style links:

[Link](Link target) - `[Link](Link target)`

## Linking to a tag

To link to a *tag*, use `/tag/tag_name` as your target.

[[/tag/meta]]  - `[[/tag/meta]]`

## Link to document with blurb autogeneration

To link to a document and automatically provide its blurb (if it has one), use triple angle brackets.


`<<<Wiki formatting>>>`

<<<Wiki formatting>>>


This is basically shorthand for:  

`[[Wiki formatting]] -- <<meta doc="Wiki formatting" key="blurb">>`

# Images

To include an image inline, use Markdown image format:

```
![](Image.jpg)
![](https://host.com/Image.jpg)
```

# Literal formatting

Use backticks to fence off inline literals. 

```
Inline literal ``[[test]]``
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

#Heading 1

`# Heading 1`

##Heading 2

`## Heading 2`

###Heading 3

`### Heading 3`

####Heading 4

`#### Heading 4`

#####Heading 5

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



Image with link

To link to an image's asset page

## Image styles and formatting

# Includes

To include the rendered contents of one document inside another, place the name of the document in double curly braces.

`{{Pastries}}` would include the contents of the document named `Pastries`.

If you want to include the *literal text* of another document, not its rendered/formatted text, use *triple* curly braces.

To show curly braces as-is, escape them with slashes: `\{\{` and `\}\}` yields \{\{ and \}\}.

# Metadata and tags

**Metadata** can be assigned to an article in the form of key-value pairs. The key is a single word (or a `camel_case` or `hyphen-case` term), followed by a colon, followed on the rest of the line by the value.

To add metadata to an article, add the metadata lines at the top of the article, separated from the body of the article by a blank line.

```
tag: Fiction
author: Kurt Vonnegut

*Slaughterhouse-five* stemmed from Vonnegut's own experiences in WWII. ...
```

The wiki recognizes some metadata natively:

## `tag`

The `tag` meta is used to assign a tag to the article. Use multiple `tag` metas for multiple tags.

```
tag: Fiction
tag: Time Travel
tag: 20th Century
```

## `blurb`

The `blurb` meta lets you specify a snippet of text that's used to describe the article apart from its title, like a subhed. Blurbs can contain inline formatting and linking.

```
tag: Character
blurb: A man who has become "unstuck in time."

We are told in the first lines of the book about Billy Pilgrim's strange plight ...
```

# Macros

**Macros** allow parts of articles to be included in other articles. Macros look like XML tags, but with double angle brackets.


## `documents|articles|items`

Use `documents` (`articles` and `items` are synonyms) to generate a list of all articles in the wiki that match certain parameters.


`<<documents|articles|items tag="tagname">>`

* `tag`: Match any articles that have the following tag. Use multiple `tag` items to match against multiple tags.  `<<items tag="Fiction">>` would insert a list of all articles with the tag `Fiction`.

## `meta`

Extracts a given piece of metadata from a specific article with a specific metadata key. If no document is specified, the current document is used.


`<<meta doc|article|item="name" key|key_opt="key_name" pre="pre_text" post="post_text">>`

* `doc` / `article` / `item`
* `key`
* `key_opt`
* `pre` / `post`

Common macro recipes:

* `` -- Display the blurb for the current document (if any).
* `<<items tag="Places">>` -- Display all documents (items) tagged with `Places`, in alpha sort, with blurbs if available."""},
}