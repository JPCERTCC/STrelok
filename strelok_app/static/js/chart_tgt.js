function tgtChart(data, prop){
subtitle = 'Click on a slice -> Drilldown';
//subtitle = null;
xaxis = 'Identity';
function setChart(options)  {
    chart.series[0].remove(false);
    chart.addSeries({
        type: options.type,
        //name: options.name,
        data: options.data,
        //color: options.color || 'white'
        colorByPoint: true,
    }, false);
    if (options.name){
        chart.setTitle(null, { text: options.name});
    }else{
        chart.setTitle(null, { text: subtitle});
    };
    //chart.xAxis[0].remove(false);
    chart.redraw();
};
chart = new Highcharts.chart({
    chart: { renderTo: 'container' },
    title: { text: 'Count of Targets by ' +  prop },
    subtitle: { text: subtitle },
    credits: {"enabled":false},
    xAxis: { 
        type: 'category', 
        //title: {text: xaxis } ,
    },
    yAxis: { 
        title: {text: 'Total' } 
    },
    legend: { enabled: false },
    exporting: { enabled: false },
    plotOptions: {
        series: {
            cursor: 'pointer',
            datalabels: {
                enabled: false,
            },
            point: {
                events: {
                    click: function(){
                        var drilldown = this.drilldown;
                        var options;
                        if (drilldown){
                            options = {
                                'name': drilldown.name,
                                //'categories': drilldown.categories,
                                'data': drilldown.data,
                                'type': 'pie',
                            }
                        }else{
                            options = {
                                //'name':name,
                                //'categories':categories,
                                'data':data,
                                'type':'pie',
                            }
                        }
                        setChart(options);
                    }
                }
            }
        }
    },
    tooltip: {
        //headerFormat: '<span>{series.name}</span><br>',
        pointFormat: '{point.y} targets'
    },
    series: [{
        colorByPoint: true,
        type: 'pie',
        name: name,
        data: data,
    }]
});
}
