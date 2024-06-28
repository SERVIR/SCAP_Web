var index = $("#container1").data('highchartsChart');
var chart1 = Highcharts.charts[index];

var series = chart1.series;
var newseries = series;

var result1 = "";

function get_name(elem) {
    // var result1="";
    const xhr = ajax_call("get-series-name1", {'ds_lc': elem[1], 'ds_agb': ""});
    xhr.done(function (result) {
        result1 = result.name;
        // console.log(result1);
    });
}

function standardize_color(str) {
    var ctx = document.createElement("canvas").getContext("2d");
    ctx.fillStyle = str;
    return ctx.fillStyle;
}

// This function is to set the brightness of the lines on the chart
function increase_brightness(hex, percent) {
    hex = hex.replace(/^\s*#|\s*$/g, '');

    // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
    if (hex.length == 3) {
        hex = hex.replace(/(.)/g, '$1$1');
    }

    var r = parseInt(hex.substr(0, 2), 16),
        g = parseInt(hex.substr(2, 2), 16),
        b = parseInt(hex.substr(4, 2), 16);

    return '#' +
        ((0 | (1 << 8) + r + (256 - r) * percent / 100).toString(16)).substr(1) +
        ((0 | (1 << 8) + g + (256 - g) * percent / 100).toString(16)).substr(1) +
        ((0 | (1 << 8) + b + (256 - b) * percent / 100).toString(16)).substr(1);
}


var color = "#000000";
var ta = [], nfc = [];
var percent = 10;
var m = 0;
var n = 0;
// Loop through each series and set the color
for (var i = 0; i < newseries.length; i++) {
    for (var j = 0; j < lc_colors.length; j++) {
        if ('LC' + lc_colors[j]['LC'] == (newseries[i].name)) {

            color = lc_colors[j]['color'];
            chart1.series[i].update({color: color});

        }
    }

}

chart1.update({
    yAxis: {
        title: {
            text: 'Values (Ha)'
        }
    },
    tooltip: {
        useHTML: true,
        enabled: true,
        backgroundColor: null,
        borderWidth: 0,
        shadow: false,
        formatter: function () {
            const ss = this.series.name;
            const lc = ss;
            const color = this.series.color;
            // const s_name = get_name(ss);
            // if (this.y > 0) {
            //     label = "Forest Gain";
            // } else {
            //     label = "Forest Loss";
            // }
            label = 'Net Forest Change';
            var labellc = ss;
            var value = '<div style="background-color:' + standardize_color(color) + "E6" + ';padding:10px">' +
                '<span>' + label + ' ' + this.x + '<br>  <b>' + (this.y).toLocaleString('en-US') + ' Ha</b>' +
                '<span style=\'padding-left:50px\'></span> ' + result1.split(',')[0] + '<br/>' + labellc + ' </span><div>';
            return value;
        }
    }
});

// Update chart options
chart1.update({
        chart: {
            type: 'spline'
        },
       exporting: {
    buttons: {
      contextButton: {
        menuItems: ["viewFullscreen",
                        "printChart",
                    "separator",
                    "downloadPNG",
                    "downloadJPEG",
                    "downloadPDF",
                    "downloadSVG",
                    "separator",
                    "downloadCSV",
                    "downloadXLS",]
      }
    }
  },

        plotOptions: {
            series: {
                connectNulls: true,
                marker: {
                    enabled: false,
                    states: {
                        hover: {
                            enabled: false
                        }
                    }
                }, showCheckbox: false,
                selected: true,

                events: {
                    checkboxClick: function (event) {
                        if (this.visible) {
                             this.setVisible(false,false);
                        } else {
                             this.setVisible(true,false);
                        }
                    }
                }
            }
        }
    }
);

//  Hide lines on the chart based on checkbox selection
function hide_line_fc(elem) {
    var index = $("#container1").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        console.log(newseries[i].name)
        if (newseries[i].name === document.getElementById(elem).innerText) {
            chart.series[i].hide();
        }
    }
}

// Show lines on the chart based on checkbox selection
function show_line_fc(elem) {
    var index = $("#container1").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name===document.getElementById(elem).innerText) {
            chart.series[i].show();
        }
    }
}

// Show/Hide lines on the chart based on checkbox selection
function access_lines_fc(elem, dataset) {
    console.log(elem.checked);
    var msg = all_unchecked_fc();
    // if (msg.length == 0) {
    if (elem.checked) {
        show_line_fc(dataset + elem.value);

    } else {
        hide_line_fc(dataset + elem.value);
    }
    // } else {
    //     alert(msg);
    //     elem.checked = true;
    // }
}

// Show alert if all checkboxes are unchecked
function all_unchecked_fc() {
    var msg = "";
    var checked1 = document.querySelectorAll('input.LC_cb_cf:checked');

    if (checked1.length === 0) {

        msg = 'No LC checkboxes checked. Please select at least one Land Cover checkbox.';
    } else {

        console.log(checked1.length + ' checkboxes checked');
    }
    return msg;
}

