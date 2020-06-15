/* global web, google */
var ranking_task_graphic_options_default = {
    height: 240,
    fontSize:12,
    animation:{'duration':0},
    title:'',
    backgroundColor:'transparent',
    chartArea:{left:50,top:20,width:350,height:180},
    width: 400,
    focusTarget:'category',
    legend: {position:'bottom'},
    vAxis:{

        format:'none',
        textStyle:{fontSize: 8},
        //title:'%',
        titleTextStyle:{fontSize: 12,fontStyle:'bold'},
        textPosition:'out'
    },
    hAxis:{
        textStyle:{fontSize: 8}
    }
};

function delete_methods(){
    
    if(!confirm("Are you sure to delete all methods?")){
        return;
    }
    var url = "/delete_all";
    $.post(url, function (data) {
        document.location.reload();
    });
}

function delete_method(id){
    if(!confirm("Are you sure to delete the method?")){
        return;
    }
    var url = "/delete_method";
    $.post(url,{"id":id} , function (data) {
        document.location.reload();
    });
}

function edit_method(id,el){
    
    var current_name = $(el).closest("tr").find("span.title").text();
    var name = prompt("Enter the method's name", current_name);
    if (name != null) {
        var url = "/edit_method";
        $.post(url,{"id":id,"name":name} , function (data) {
            document.location.reload();
        });
    }
}

function upload_subm(){
    $("form").submit();
}

function wait_screen(msg){
    $("body").append("<div class='overlay'>" + (msg!=undefined? "<div class='info'><span class='msg'>" + msg + "</span><img class='wait' src='/static/wait.gif'></div>" : "<img src='/static/wait.gif'>") + "</div>");
}

function close_overlay(){
    $("div.overlay").remove();
}

function show_error(msg){
    if(!$("div.overlay").length){
        $("body").append("<div class='overlay'></div>");
    }
    $("div.overlay").html("<div class='error'><span class='msg'>" + msg + "</span><button onclick='close_overlay()'>OK</button></div>");
}
function show_info(msg){
    if(!$("div.overlay").length){
        $("body").append("<div class='overlay'></div>");
    }
    $("div.overlay").html("<div class='info'><span class='msg'>" + msg + "</span><button onclick='close_overlay()'>OK</button></div>");
}

