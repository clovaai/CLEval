/* global web, visualization, ClassVisualization */

ClassVisualization.prototype.load_visualization = function(){

    var self = this;

    var sampleData = this.sampleData;

    var urlImg = "/image/?ch=" + getUrlParameter("ch") + "&task=" + getUrlParameter("task") + "&sample=" + getUrlParameter("sample") +  "&gtv=" + getUrlParameter("gtv");

    var template = "<div class='im_filters'><input type='checkbox' checked='checked' id='chk_image'><label for='chk_image'>Show Image</label></div>"+
                    "<div class='container_canvas'>" +
                    "<h3>Ground Truth</h3>" +
                    "<div id='div_canvas_gt'></div>" +
                   "</div>"+
                   "<div class='container_canvas'>" +
                    "<h3>Detection</h3>" +
                    "<div id='div_canvas_det'></div>" +
                   "</div>"+
                   "<div class='container_canvas'>" +
                    "<h3>Overlay</h3>" +
                    "<div id='div_canvas_overlay'></div>" +
                   "</div>"+
                   "<div class='container_canvas'>" +
                    "<h3>Logs</h3>" +
                    "<div id='div_logs'><span>loading...</span></div>" +
                   "</div>"+
                   "<img id='img_gt_image2'>"+
                   "<div class='div_sample_info'>"+
                   "<div id='div_precision' class='sameRow'><div class='div_table'><h3>Area Precision</h3></div></div>"+
                   "<div id='div_detail' class='sameRow'><div class='div_table'><h3>Scoring Detail</h3></div></div>"+
                   "<div id='div_char' class='sameRow' style='display: none;'><div class='div_table'><h3>Character score</h3>loading..</div></div>"+
                   "</div>";

    $("#div_sample").html(template);

    if(!this.image_details_loaded){
        this.image_details_loaded=true;
        this.init_image_details();
    }   
    this.image_loaded = false;
    this.draw();
    
    $("#chk_image").change(function(){
        self.draw();
    });

    $("#chk_pcc").change(function(){
        self.draw();
    });

    $("#overlay_image").change(function() {
        self.draw();
    });
    
    $("#img_gt_image2").attr("src",urlImg).one("load",function(){
        self.image_loaded = true;
        self.im_w = this.width;
        self.im_h = this.height;
        self.scale = Math.min($("#div_canvas_gt").width()/self.im_w,$("#div_canvas_det").height()/self.im_h );
        self.zoom_changed();
        self.correct_image_offset();
        self.draw();
    });

    var numGt = sampleData.gtPolPoints==undefined? 0 : sampleData.gtPolPoints.length;
    var numDet = sampleData.detPolPoints==undefined? 0 : sampleData.detPolPoints.length;

    var html_recall = "";
    var html_precision = "";

        var stylesMat = new Array();
        for ( var j=0;j<numGt+2;j++){
            stylesMat[j] = new Array();
            for ( var i=0;i<numDet+2;i++){
                stylesMat[j][i] = "value";
            }
        }
        
        sampleData.gtTypes = new Array();
        sampleData.detTypes = new Array();
        for ( var j=0;j<numGt;j++){
            var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
            sampleData.gtTypes.push( gtDontCare? 'DC' : 'NM' );
        }
        for ( var j=0;j<numDet;j++){
            var detDontCare = $.inArray(j,sampleData.detDontCare)>-1;
            sampleData.detTypes.push( detDontCare? 'DC' : 'NM' );
        }


        if (sampleData.pairs!=undefined){
            for ( var k=0;k<sampleData.pairs.length;k++){
                var pair = sampleData.pairs[k];
                
                var gts = new Array();
                var dets = new Array();
                
                if(pair.gt.length==undefined){
                    gts.push(pair.gt);
                }else{
                    gts = pair.gt;
                }
                if(pair.det.length==undefined){
                    dets.push(pair.det);
                }else{
                    dets = pair.det;
                }
                for(var i=0;i<gts.length;i++){
                    for(var j=0;j<dets.length;j++){
                        stylesMat[gts[i]][dets[j]] += " " + pair.type;
                        sampleData.gtTypes[gts[i]] = pair.type;
                        sampleData.detTypes[dets[j]] = pair.type;
                    }
                }
            }
        }
    
    // Area Precision logging
    if(numDet>100){
        html_precision = "<p class='red'>The algorithm has detected more than 100 bounding boxes, the visualization are not posible</p></p>";
    }else{        
        var html_precision = "<table><thead><tr><th>GT / Det</th>";
        for ( var i=0;i<numDet;i++){
            var detDontCare = $.inArray(i,sampleData.detDontCare)>-1;
            html_precision += "<th style='" + (detDontCare? "" : "font-weight:bold;") + "'>#" + i + "</th>";
        }
        html_precision += "</tr></thead><tbody id='tbody_precision'>";

        for ( var j=0;j<numGt;j++) {
            var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
            html_precision += "<tr>";
            html_precision += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>#" + j + "</td>";
            for ( var i=0;i<numDet;i++){

                var precisionClass = (sampleData.precisionMat[j][i]>=sampleData.evaluationParams.AREA_PRECISION_CONSTRAINT ? ' green' : ' red' );
                html_precision += "<td data-col='" + i + "' data-row='" + j + "' class='" + stylesMat[j][i] + " " + precisionClass + "'>" + Math.round(sampleData.precisionMat[j][i]*10000)/100 + "</td>";    
            }
            html_precision += "</tr>";
        }
        html_precision += "</tbody></table>";
    }
    $("#div_precision").html("<div class='div_table'><h3>Area Precision</h3>" + html_precision + "</div>");
    
        
    if(numDet>100){
        html_detail = "<p class='red'>The algorithm has detected more than 100 bounding boxes, the visualization are not posible</p></p>";
    }else{        
        var html_detail = "<table><thead><tr><th>GT / Det</th>";
        for ( var i=0;i<numDet;i++){
            var detDontCare = $.inArray(i,sampleData.detDontCare)>-1;
            html_detail += "<th style='" + (detDontCare? "" : "font-weight:bold;") + "'>#" + i + "</th>";
        }
        html_detail += "<th>Correct<br />Length</th>";
        html_detail += "<th>Granluarity<br />Penalty</th>";
        html_detail += "</tr></thead><tbody id='tbody_recall'>";

        for ( var j=0;j<numGt+2;j++){
            var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
            html_detail += "<tr>";
            if (j == numGt) {
                html_detail += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>" + "Correct<br />Length" +"</td>";
            } else if (j == numGt+1) {
                html_detail += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>" + "Granularity<br />Penalty" + "</td>";
            } else{
                html_detail += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>#" + j + "</td>";
            }
            for ( var i=0;i<numDet+2;i++){
                html_detail += "<td data-col='" + i + "' data-row='" + j + "' class='" + stylesMat[j][i] + "'>" + sampleData.detectionMat[j][i] + "</td>";    
            }
            html_detail += "</tr>";
        }
        html_detail += "</tbody></table>";
    }
    $("#div_detail").html("<div class='div_table'><h3>Scoring Detail(Detection, PCC)</h3>" + html_detail + "</div>");

    if (!(sampleData.evaluationParams.E2E)) {
        // print character score
        // if(numDet>100){
        //     html_char = "<p class='red'>The algorithm has detected more than 100 bounding boxes, the visualization are not posible</p></p>";
        // } else{
        //     var html_char = "<table><thead><tr><th>GT / Det</th>";
        //     for ( var i=0;i<numDet;i++){
        //         var detDontCare = $.inArray(i,sampleData.detDontCare)>-1;
        //         html_char += "<th style='" + (detDontCare? "" : "font-weight:bold;") + "'>#" + i + "</th>";
        //     }
        //     // html_char += "<th style='" + "font-weight:bold;" + "'>" + "Rec Score" + "</th>";
        //     html_char += "</tr></thead><tbody id='tbody_char'>";

        //     for ( var j=0;j<numGt;j++){
        //         var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
        //         html_char += "<tr>";
        //         html_char += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>#" + j + "</td>";
        //         for ( var i=0;i<numDet;i++){
        //             var charClass = 'green';
        //             html_char += "<td data-col='" + i + "' data-row='" + j + "' class='" + stylesMat[j][i] + " " + charClass + "'>" + sampleData.charCounts[j][i] + "</td>";
        //         }
        //         html_char += "<td data-col='" + (i+1) + "' data-row='" + j + "' class='" + "value" + " " + charClass + "'>" + sampleData.recallScore[j] + "</td>";
        //         html_char += "</tr>";
        //     }

        //     // html_char += "<tr>";
        //     // html_char += "<tr><td style='" + "font-weight:bold" + "'>" + "Prec Score" + "</td>";
        //     // for ( var i=0;i<numDet;i++){
        //     //     var charClass = 'green';
        //     //     html_char += "<td data-col='" + i + "' data-row='" + (j+1) + "' class='" + "value" + " " + charClass + "'>" + sampleData.precisionScore[i] + "</td>";
        //     // }
        //     // html_char += "<td data-col='" + (i+1) + "' data-row='" + (j+1) + "' class='" + "value" + " " + charClass + "'>" + "</td>";
        //     // html_char += "</tr>";

        //     html_char += "</tbody></table>";

        // }
        // $("#div_char").html("<div class='div_table'><h3>Character Count</h3>" + html_char + "</div>");
        // $("#div_char").css("display", "block");

    } else {
        // write end-to-end recall / precision matrix on web
        var html_recall_e2e = "<table><thead><tr><th>GT / Det</th>";
        for ( var i=0;i<numDet;i++){
            var detDontCare = $.inArray(i,sampleData.detDontCare)>-1;
            html_recall_e2e += "<th style='" + (detDontCare? "" : "font-weight:bold;") + "'>#" + i + "</th>";
        }
        html_recall_e2e += "</tr></thead><tbody id='tbody_recall'>";

        for ( var j=0;j<numGt;j++){
            var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
            html_recall_e2e += "<tr>";
            html_recall_e2e += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>#" + j + "</td>";
            for ( var i=0;i<numDet;i++){
                
                var recallClass = 'red';
                // if (sampleData.recallMatE2E[j][i] == 1) {
                //     recallClass = 'green';
                // } else if (sampleData.recallMatE2E[j][i] == 0) {
                //     recallClass = 'red';
                // }
                // var recallClass = (sampleData.recallMatE2E[j][i]>=sampleData.evaluationParams.AREA_RECALL_CONSTRAINT ? ' green' : ' red' );
                html_recall_e2e += "<td data-col='" + i + "' data-row='" + j + "' class='" + stylesMat[j][i] + " " + recallClass + "'>" + Math.round(sampleData.end2endMat[j][i]*100)/100 + "</td>";    
            }
            html_recall_e2e += "</tr>";
        }
        html_recall_e2e += "</tbody></table>";

        var html_precision_e2e = "<table><thead><tr><th>GT / Det</th>";
        for ( var i=0;i<numDet;i++){
            var detDontCare = $.inArray(i,sampleData.detDontCare)>-1;
            html_precision_e2e += "<th style='" + (detDontCare? "" : "font-weight:bold;") + "'>#" + i + "</th>";
        }
        html_precision_e2e += "</tr></thead><tbody id='tbody_precision'>";

        for ( var j=0;j<numGt;j++){
            var gtDontCare = $.inArray(j,sampleData.gtDontCare)>-1;
            html_precision_e2e += "<tr>";
            html_precision_e2e += "<td style='" + (gtDontCare? "" : "font-weight:bold;") + "'>#" + j + "</td>";
            for ( var i=0;i<numDet;i++){
                var precisionClass = 'red';
                // var precisionClass = (sampleData.precisionMat[j][i]>=sampleData.evaluationParams.AREA_PRECISION_CONSTRAINT ? ' green' : ' red' );
                html_precision_e2e += "<td data-col='" + i + "' data-row='" + j + "' class='" + stylesMat[j][i] + " " + precisionClass + "'>" + Math.round(sampleData.end2endMat[j][i]*100)/100 + "</td>";    
            }
            html_precision_e2e += "</tr>";
        }
        html_precision_e2e += "</tbody></table>";
        $("#div_recall_e2e").html("<div class='div_table'><h3>E2E Recall Score </h3>" + html_recall_e2e + "</div>");
        $("#div_recall_e2e").css("display", "block");
        $("#div_precision_e2e").html("<div class='div_table'><h3>E2E Precision Score </h3>" + html_precision_e2e + "</div>");
        $("#div_precision_e2e").css("display", "block");
    }

    var evalLog = sampleData.evaluationLog;
    if (evalLog==undefined){
        evalLog = "";
    }else{
        evalLog = evalLog.replace(/\n/g, "<br/>")
    }

    $("#div_logs").html("<div class='div_log'>" + sampleData.evaluationLog.replace(new RegExp("\n", 'g'),"<br/>") + "</div>");

    this.table_sizes();

    $("#div_matrices tbody td").mouseover(function(){
        self.det_rect = -1;
        self.gt_rect = -1;
        if ( $(this).attr("data-col")!=undefined && $(this).attr("data-row")!=undefined){
            self.det_rect = $(this).attr("data-col");
            self.gt_rect = $(this).attr("data-row");
            $("#div_matrices tbody td").removeClass("selected");
            $("#div_matrices tbody td").removeClass("col_selected").removeClass("row_selected");
            $(this).addClass("selected");
            $("td[data-col=" + $(this).attr("data-col") + "]").addClass("col_selected");
            $("td[data-row=" + $(this).attr("data-row") + "]").addClass("row_selected");
        }
        self.draw();
    });

    $("#div_recall tbody td").mouseover(function(){
        self.det_rect = -1;
        self.gt_rect = -1;
        if ( $(this).attr("data-col")!=undefined && $(this).attr("data-row")!=undefined){
            self.det_rect = $(this).attr("data-col");
            self.gt_rect = $(this).attr("data-row");
            $("#div_recall tbody td").removeClass("selected");
            $("#div_recall tbody td").removeClass("col_selected").removeClass("row_selected");
            $(this).addClass("selected");
            $("td[data-col=" + $(this).attr("data-col") + "]").addClass("col_selected");
            $("td[data-row=" + $(this).attr("data-row") + "]").addClass("row_selected");
        }
        self.draw();
    });

    $("#div_precision tbody td").mouseover(function(){
        self.det_rect = -1;
        self.gt_rect = -1;
        if ( $(this).attr("data-col")!=undefined && $(this).attr("data-row")!=undefined){
            self.det_rect = $(this).attr("data-col");
            self.gt_rect = $(this).attr("data-row");
            $("#div_precision tbody td").removeClass("selected");
            $("#div_precision tbody td").removeClass("col_selected").removeClass("row_selected");
            $(this).addClass("selected");
            $("td[data-col=" + $(this).attr("data-col") + "]").addClass("col_selected");
            $("td[data-row=" + $(this).attr("data-row") + "]").addClass("row_selected");
        }
        self.draw();
    });

    $("#div_char tbody td").mouseover(function(){
        self.det_rect = -1;
        self.gt_rect = -1;
        if ( $(this).attr("data-col")!=undefined && $(this).attr("data-row")!=undefined){
            self.det_rect = $(this).attr("data-col");
            self.gt_rect = $(this).attr("data-row");
            $("#div_char tbody td").removeClass("selected");
            $("#div_char tbody td").removeClass("col_selected").removeClass("row_selected");
            $(this).addClass("selected");
            $("td[data-col=" + $(this).attr("data-col") + "]").addClass("col_selected");
            $("td[data-row=" + $(this).attr("data-row") + "]").addClass("row_selected");
        }
        self.draw();
    });

    this.draw();
};

