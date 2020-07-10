% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">
      <h2>Media for {{wiki.title}}</h2>
      <div id="paste-area">
        <p>To insert an image from the clipboard, click here, then paste.</p>
      </div>
      <hr />
      {{!paginator}}
      <p>
      <ul class="list-unstyled">
        % if media.count()==0:
        [<i>No media in this wiki. Drag images anywhere onto this page to upload media.</i>]
        % else:
        % for media_item in media:
        <li class="media">
          <a href="{{media_item.edit_link}}"><img class="img-fluid align-self-start mr-3" src="{{media_item.link}}"></a>
          <div class="media-body">
            <a href="{{media_item.edit_link}}">{{media_item.file_path}}</a>
          </div>
        </li>
        % end
        % end
      </ul>
      <p>
      {{!paginator}}
      <hr />
    </div>
    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
    </div>
  </div>

</main>

% include('includes/footer.tpl')

<script>
  var mediaPaste = "{{wiki.media_paste_link}}";
  $("#paste-area").on("paste", handleImagePaste);
</script>