% include('includes/header.tpl')

<main role="main" class="container-wiki">

    <div id="article-row" class="row">
        <div id="article-col" class="col">
            % include('includes/messages.html')
            <h1>Create your new wiki</h1>
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
                    <span class="float-right">
                        <a href="/">
                            <button type="button" class="btn btn-sm btn-warning">Quit creating new wiki</button>
                        </a>
                    </span>

                    <button type="submit" name="save" value="save" class="btn btn-sm btn-success">Save</button>

                </div>

            </form>
        </div>
    </div>

</main>

% include('includes/footer.tpl')