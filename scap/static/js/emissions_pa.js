var index = $("#emissions_chart_pa").data('highchartsChart');
var chart_em_obj_pa = Highcharts.charts[index];
var chart_obj_empa=chart_em_obj_pa;
var series = chart_obj_empa.series;

let defaultLC_empa="";
let defaultAGB_empa="";

showDefault_pa();
function standardize_color(str) {
    var ctx = document.createElement("canvas").getContext("2d");
    ctx.fillStyle = str;
    return ctx.fillStyle;
}


function showDefault_pa() {
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    let checkboxElement = document.getElementsByClassName('LC_cb_pa');
    let myValue = def_lc;
    for (var i = 0; i < checkboxElement.length; i++) {
        if (document.getElementById('emLC' + checkboxElement[i].value).innerHTML === myValue) {
            defaultLC_empa = 'LC' + checkboxElement[i].value;
            checkboxElement[i].checked = true;
        } else {

            checkboxElement[i].checked = false;
        }

    }
         checkboxElement = document.getElementsByClassName('AGB_cb_pa');
     myValue = def_agb;
    for (var i = 0; i < checkboxElement.length; i++) {
        if (document.getElementById('emAGB' + checkboxElement[i].value).innerHTML === myValue) {
            defaultAGB_empa = 'AGB' + checkboxElement[i].value;
            checkboxElement[i].checked = true;
        } else {

            checkboxElement[i].checked = false;
        }

    }
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name[0]===defaultLC_empa&& newseries[i].name[1]==defaultAGB_empa) {
            chart.series[i].setVisible(true, false);
        } else {
            chart.series[i].setVisible(false, false);
        }
    }


}

var newseries = series;
var new_updated = series;

