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
var lcs=[];
var agbs=[];


function get_chart(series){
 $('#container').highcharts({

            chart: {

                type: 'spline',
marginBottom: 120,
                zoomType: 'x'
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
                enabled: false
       //  align: 'left',
       // floating: true,

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
        }
            );
    };
  const xhr = ajax_call("get-series", {

    });
        var series_arr=[];

    xhr.done(function (result) {
        var colors = Highcharts.getOptions().colors;
        var year_arr=[];
        var value_arr=[];

        let series = result.final;
        lcs=result.lcs;
        agbs=result.agbs;
        $.each(lcs, function(index){
	$('.LC_checkboxlist').append("<input type='checkbox' checked name='students[]' onclick='get_updated_chart(this)' value='" + lcs[index] + "' />" + lcs[index] + "<br/>");
});

$.each(agbs, function(index){
	$('.AGB_checkboxlist').append("<input type='checkbox' checked name='students[]'  onclick='get_updated_chart(this)' value='" + agbs[index] + "' />" + agbs[index] + "<br/>");
});
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
        series_arr=series;
        get_chart(series);

    });

function get_updated_chart(this_obj) {
    console.log(series_arr);
    var sarr = series_arr;
    var temp_series_arr_uncheck = series_arr;
    var temp_series_arr_check = series_arr;
    var dataset = this_obj.value;
    if (this_obj.checked) {
        console.log("checked");
        for (var i = 0; i < sarr.length; i++) {
            if (sarr[i].name.includes(dataset)) {
                sarr[i].visible = true;
            }
        }
        get_chart(sarr);


    } else {
        for (var j = 0; j < temp_series_arr_uncheck.length; j++) {
            if (temp_series_arr_uncheck[j].name.includes(dataset)) {
                temp_series_arr_uncheck[j].visible = false;
            }

        }
        get_chart(temp_series_arr_uncheck);

    }

}