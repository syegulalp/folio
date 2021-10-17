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
      <div class="mb-3" id="wiki-search-div">
      <input class="form-control" id="wiki-search" placeholder="Type to search by name">
      </div>
      
      % include('includes/wiki_listing.tpl')    
      
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
% wiki = wikis[0]
% include('includes/footer.tpl')
<script src="{{wiki.static_folder_link}}/homesearch.js"></script>