var percent = 10;
var ns = [];
var lcss = get_checked_lcs_pa();
var agbss = get_checked_agbs_pa();
var min_arr = [];
var res_mmm = [];
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
    $.each(chart_em_obj_pa.series, function (i, s) {
        for (var j = 0; j < lc_colors.length; j++) {

            if (('LC' + lc_colors[j]['LC'] === s.name[0])&& ('AGB' + lc_colors[j]['AGB'] === s.name[1])) {
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
    chart_em_obj_pa.update({series: ns});
    chart_em_obj_pa.addSeries(min_arr);
    chart_em_obj_pa.addSeries(max_arr);
    chart_em_obj_pa.addSeries(avg_arr);


    chart_em_obj_pa.update({
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


chart_em_obj_pa.update({
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
            selected: false,

            events: {
                checkboxClick: function (event) {
                    if (this.visible) {
                        this.setVisible(false, false);
                    } else {
                        this.setVisible(true, false);
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

function redraw_mma_pa(chart) {

    var ns = [];
    var lcss = get_checked_lcs_pa();
    var agbss = get_checked_agbs_pa();
    var min_arr = [];
    var res_mmm = [];
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
        var flag=0;
        if (chart!=undefined) {
            $.each(chart.series, function (i, s) {

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
            chart.update({series: ns});
            // $.each(chart.series, function (i, s) {
            //      if (s.name === 'Min') {
            //     s.update({
            //         data: min_arr.data
            //     }, true);
            //       s.setVisible(true,false);
            //
            // }
            // if (s.name === 'Max') {
            //     s.update({
            //         data: max_arr.data
            //     }, true);
            //       s.setVisible(true,false);
            // }
            // if (s.name === 'Avg') {
            //     s.update({
            //         data: avg_arr.data
            //     }, true);
            //     s.setVisible(true,false);
            //
            // }
            // });
                // chart_cs_obj.addSeries(min_arr);
                // chart_cs_obj.addSeries(max_arr);
                // chart_cs_obj.addSeries(avg_arr);



        }
        else {
            console.log("Error: Chart object does not exist")
        }
    });

}

function show_line_pa(elem) {
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
    for (var i = 0; i < newseries.length; i++){
        if (LC_arr.includes(newseries[i].name[0]) && AGB_arr.includes(newseries[i].name[1])) {
             chart.series[i].setVisible(true,false);
        }
    }
     redraw_mma_pa(chart);
}
function access_lines(elem, dataset) {
    // var msg = all_unchecked();

    // if (msg.length == 0) {
    if (elem.checked) {
        show_line_pa(dataset + elem.value);

    } else {
        hide_line_pa(dataset + elem.value);
    }
    // }
    // } else {
    //     alert(msg);
    //     elem.checked = true;
    // }
    var ns = [];
    var lcss = get_checked_lcs_pa();
    var agbss = get_checked_agbs_pa();
    var min_arr = [];
    var max_arr = [];
    var avg_arr = [];


}
function hide_line_pa(elem) {
     var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name.includes(elem)) {
             chart.series[i].setVisible(false,false);
        }
    }
    // redraw_mma_cs(chart);
}

function reset_lcs_pa() {
    var checked1 = document.querySelectorAll('input.LC_cb_pa:checked');
    var checked2 = document.querySelectorAll('input.AGB_cb_pa:checked');

    var uncheck = document.getElementsByClassName('LC_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart_cs = Highcharts.charts[index];
    var series = chart_cs.series;
    var agb = [];
    var AGB_arr = get_checked_agbs_pa();
    for (var i = 0; i < AGB_arr.length; i++) {
        agb[i] = 'AGB' + AGB_arr[i];
    }
    for (var i = 0; i < chart_cs.series.length; i++) {
        if (agb.includes(series[i].name[1])) {
            chart_cs.series[i].setVisible(true, false);
        }
    }
    redraw_mma_pa(chart_cs);
}

function reset_agbs_pa() {
       var checked1 = document.querySelectorAll('input.LC_cb_pa:checked');
    var checked2 = document.querySelectorAll('input.AGB_cb_pa:checked');

    var uncheck = document.getElementsByClassName('AGB_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart_cs = Highcharts.charts[index];
    var series = chart_cs.series;
    var LC_arr = get_checked_lcs_pa();
    var lc = [];
    for (var i = 0; i < LC_arr.length; i++) {
        lc[i] = 'LC' + LC_arr[i];
    }
    for (var i = 0; i < chart_cs.series.length; i++) {
          if (lc.includes(series[i].name[0])) {
              chart_cs.series[i].setVisible(true, false);
          }
    }
    redraw_mma_pa(chart_cs);
}
function clear_lcs_pa() {
    var uncheck = document.getElementsByClassName('LC_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
     for (var i = 0; i < chart.series.length; i++) {
               chart.series[i].setVisible(false,false);
    }
}
function clear_agbs_pa() {
     var uncheck = document.getElementsByClassName('AGB_cb_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'LC');
    }
    var index = $("#emissions_chart_pa").data('highchartsChart');
    var chart = Highcharts.charts[index];
     for (var i = 0; i < chart.series.length; i++) {
               chart.series[i].setVisible(false,false);
    }

}

function get_checked_lcs_pa() {
    var lcs = [];
    $('.LC_checkboxlist input[type="checkbox"]:checked').each(function () {

        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        lcs.push(temp.replace('L', '').replace('C', ''));
    });
    return lcs;
}

function get_checked_agbs_pa() {
    var agbs = [];
    $('.AGB_checkboxlist input[type="checkbox"]:checked').each(function () {
        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        agbs.push(temp.replace('A', '').replace('G', '').replace('B', ''));
    });
    return agbs;
}
function reset_lcs_fc_pa() {

    var uncheck = document.getElementsByClassName('LC_cb_cf_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = true;
        // show_line(uncheck[i]);
// access_lines(uncheck[i],'LC');
    }
    var index = $("#container_fcpa").data('highchartsChart');
        if(document.getElementById('container_fcpa').style.display=='none'){
        index = $("#container_deforestation_pa").data('highchartsChart');
    }
    var chart = Highcharts.charts[index];

    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
         chart.series[i].setVisible(true,false);
    }
        chart.redraw();
}
function clear_lcs_fc_pa() {
    var uncheck = document.getElementsByClassName('LC_cb_cf_pa');
    for (var i = 0; i < uncheck.length; i++) {

        uncheck[i].checked = false;
        // access_lines(uncheck[i],'LC');
    }
    var index = $("#container_fcpa").data('highchartsChart');
        if(document.getElementById('container_fcpa').style.display=='none'){
        index = $("#container_deforestation_pa").data('highchartsChart');
    }
    var chart = Highcharts.charts[index];
    var series = chart.series;
    for (var i = 0; i < series.length; i++) {
                chart.series[i].setVisible(false,false);

    }

}