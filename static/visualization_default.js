/* global web */
var ClassVisualization = function(){
    this.sampleData = null;
    
    //Parameters for GT/Det Canvas visualization
    this.canvas_gt = null;
    this.canvas_det = null;
    this.canvas_overlay = null;
    this.ctx_gt = null;
    this.ctx_det = null;
    this.ctx_overlay = null;
    this.scale=2;
    this.offset_x=0;
    this.offset_y=0;
    this.im_w=0;
    this.im_h=0;
    this.curr_im_w=0;
    this.curr_im_h=0;
    this.det_rect=-1;
    this.gt_rect=-1;
    this.draws=0;
    
    //Mouse events on canvas
    this.mm_point=null;
    this.initial_point=null;
    this.last_point=null;
    this.mouse_clicked=false;
    this.initial_offset=null;
    
    this.image_loaded = false;
    this.image_details_loaded=false;
    this.sampleData = null;    
    
    var self = this;
    
    this.load_sample_info = function(){
        //web.pantalla_espera();
        
        var urlInfo = "/sampleInfo/?m=" + getUrlParameter("m");
        var extraParmasNames = ["file","eval","sample","gtv"];
        for(var i=0;i<extraParmasNames.length;i++){
            var parameterValue = getUrlParameter( extraParmasNames[i] );
            if (parameterValue!= undefined){
                urlInfo += "&" + extraParmasNames[i] + "=" + parameterValue;
            }
        }
        $.get(urlInfo, function (data) {
            visualization.sampleData = data;
            visualization.load_visualization();
        }, "json");
    };
    
    this.init_image_details = function(){
        this.canvas_gt = document.createElement("canvas");
        var dest = document.getElementById("div_canvas_gt");
        dest.appendChild(this.canvas_gt);
        this.canvas_gt.setAttribute("id","canvas_gt");

        this.canvas_det = document.createElement("canvas");
        var dest2 = document.getElementById("div_canvas_det");
        dest2.appendChild(this.canvas_det);
        this.canvas_det.setAttribute("id","canvas_det");

        this.canvas_overlay = document.createElement("canvas");
        var dest3 = document.getElementById("div_canvas_overlay");
        dest3.appendChild(this.canvas_overlay);
        this.canvas_overlay.setAttribute("id", "canvas_overlay");

        this.canvas_gt.width=$("#div_canvas_gt").width();
        this.canvas_gt.height=$("#div_canvas_gt").height();
        this.canvas_det.width=$("#div_canvas_gt").width();
        this.canvas_det.height=$("#div_canvas_gt").height();
        this.canvas_overlay.width=$("#div_canvas_gt").width();
        this.canvas_overlay.height=$("#div_canvas_gt").height();

        var self = this;
        
        $("#canvas_gt").mousedown(function(e) {self.mousedown(e);});
        $("#canvas_gt").mousemove(function(e) {self.mousemove(e);});
        $("#canvas_gt").mouseup(function(e) {self.mouseup(e);});
        $("#canvas_gt").mouseleave(function(e) {self.mouseleave(e);});
        $("#canvas_gt").mousewheel(function(e, d) {self.mousewheel(e,d);});
        $("#canvas_det").mousedown(function(e) {self.mousedown(e);});
        $("#canvas_det").mousemove(function(e) {self.mousemove(e);});
        $("#canvas_det").mouseup(function(e) {self.mouseup(e);});
        $("#canvas_det").mouseleave(function(e) {self.mouseleave(e);});
        $("#canvas_det").mousewheel(function(e, d) {self.mousewheel(e,d);});
        $("#canvas_overlay").mousedown(function(e) {self.mousedown(e);});
        $("#canvas_overlay").mousemove(function(e) {self.mousemove(e);});
        $("#canvas_overlay").mouseup(function(e) {self.mouseup(e);});
        $("#canvas_overlay").mouseleave(function(e) {self.mouseleave(e);});
        $("#canvas_overlay").mousewheel(function(e, d) {self.mousewheel(e,d);});

        this.ctx_gt = canvas_gt.getContext("2d");
        this.ctx_det = canvas_det.getContext("2d");
        this.ctx_overlay = canvas_overlay.getContext("2d")
        this.ctx_gt.mozImageSmoothingEnabled = false;
        this.ctx_gt.webkitImageSmoothingEnabled = false;
        this.ctx_det.mozImageSmoothingEnabled = false;
        this.ctx_det.webkitImageSmoothingEnabled = false;
        this.ctx_overlay.mozImageSmoothingEnabled = false;
        this.ctx_overlay.webkitImageSmoothingEnabled = false;
        this.scale = Math.min($("#canvas_gt").width()/this.im_w,$("#canvas_gt").height()/this.im_h );
        setTimeout(function(){self.adapt_controls();},500);

    };
    this.adapt_controls = function(){
        if(!this.image_details_loaded){
            return;
        }
        var height = Math.max(220,$(window).height()-536);
        $("#div_container_gt").css("height",height + "px");
        $("#div_container_det").css("height",height + "px");
        $("#div_container_overlay").css("height",height + "px");

        this.canvas_gt.width=$("#div_canvas_gt").width();
        this.canvas_gt.height=$("#div_canvas_gt").height();
        this.canvas_det.width=$("#div_canvas_gt").width();
        this.canvas_det.height=$("#div_canvas_gt").height();
        this.canvas_overlay.width=$("#div_canvas_gt").width();
        this.canvas_overlay.height=$("#div_canvas_gt").height();
        this.ctx_gt.mozImageSmoothingEnabled = false;
        this.ctx_gt.webkitImageSmoothingEnabled = false;
        this.ctx_det.mozImageSmoothingEnabled = false;
        this.ctx_det.webkitImageSmoothingEnabled = false;
        this.ctx_overlay.mozImageSmoothingEnabled = false;
        this.ctx_overlay.webkitImageSmoothingEnabled = false;
        $("#div_container_method").css({"height": ($(window).height()-80)+ "px"});

        this.table_sizes();      
        this.zoom_changed();
        this.correct_image_offset();
        this.draw();
    };
    
    this.mousemove = function(e){
        var layer = this.getOffset(e);
        this.mm_point = Array(layer.x,layer.y);
    };

    this.mousedown = function(e){
        var layer = this.getOffset(e);
        var mouseX = layer.x;
        var mouseY = layer.y;
        this.initial_point = Array(mouseX,mouseY);
        this.initial_offset = Array(this.offset_x,this.offset_y);
        this.mm_point = Array(mouseX,mouseY);
        this.last_point = Array(mouseX,mouseY);
        this.mouse_clicked = true;
        this.refresh_canvas_position_on_mousemove();
    };
    this.mouseup = function(e){    
        this.mouse_clicked = false;
    };
    this.mouseleave = function(e){
        this.mouse_clicked = false;
    };
    this.mousewheel = function(e,d){        
         var new_scale = this.scale + ((d>0)? this.scale*0.1 : -this.scale*0.1);

        var point = this.mm_point;
        var real_point = this.zoom_to_original(point);

        var dx = point[0] - this.original_to_zoom_val(real_point[0]);
        var dy = point[1] - this.original_to_zoom_val_y(real_point[1]);
        this.offset_x= point[0] - real_point[0]*new_scale - dx;// - this.scale;
        this.offset_y= point[1] - real_point[1]*new_scale - dy;// - this.scale;

        this.scale = new_scale;

        this.zoom_changed();
        this.correct_image_offset();
        this.draw();
        e.preventDefault();
        return false;
    };

    this.original_to_zoom = function(punt){
        return Array(this.original_to_zoom_val(punt[0]),this.original_to_zoom_val_y(punt[1]));
    };
    this.original_to_zoom_val = function(x){
        return Math.floor(x*this.scale + this.offset_x);
    };
    this.original_to_zoom_val_y = function(y){
        return Math.floor(y*this.scale+this.offset_y);
    };
    this.zoom_to_original = function(punt){
        return Array(this.zoom_to_original_val(punt[0]),this.zoom_to_original_val_y(punt[1]));
    };
    this.zoom_to_original_val = function(x){
        return Math.floor((x-this.offset_x)/this.scale);
    };
    this.zoom_to_original_val_y = function(y){
        //return Math.floor(y/this.scale-this.offsetY);
        return Math.floor((y-this.offset_y)/this.scale);
    };
    this.zoom_changed = function(){
        this.curr_im_w = this.im_w * this.scale;
        this.curr_im_h = this.im_h * this.scale;

    };
    this.correct_image_offset = function(){    
        //Ensure that image position is correct and center image
        if ( this.curr_im_w < this.canvas_gt.width){
            this.offset_x = (this.canvas_gt.width - this.curr_im_w)/2;
        }else{
            if (this.offset_x>0) this.offset_x= 0;
            if (this.offset_x < (this.canvas_gt.width - this.curr_im_w)) this.offset_x = this.canvas_gt.width - this.curr_im_w ;
        }
        if (this.curr_im_h < this.canvas_gt.height){
            this.offset_y = ( this.canvas_gt.height - this.curr_im_h)/2;
        }else{
            if (this.offset_y>0) this.offset_y = 0;
            if (this.offset_y< (this.canvas_gt.height-this.curr_im_h)) this.offset_y = this.canvas_gt.height - this.curr_im_h ;
        }
    };
    
    this.refresh_canvas_position_on_mousemove = function(){    
       var dx = self.mm_point[0]-self.initial_point[0];
       var dy = self.mm_point[1]-self.initial_point[1];

       var ox = self.initial_offset[0] + dx;
       var oy = self.initial_offset[1] + dy;

       var co = self.correct_offset(ox,oy);

       if (self.mouse_clicked){

           if (co[0]!=self.offset_x ||co[1]!=self.offset_y) {

               self.offset_x = self.initial_offset[0] + dx;
               self.offset_y = self.initial_offset[1] + dy;
               self.correct_image_offset();
               self.draw();
           }
           setTimeout(self.refresh_canvas_position_on_mousemove,100);
       }
    };
    this.correct_offset = function(ox,oy){    
        //Ensure that image position is correct and center image
        if ( this.curr_im_w < this.canvas_gt.width){
            ox = (this.canvas_gt.width - this.curr_im_w)/2;
        }else{
            if (ox>0) ox = 0;
            if (ox< (this.canvas_gt.width - this.curr_im_w)) ox = this.canvas_gt.width - this.curr_im_w ;
        }
        if (this.curr_im_h < this.canvas_gt.height){
            oy = (this.canvas_gt.height - this.curr_im_h)/2;
        }else{
            if (oy>0) oy = 0;
            if (oy< (this.canvas_gt.height - this.curr_im_h)) oy = this.canvas_gt.height - this.curr_im_h ;
        }
        return Array(ox,oy);
    };
    this.getOffset = function(evt){      
      var el = evt.target,
          x = y = 0;

        while (el && !isNaN(el.offsetLeft) && !isNaN(el.offsetTop)) {
          x += el.offsetLeft - el.scrollLeft;
          y += el.offsetTop - el.scrollTop;
          el = el.offsetParent;
       }
        x = evt.clientX - x;
        y = evt.clientY - y;


      return {x: x, y: y};
    };
    
   
    this.table_sizes = function(){
        $(".div_table").scroll(function(e){
            var pos_y = $(this).scrollTop();
            var pos_x = $(this).scrollLeft();
            $(".div_table").not(this).scrollTop(pos_y).scrollLeft(pos_x);
        });  
    };
    

    this.writeText = function(ctx,bb,text,q){
        
        var TL,TR,BL,BR;
        
        if (bb.length == 8){
            //bb has 8 points, we want to find TL,TR,BL,BR
            //1st. sort points by Y
            var p1 = {"x":bb[0],"y":bb[1]};
            var p2 = {"x":bb[2],"y":bb[3]};
            var p3 = {"x":bb[4],"y":bb[5]};
            var p4 = {"x":bb[6],"y":bb[7]};

            var pointsList = [p1,p2,p3,p4];
            pointsList = pointsList.sort(function sortPointsByY(a,b){
                if (a.y<b.y){
                    return 1;
                }else if (a.y==b.y){
                    return 0;
                }else{
                    return -1;
                }
            });

            if (pointsList[0].x < pointsList[1].x){
                 TL = pointsList[0];
                 TR = pointsList[1];
             }else{
                 TL = pointsList[1];
                 TR = pointsList[0];
             }
            if (pointsList[2].x < pointsList[3].x){
                 BL = pointsList[2];
                 BR = pointsList[3];
             }else{
                 BL = pointsList[3];
                 BR = pointsList[2];
             }
         } else if (bb.length == 4){
             TL = {"x" : bb[0] , "y":bb[3]};
             TR = {"x" : bb[2] , "y":bb[3]};
             BL = {"x" : bb[0] , "y":bb[1]};
             BR = {"x" : bb[2] , "y":bb[1]};
         } else {
            // bb has 2*N points. we want to find TL, TR, BL, BR point to cover polygon
            var num_points = Math.round(bb.length/2);
            BL = {"x" : bb[0] , "y":bb[1]};
            BR = {"x" : bb[num_points-2] , "y":bb[num_points-1]};
            TR = {"x" : bb[num_points] , "y":bb[num_points+1]};
            TL = {"x" : bb[2*num_points-2] , "y":bb[2*num_points-1]};
         }
        var height = Math.round(this.original_to_zoom_val_y(parseInt( Math.min(TL.y,TR.y) )+1) - this.original_to_zoom_val_y(parseInt(Math.max(BL.y,BR.y)))) - 3;
        var width = Math.round(this.original_to_zoom_val(parseInt( Math.min(TR.x,BR.x) )+1) - this.original_to_zoom_val(parseInt(Math.max(TL.x,BL.x)))) - 3;

        var fontSize = height;
        if(fontSize<10){
            fontSize=10;
        }

        var textPos = this.original_to_zoom_val(parseInt(BL.x)) + 3;
        for(var i=0;i<text.length;i++){
            if(q.includes(text[i])){
                ctx.fillStyle = "rgba(255,255,255,1)";
                q = q.replace(text[i], '', 1)
            }else{
                ctx.fillStyle = "rgba(255,0,0,1)";
            }
            ctx.font= fontSize + "px Verdana";

            var textWidth = ctx.measureText(text).width;
            while(textWidth>width && fontSize>10){
                fontSize--;
                ctx.font = fontSize + "px Verdana";
                textWidth = ctx.measureText(text).width;
            }
            ctx.fillText(text[i],textPos,this.original_to_zoom_val_y(parseInt(BL.y)) + fontSize);
            textPos += ctx.measureText(text[i]).width;
        }
    };
    
};

ClassVisualization.prototype.load_visualization = function(){
    var urlGtImg = "/image/?sample=" + getUrlParameter("sample");
    var extraParmasNames = ["ch","task","gtv"];
    for(var i=0;i<extraParmasNames.length;i++){
        var parameterValue = getUrlParameter( extraParmasNames[i] );
        if (parameterValue!= undefined){
            urlGtImg += "&" + extraParmasNames[i] + "=" + parameterValue;
        }
    }    
    $("#div_sample").append("<img src='" + urlGtImg + "'>");
    for (var key in visualization.sampleData){
        $("#div_sample").append("<br>" + key + " = " + visualization.sampleData[key]);
    }
    //web.tancar_pantalla_espera();
    
};

ClassVisualization.prototype.draw = function(){
    
};

var visualization = new ClassVisualization();


$(document).ready(function () {
    visualization.load_sample_info();
});

$(window).resize(function(){
    visualization.adapt_controls();
});