% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">
      % include('includes/messages.tpl')
      <h2>List of all tags in this wiki</h2>
      <ul>
        % for tag in tags:
        <li><a href="{{tag.link}}">{{tag.title}}</a></li>
        % end
      </ul>
      <hr />
    </div>

    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
      <hr />
    </div>
  </div>

</main>

% include('includes/footer.tpl')