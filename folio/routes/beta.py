from bottle import route
from models import Wiki, Author
from .decorators import wiki_env


def default(obj):
    return str(obj)


def export(wiki: Wiki) -> dict:
    import json
    from playhouse import shortcuts

    tags = []
    for _ in wiki.tags:
        tags.append(
            {
                "id": _.id,
                "title": _.title,
                "articles": [a.article.id for a in _.articles],
            }
        )

    return json.dumps(
        {
            "wiki": shortcuts.model_to_dict(wiki, recurse=False),
            "articles": [
                shortcuts.model_to_dict(_, recurse=False) for _ in wiki.articles
            ],
            "media": [shortcuts.model_to_dict(_, recurse=False) for _ in wiki.media],
            "metadata": [
                shortcuts.model_to_dict(_, recurse=False) for _ in wiki.metadata
            ],
            "tags": tags,
        },
        default=default,
        indent=4,
    )

    # tags
    # metadata
    # note: we need to regenerate the metadata for the cover image

    # into zip file with media in subdir labeled media
    # zip file can be saved into subdir


@route(f"{Wiki.PATH}/export")
@wiki_env
def articles(wiki: Wiki, user: Author):
    return export(wiki)
