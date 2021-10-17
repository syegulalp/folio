<div id="wiki-listing">
% for wiki in wikis:
<div class="row wiki-listing-row">
    <div class="col-2">
    % if wiki.cover_img:
        <a href="{{wiki.link}}">
            <img src="{{wiki.cover_img}}" class="img-fluid" alt="{{wiki.title}}"></a>
    % end
        </div>
        <div class="col-10">
            <h3 class="mt-0">
                <a href="{{wiki.link}}">{{wiki.title}}</a>
            </h3>
    % if wiki.description:
            <h4>{{wiki.description}}</h4>
    % end
            <ul>
                <li>{{wiki.articles.count()}} articles</li>
                <li>Last edited: {{wiki.last_edited}}</li>
            </ul>
        </div>
    </div>
% end
</div>