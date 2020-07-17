% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">
      % include('includes/messages.tpl')
      % for article in articles:
      % include('includes/article_core.tpl')
      <hr style="clear: both;">
      % end
    </div>
    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
    </div>
  </div>

</main>

% include('includes/footer.tpl')

<script src="{{wiki.static_folder_link}}/article.js?0.0.6"></script>
