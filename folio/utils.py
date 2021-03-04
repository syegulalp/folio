import html


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


def export():
    # example export, just fooling around for now
    # for import we need to resolve primary keys in an in-memory temp table I think
    # we don't even need a table, a simple dictionary will do it

    from models import Article
    import json
    from playhouse import shortcuts

    print([shortcuts.model_to_dict(_, recurse=False) for _ in Article.select()])


class Unsafe:
    def __init__(self, data: str):
        self.data = str(data)

    def __str__(self):
        return html.escape(self.data, True)
