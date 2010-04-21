(function($){

    $(function(){ // onload
        $('.process').makeChart()

    }) // end onload

})(jQuery)


jQuery.fn.makeChart = function(){
    function update_ws(id, ws){
        jQuery.fn.makeChart.web_sockets[id] = ws
    }
    jQuery.each(this, function(i, process_elem){
        self = jQuery(process_elem);
        var process_id = self.attr('id');
        var chart_target = self.find('.chart-wrapper').attr('id')
        var ws_url = self.find('a.process-link').attr('href');
        var chart_socket = new WebSocket('ws://' + window.location.host + ws_url);
        update_ws(process_id, chart_socket);


    //    $.jqplot(target_id, [line1], {
    //        title:'Customized Date Axis',
    //        gridPadding:{right:35},
    //        axes:{
    //            xaxis:{
    //                renderer:$.jqplot.DateAxisRenderer,
    //                tickOptions:{formatString:'%b %#d, %y'},
    //                min:'May 30, 2008',
    //                tickInterval:'1 month'
    //            }
    //        },
    //        series:[{lineWidth:4, markerOptions:{style:'square'}}]
    //
    //    });
        chart_socket.onopen = function(e){
            chart_socket.send('hi');
            console.log(e);
        };
        chart_socket.onclose = function(e){
            console.log(e);
        };
        chart_socket.onmessage = function(e){
            console.log(e.data, process_id);
        };
    });

    return this
}

jQuery.fn.makeChart.web_sockets = {}