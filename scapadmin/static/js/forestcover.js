 var index=$("#container1").data('highchartsChart');
 var chart=Highcharts.charts[index];

var series = chart.series;
var newseries=series;


for (var i = 0; i < newseries.length; i++) {


}

chart.update({ chart: { type: 'spline'}});
chart.update({
        plotOptions: {
            series: {
                marker: {
                    enabled: false,
                    states: {
                        hover: {
                            enabled: false
                        }
                    }
                }, showCheckbox: true,
                selected: true,

                events: {
                    checkboxClick: function (event) {
                        if (this.visible) {
                            this.hide();
                        } else {
                            this.show();
                        }
                    }
                }
            }
        }
    }
);
function test(){
        alert("test");
}
