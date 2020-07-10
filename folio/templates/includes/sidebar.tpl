% if wiki.sidebar_cache:
{{!wiki.sidebar_cache}}
% else:

% if wiki.cover_img:
<div class="wiki-cover-img">
    <a href="{{wiki.homepage_link}}"><img class="img img-fluid" src="{{wiki.cover_img}}"></a>
</div>
% end

<div class="wiki-title">
    <a href="{{wiki.homepage_link}}" title="Start page">{{wiki.title}}</a>
</div>
<div class="wiki-description">
    {{wiki.description}}
</div>
<div class="wiki-icons">
<a href="{{wiki.new_page_link}}" title="Create new wiki entry"><span class="oi oi-file"></span></a>
<a id="wiki_search_link" href="{{wiki.search_link}}"><span title="Search this wiki" class="oi oi-magnifying-glass"></span></a>
<a href="{{wiki.media_link}}"><span title="See wiki media" class="oi oi-image"></span></a>
<a href="{{wiki.edit_link}}" title="Edit wiki settings"><span class="oi oi-cog"></span></a>
<a href="{{wiki.server_homepage_link}}"><span title="Wiki server homepage" class="oi oi-home"></span></a>

</div>  

<div class="wiki-sidebar-controls">

    <ul class="nav nav-tabs" id="sidebar_tabs">
        <li class="nav-item">
            <a title="Most recently edited articles" class="nav-link active" id="tab_history" data-toggle="tab"
                aria-controls="history" aria-selected="true" role="tab" href="#history">History</a>
        </li>
        <li class="nav-item">
            <a title="All articles in this wiki" class="nav-link" id="tab_articles" data-toggle="tab"
                aria-controls="articles" aria-selected="false" role="tab" href="#articles">Articles</a>
        </li>
        <li class="nav-item">
            <a title="All tags in this wiki" class="nav-link" id="tab_tags" data-toggle="tab" aria-controls="tags"
                aria-selected="false" role="tab" href="#tags">Tags</a>
        </li>
    </ul>

    <div class="tab-content">
        <div class="tab-pane active" id="history" role="tabpanel" aria-labelledby="tab_history">
            <div class="wiki-recent-list">
                % include('includes/recent_article_list.tpl')
            </div>
        </div>
        <div class="tab-pane" id="articles" role="tabpanel" aria-labelledby="tab_articles">
            
            <ul class="nav nav-tabs" id="article_tabs">
                <li class="nav-item">
                    <a title="All articles" class="nav-link active" id="tab-articles-all" data-toggle="tab" aria-controls="all-articles" aria-selected="false" role="tab" href="#all-articles">Live</a>
                </li>
                <li class="nav-item">
                    <a title="Drafts" class="nav-link" id="tab-articles-drafts" data-toggle="tab" aria-controls="articles-drafts" aria-selected="false" role="tab" href="#articles-drafts">Drafts</a>
                </li>                
            </ul>
            <div class="tab-content">
                <div class="tab-pane active" id="all-articles" role="tabpanel" aria-labelledby="all-articles">
                    <div class="wiki-all-articles">
                        % include('includes/all_article_list.tpl')
                    </div>
                </div>
                <div class="tab-pane" id="articles-drafts" role="tabpanel" aria-labelledby="articles-drafts">
                    <div class="wiki-draft-articles">
                        % include('includes/draft_article_list.tpl')
                    </div>                    
                </div>
            </div>

        </div>
        <div class="tab-pane" id="tags" role="tabpanel" aria-labelledby="tag_tags">
            <div class="wiki-tag-items">
                % include('includes/wiki_tag_list.tpl')
            </div>
        </div>
    </div>

</div>

% end