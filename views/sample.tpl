<!DOCTYPE html>
<html lang="en">
    <head>
        <title>{{title}}</title>        
        <meta charset="utf-8" />
        <script type="text/javascript" src="{{ url('static', path='jquery-1.8.2.min.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='jquery-ui.min.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='jquery-mousewheel.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='visualization_default.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='funcs.js') }}" charset="utf-8"></script>
        <link rel='stylesheet' href='{{ url('static', path='style.css') }}' />
        <link rel='stylesheet' href='{{ url('static', path='jquery-ui.min.css') }}' />
        <link rel='stylesheet' href='{{ url('static', path='visualization.css') }}' />
        
        <script type="text/javascript" src="{{ url('static_custom', path='visualization_TL_iou.js') }}" charset="utf-8"></script>
        <link rel='stylesheet' href='{{ url('static_custom', path='visualization_TL_iou.css') }}' />
    </head>
    <body>
        
        <h1><a href="/"><img id='logo' src='/static/Clova.png'></a>{{title}} <span class="right_anch"><a target="_blank" href="http://clova.ai/ocr">Visit our OCR Demo!</a></span></h1>
        
        % submitId, methodTitle, submitDate, methodResultJson = subm_data
        % import math
        % page = 1
        % if int(sample)>1:
            %page = (0 if sample % 20 == 0 else 1) + int(math.ceil(sample/20))  
        % end
        
        <div class="breadcrumbs">
            <a href='/'>Methods</a> > 
            <a href="/method/?m={{submitId}}&p={{page}}" style='margin-right: 40px;'>{{methodTitle}}</a>

            % if int(sample)>1:
                <a class="pure-button button-secondary" href="/sample/?m={{submitId}}&sample={{int(sample)-1}}">< previous</a>
            % end

            Sample {{sample}} of {{num_samples}}

            % if int(sample) < int(num_samples):
                <a class="pure-button button-secondary" href="/sample/?m={{submitId}}&sample={{int(sample)+1}}">next ></a>
            % end        
        </div>
        
        <div id='div_comparation'>
            <table class='sample_methods'>
                <thead>
                    <th>Method</th>
                    <% 
                    num_column = -1
                    num_column_order = -1
                    for k,v in sample_params['Detection'].items():
                       num_column+=1
                       if v['order'] != "":
                           num_column_order = num_column
                           sort_order = v['order']
                       end
                       %>
                       <th>{{v['long_name']}}</th>
                    <% end
                    for k,v in sample_params['EndtoEnd'].items():
                       num_column+=1
                       if v['order'] != "":
                           num_column_order = num_column
                           sort_order = v['order']
                       end
                       %>
                       <th>{{v['long_name']}}</th>
                    % end
                </thead>
                <tbody>
                    <%
                    samplesData = []
                    sort_by_e2e = True
                    for row in samplesValues:
                        sampleData = [row['id'],row['title']]
                        for k,v in sample_params['Detection'].items():
                            sampleData.append(row['Detection'][k])
                        end
                        for k,v in sample_params['EndtoEnd'].items():
                            if 'EndtoEnd' in row:
                                sampleData.append(row['EndtoEnd'][k])
                            else:
                                if row['id']==submitId:
                                    sort_by_e2e = False
                                end
                                sampleData.append(0.0)
                            end
                        end
                        samplesData.append(sampleData)
                    end
                    if not sort_by_e2e:
                        num_column_order -= 3
                    end
                    samplesData = sorted(samplesData, key=lambda sample: sample[num_column_order],reverse=sort_order=="desc")                    
                    for row in samplesData:
                        methodClass = "current" if row[0]==submitId else "other"
                    %>
                        <tr class="{{methodClass}}">
                            <td>{{row[1]}}</td>
                            <%  index = 2 #omit fields id,title
                                for k,v in sample_params['Detection'].items():
                                    colValue = row[index]
                                    if v['format'] == "perc" :
                                        value = str(round(colValue*100,2)) + " %"
                                    elif v['type'] == "double" :
                                        value = str(round(colValue*100,2))
                                    else:
                                        value = colValue
                                    end                                 
                                    index = index+1
                            %>
                                    <td>{{value}}</td>
                            <%  end
                                for k,v in sample_params['EndtoEnd'].items():
                                    colValue = row[index]
                                    if v['format'] == "perc" :
                                        value = str(round(colValue*100,2)) + " %"
                                    elif v['type'] == "double" :
                                        value = str(round(colValue*100,2))
                                    else:
                                        value = colValue
                                    end                                 
                                    index = index+1
                            %>
                                <td>{{value}}</td>
                            % end
                        </tr>
                    % end
                    </tbody>
            </table>
        </div>
        
        <div id='div_sample'></div>
        
    </body>
</html>