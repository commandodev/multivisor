var make_server_chart = null;

(function($){

    $(function(){ // onload
        $('.process').makeChart();

        make_server_chart = function(target, stats){
            return;
            $('#' + target).empty();

            server_chart = $.jqplot(target, stats, {
                stackSeries: true,
                seriesColors: ['#741111', '#117422'],
                //legend: {show: true, location: 'nw'},
                //title: 'Unit Revenues: Acme Traps Division',
                seriesDefaults: {
                    renderer: $.jqplot.BarRenderer,
                    rendererOptions: {
                        barMargin: 15
                    }
                },//,rendererOptions: {barWidth: 50}},
                series: [{label: 'running'}, {label: 'stopped'}],
                axesDefaults: {
                    show: false,
                    tickOptions: {
                        showMark: false,
                        showLabel: false,
                        showGridline: false
                    }
                },
                grid: {
                    drawGridlines: false,
                    background: '#000',
                    borderColor: '#000',
                    shadow: false
                },
                axes: {
                    xaxis: {
                        show: false,
                        renderer: $.jqplot.CategoryAxisRenderer,
                        ticks: labels
                    },
                    yaxis: {
                        min: 0
                    }
                }
            });
        };

        make_server_chart('server-chart', server_data)

    }); // end onload

})(jQuery);


(function($){
    $.fn.makeChart = function(){

        function update_ws(ws){
            $.fn.makeChart.web_sockets[ws.process] = ws
        }


        $.each(this, function(i, process_elem){
            var self = jQuery(process_elem);
            var ws_url = self.find('a.process-link').attr('href');
            var chart_socket = new WebSocket('ws://' + window.location.host + ws_url);
            chart_socket.process = self.attr('id');
            chart_socket.chart_target = self.find('.chart-wrapper').attr('id')
            update_ws(chart_socket);

            chart_socket.make_process_chart = function(){
                $('#' + this.chart_target).empty();
                var x = [];
                var cpu = [];
                var mem = [];
                $.each(this.mem_use, function(i, o){
                    x.push(o[0]);
                    mem.push(o[1]);
                    cpu.push(chart_socket.cpu_use[i][1]);
                })
                r = Raphael(this.chart_target, 250, 100);
                r.g.barchart(0, 0, 250, 100, [mem], {colors:[r.g.colors[2]]});
                r.g.linechart(0, 0, 250, 100, x, cpu);



            };


            chart_socket.onopen = function(e){
                chart_socket.send('hi');
                this.mem_use = [];
                this.cpu_use = [];
            };
            chart_socket.onclose = function(e){
                console.log(e);
            };

    /*
    {u'description': u'pid 11083, uptime 0:00:01',
     u'exitstatus': 0,
     u'group': u'mv-listener',
     u'logfile': u'/tmp/mv-listener-stdout---supervisor-DFSwcr.log',
     u'name': u'mv-listener',
     u'now': 1271310522,
     u'pid': 11083,
     u'process_info': {u'cpu_percent': 75.581395348837205,
                       u'mem_percent': 0.30269622802734375,
                       u'mem_resident': 13000704,
                       u'mem_virtual': 2515353600},
     u'spawnerr': u'',
     u'start': 1271310521,
     u'state': 20,
     u'statename': u'RUNNING',
     u'stderr_logfile': u'/tmp/mv.stdout',
     u'stdout_logfile': u'/tmp/mv-listener-stdout---supervisor-DFSwcr.log',
     u'stop': 0}
     */


            chart_socket.onmessage = function(e){

                this.mem_use = this.mem_use.slice(-20)
                this.cpu_use = this.cpu_use.slice(-20)
                var data = $.parseJSON(e.data);
                //console.log(data);
                var ts = data['now']*1000;
                var proc_info = data['process_info'];
                if (proc_info) {
                    this.cpu_use.push([ts, proc_info['cpu_percent']]);
                    this.mem_use.push([ts, proc_info['mem_percent']*100]);
                }
                this.make_process_chart();
                

                //console.log(this.process, this.cpu_use.slice(-2));
                //this.send('');

            };
        });

        return this
    }
})(jQuery);

jQuery.fn.makeChart.web_sockets = {}
jQuery.fn.makeChart.processes = {}