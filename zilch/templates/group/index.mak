<table width="100%">
    <thead>
        <tr>
            <th>Message</th>
            <th>Tags</th>
            <th>Type</th>
            <th>Times Seen</th>
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
        <td>${group.last_seen}</td>
        <td>${group.first_seen}</td>
    </tr>
    % endfor
    </tbody>
</table>

<%inherit file="layout.mak"/>
