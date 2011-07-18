<h1>Recent Grouped Events</h1>

<section>
    <table width="100%">
        <thead>
            <tr>
                <th>Message</th>
                <th>Tags</th>
                <th>Type</th>
                <th>Count</th>
                <th>Last Seen</th>
                <th>First Seen</th>
            </tr>
        </thead>
        <tbody>
        % for group in groups:
        <tr>
            <td><a href="${request.resource_url(request.context)}${group.id}">${group.message}</a></td>
            <td>${group.tags}</td>
            <td>${group.event_type.name}</td>
            <td>${group.count}</td>
            <td>${display_date(group.last_seen)}</td>
            <td>${display_date(group.first_seen)}</td>
        </tr>
        % endfor
        </tbody>
    </table>
</section>
<%def name="javascript()">
${parent.javascript()}
<script>
$(document).ready(function() {
    $('section table tr').click(function(event) {
        event.stopPropagation();
        document.location = $(this).find('td a').attr('href');
        return false;
    });
});
</script>
</%def>
<%inherit file="layout.mak"/>
<%namespace file="/common.mak" import="display_date"/>