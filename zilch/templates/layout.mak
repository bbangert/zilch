<!doctype html> 
<html lang="en"> 
    <head>
        <meta charset="UTF-8"> 
        <title>${self.title()}</title>
        <!--[if lt IE 9]>
        <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
        <![endif]--> 
    </head>
    <body>
        ${next.body()}
    </body>
</html>
<%def name="title()">zilch</%def>
