% include('includes/header.tpl')

<main role="main" class="container-wiki">

  % include('includes/messages.tpl')

  <div class="row">
    <div class="col">

    </div>
    % if get("sidebar", True):
    <div id="sidebar" class="sidebar-col">
      % include includes/sidebar.tpl
    </div>
    % end
  </div>

</main>

% include('includes/footer.tpl')
