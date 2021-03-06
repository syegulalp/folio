% include('includes/header.tpl')

<main role="main" class="container-wiki">

    <div id="article-row" class="row">
        <div id="article-col" class="col">
            % include('includes/messages.tpl')
            % if not wiki.id:
            <h1>Create your new wiki</h1>
            % else:
            <h1>Edit wiki settings</h1>
            % end

            <form method="POST">

                <div id="wiki-title" class="form-group">
                    <label for="wiki_title">Title of wiki:</label>
                    <input class="form-control form-control-lg" placeholder="My Amazing Wiki" id="wiki_title"
                        name="wiki_title" value="{{wiki.title}}">
                </div>

                <div id="wiki-description" class="form-group">
                    <label for="wiki_description">Description:</label>
                    <input class="form-control form-control-lg" id="wiki_description" name="wiki_description"
                        placeholder="A place for my stuff." value="{{wiki.description}}">
                </div>

                <div id="wiki-buttons">

                    % if wiki.id:
                    <span class="float-right">
                        <a href="{{original_wiki.link}}">
                            <button type="button" class="btn btn-sm btn-warning">Quit editing</button>
                        </a>
                    </span>
                    % else:
                    <span class="float-right">
                        <a href="/">
                            <button type="button" class="btn btn-sm btn-warning">Quit creating new wiki</button>
                        </a>
                    </span>
                    % end

                    <button type="submit" name="save" value="save" class="btn btn-sm btn-success">Save</button>

                    % if wiki.id:
                    <button type="submit" name="save" value="quit" class="btn btn-sm btn-info">Save and exit</button>

                    <hr />

                    <a href="{{original_wiki.link}}/clone">
                        <button type="button" name="save" value="quit" class="btn btn-sm btn-secondary">Create a new
                            wiki using this one as a template</button>
                    </a>


                    <hr />

                    <a href="{{wiki.delete_link}}">
                        <button type="button" class="btn btn-sm btn-danger">Delete this wiki</button>
                    </a>
                    % end

                </div>

            </form>
        </div>
        % if wiki.id:
        <div id="sidebar" class="sidebar-col">
            % include('includes/sidebar.tpl')
        </div>
        % end
    </div>

</main>

% include('includes/footer.tpl')