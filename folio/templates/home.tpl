% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div class="container">

    % include('includes/messages.tpl')
    
    <h1>Your Wikis</h1>
    <hr />

    <a href="/new"><button type="button" class="btn btn-sm btn-success">Create a new wiki</button></a>

    <hr />

    <div class="row">
      <div class="col-8">
        % for wiki in wikis:
        <div class="row wiki-listing-row">
          <div class="col-2">
            % if wiki.cover_img:
            <a href="{{wiki.link}}"><img src="{{wiki.cover_img}}" class="img-fluid" alt="{{wiki.title}}"></a>
            % end
          </div>
          <div class="col-10">
            <h3 class="mt-0"><a href="{{wiki.link}}">{{wiki.title}}</a></h3>
            % if wiki.description:
            <h4>{{wiki.description}}</h4>
            % end
            <ul>          
              <li>{{wiki.articles.count()}} articles</li>
              <li>Last edited: {{wiki.last_edited}}</li>
            </ul>      </div>
        </div>
        % end
    
      </div>
      <div class="col-4">
        <h2>Most recently edited:</h2>
        <ul>
        % for article in articles:
          <li><b><a href="{{article.link}}">{{article.title}}</a></b> / <a href="{{article.wiki.link}}">{{article.wiki.title}}</a> ({{article.formatted_date}})</li>
        % end
        </ul>
      </div>
    </div>

  </div>

</main>

% include('includes/footer.tpl')