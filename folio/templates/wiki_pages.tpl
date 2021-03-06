% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">

      % include('includes/messages.tpl')
      <h2>List of all articles in this wiki tagged <b>{{tag.title}}</b></h2>

      % if article_with_tag_name:
      <h3><a href="{{article_with_tag_name.link}}">{{article_with_tag_name.title}}</a> is also an article in this wiki.
      </h3>
      % else:
      <h4>(No article named <a href="{{tag.as_article.edit_link}}">{{tag.title}}</a> - click to create)</h4>
      % end

      <ul>
        % for article in articles:
        <li><a href="{{article.link}}">{{article.title}}</a></li>
        % end
      </ul>
      <hr />
    </div>

    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
    </div>
  </div>

</main>

% include('includes/footer.tpl')