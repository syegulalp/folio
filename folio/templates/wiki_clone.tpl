% include('includes/header.tpl')

<main role="main" class="container-wiki">

    % include('includes/messages.tpl')

    <h1>Create a new wiki from <b>{{wiki.title}}</b></h1>

    % if wiki.template:

    <p>This will create a new wiki from the articles in <b>{{wiki.title}}</b> tagged with <code>@template</code>.</p>

    <p>When it's ready, you'll be redirected to the Properties page for the new wiki.</p>

    <hr />

    <span class="float-right">
        <a href="{{wiki.link}}">
            <button type="button" class="btn btn-sm btn-warning">Quit creating new wiki</button>
        </a>
    </span>
    
    <form method="POST">
        <button type="submit" name="go" class="btn btn-sm btn-success">Create the new wiki</button>
    </form>

    <hr />

    <h2>Articles that will be used for the new wiki:</h2>
    <ul>
    % for article in wiki.template:    
        <li><a href="{{article.link}}">{{article.title}}</a></li>
    % end
    </ul>

    <hr />

    % else:

    <hr/>

    <p>Sorry, no articles are tagged <code>@template</code> in the current wiki. Nothing will be copied.</p>
    <p>At least one article must be tagged <code>@template</code> to allow this wiki to be used as a template.</p>

    <hr/>

    <a href="{{wiki.link}}">
        <button type="button" class="btn btn-sm btn-warning">Quit creating new wiki</button>
    </a>

    % end

</main>

% include('includes/footer.tpl')