var index = $("#container1").data('highchartsChart');
var chart1 = Highcharts.charts[index];
var index_def = $("#container_deforestation").data('highchartsChart');
var chart_def = Highcharts.charts[index_def];

var series = chart1.series;
var newseries = series;
// console.log(series)
// chart1.addSeries({
//             name: "Net Loss",
//     data:[{x:2003,y:5555},{x:2004,y:5555},{x:2005,y:5555},{x:2006,y:5555},{x:2007,y:5555}],
// dashStyle: 'dot',
// color:'grey',
//     marker: {
//        enabled: false
//     }
//         }, true);

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

chart_def.update({
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
            label = 'Deforestation';
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

// Update chart options
chart_def.update({
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
        if(document.getElementById('container1').style.display=='none'){
        index = $("#container_deforestation").data('highchartsChart');
    }
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
    if(document.getElementById('container1').style.display=='none'){
        index = $("#container_deforestation").data('highchartsChart');
    }
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
function populate_nr_nfc(){
    var nr_data = {
            "Ghana": {'value': -1475.80, 'start_year': 2001, 'end_year': 2015},
            "Kenya": {'value': -12069, 'start_year': 2002, 'end_year': 2018},
            "Nepal": {'value': -871.60, 'start_year': 2000, 'end_year': 2010},
            "Guatemala": {'value': -104850.05, 'start_year': 2001, 'end_year': 2010},
            "Cote d'Ivorie": {'value': -109411.81, 'start_year': 2000, 'end_year': 2015},
            "Bhutan": {'value': -53.81, 'start_year': 2000, 'end_year': 2015},
        }
        var data_obj = [];
            if( nr_data[country_name]!=undefined) {
                var current_country_value = nr_data[country_name]['value'];
                     for (var i = 2000; i <= 2022; i++) {
            if (i<nr_data[country_name]['start_year']){
                            data_obj.push({x: i, y: null});

            }
            else if (i>nr_data[country_name]['end_year']){
                    data_obj.push({x: i, y: null});
            }
            else{
                data_obj.push({x: i, y: current_country_value});

            }
        }
            }
           var seriesLength = chart1.series.length;
                for(var i = seriesLength - 1; i > -1; i--)
                {
                    //chart.series[i].remove();
                    if(chart1.series[i].name =="National Reporting")
                        chart1.series[i].remove();
                }
                if (data_obj.length>0) {
                    chart1.addSeries({
                        name: "National Reporting",
                        id: "National Reporting",

                        data: data_obj,
                        dashStyle: 'dot',
                        lineWidth: 5,

                        color: 'grey',
                        marker: {
                            enabled: false
                        }
                    }, true);
                }
}
function  populate_nr_def(){
     var nr_data = {
            "Costa Rica": {'value': 5616.19, 'start_year': 2000, 'end_year': 2014},
            "Peru": {'value': 118080.07, 'start_year': 2001, 'end_year': 2014},
            "Ghana": {'value': 18340.46, 'start_year': 2001, 'end_year': 2015},
            "Zambia": {'value': 191596.23, 'start_year': 2009, 'end_year': 2018},
            "Vietnam": {'value': 101000.00, 'start_year': 1995, 'end_year': 2010},
            "Thailand": {'value': 27401.64, 'start_year': 2006, 'end_year': 2016},
            "Guyana": {'value': 5791.67, 'start_year': 2001, 'end_year': 2012},
            "Kenya": {'value': 338863.00, 'start_year': 2002, 'end_year': 2018},
            "Nepal": {'value': 2231.40, 'start_year': 2000, 'end_year': 2010},
            "Guatemala": {'value': 106845.00, 'start_year': 2001, 'end_year': 2010},
            "Bangladesh": {'value': 14070.00, 'start_year': 2000, 'end_year': 2015},
            "Colombia": {'value': 145943.00, 'start_year': 2000, 'end_year': 2017},
            "Ivory Coast": {'value': 124551.68, 'start_year': 2000, 'end_year': 2015},
            "Bhutan": {'value': 175.60, 'start_year': 2000, 'end_year': 2015},
            "Cambodia": {'value': 268803.00,'start_year': 2011, 'end_year': 2018},
        }
        var data_obj = [];
        var current_country_value = nr_data[country_name]['value'];
        for (var i = 2000; i <= 2022; i++) {
            if (i<nr_data[country_name]['start_year']){
                            data_obj.push({x: i, y: null});

            }
            else if (i>nr_data[country_name]['end_year']){
                    data_obj.push({x: i, y: null});
            }
            else{
                data_obj.push({x: i, y: current_country_value});

            }
        }
           var seriesLength = chart_def.series.length;
                for(var i = seriesLength - 1; i > -1; i--)
                {
                    //chart.series[i].remove();
                    if(chart_def.series[i].name =="National Reporting")
                        chart_def.series[i].remove();
                }
                 if (data_obj.length>0) {
                     chart_def.addSeries({
                         name: "National Reporting",
                         data: data_obj,
                         dashStyle: 'dot',
                         lineWidth: 5,

                         color: 'grey',
                         marker: {
                             enabled: false
                         }
                     }, true);
                 }
}
function checkbox_toggle(elem){
    if (elem.checked) {
        console.log('checked');
        $('#toggle_label').html('Net Forest Change');

        document.getElementById('container_deforestation').style.display = 'none';
        document.getElementById('container1').style.display = 'block';


populate_nr_nfc();
    }
    else {
        document.getElementById('container_deforestation').style.display = 'block';
        document.getElementById('container1').style.display = 'none';
        $('#toggle_label').html('Deforestation');

       populate_nr_def();

    }
};
populate_nr_nfc();