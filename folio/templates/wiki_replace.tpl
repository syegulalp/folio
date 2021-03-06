% include('includes/header.tpl')

<main role="main" class="container-wiki">

    <div id="article-row" class="row">
        <div id="article-col" class="col">

            % include('includes/messages.tpl')

            <h1>Search {{wiki.title}}</h1>

            <form method="POST">

                <div id="wiki-search" class="form-group">
                    <label for="search_query">Search for (case-sensitive):</label>
                    <input autofocus="autofocus" class="form-control form-control-lg"
                        placeholder="Any string of characters" id="search_query" name="search_query"
                        value="{{search_query}}">
                </div>

                <div id="wiki-replace" class="form-group">
                    <label for="replace_query">Replace with:</label>
                    <input autofocus="autofocus" class="form-control form-control-lg"
                        placeholder="Any string of characters" id="replace_query" name="replace_query"
                        value="{{replace_query}}">
                </div>                

                <div id="wiki-buttons">

                    <span class="float-right">
                        <a href="{{wiki.link}}">
                            <button type="button" class="btn btn-sm btn-warning">Quit searching</button>
                        </a>
                    </span>

                    % if search_results and replace_query:

                    <button type="submit" name="replace" value="replace" class="btn btn-sm btn-danger">Replace all</button>

                    <button type="submit" name="search" value="search" class="btn btn-sm btn-success">Search again</button>

                    % else:

                    <button type="submit" name="search" value="search" class="btn btn-sm btn-success">Search</button>

                    % end

                </div>
                <hr />
            </form>

            % if search_results:
                % for result in search_results:
                    <h3><a href="{{result.link}}">{{ result.title }}</a></h3>
                    % last_find = 0
                    % while last_find != -1:
                        % extract_position_start = result.content.find(result_query, last_find)
                        % if extract_position_start == -1:
                        % last_find = -1
                        % continue
                        % end
                        % content_length = len(result.content)                                
                        % extract_position_end = extract_position_start+len(result_query)
                        <p>... {{result.content[max(0, extract_position_start-30):extract_position_start]}}<b><a href="{{result.link}}">{{result_query}}</a></b>{{result.content[extract_position_end:min(content_length, extract_position_end+30)]}} ...
                        </p>
                        % last_find = extract_position_start+1
                    % end
                % end
            % end

        </div>
        <div id="sidebar" class="sidebar-col">
            % include('includes/sidebar.tpl')
        </div>
    </div>

</main>

% include('includes/footer.tpl')