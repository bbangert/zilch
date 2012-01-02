<%def name="post_body()">
<section class="filters">
    <h3>Filters</h3>
    <div>
        <p>Apply Filter 1</p>
    </div>
</section>
</%def>

<h1>${group.message}</h1>

<p class="event">Event: 
<select id="event_selector" name="event_selection">
    % for ev in latest_events:
        <% current_event = ev.event_id==event.event_id %>
    <option value="${ev.event_id}" ${'selected="selected"' if current_event else ''}>${'-> ' if current_event else ''}${ev.event_id} - ${display_date(ev.datetime)}</option>
    % endfor
</select></p>

${display_httpexception(event)}

<%def name="javascript()">
${parent.javascript()}
<script>
$(document).ready(function() {
    $('div.traceback-frames div.frame > h4').toggle(function() {
        $(this).parent().find('pre.around, div.localvars').toggle();
        $(this).parent().find('pre.context_line').toggleClass('highlight');
        return false;
    }, function() {
        $(this).parent().find('pre.around, div.localvars').toggle();
        $(this).parent().find('pre.context_line').toggleClass('highlight');        
        return false;
    });
    
    $('div.traceback-frames div.frame h4:first').click();
    
    $('#event_selector').change(function() {
        document.location = '${request.application_url}/group/${group.id}/event/' + $(this).val()
        return false;
    });
    
    $('#show_hidden_frames').toggle(function () {
        $('div.frame.hidden').toggle();
        $(this).html('Hide Hidden Frames');
    }, function () {
        $(this).html('Show Hidden Frames');
        $('div.frame.hidden').toggle();        
    });
});
</script>
</%def>

<%def name="display_httpexception(event)">
<section class="httpexception">
    <% extra = event.data.get('extra', {}) %>
    <div class="tags">
    % for tag in sorted(event.tags, key=lambda v: v.name):
        <div class="tag"><mark span="name">${tag.name}</mark><em>${tag.value}</em></div>
    % endfor
    </div>
    <div class="full_traceback">
        ${full_traceback(event.data['frames'])}
    </div>
    % if 'CGI Variables' in extra:
    <div class="cgi">
        ${display_table('CGI Variables', ('Variable', 'Value'), extra['CGI Variables'], header_type=2)}
    </div>
    % endif
    % if 'WSGI Variables' in extra:
    <div class="wsgi">
        ${display_table('WSGI Variables', ('Variable', 'Value'), extra['WSGI Variables'], header_type=2)}
    </div>
    % endif
    <div class="plain_traceback">
        <h2>Plaintext Traceback</h2>
        <pre>
${event.data['traceback'].strip()}
</pre>
    </div>
</section>
</%def>
<%def name="full_traceback(frames)">
<div class="traceback-frames">
<% 
    visible = len(filter(lambda x: x['visible'] == 'False', frames)) == 0
%>
% if not visible:
<a id="show_hidden_frames" href="#">Show Hidden Frames</a>
% endif
% for frame in frames[::-1]:
    <div class="frame ${'hidden' if frame['visible'] == 'False' else ''}">
        <h4><cite class="module">${frame['module']}</cite>:
            <em class="line">${frame['lineno']}</em>,
            in <code class="function">${frame['function']}</code></h4>
        <div class="context">
            <pre class="around">${'\n'.join(frame.get('with_context', '').split('\n')[:5][-3:])}</pre>
            <pre class="context_line">${frame.get('context_line')}</pre>
            <pre class="around">${'\n'.join(frame.get('with_context', '').split('\n')[6:][:3])}</pre>
        </div>
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
            <td class="key">${key}</td><td>${table_dict[key]}</td>
        </tr>
    % endfor
    </tbody>
</table>

</%def>
<%def name="title()">${parent.title()} - Group ${group.id}</%def>
<%def name="breadcrumbs()">${parent.breadcrumbs()} &gt; ${group.id}</%def>
<%inherit file="layout.mak"/>
<%namespace file="/common.mak" import="display_date"/>
