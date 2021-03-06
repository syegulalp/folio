% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">
      <h2>Revision history for <a href="{{article.link}}">{{article.title}}</a></h2>
      <hr/>
      % if article.revisions.count()==0:
      <h3>[No revisions saved for this article]</h3>
      % else:
      <ul class="list">
        % for revision in article.revisions_chrono:
        <li><a href="{{revision.id_link}}">{{revision.formatted_date}}</a></li> 
        % end
      </ul>
      % end
      <hr/>
    </div>
    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
    </div>
  </div>

</main>

% include('includes/footer.tpl')