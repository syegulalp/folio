<!doctype html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <link rel="stylesheet" href="{{ wiki.static_folder_link }}/bootstrap.css">
  <link href="{{ wiki.static_folder_link }}/open-iconic-bootstrap.css" rel="stylesheet">
      <link href="{{ wiki.static_folder_link }}/wiki.css?{{wiki.settings.PRODUCT_VERSION}}" rel="stylesheet">
    <title>{{page_title if "page_title" in locals() else wiki.title}}</title>
    % for css in getattr(wiki.config, "CSS",[]):
    <link href="{{ wiki.static_folder_link }}/{{css}}?{{wiki.settings.PRODUCT_VERSION}}" rel="stylesheet">
    % end
</head>

<body>
  <div id="drop-target"></div>
  <div id="drop-message"></div>