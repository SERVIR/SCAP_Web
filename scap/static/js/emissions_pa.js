// Retrieve the chart from the DOM, and instantiate it
var index = $("#emissions_chart_pa").data('highchartsChart');
var chart_emissions_pa = Highcharts.charts[index];
var series = chart_emissions_pa.series;
var newseries = series;
var new_updated = series;
var result1 = "";
var gname = "";

function get_name(elem) {
    var result1 = "";
    const xhr = ajax_call("get-series-name", {'ds_lc': elem[0], 'ds_agb': elem[1]});
    xhr.done(function (result) {
        result1 = result.name;
    });
    return result1;
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

var percent = 10;
var ns = [];
var lcss =get_checked_lcs();
var agbss = get_checked_agbs();
var min_arr = [];
var res_mmm = [];
var max_arr = [];
var avg_arr = [];

function standardize_color(str) {
    var ctx = document.createElement("canvas").getContext("2d");
    ctx.fillStyle = str;
    return ctx.fillStyle;
}

const xhr = ajax_call("get-min-max", {"lcs": lcss, "agbs": agbss});
xhr.done(function (result2) {
    console.log((result2.min))
    min_arr = {
        "name": "Min",
        "data": result2.min,
        "color": 'green',
        "visible": true,
        legendIndex: -1,
        lineWidth: 5,
        dashStyle: 'shortdash'
    };
    max_arr = {
        "name": "Max",
        "data": result2.max,
        "color": 'red',
        "visible": true,
        lineWidth: 5,
        legendIndex: -2,

        dashStyle: 'shortdash'
    };
    avg_arr = {
        "name": "Avg",
        "data": result2.avg,
        "color": 'orange',
        "visible": true,
        lineWidth: 5,
        legendIndex: -3,
        dashStyle: 'shortdash'
    };
    $.each(chart_emissions_pa.series, function (i, s) {
        for (var j = 0; j < lc_colors.length; j++) {

            if (('LC' + lc_colors[j]['LC'] === s.name[0]) && ('AGB' + lc_colors[j]['AGB'] === s.name[1])) {
                s.color = lc_colors[j]['color'];
                ns.push({
                    name: s.name,
                    data: s.data,
                    color: s.color,
                    visible: true,
                    lineWidth: 2,
                    legendIndex: null,
                    dashStyle: ''
                });

            }


        }
    });

    chart_emissions_pa.update({series: ns});
    chart_emissions_pa.addSeries(min_arr);
    chart_emissions_pa.addSeries(max_arr);
    chart_emissions_pa.addSeries(avg_arr);

    chart_emissions_pa.update({
        yAxis: {
            title: {
                text: 'Values (Tons)'
            }
        },
        tooltip: {
            useHTML: true,
            enabled: true,
            backgroundColor: null,
            borderWidth: 0,
            shadow: false,
            formatter: function () {
                const color = this.series.color;
                const ss = this.series.name;
                if (ss === "Min" || ss === "Max" || ss === "Avg") {


                    var value = '<div style="background-color:' + standardize_color(color) + "60" + ';padding:10px"><span>' +
                        '<b>Emissions ' + this.x + ': ' + (this.y).toLocaleString('en-US') + ' Tons</b></span><div>';
                    //  var value = '<div style="background-color:' + color + ';padding:10px"><span>' +
                    //     '<b>Emissions ' + this.x + ': ' + (this.y).toLocaleString('en-US') + ' Tons</b>' +
                    //     '<span style=\'padding-left:50px\'></span><br/> ' +  lc+'<br/>' + agb+'</span><div>';
                    return value;
                }
                const lc = ss[0];
                const agb = ss[1];
                // const s_name = get_name(ss);
                var labellc = document.getElementById(lc).innerText;
                var labelagb = document.getElementById(agb).innerText;
                labellc = labellc.replace(/ *\([^)]*\) */g, "");
                labelagb = labelagb.replace(/ *\([^)]*\) */g, "");
                var value = '<div style="background-color:' + standardize_color(color) + "60" + ';padding:10px"><span>' +
                    '<b>Emissions ' + this.x + ': ' + (this.y).toLocaleString('en-US') + ' Tons</b>' +
                    '<span style=\'padding-left:50px\'></span><br/> Forest cover: ' + labellc + '<sub>' + lc + '</sub><br/> AGB: ' +
                    labelagb + '<sub>' + agb + '</sub></span><div>';
                //  var value = '<div style="background-color:' + color + ';padding:10px"><span>' +
                //     '<b>Emissions ' + this.x + ': ' + (this.y).toLocaleString('en-US') + ' Tons</b>' +
                //     '<span style=\'padding-left:50px\'></span><br/> ' +  lc+'<br/>' + agb+'</span><div>';
                return value;
            }
        }
    });
});