ClassVisualization.prototype.draw = function(){
    // variables for overlay part
    var opacity_overlay = 0.2;
    var gt_pattern_tmp = document.createElement('canvas');
    var gt_pat_ctx = gt_pattern_tmp.getContext('2d');
    var color1 = "rgba(255,0,0," + 0.5 + ")";
    var color2= "rgba(0,0,0," + 0.0 + ")";
    var numberOfStripes = 100;
    for (var i=0;i<numberOfStripes*2;i++){
        var thickness = 300 / numberOfStripes;
        gt_pat_ctx.beginPath();
        gt_pat_ctx.strokeStyle = i % 2?color1:color2;
        gt_pat_ctx.lineWidth =thickness;
        gt_pat_ctx.lineCap = 'round';
        gt_pat_ctx.moveTo(i*thickness + thickness/2 - 300,0);
        gt_pat_ctx.lineTo(0 + i*thickness+thickness/2,300);
        gt_pat_ctx.stroke();
    }

    this.ctx_gt.clearRect(0,0,this.canvas_gt.width,this.canvas_gt.height);
    this.ctx_det.clearRect(0,0,this.canvas_gt.width,this.canvas_gt.height);
    this.ctx_overlay.clearRect(0,0,this.canvas_gt.width,this.canvas_gt.height);
    
    if(!this.image_loaded){
        this.ctx_det.fillStyle = "rgba(255,0,0,1)";
        this.ctx_det.font= "12px Verdana";
        this.ctx_det.fillText("Loading image..", 20,60);
        this.ctx_gt.fillStyle = "rgba(255,0,0,1)";
        this.ctx_gt.font= "12px Verdana";
        this.ctx_gt.fillText("Loading image..", 20,60);
        this.ctx_overlay.fillStyle = "rgba(255,0,0,1)";
        this.ctx_overlay.font= "12px Verdana";
        this.ctx_overlay.fillText("Loading image..", 20,60);
        return;
    }
    
    
    if( $("#chk_image").is(":checked")){
        this.ctx_gt.drawImage(img_gt_image2,this.offset_x,this.offset_y,this.curr_im_w,this.curr_im_h);
        this.ctx_overlay.drawImage(img_gt_image2, this.offset_x, this.offset_y, this.curr_im_w, this.curr_im_h);
    }else{
        this.ctx_gt.strokeStyle = "rgba(0,0,0,1)";
        this.ctx_gt.strokeRect(this.offset_x,this.offset_y,this.curr_im_w,this.curr_im_h);
        this.ctx_gt.fillStyle = "black";
        this.ctx_gt.fillRect(0, 0, this.canvas_gt.width, this.canvas_gt.height);
    }


    if (this.sampleData==null){
        this.ctx_gt.fillStyle = "rgba(255,0,0,1)";
        this.ctx_gt.font= "12px Verdana";
        this.ctx_gt.fillText("Loading method..", 20,60);        
        this.ctx_det.fillStyle = "rgba(255,0,0,1)";
        this.ctx_det.font= "12px Verdana";
        this.ctx_det.fillText("Loading method..", 20,60);
        this.ctx_overlay.fillStyle = "rgba(255,0,0,1)";
        this.ctx_overlay.font= "12px Verdana";
        this.ctx_overlay.fillText("Loading image..", 20,60);
        return;
    }else{

        if (this.sampleData.gtPolPoints==undefined){
             this.sampleData.gtPolPoints = [];
         }
    }

    // GT image drawing
    for (var i=0;i<this.sampleData.gtPolPoints.length;i++){
        
        //if (bb.id_s==current_id_submit){

            var opacity = 0.6;//(gt_rect==bb.i)? "0.9" : "0.6";

            var bb = this.sampleData.gtPolPoints[i];
            var type = this.sampleData.gtTypes[i];
            
            var gtDontCare = $.inArray(i,this.sampleData.gtDontCare)>-1;
            this.ctx_overlay.fillStyle = this.ctx_overlay.createPattern(gt_pattern_tmp, "repeat");

            if(type=="DC"){
                this.ctx_gt.fillStyle = "rgba(50,50,50," + opacity + ")";
                this.ctx_overlay.fillStyle = "rgba(50,50,50," + opacity + ")";
            }else if (type=="OO"){
                this.ctx_gt.fillStyle = "rgba(0,190,0," + opacity + ")";
            }else if (type=="MO"){
                this.ctx_gt.fillStyle = "rgba(247,169,34," + opacity + ")";
            }else if (type=="OM"){
                this.ctx_gt.fillStyle = "rgba(38,148,232," + opacity + ")";                
            }else{
                this.ctx_gt.fillStyle = "rgba(255,0,0," + opacity + ")";
            }

            if (bb.length==4){

                var x = this.original_to_zoom_val(parseInt(bb[0]));
                var y = this.original_to_zoom_val_y(parseInt(bb[1]));
                var x2 = this.original_to_zoom_val(parseInt(bb[2]));
                var y2 = this.original_to_zoom_val_y(parseInt(bb[3]));
                var w = x2-x+1;
                var h = y2-y+1;
                this.ctx_gt.fillRect(x,y,w,h);

                // draw on overlay
                this.ctx_overlay.fillRect(x,y,w,h);
                this.ctx_overlay.lineWidth = 2;
                this.ctx_gt.strokeStyle = 'red';
                this.ctx_overlay.strokeRect(x,y,w,h);

                if (this.gt_rect==i ){
                    this.ctx_gt.lineWidth = 2;
                    this.ctx_gt.strokeStyle = 'red';
                    this.ctx_gt.strokeRect(x,y,w,h);
                }  
            }
            else{
                    this.ctx_gt.beginPath();
                    this.ctx_overlay.beginPath();
                    this.ctx_gt.moveTo(this.original_to_zoom_val(bb[0]), this.original_to_zoom_val_y(bb[1]));
                    this.ctx_overlay.moveTo(this.original_to_zoom_val(bb[0]), this.original_to_zoom_val_y(bb[1]));
                    for (var idx = 2; idx < bb.length; idx += 2) {
                        this.ctx_gt.lineTo(this.original_to_zoom_val(parseInt(bb[idx])), this.original_to_zoom_val_y(parseInt(bb[idx+1])));
                        this.ctx_overlay.lineTo(this.original_to_zoom_val(parseInt(bb[idx])), this.original_to_zoom_val_y(parseInt(bb[idx+1])));
                    }
                    this.ctx_gt.closePath();
                    this.ctx_overlay.closePath();
                    this.ctx_gt.fill();
                    this.ctx_overlay.fill();

                    if(this.gt_rect==i){
                        this.ctx_gt.lineWidth = 2;
                        this.ctx_gt.strokeStyle = 'red';
                        this.ctx_gt.stroke();
                    }

                    // draw overlay line
                    if (type != "DC") {
                        this.ctx_overlay.lineWidth = 2.5;
                        this.ctx_overlay.strokeStyle = 'red';
                        this.ctx_overlay.stroke();
                    }
                }
            

            if($("#chk_image").is(":checked")){
                for (var k=0;k<this.sampleData.gtCharPoints[i].length;k++){
                    if (gtDontCare) {
                        continue;
                    }
                    var center = this.sampleData.gtCharPoints[i][k];
                    var count = this.sampleData.gtCharCounts[i][k];
    
                    if(count==1){
                            this.ctx_gt.fillStyle = "rgba(0,190,0," + opacity + ")";
                            this.ctx_overlay.fillStyle = "rgba(0,255,70," + 1.0 + ")";
                    } else if (count == 0){
                        this.ctx_gt.fillStyle = "rgba(255,0,0," + opacity + ")";
                        this.ctx_overlay.fillStyle = "rgba(255,0,0," + 1.0 + ")";
                    } else {
                        this.ctx_gt.fillStyle = "rgba(255,255,0," + opacity + ")";
                        this.ctx_overlay.fillStyle = "rgba(255,0,0," + 1.0 + ")";
                    }
    
                    var x = this.original_to_zoom_val(center[0]);
                    var y = this.original_to_zoom_val_y(center[1]);
    
                    this.ctx_gt.beginPath();
                    this.ctx_gt.arc(x, y, 5, 0, 2 * Math.PI, false);
                    this.ctx_gt.closePath();
                    this.ctx_gt.fill();
    
                    if( $("#chk_pcc").is(":checked")){
                        this.ctx_overlay.beginPath();
                        this.ctx_overlay.arc(x, y, 5, 0, 2 * Math.PI, false);
                        this.ctx_overlay.closePath();
                        this.ctx_overlay.fill();
                        this.ctx_overlay.strokeStyle = "rgba(50,50,50," + 1.0 + ")";
                        this.ctx_overlay.stroke();
                    }
    
                    if(this.gt_rect==i){
                        this.ctx_gt.lineWidth = 2;
                        this.ctx_gt.strokeStyle = 'red';
                        this.ctx_gt.stroke();
                    } else {
                        this.ctx_gt.lineWidth = 2;
                        this.ctx_gt.strokeStyle = "rgba(50,50,50," + opacity + ")";
                        this.ctx_gt.stroke();
                    }
                }
            }
            if(this.sampleData.evaluationParams.E2E && !$("#chk_image").is(":checked")){
                this.writeText(this.ctx_gt,bb,this.sampleData.gtTrans[i],this.sampleData.gtQuery[i]);
            }
    }

    this.ctx_overlay.fillStyle = "rgba(0,0,255," + opacity_overlay + ")";

    // Detection image drawing
    this.ctx_det.clearRect(0,0,this.canvas_gt.width,this.canvas_gt.height);
    if( $("#chk_image").is(":checked")){
        this.ctx_det.drawImage(img_gt_image2,this.offset_x,this.offset_y,this.curr_im_w,this.curr_im_h);
    }else{
        this.ctx_det.strokeStyle = "rgba(0,0,0,1)";
        this.ctx_det.strokeRect(this.offset_x,this.offset_y,this.curr_im_w,this.curr_im_h);
        this.ctx_det.fillStyle = "black";
        this.ctx_det.fillRect(0, 0, this.canvas_det.width, this.canvas_det.height);
    }


    for (var i=0;i<this.sampleData.detPolPoints.length;i++){
        var bb = this.sampleData.detPolPoints[i];
        var type = this.sampleData.detTypes[i];

            var opacity = 0.6;//(det_rect==bb.i)? "0.9" : "0.6";
            if(type=="DC"){
                this.ctx_det.fillStyle = "rgba(50,50,50," + opacity + ")";
            }else if (type=="OO"){
                this.ctx_det.fillStyle = "rgba(0,190,0," + opacity + ")";
            }else if (type=="MO"){
                this.ctx_det.fillStyle = "rgba(247,169,34," + opacity + ")";
            }else if (type=="OM"){
                this.ctx_det.fillStyle = "rgba(38,148,232," + opacity + ")";                
            }else{
                this.ctx_det.fillStyle = "rgba(255,0,0," + opacity + ")";
            }

            if (bb.length==4){
                
                var x = this.original_to_zoom_val(parseInt(bb[0]));
                var y = this.original_to_zoom_val_y(parseInt(bb[1]));
                var x2 = this.original_to_zoom_val(parseInt(bb[2]));
                var y2 = this.original_to_zoom_val_y(parseInt(bb[3]));
                var w = x2-x+1;
                var h = y2-y+1;
                this.ctx_det.fillRect(x,y,w,h);
                if(this.det_rect==i){
                    this.ctx_det.lineWidth = 2;
                    this.ctx_det.strokeStyle = 'red';
                    this.ctx_det.strokeRect(x,y,w,h);
                }   
                
            }else{
                this.ctx_det.beginPath();
                this.ctx_overlay.beginPath();
                this.ctx_det.moveTo(this.original_to_zoom_val(bb[0]), this.original_to_zoom_val_y(bb[1]));
                this.ctx_overlay.moveTo(this.original_to_zoom_val(bb[0]), this.original_to_zoom_val_y(bb[1]));
                for (var idx = 2; idx < bb.length; idx += 2) {
                    this.ctx_det.lineTo(this.original_to_zoom_val(parseInt(bb[idx])), this.original_to_zoom_val_y(parseInt(bb[idx+1])));
                    this.ctx_overlay.lineTo(this.original_to_zoom_val(parseInt(bb[idx])), this.original_to_zoom_val_y(parseInt(bb[idx+1])));
                }
                this.ctx_det.closePath();
                this.ctx_overlay.closePath();
                this.ctx_det.fill();
                this.ctx_overlay.fill();
                //ctx_gt.fillRect( original_to_zoom_val(parseInt(bb.x)),original_to_zoom_val_y(parseInt(bb.y)),parseInt(bb.w)*scale,parseInt(bb.h)*scale);
                if(this.det_rect==i){
                    this.ctx_det.lineWidth = 2;
                    this.ctx_det.strokeStyle = 'red';
                    this.ctx_det.stroke();
                }
                // draw overlay line
                this.ctx_overlay.lineWidth = 2.5;
                this.ctx_overlay.strokeStyle = 'blue';
                this.ctx_overlay.stroke();
            }

            if (this.sampleData.evaluationParams.E2E) {
                // End2End text drawing
                if( !$("#chk_image").is(":checked")){
                    this.writeText(this.ctx_det,bb,this.sampleData.detTrans[i],this.sampleData.detQuery[i]);
                }
            }
    }

    // draw one more for overlay visualization
    for (var i=0;i<this.sampleData.gtPolPoints.length;i++){
        var bb = this.sampleData.gtPolPoints[i];
        var type = this.sampleData.gtTypes[i];
        var gtDontCare = $.inArray(i,this.sampleData.gtDontCare)>-1;

        if(type=="DC"){
            this.ctx_overlay.fillStyle = "rgba(50,50,50," + opacity_overlay + ")";
        }
    
        this.ctx_overlay.beginPath();
        this.ctx_overlay.moveTo(this.original_to_zoom_val(bb[0]), this.original_to_zoom_val_y(bb[1]));
        for (var idx = 2; idx < bb.length; idx += 2) {
            this.ctx_overlay.lineTo(this.original_to_zoom_val(parseInt(bb[idx])), this.original_to_zoom_val_y(parseInt(bb[idx+1])));
        }
        this.ctx_overlay.closePath();
    
        // draw overlay line
        if (type != "DC") {
            this.ctx_overlay.lineWidth = 2.5;
            this.ctx_overlay.strokeStyle = 'red';
            this.ctx_overlay.stroke();
        }
    }


    this.draws++;
};