$(document).ready( function(){

    $("form").submit(function() {
       wait_screen("Please wait, your results are being uploaded,validated and evaluated..");
       var options = {
       url : '/evaluate?json=1' ,
       dataType: 'json',
       success : function(result){
           close_overlay();
           if (result.calculated){
               document.location.href = "/method/?m=" + result.id;
           }else{
               show_error(result.Message);
           }
       },
       error : function(){
           close_overlay();
           show_error("Error on server");
       }
       };
       var $form = $(this);
       setTimeout(function(){
           $form.ajaxSubmit(options);
       },10);
       return false;
    });

    function carregar_api_grafics(callback){
          google.load('visualization', '1',
          {packages:['corechart'],callback:callback});
    };

    var grafic_1 = null;
    var grafic_2 = null;
    var loaded=false;

    function init_graphic(){
        carregar_api_grafics(function(){
            grafic_1 = new google.visualization.ColumnChart(document.getElementById('div_ranking_1'));
            if($("#div_ranking_2").length){
                grafic_2 = new google.visualization.ColumnChart(document.getElementById('div_ranking_2'));
            }
            loaded=true;
            show_current_graphic();
        });
    }
    
    if ($("#div_ranking_1").length){
        show_current_graphic();
    }
    
    function show_current_graphic(){
        if(!loaded){
            init_graphic();
            return;
        }
        var Base64={_keyStr:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",encode:function(e){var t="";var n,r,i,s,o,u,a;var f=0;e=Base64._utf8_encode(e);while(f<e.length){n=e.charCodeAt(f++);r=e.charCodeAt(f++);i=e.charCodeAt(f++);s=n>>2;o=(n&3)<<4|r>>4;u=(r&15)<<2|i>>6;a=i&63;if(isNaN(r)){u=a=64}else if(isNaN(i)){a=64}t=t+this._keyStr.charAt(s)+this._keyStr.charAt(o)+this._keyStr.charAt(u)+this._keyStr.charAt(a)}return t},decode:function(e){var t="";var n,r,i;var s,o,u,a;var f=0;e=e.replace(/[^A-Za-z0-9+/=]/g,"");while(f<e.length){s=this._keyStr.indexOf(e.charAt(f++));o=this._keyStr.indexOf(e.charAt(f++));u=this._keyStr.indexOf(e.charAt(f++));a=this._keyStr.indexOf(e.charAt(f++));n=s<<2|o>>4;r=(o&15)<<4|u>>2;i=(u&3)<<6|a;t=t+String.fromCharCode(n);if(u!=64){t=t+String.fromCharCode(r)}if(a!=64){t=t+String.fromCharCode(i)}}t=Base64._utf8_decode(t);return t},_utf8_encode:function(e){e=e.replace(/rn/g,"n");var t="";for(var n=0;n<e.length;n++){var r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r)}else if(r>127&&r<2048){t+=String.fromCharCode(r>>6|192);t+=String.fromCharCode(r&63|128)}else{t+=String.fromCharCode(r>>12|224);t+=String.fromCharCode(r>>6&63|128);t+=String.fromCharCode(r&63|128)}}return t},_utf8_decode:function(e){var t="";var n=0;var r=c1=c2=0;while(n<e.length){r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r);n++}else if(r>191&&r<224){c2=e.charCodeAt(n+1);t+=String.fromCharCode((r&31)<<6|c2&63);n+=2}else{c2=e.charCodeAt(n+1);c3=e.charCodeAt(n+2);t+=String.fromCharCode((r&15)<<12|(c2&63)<<6|c3&63);n+=3;}}return t}};
        var id_data = "graphic";
        var dadesArray = eval(Base64.decode($("#" + id_data + "").val()));
        var ordenacio = $("#" + id_data + "-sort").val();
        var format = $("#" + id_data + "-format").val();
        var type = $("#" + id_data + "-type").val();
        
        var dades = google.visualization.arrayToDataTable(dadesArray);
        var width = $(window).width() - $("table.results").width()-40;
        
        if (width<$(window).width()/2){
            width = $(window).width() - 20;
            $("#div_rankings").removeClass("ib");
        }else{
            $("#div_rankings").addClass("ib");
        }
        if(grafic_2!=null){
            width = width/2 -10;
        }
        var height = $(window).height() - 320;
        
        var options = jQuery.extend(true, {}, ranking_task_graphic_options_default);
        options.animation.duration= 300;
        options.width= width;
        options.height= height;
        options.chartArea.width =  width-40;
        options.chartArea.height =  height-100;
        options.vAxis.title =  ordenacio;
        options.vAxis.format =  (format=="perc"? 'percent' : ( type!="string"? 'decimal' : 'none' ) );
        if(format=="perc"){
            options.vAxis.minValue = 0;
            options.vAxis.maxValue = 1;
        }

        grafic_1.draw(dades,options);
        
        if(grafic_2!=null){
            var ordenacio = $("#" + id_data + "-gr2-sort").val();
            var format = $("#" + id_data + "-gr2-format").val();
            var type = $("#" + id_data + "-gr2-type").val();
            var options = jQuery.extend(true, {}, ranking_task_graphic_options_default);
            options.animation.duration= 300;
            options.width= width;
            options.height= height;
            options.chartArea.width =  width-40;
            options.chartArea.height =  height-100;
            options.vAxis.title =  ordenacio;
            options.vAxis.format =  (format=="perc"? 'percent' : ( type!="string"? 'decimal' : 'none' ) );
            if(format=="perc"){
                options.vAxis.minValue = 0;
                options.vAxis.maxValue = 1;
            }
            var dadesArray = eval(Base64.decode($("#" + id_data + "-gr2").val()));
            var dades = google.visualization.arrayToDataTable(dadesArray);
            options.vAxis.title = ordenacio;
            grafic_2.draw(dades,options);
        }        

    }

});


function instructions(){
    $("#div_instructions").removeClass("hidden");
}

$(document).ready(function(){
    $("#div_instructions button.close").click(function(){
        $("#div_instructions").addClass("hidden");
    });
});