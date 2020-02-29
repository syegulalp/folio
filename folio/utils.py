class Message:
    def __init__(self, message, color=None, **ka):
        self.message = message
        self.color = color if color is not None else "warning"
        self.ka = ka
        if self.ka.get("yes"):
            self.message += "<br/>Do you want to proceed?"

    def __str__(self):
        buttons = ""
        if self.ka.get("yes"):
            buttons = f"""<div class="alert-box-buttons"><a href="{self.ka['yes']}"><button class="btn btn-danger" type="button">Yes, I want to do this.</button></a>
            <a href="{self.ka['no']}"><button class="btn btn-primary" type="button">No, I do not want to do this.</button></a></div>"""
        return f"""<div class="alert-box alert alert-{self.color}">{self.message}{buttons}</div>"""


class Error:
    def __init__(self, error, color=None, **ka):
        self.error = error
        self.color = color if color is not None else "warning"
        self.ka = ka

    def __str__(self):
        return f"""<div class="alert-box alert alert-{self.color}">{self.error}</div>"""

wiki_init = {
    'Quickstart': {
        'tags':['@meta'],
        'content':'''
# What's a wiki?

<small>(If you already know what a wiki is, go ahead and skip this.)</small>

A *wiki* is a system for storing and interlinking web documents, using a text format that makes writing and editing documents easy and fast.  [Wikipedia](https://www.wikipedia.org) popularized the concept of the wiki, and many other projects -- not just wiki sites, but the underlying wiki *software* -- have taken inspiration from the same idea.

This is a wiki you can use for anything from simple to-do lists to organizing all the details that go into a large creative project. Unlike Wikipedia, though, it's meant to be used by a single person at a time. But it has many of the same features, as you'll see in this document.

# Creating a basic wiki article

To create a new article, click on the <span class="oi oi-file"></span> icon in the sidebar at right. (You'll want to Ctrl-click the icon to open the new article in a new tab, so you don't close these instructions.)

Type a title in the top bar, then click the "Save and create article" button. This creates the article with a blank body.

Next, type some text in the editor pane. Use plain text, and separate paragraphs with double line breaks.

When you're done, click the "Publish" button. The article will then be saved and displayed. To edit the article again, click the <span class="oi oi-pencil"></span> icon to the right of the article title.

* [Learn about the editor and how it works.](Editor)
* [Learn how to insert formatting into articles with Markdown.](Wiki formatting)

# Linking

When you've created more than one article, you typically want to link to one from the other. The easiest way to do this is to type the name of the article surrounded by a double pair of square brackets. If you have an article named "Storyline", you'd make a link by typing `[[Storyline]]`.

If you want to link to an article, but you want to use a different text in the link than the article name, use the Markdown format for links: the text in square brackets, followed immediately by the link in parenthesis. For instance, `[This is my storyline](Storyline)` would link to the article **Storyline** with the link text *This is my storyline*.

* [Learn more about linking, including showing images and linking to external sites.](Linking)

# Tags

Sometimes you want to associate additional information with articles other than its title and text. For this, you can add **tags**.

To add tags to an article, click on the <span class="oi oi-tag"></span> icon in the row of icons above the article editor. Type the tag you want to add in the provided box.

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
* [Learn more about macros.](Macros)
'''        
    },
    'Wiki formatting':{
        'content':'''This wiki uses the Markdown formatting system, with a few changes. If you're already familiar with Markdown, you should be able to use most of its functionality, but for your convenience here's a rundown of how to add all the formatting supported.

# Inline formatting

*Italics*: `*Italics*`

**Bold**: `**Bold**`

***Italic and bold***: `***Italic and bold***`

# Literal formatting

Use backticks to fence off inline literals. 

`Inline literal ``[[test]]`` `

Inline literal `[[test]]`

Use three backticks to fence off block literals.

```
\`\`\`
[[block]] {{literal}}
\`\`\`
```

# Block formatting

Outline-level headers are preceded by one to five `# inline` symbols:

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


`> Blockquoted text.`

> Blockquoted text.

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

Image with link

To link to an image's asset page

## Image styles and formatting

# Includes

To include the contents of one document inside another, place the name of the document in double curly braces.

`{{Pastries}}` would include the contents of the document named `Pastries`.

To show curly braces as-is, escape them with slashes: `\{\{` and `\}\}` yields \{\{ and \}\}.

# Macros

`<<documents|articles|items tag="tagname">>`

* `tag`

`<<meta doc|article|item="name" key|key_opt="key_name" pre="pre_text" post="post_text">>`

* `doc` / `article` / `item`
* `key` / `key_opt`
* `pre` / `post`

Recipes:

* `<<meta key="blurb">>` -- Display the blurb for the current document (if any).
* `<<items tag="Places">>` -- Display all documents (items) tagged with `Places`, in alpha sort, with blurbs if available.
''',
'tags':['@meta']},
'@meta': {
    'tags':[],
    'content':'''
$[`@meta`-tagged articles are part of the general infrastructure of a wiki.]$

<<items tag="@meta">>
'''
},
"Contents":{
    'content':'''
Welcome to Folio!

This wiki has been automatically generated with your new Folio install. It contains some basic details about how to use Folio.

* [[Quickstart]] instructions. (*Not complete yet but readable*)
* Learn about [wiki formatting](Wiki formatting). ''',
    'tags':['@meta']
}
}