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
        console.log(temp.replace('L', '').replace('C', ''));
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


var lcs = [];
var agbs = [];


function get_chart(series) {
    $('#container').highcharts({
            chart: {
                type: 'spline',
                marginBottom: 230,

                zoomType: 'x',
            },
            title: {
                text: 'S-CAP Yearly Emissions Sample Chart (random values)',
                align: 'left'
            },

            subtitle: {
                align: 'left'
            },

            yAxis: {
                title: {
                    text: 'Emissions'
                }
            },

            xAxis: {
                tickInterval: 1,
            title: {
                    text: 'Years'
                }
            },

          legend: {
    useHTML: true,
    enabled: true,
    reversed: false,
		itemWidth:120,


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
                    },
                    showCheckbox: false,
                    label: {
                        enabled: false,
                    },
                    pointStart: series[0]['years'][0],

                }
            },

            series: series,

            responsive: {
                rules: [{
                    condition: {
                        maxWidth: 500
                    },
                    chartOptions: {
                        legend: {
                            layout: 'horizontal',
                            align: 'center',
                            verticalAlign: 'bottom'
                        }
                    }
                }]
            }
        }
    );
}
const xhr = ajax_call("get-series", {});
var series_arr = [];

xhr.done(function (result) {
    var colors = Highcharts.getOptions().colors;

    let series = result.final;
    // series.push(min_arr, max_arr, avg_arr);
    // console.log(series);
    lcs = result.lcs;
    agbs = result.agbs;
    $.each(lcs, function (index) {
        $('.LC_checkboxlist').append("<input type='checkbox' checked name='students[]' class='LC_cb' onclick='get_updated_chart(this)' value='" + lcs[index] + "' />" + lcs[index] + "<br/>");
    });

    $.each(agbs, function (index) {
        $('.AGB_checkboxlist').append("<input type='checkbox' checked name='students[]' class='AGB_cb' onclick='get_updated_chart(this)' value='" + agbs[index] + "' />" + agbs[index] + "<br/>");
    });
    console.log(series);
    for (var i = 0; i < series.length; i++) {
        series[i]['selected'] = true;
        series[i]['events'] =
            {
                checkboxClick() {
                    if (this.visible) {
                        this.hide();
                    } else {
                        this.show();
                    }
                }
                ,
                legendItemClick(e) {
                    const chart = e.target.chart,
                        index = e.target.index;
                    chart.series[index].checkbox.checked = this.selected = !this.visible;
                }
            };
    }
    var lcss = get_checked_lcs();
    var agbss = get_checked_agbs();

    const xhr = ajax_call("get-min-max", {"lcs": lcss, "agbs": agbss});
    xhr.done(function (result1) {
        var min_arr = {
            "name": "min",
            "data": result1.min,
            "color": 'green',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        var max_arr = {
            "name": "max",
            "data": result1.max,
            "color": 'red',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        var avg_arr = {
            "name": "avg",
            "data": result1.avg,
            "color": 'orange',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        series_arr = series;
        series.push(min_arr, max_arr, avg_arr);
        console.log(series);
        get_chart(series);
    });

});

function cleanData(data, deletingKeys) {
    function isEmpty(obj) {
        if (obj === null) return true;
        if (Array.isArray(obj))
            return obj.length === 0;
        if (typeof obj === "object")
            return Object.keys(obj).length === 0;
    }

    function removeKeyFrom(aData) {
        if (Array.isArray(aData)) {
            const done = aData.reduce((accum, ele) => {
                const done = removeKeyFrom(ele);
                if (!isEmpty(done))
                    accum.push(done);
                return accum;
            }, []);
            return done.length > 0 ? done : null;
        }
        if (typeof aData === "object" && aData !== null) {
            const done = Object.keys(aData).reduce((accum, key) => {
                if (!deletingKeys.includes(key)) {
                    const done = removeKeyFrom(aData[key]);
                    if (!isEmpty(done)) // required for empty object element
                        accum[key] = done;
                }
                return accum;
            }, {});
            return (Object.keys(done).length > 0) ? done : null;
        }
        return aData;
    }

    return removeKeyFrom(data);
}

function get_updated_chart(this_obj) {
    if (series_arr.length > 24) {
        series_arr.splice(-3, 3);
    }

    var sarr = series_arr;
    var temp_series_arr_uncheck = series_arr;
    var temp_series_arr_check = series_arr;
    var lcs = get_checked_lcs();
    console.log(lcs);
    var agbs = get_checked_agbs();
    const xhr = ajax_call("get-min-max", {"lcs": lcs, "agbs": agbs});
    xhr.done(function (result) {
        var min_arr = {
            "name": "min",
            "data": result.min,
            "color": 'green',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        var max_arr = {
            "name": "max",
            "data": result.max,
            "color": 'red',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        var avg_arr = {
            "name": "avg",
            "data": result.avg,
            "color": 'orange',
            "visible": true,
            lineWidth: 5,
            dashStyle: 'shortdash'
        };
        var dataset = this_obj.value;
        var si = dataset.indexOf('(');
        var ei = dataset.indexOf(')');
        var dataset1 = dataset.substring(si + 1, ei);

        if (this_obj.checked) {

            console.log("checked");
            for (var i = 0; i < sarr.length; i++) {
                if (sarr[i].name.includes(dataset1)) {
                    sarr[i].visible = true;
                }
            }
            get_chart(sarr.concat(min_arr, max_arr, avg_arr));


        } else {
            var msg = all_unchecked();
            if (msg.length > 0) {
                alert(msg);
            } else {
                for (var j = 0; j < temp_series_arr_uncheck.length; j++) {
                    if (temp_series_arr_uncheck[j].name.includes(dataset1)) {
                        temp_series_arr_uncheck[j].visible = false;
                    }

                }
                get_chart(temp_series_arr_uncheck.concat(min_arr, max_arr, avg_arr));

            }
        }

    });
}

function all_unchecked() {
    var msg = "";
    var checked1 = document.querySelectorAll('input.LC_cb:checked');

    if (checked1.length === 0) {

        msg = 'No LC checkboxes checked. Please select at least one Land Cover checkbox.';
    } else {

        console.log(checked1.length + ' checkboxes checked');
    }
    var checked2 = document.querySelectorAll('input.AGB_cb:checked');

    if (checked2.length === 0) {

        msg = 'No AGB checkboxes checked';
    } else {

        console.log(checked2.length + ' checkboxes checked. Please select at least one Above Ground Biomass checkbox.');
    }
    return msg;
}