chart_emissions_pa.update({
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
                connectNulls: false,
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
        },
      legend: {
    itemDistance: 50,
    maxHeight: 100
    /* floating: true,
    y: 75 */
  },
        lang: {
            noData: "No data found. Please select LC/AGB from the list."
        },
        noData: {
            style: {
                fontWeight: 'bold',
                fontSize: '15px'
            }
        },



    }
);

//  Hide lines on the chart based on checkbox selection
function hide_line(elem) {
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name.includes(elem)) {
             chart.series[i].setVisible(false,false);
        }
    }
    redraw_mma();
}

// Show lines on the chart based on checkbox selection
function show_line(elem) {
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    var checked1 = document.querySelectorAll('input.LC_cb_pa:checked');
    var LC_arr = [];
    for (var i = 0; i < checked1.length; i++) {
        LC_arr.push('LC' + checked1[i].value);
    }
    var checked2 = document.querySelectorAll('input.AGB_cb_pa:checked');
    var AGB_arr = [];
    for (var i = 0; i < checked2.length; i++) {
        AGB_arr.push('AGB' + checked2[i].value);
    }
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name.includes(elem) && LC_arr.includes(newseries[i].name[0]) && AGB_arr.includes(newseries[i].name[1])) {
             chart.series[i].setVisible(true,false);
        }
    }
    redraw_mma();
}


// Show lines on the chart based on checkbox selection

