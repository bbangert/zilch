${display_httpexception(last_event)}
<%def name="display_httpexception(event)">
<section class="httpexception">
    <% extra = event.data.get('extra', {}) %>
    <div class="plain_traceback">
        <pre>
        ${event.data['traceback']}
        </pre>
    </div>
    <div class="full_traceback">
        ${full_traceback(event.data['frames'])}
    </div>
    % if 'CGI Variables' in extra:
    <div class="cgi">
        ${display_table('CGI Variables', ('Variable', 'Value'), extra['CGI Variables'])}
    </div>
    % endif
    % if 'WSGI Variables' in extra:
    <div class="wsgi">
        ${display_table('WSGI Variables', ('Variable', 'Value'), extra['WSGI Variables'])}
    </div>
    % endif
</section>
</%def>
<%def name="full_traceback(frames)">
<div class="traceback-frames">
% for frame in frames:
    <div class="frame">
        <h4>File <cite class="filename">${frame['filename']}</cite>,
            line <em class="line">${frame['lineno']}</em>,
            in <code class="function">${frame['function']}</code></h4>
        <pre>${frame.get('context_line')}</pre>
        <div class="localvars">
            ${display_table('Local Variables', ('Variable', 'Value'), frame['vars'], 4)}
        </div>
    </div>
% endfor
</div>
</%def>
<%def name="display_table(header_name, table_header, table_dict, header_type='3')">
<h${header_type}>${header_name}</h${header_type}>
<table>
    <thead>
        % for header in table_header:
        <th>${header}</th>
        % endfor
    </thead>
    <tbody>
    % for key in sorted(table_dict.keys()):
        <tr>
            <td>${key}</td><td>${table_dict[key]}</td>
        </tr>
    % endfor
    </tbody>
</table>

</%def>
<%def name="title()">${parent.title()} - Group ${group.id}</%def>
<%inherit file="layout.mak"/>
<%!
import pprint
%>
