var index = $("#container1").data('highchartsChart');
var chart = Highcharts.charts[index];

var series = chart.series;
var newseries = series;

var result1="";

function get_name(elem) {
    // var result1="";
    const xhr = ajax_call("get-series-name", {'ds_lc': elem[0],'ds_agb':elem[1]});
    xhr.done(function (result) {
        result1=result.name;
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

var percent = 10;
// Loop through each series and set the color
for (var i = 0; i < newseries.length; i++) {

    // Making the percentage 100 will makes the lines black
    if (percent > 50) {
        percent = percent - 5;
    } else {
        percent = percent + 5;
    }
    var color = "#000000";
    for (var j = 0; j < lc_colors.length; j++) {
        if ('LC' + lc_colors[j]['lc_id'] == (newseries[i].name[1])) {
            color = increase_brightness(lc_colors[j]['lc_color'], percent);
        }
    }
    chart.series[i].update({color: color});
}
 chart.update({
    tooltip: {
       useHTML: true,
        enabled: true,
        backgroundColor: null,
        borderWidth: 0,
        shadow: false,
        formatter: function () {
             const ss = this.series.name;
            const lc=ss[0];
            const color=this.series.color;
            const s_name = get_name(ss);
             var value = '<div style="background-color:' + color + ';padding:10px"><span><b>Forest Cover '+ this.x +' -  (' + (this.y).toLocaleString('en-US') + ') Tons</b><span style=\'padding-left:50px\'></span><br/> ' + result1.split(',')[0] +' ('+ lc+')<br/> </span><div>';
                return value;
        }
    }
  });

// Update chart options
chart.update({
        chart: {
            type: 'spline'
        },
        plotOptions: {
            series: {
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
function hide_line(elem) {
    var index = $("#container1").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name[1] === elem) {
            chart.series[i].hide();
        }
    }
}

// Show lines on the chart based on checkbox selection
function show_line(elem) {
    var index = $("#container1").data('highchartsChart');
    var chart = Highcharts.charts[index];
    var series = chart.series;
    var newseries = series;
    for (var i = 0; i < newseries.length; i++) {
        if (newseries[i].name[1] === elem) {
            chart.series[i].show();
        }
    }
}

// Show/Hide lines on the chart based on checkbox selection
function access_lines(elem, dataset) {
    var msg = all_unchecked();
    if (msg.length == 0) {
        if (elem.checked) {
            show_line(dataset + elem.value);

        } else {
            hide_line(dataset + elem.value);
        }
    } else {
        alert(msg);
        elem.checked = true;
    }
}

// Show alert if all checkboxes are unchecked
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

