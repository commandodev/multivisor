(function($){

    $(function(){ // onload
        $('.process').makeChart()

    }) // end onload

})(jQuery)

jQuery.fn.makeChart = function(){
    var target_id = this.find('.chart-wrapper').attr('id');
    var ws_url = this.find('a.process-link').attr('href');
    chart_socket = new WebSocket('ws://' + window.location.host + ws_url);


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
    }
    chart_socket.onclose = function(e){
        console.log(e);
    }
    chart_socket.onmessage = function(e){
        console.log(e.data);
    }
}