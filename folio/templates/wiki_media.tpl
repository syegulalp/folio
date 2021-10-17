% include('includes/header.tpl')

<main role="main" class="container-wiki">

  <div id="article-row" class="row">
    <div id="article-col" class="col">
      <h2>Media for {{wiki.title}}</h2>
      <div >
        <p style="background-color:blue" id="paste-area">To insert an image from the clipboard, click here, then paste (Ctrl-V).</p>
      </div>
      <hr />
      <center>{{!paginator}}</center>
      <p>
        % if media.count()==0:
        [<i>No media in this wiki. Drag images anywhere onto this page to upload media.</i>]
        % else:
        % col = 0
        % for media_item in media:
        % if col == 0:
      <div class="row">
        % end
        <div class="col-3 img-gallery">
          <a class="img-gallery-title" href="{{media_item.edit_link}}">{{media_item.file_path}}</a><br>
          <a href="{{media_item.edit_link}}"><img class="img-fluid align-self-start"
              src="{{media_item.link}}"></a>
        </div>
        % col += 1
        % if col == 4:
      </div>
      % col = 0
      % end
      % end
      % if col!=0:
    </div>
    % end
    % end

    <p>
      <center>{{!paginator}}</center>
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