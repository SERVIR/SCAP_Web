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

function hide_line(elem){
    var index=$("#container1").data('highchartsChart');
    var chart=Highcharts.charts[index];
    var series = chart.series;
    var newseries=series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name[1] === elem) {
            chart.series[i].hide();
        }
    }
}

function show_line(elem){
    var index=$("#container1").data('highchartsChart');
    var chart=Highcharts.charts[index];
    var series = chart.series;
    var newseries=series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name[1] === elem) {
            chart.series[i].show();
        }
    }
}
function access_lines(elem,dataset){
    var msg = all_unchecked() ;
    if(msg.length == 0) {
        if (elem.checked) {
            show_line(dataset + elem.value);

        } else {
            hide_line(dataset + elem.value);
        }
    }
    else {
        alert(msg);
        elem.checked = true;
    }
}

function all_unchecked() {
    var msg = "";
    var checked1 = document.querySelectorAll('input.LC_cb:checked');

    if (checked1.length === 0) {

        msg = 'No LC checkboxes checked. Please select at least one Land Cover checkbox.';
    } else {

        console.log(checked1.length + ' checkboxes checked');
    }
    return msg;
}
