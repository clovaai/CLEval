% import json
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>{{title}}</title>
        <meta charset="utf-8" />
        <link rel='stylesheet' href='{{ url('static', path='style.css') }}' />
        <script type="text/javascript" src="{{ url('static', path='jquery-1.8.2.min.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='jquery.form-3.51.js') }}" charset="utf-8"></script>             
        <script type="text/javascript" src="{{ url('static', path='ranking.js') }}" charset="utf-8"></script>        
        <script type='text/javascript' src='https://www.google.com/jsapi'></script>
        <script>
            $(document).ready(function() {
                $(".tab_content").hide(); //Hide all content
                $("ul.tabs li:first").addClass("active").show(); //Activate first tab
                $(".tab_content:first").show(); //Show first tab content

                $("ul.tabs li").click(function() {
                    $("ul.tabs li").removeClass("active"); //Remove any "active" class
                    $(this).addClass("active"); //Add "active" class to selected tab
                    $(".tab_content").hide(); //Hide all tab content
                    
                    var activeTab = $(this).find("a").attr("href"); //Find the href attribute value to identify the active tab + content
                    $(activeTab).fadeIn(); //Fade in the active ID content
                    if (activeTab === '#tab2') {
                        $('#inp_transcription').prop('checked', true);
                        $('#inp_transcription').attr('disabled', true);
                    } else {
                        $('#inp_transcription').prop('checked', false);
                        $('#inp_transcription').removeAttr('disabled');
                    }
                    return false;
                });
                
                $("input:radio[name=mode]").click(function() {
                    var st = $(":input:radio[name=mode]:checked").val();
                    if (st === 'endtoend') {
                        $('#inp_transcription').prop('checked', true);
                        $('#inp_transcription').attr('disabled', true);
                    } else {
                        $('#inp_transcription').prop('checked', false);
                        $('#inp_transcription').removeAttr('disabled');
                    }
                });
            });
        </script>
    </head>
    <body>
        <h1><a href="/"><img id='logo' src='/static/Clova.png'></a>{{title}} <span class="right_anch"><a target="_blank" href="http://clova.ai/ocr">Visit our OCR Demo!</a></span></h1>
        
        <div class='breadcrumbs'>
            Methods
            % if len(subm_data)>0:
                <button class='ml20 button-error pure-button' onclick="delete_methods()">Delete all methods</button> <span class="small">(You can also delete all methods by supressing all files from the output folder)</span>
            % end
            
            <a class="right" href="/exit">Exit</a><br />
        </div>
        
        <form action="/evaluate" method="post" enctype="multipart/form-data">
          UPLOAD YOUR METHOD <br /><br />
          <label for='inp_title'>Method Name:</label><input type='text' name='title' maxlength="50" id='inp_title'><br />
          <label for='inp_mode'>Evaluation: </label><input type='radio' name='mode' id='inp_detection' value='detection' checked>Detection
                                                    <input type='radio' name='mode' id='inp_endtoend' value='endtoend'>End-to-End<br />
          Result Format:
          <label for='inp_transcription'>Transcription: </label><input type='checkbox' name='transcription' id='inp_transcription'>
          <label for='inp_confidence'>Confidence: </label><input type='checkbox' name='confidence' id='inp_confidence'> <br />
          File:
          <input type="file" name="submissionFile" />
          % for k,v in submit_params.items():
                <label for='inp_{{k}}'>{{v['title']}}: </label>
                <select id='inp_{{k}}' name='{{k}}'>
                % for option in v['values']:
                    <option value='{{option['value']}}'>{{option['name']}}</option>
                % end
                </select>
          % end
          <br /><br /><button class="pure-button pure-button-primary" type="button" onclick="upload_subm()" >Evaluate</button>
        </form>
        <p class='info'>- Dataset files of this Standalone: <a href='gt/images.zip'>Images</a> - <a href='gt/gt.{{extension}}'>Ground Truth</a> <button class="ml20 pure-button pure-button-secondary" type="button" onclick="instructions()" >See upload instructions..</button><br />
        </p>
        <div id='div_instructions' class='hidden'>
            <div class='wrap'><button class='close pure-button button-error'>close</button><h1>Upload instructions</h1>
            <p class='info'>Note that the following instructions are for the Test Dataset, the example links may not work here if the dataset is not the Test Set.</p>
            {{ !instructions }}
            </div>
        </div>
        <div id="wrapper">
            <ul class="tabs">
                <li><a href="#tab1">Result - Detection</a></li>
                <li><a href="#tab2">Result - EndtoEnd</a></li>
            </ul>

            <div class="tab_container">
                <div id="tab1" class="tab_content">
                <%
                if len(subm_data)>0:
                    graphicRows = []
                    graphic2Rows = []
                %>
                <div class='flex'>
                    <div class="sameRow">
                        <table class='results ib'>
                        <thead>
                            <th>Method</th>
                            <th>Submit date</th>
                            <% 
                            row = ["'Title'"]
                            row2 = ["'Title'"]
                            num_column = -1
                            num_column_order = -1
                            show2ndGraphic = False
                            for k,v in method_params['Detection'].items():
                                num_column+=1
                                if v['grafic'] == "1":
                                    row.append("'" + v['long_name'] + "'")
                                elif v['grafic'] == "2":
                                    row2.append("'" + v['long_name'] + "'")
                                end
                                if v['order'] != "":
                                    if v['grafic'] == "1":
                                        num_column_order = num_column
                                        sort_name = k
                                        sort_name_long = v['long_name']
                                        sort_order = v['order']
                                        sort_format = v['format']
                                        sort_type = v['type']
                                    elif v['grafic'] == "2":
                                        show2ndGraphic = True
                                        sort2_name = k
                                        sort2_name_long = v['long_name']
                                        sort2_order = v['order']
                                        sort2_format = v['format']
                                        sort2_type = v['type']
                                    end
                                end         
                            %>
                            <th>{{v['long_name']}}</th>
                            <%
                            end
                            for k,v in method_params['Detection_Metadata'].items():
                                num_column+=1
                                if v['grafic'] == "1":
                                    row.append("'" + v['long_name'] + "'")
                                elif v['grafic'] == "2":
                                    row2.append("'" + v['long_name'] + "'")
                                end
                                if v['order'] != "":
                                    if v['grafic'] == "1":
                                        num_column_order = num_column
                                        sort_name = k
                                        sort_name_long = v['long_name']
                                        sort_order = v['order']
                                        sort_format = v['format']
                                        sort_type = v['type']
                                    elif v['grafic'] == "2":
                                        show2ndGraphic = True
                                        sort2_name = k
                                        sort2_name_long = v['long_name']
                                        sort2_order = v['order']
                                        sort2_format = v['format']
                                        sort2_type = v['type']
                                    end
                                end
                            %>
                            <th>{{v['long_name']}}</th>
                            % end
                            % graphicRows.append("[" + ','.join(row) + "]")
                            % graphic2Rows.append("[" + ','.join(row2) + "]")
                        <th></th>
                        </thead>
                        <tbody>
                        <%
                        methodsData = []
                        for id, title, date, methodResultJson in subm_data:
                            methodData = [id, title, date]
                            methodResult = json.loads(methodResultJson)
                            for k,v in method_params.items():
                                methodData.append(methodResult[k])
                            end
                            methodsData.append(methodData)
                        end
                        methodsData = sorted(methodsData, key=lambda methodData: methodData[2],reverse=sort_order=="desc")
                        for methodData in methodsData:
                            id = methodData[0]
                            title = methodData[1]
                            date = methodData[2]
                        %>
                        <tr>
                            <td><a class='methodname' href='method/?m={{id}}'>{{id}}: <span class="title">{{title}}</span></a></td>
                            <td><a href='method/?m={{id}}'>{{date}}</a></td>
                        <%
                            row = ["'" + title.replace("'","\'") + "'"]
                            row2 = ["'" + title.replace("'","\'") + "'"]
                            index=0
                            
                            # Detection ( ==methodData[3] )
                            det_result = dict(methodData[3])
                            for k,v in method_params['Detection'].items():
                                colValue = det_result[k]
                                if v['format'] == "perc" :
                                    value = str(round(colValue*100,2)) + " %"
                                    graphicValue = "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + " %'}";
                                elif v['type'] == "double" :
                                    value = str(round(colValue*100,2))
                                    graphicValue =  "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + "'}";
                                else:
                                    value = colValue
                                    graphicValue = "{v:" + str(colValue) + ", f:'" + str(colValue) + "'}";
                                end
                                if v['grafic'] == "1":
                                    row.append(graphicValue)
                                elif v['grafic'] == "2":
                                    row2.append(graphicValue)
                                end 
                        %>
                            <td>{{value}}</td>
                        <%
                                index += 1
                            end
                        %>
                        <%
                        meta_result = dict(methodData[5])
                        for k,v in method_params['Detection_Metadata'].items():
                            colValue = meta_result[k]
                            if v['format'] == "perc" :
                                value = str(round(colValue*100,2)) + " %"
                                graphicValue = "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + " %'}";
                            elif v['type'] == "double" :
                                value = str(round(colValue*100,2))
                                graphicValue =  "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + "'}";
                            else:
                                value = colValue
                                graphicValue = "{v:" + str(colValue) + ", f:'" + str(colValue) + "'}";
                            end                    
                            if v['grafic'] == "1":
                                row.append(graphicValue)
                            elif v['grafic'] == "2":
                                row2.append(graphicValue)
                            end
                        %>
                            <td>{{value}}</td>
                        <%
                            index += 1
                        end %>
                        <td><button class="mr5 pure-button" onclick="edit_method({{id}},this)">edit</button><button class="pure-button button-error"  onclick="delete_method({{id}})">x</button></td>
                        </tr>
                        % end
                        </tbody>
                        </table>
                    </div>
                </div>
            </div>
                <!-- End-to-End tab -->
                <div id="tab2" class="tab_content">
                <%
                if len(subm_data)>0:
                    graphicRows = []
                    graphic2Rows = []
                %>
                <div class='flex'>
                    <div class="sameRow">
                        <table class='results ib'>
                        <thead>
                            <th>Method</th>
                            <th>Submit date</th>
                            <% 
                            row = ["'Title'"]
                            row2 = ["'Title'"]
                            num_column = -1
                            num_column_order = -1
                            show2ndGraphic = False
                            for k,v in method_params['EndtoEnd'].items():
                                num_column+=1
                                if v['grafic'] == "1":
                                    row.append("'" + v['long_name'] + "'")
                                elif v['grafic'] == "2":
                                    row2.append("'" + v['long_name'] + "'")
                                end
                                if v['order'] != "":
                                    if v['grafic'] == "1":
                                        num_column_order = num_column
                                        sort_name = k
                                        sort_name_long = v['long_name']
                                        sort_order = v['order']
                                        sort_format = v['format']
                                        sort_type = v['type']
                                    elif v['grafic'] == "2":
                                        show2ndGraphic = True
                                        sort2_name = k
                                        sort2_name_long = v['long_name']
                                        sort2_order = v['order']
                                        sort2_format = v['format']
                                        sort2_type = v['type']
                                    end
                                end         
                            %>
                            <th>{{v['long_name']}}</th>
                            <%
                            end
                            for k,v in method_params['EndtoEnd_Metadata'].items():
                                num_column+=1
                                if v['grafic'] == "1":
                                    row.append("'" + v['long_name'] + "'")
                                elif v['grafic'] == "2":
                                    row2.append("'" + v['long_name'] + "'")
                                end
                                if v['order'] != "":
                                    if v['grafic'] == "1":
                                        num_column_order = num_column
                                        sort_name = k
                                        sort_name_long = v['long_name']
                                        sort_order = v['order']
                                        sort_format = v['format']
                                        sort_type = v['type']
                                    elif v['grafic'] == "2":
                                        show2ndGraphic = True
                                        sort2_name = k
                                        sort2_name_long = v['long_name']
                                        sort2_order = v['order']
                                        sort2_format = v['format']
                                        sort2_type = v['type']
                                    end
                                end
                            %>
                            <th>{{v['long_name']}}</th>
                            % end
                            % graphicRows.append("[" + ','.join(row) + "]")
                            % graphic2Rows.append("[" + ','.join(row2) + "]")
                        <th></th>
                        </thead>
                        <tbody>
                        <%
                        methodsData = []
                        for id, title, date, methodResultJson in subm_data:
                            methodData = [id, title, date]
                            methodResult = json.loads(methodResultJson)
                            if methodResult['EndtoEnd']['hmean'] != 0:
                                for k,v in method_params.items():
                                    methodData.append(methodResult[k])
                                end
                                methodsData.append(methodData)
                            end
                        end
                        methodsData = sorted(methodsData, key=lambda methodData: methodData[2],reverse=sort_order=="desc")
                        for methodData in methodsData:
                            id = methodData[0]
                            title = methodData[1]
                            date = methodData[2]
                        %>
                        <tr>
                            <td><a class='methodname' href='method/?m={{id}}'>{{id}}: <span class="title">{{title}}</span></a></td>
                            <td><a href='method/?m={{id}}'>{{date}}</a></td>
                        <%
                            row = ["'" + title.replace("'","\'") + "'"]
                            row2 = ["'" + title.replace("'","\'") + "'"]
                            index=0
                            
                            # End-to-End ( ==methodData[4] )
                            e2e_result = dict(methodData[4])
                            for k,v in method_params['EndtoEnd'].items():
                                colValue = e2e_result[k]
                                if v['format'] == "perc" :
                                    value = str(round(colValue*100,2)) + " %"
                                    graphicValue = "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + " %'}";
                                elif v['type'] == "double" :
                                    value = str(round(colValue*100,2))
                                    graphicValue =  "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + "'}";
                                else:
                                    value = colValue
                                    graphicValue = "{v:" + str(colValue) + ", f:'" + str(colValue) + "'}";
                                end
                                if v['grafic'] == "1":
                                    row.append(graphicValue)
                                elif v['grafic'] == "2":
                                    row2.append(graphicValue)
                                end 
                        %>
                            <td>{{value}}</td>
                        <%
                                index += 1
                            end
                        %>
                        <%
                        # End-to-End Metadata ( ==methodData[6] )
                        e2e_meta_result = dict(methodData[6])
                        for k,v in method_params['EndtoEnd_Metadata'].items():
                            colValue = e2e_meta_result[k]
                            if v['format'] == "perc" :
                                value = str(round(colValue*100,2)) + " %"
                                graphicValue = "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + " %'}";
                            elif v['type'] == "double" :
                                value = str(round(colValue*100,2))
                                graphicValue =  "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + "'}";
                            else:
                                value = colValue
                                graphicValue = "{v:" + str(colValue) + ", f:'" + str(colValue) + "'}";
                            end                    
                            if v['grafic'] == "1":
                                row.append(graphicValue)
                            elif v['grafic'] == "2":
                                row2.append(graphicValue)
                            end
                        %>
                            <td>{{value}}</td>
                        <%
                            index += 1
                        end %>
                        <td><button class="mr5 pure-button" onclick="edit_method({{id}},this)">edit</button><button class="pure-button button-error"  onclick="delete_method({{id}})">x</button></td>
                        </tr>
                        % end
                        </tbody>
                        </table>
                    </div>
                </div>
            </div>
    </body>
</html>