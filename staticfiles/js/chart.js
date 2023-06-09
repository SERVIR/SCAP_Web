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
        console.log(series);
        for (var i = 0; i < series.length; i++) {
            series[i]['selected']=true;
               series[i]['events']=
            {
                checkboxClick()
                {
                    if (this.visible) {
                        this.hide();
                    } else {
                        this.show();
                    }
                }
            ,
                legendItemClick(e)
                {
                    const chart = e.target.chart,
                        index = e.target.index;
                    chart.series[index].checkbox.checked = this.selected = !this.visible;
                }
            };
        }
        $('#container').highcharts({

            chart: {

                type: 'spline',
marginBottom: 120,
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
        align: 'left',
       floating: true,

    // itemMarginBottom: 5,
    // width: 180,
    // itemWidth: 300,
    // useHTML: true,
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