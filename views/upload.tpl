<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>{{title}}</title>
        <link rel='stylesheet' href='{{ url('static', path='style.css') }}' />        
    </head>
    <body>
        
        <h1><a href="http://rrc.cvc.uab.es/" target="_blank"><img id='logo' src='/static/CVC.png'></a>{{title}}</h1>
        
        <div class='breadcrumbs'>
            <a href='/'>Methods</a>
        </div>    
        
        % if resDict['calculated']==False:
            <h2>The method has not been calculated</h2>
            <p>{{resDict['Message']}}</p>
        %else:
            <h2>The method has been calculated</h2>
            <p>See the <a href='/method/?m={{id}}'>method results</a></p>
        % end
        
    </body>
</html>