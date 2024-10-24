var index_fc = $("#container_fcpa").data('highchartsChart');
var chart1 = Highcharts.charts[index_fc];
var index_def_pa = $("#container_deforestation_pa").data('highchartsChart');
var chart_def_pa = Highcharts.charts[index_def_pa];

var series = chart1.series;
var newseries = series;

var result1 = "";

function get_name(elem) {
    // var result1="";
    const xhr = ajax_call("get-series-name1", {'ds_lc': elem[1], 'ds_agb': ""});
    xhr.done(function (result) {
        result1 = result.name;
    });
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
            text: 'Values (Ha)',
        }
    }, tooltip: {
        useHTML: true,
        enabled: true,
        backgroundColor: null,
        borderWidth: 0,
        shadow: false,
        formatter: function () {
            const ss = this.series.name;
            const lc = ss;
            const color = this.series.color;
            //    if (ss[0]==='NFC') {
            //     var label = "Net Forest Change";
            // } else {
            //     var label = "Total Forest Area";
            // }
            var label = "Net Forest Change";

            var labellc = document.getElementById(lc).innerText;
            var value = '<div style="background-color:' + standardize_color(color) + "E6" + ';padding:10px">' +
                '<span>' + label + ' ' + this.x + '<br>  <b>' + (this.y).toLocaleString('en-US') + ' Ha</b>' +
                '<span style=\'padding-left:50px\'></span> <br/>' + labellc + ' </span><div>';
            return value;
        }
    }
});

chart_def_pa.update({
    yAxis: {
        title: {
            text: 'Values (Ha)',
        }
    }, tooltip: {
        useHTML: true,
        enabled: true,
        backgroundColor: null,
        borderWidth: 0,
        shadow: false,
        formatter: function () {
            const ss = this.series.name;
            const lc = ss;
            const color = this.series.color;
            //    if (ss[0]==='NFC') {
            //     var label = "Net Forest Change";
            // } else {
            //     var label = "Total Forest Area";
            // }
            var label = "Deforestation";

            var labellc = document.getElementById(lc).innerText;
            var value = '<div style="background-color:' + standardize_color(color) + "E6" + ';padding:10px">' +
                '<span>' + label + ' ' + this.x + '<br>  <b>' + (this.y).toLocaleString('en-US') + ' Ha</b>' +
                '<span style=\'padding-left:50px\'></span> <br/>' + labellc + ' </span><div>';
            return value;
        }
    }
});

function getFC(pa_selected_name, data_obj) {
    chart1.update({series: data_obj.series, title: data_obj.title});
}

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

// Update chart options
chart_def_pa.update({
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

//  Hide lines on the chart based on checkbox selection
function hide_line_fc(elem) {
    var index = $("#container_fcpa").data('highchartsChart');
    if(document.getElementById('container_fcpa').style.display=='none'){
        index = $("#container_deforestation_pa").data('highchartsChart');
    }
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (document.getElementById(elem).innerText.includes(newseries[i].name)) {
            chart.series[i].hide();
        }
    }
}

// Show lines on the chart based on checkbox selection
function show_line_fc(elem) {
    var index = $("#container_fcpa").data('highchartsChart');
    if(document.getElementById('container_fcpa').style.display=='none'){
        index = $("#container_deforestation_pa").data('highchartsChart');
    }
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (document.getElementById(elem).innerText.includes(newseries[i].name)) {
            chart.series[i].show();
        }
    }
}

// Show/Hide lines on the chart based on checkbox selection
function access_lines_fc(elem, dataset) {
    // var msg = all_unchecked_fc();
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
    var checked1 = document.querySelectorAll('input.LC_cb_cf_pa:checked');

    if (checked1.length === 0) {

        msg = 'No LC checkboxes checked. Please select at least one Land Cover checkbox.';
    } else {

        console.log(checked1.length + ' checkboxes checked');
    }
    return msg;
}

function checkbox_toggle(elem){
    if (elem.checked) {
        console.log('checked');
        $('#toggle_label').html('Net Forest Change');

        document.getElementById('container_deforestation_pa').style.display = 'none';
        document.getElementById('container_fcpa').style.display = 'block';

    }
    else {
        document.getElementById('container_deforestation_pa').style.display = 'block';
        document.getElementById('container_fcpa').style.display = 'none';
        $('#toggle_label').html('Deforestation');
    }
};