// Show/Hide lines on the chart based on checkbox selection
function access_lines(elem, dataset) {
    if (elem.checked) {
        show_line(dataset + elem.value);

    } else {
        hide_line(dataset + elem.value);
    }
    var ns = [];
    var lcss = get_checked_lcs();
    var agbss = get_checked_agbs();
    var min_arr = [];
    var max_arr = [];
    var avg_arr = [];
    const xhr = ajax_call("get-min-max", {"lcs": lcss, "agbs": agbss});
    xhr.done(function (result2) {
        min_arr = {
            "name": "Min",
            "data": result2.min,
            "color": 'green',
            "visible": true,
            legendIndex: -1,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        max_arr = {
            "name": "Max",
            "data": result2.max,
            "color": 'red',
            "visible": true,
            lineWidth: 5,
            legendIndex: -2,

            dashStyle: 'shortdash'
        };
        avg_arr = {
            "name": "Avg",
            "data": result2.avg,
            "color": 'orange',
            "visible": true,
            lineWidth: 5,
            legendIndex: -3,
            dashStyle: 'shortdash'
        };

        $.each(chart_emissions_pa.series, function (i, s) {
            for (var j = 0; j < lc_colors.length; j++) {
                if (('LC' + lc_colors[j]['LC'] === s.name[0]) && ('AGB' + lc_colors[j]['AGB'] === s.name[1])) {
                    s.color = lc_colors[j]['color'];
                    ns.push({
                        name: s.name,
                        data: s.data,
                        color: s.color,
                        visible: true,
                        lineWidth: 2,
                        legendIndex: null,
                        dashStyle: ''
                    });

                }


            }
            console.log(s.name === 'Min')
            if (s.name === 'Min') {
                s.update({
                    data: min_arr.data
                }, true);
                 s.setVisible(true,false);
            }
            if (s.name === 'Max') {
                s.update({
                    data: max_arr.data
                }, true);
                 s.setVisible(true,false);
            }
            if (s.name === 'Avg') {
                s.update({
                    data: avg_arr.data
                }, true);
                s.setVisible(true,false);
            }
        });


        chart_emissions_pa.update({series: ns});


    });


}



// Show alert if all checkboxes are unchecked
function all_unchecked() {
    var msg = "";
    var checked1 = document.querySelectorAll('input.LC_cb_pa:checked');

    if (checked1.length === 0) {

        msg = 'No LC checkboxes checked. Please select at least one Land Cover checkbox.';
    } else {

        console.log(checked1.length + ' checkboxes checked');
    }
    var checked2 = document.querySelectorAll('input.AGB_cb_pa:checked');

    if (checked2.length === 0) {

        msg = 'No AGB checkboxes checked. Please select at least one Above Ground Biomass checkbox.';
    } else {

        console.log(checked2.length + ' checkboxes checked');
    }
    return msg;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function ajax_call(ajax_url, ajax_data) {
    //update database
    return jQuery.ajax({
        type: "POST",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        url: ajax_url.replace(/\/?$/, '/'),
        dataType: "json",
        data: ajax_data
    })
        .fail(function (xhr, status, error) {
            console.log(xhr.responseText);
        });
}

function get_checked_lcs() {
    var lcs = [];
    $('.LC_checkboxlist input[type="checkbox"]:checked').each(function () {

        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        // console.log(temp.replace('L', '').replace('C', ''));
        lcs.push(temp.replace('L', '').replace('C', ''));
    });
    return lcs;
}


function get_checked_agbs() {
    var agbs = [];
    $('.AGB_checkboxlist input[type="checkbox"]:checked').each(function () {
        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        agbs.push(temp.replace('A', '').replace('G', '').replace('B', ''));
    });
    return agbs;
}

function redraw_mma(){
      var ns = [];
    var lcss = get_checked_lcs();
    var agbss = get_checked_agbs();
    var min_arr = [];
    var max_arr = [];
    var avg_arr = [];
     console.log(lcss)
    const xhr = ajax_call("get-min-max", {"lcs": lcss, "agbs": agbss});

    xhr.done(function (result2) {
        min_arr = {
            "name": "Min",
            "data": result2.min,
            "color": 'green',
            "visible": true,
            legendIndex: -1,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        max_arr = {
            "name": "Max",
            "data": result2.max,
            "color": 'red',
            "visible": true,
            lineWidth: 5,
            legendIndex: -2,

            dashStyle: 'shortdash'
        };
        avg_arr = {
            "name": "Avg",
            "data": result2.avg,
            "color": 'orange',
            "visible": true,
            lineWidth: 5,
            legendIndex: -3,
            dashStyle: 'shortdash'
        };

        $.each(chart_emissions_pa.series, function (i, s) {
            for (var j = 0; j < lc_colors.length; j++) {
                if (('LC' + lc_colors[j]['LC'] === s.name[0]) && ('AGB' + lc_colors[j]['AGB'] === s.name[1])) {
                    s.color = lc_colors[j]['color'];
                    ns.push({
                        name: s.name,
                        data: s.data,
                        color: s.color,
                        visible: true,
                        lineWidth: 2,
                        legendIndex: null,
                        dashStyle: ''
                    });

                }


            }
            console.log(s.name === 'Min')
            if (s.name === 'Min') {
                s.update({
                    data: min_arr.data
                }, true);

            }
            if (s.name === 'Max') {
                s.update({
                    data: max_arr.data
                }, true);
            }
            if (s.name === 'Avg') {
                s.update({
                    data: avg_arr.data
                }, true);

            }

        });

});
}

function reset_lcs_pa() {

    var uncheck = document.getElementsByClassName('LC_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
         chart.series[i].setVisible(true,false);
    }
redraw_mma();
}

function reset_lcs_fc_pa() {

    var uncheck = document.getElementsByClassName('LC_cb_cf_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'LC');
    }
    var index = $("#container_fcpa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
         chart.series[i].setVisible(true,false);
    }
}

function get_checked_agbs() {
    var agbs = [];
    $('.AGB_checkboxlist input[type="checkbox"]:checked').each(function () {
        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        agbs.push(temp.replace('A', '').replace('G', '').replace('B', ''));
    });
    return agbs;
}

function reset_agbs_pa() {
    var uncheck = document.getElementsByClassName('AGB_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'AGB');
    }

    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
               chart.series[i].setVisible(true,false);
    }
redraw_mma();
}


function clear_lcs_pa() {
    var uncheck = document.getElementsByClassName('LC_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
        chart.series[i].setVisible(false,false);
    }

    	 // $("#container").highcharts().destroy();
         // chart.showNoData('jfjkf');

}
function clear_lcs_fc_pa() {
    var uncheck = document.getElementsByClassName('LC_cb_cf_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'LC');
    }
    var index = $("#container_fcpa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
                chart.series[i].setVisible(false,false);

    }

}

function clear_agbs_pa() {

    var uncheck = document.getElementsByClassName('AGB_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'AGB');

    }

    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
               chart.series[i].setVisible(false,false);

    }

}