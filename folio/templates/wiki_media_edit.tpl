% include('includes/header.tpl')

<main role="main" class="container-wiki">

  % include('includes/messages.tpl')
  % filename_body, filename_ext = media.file_path.rsplit('.',1)
  
  <div id="article-row" class="row">
    <div id="article-col" class="col">

      <h2>{{media.file_path}}</h2>
      <hr />
      <div class="row">
        <div class="col-6">
          <img class="img-fluid" src="{{media.link}}">
        </div>
        <div class="col-6">
          <form method="POST">

            <label for="media-filename">Filename (edit to change):</label>

            <div id="media-filename-div" class="input-group mb-3">
              <input class="form-control form-control-lg" placeholder="{{filename_body}}" id="media-filename"
                name="media-filename" value="{{filename_body}}">

              <div class="input-group-append">
                <span class="input-group-text" id="basic-addon2">.{{filename_ext}}</span>
              </div>

            </div>

            <label for="media-datetime">Date uploaded:</label>

            <div id="media-datetime-div" class="input-group mb-3">
              <input class="form-control form-control-lg" placeholder="{{filename_body}}" id="media-datetime" value="{{media.uploaded_on}}" disabled>
            </div>

            <div class="input-group mb-3">
              <button type="submit" name="save" value="save" class="btn btn-sm btn-success">Save changes to filename</button>
            </div>

            <div class="input-group mb-3">
              <button type="submit" name="select" value="select" class="btn btn-sm btn-info">Use this image as the
                wiki's cover image</button>
            </div>            

          </form>

        </div>
      </div>
      <hr />
      <a href="{{media.delete_link}}">
        <button type="button" class="btn btn-sm btn-danger">Delete this image</button>
      </a>
    </div>
    <div id="sidebar" class="sidebar-col">
      % include('includes/sidebar.tpl')
    </div>
  </div>

</main>

% include('includes/footer.tpl')