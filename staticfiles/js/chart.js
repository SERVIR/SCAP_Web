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
    const xhr = ajax_call("get-series", {

    });
function onlyUnique(value, index, array) {
  return array.indexOf(value) === index;
}


    xhr.done(function (result) {
        var colors = Highcharts.getOptions().colors;
        var year_arr=[];
        var value_arr=[];
        var series_arr=[];

        let series = result.final;
        for (var i = 0; i < series.length; i++) {
            series[i]['selected']=true;
        }
        $('#container').highcharts({

            chart: {
                events: {
                    load() {
                        // Check all checkboxes on load
                        const chart = this;
                        chart.series.forEach(series => {
                            series.checkbox.checked = true;
                            series.selected = true;
                        })
                    }
                },
                type: 'spline',
                marginBottom: 30,
                zoomType: 'x'
            },
            title: {
                text: 'line Chart SCAP',
                align: 'left'
            },

            subtitle: {
                align: 'left'
            },

            yAxis: {
                title: {
                    text: 'LC/AGB Value'
                }
            },

            xAxis: {
                tickInterval: 1,

                accessibility: {
                    rangeDescription: 'Range: 1980 to 2004'
                }
            },

            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle'
            },

            plotOptions: {
                series: {
                    showCheckbox: true,
                    label: {
                        enabled: false,
                    },
                    pointStart: 1980
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
        });
    });