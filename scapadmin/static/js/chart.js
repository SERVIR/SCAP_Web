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
        result.map(function (item) {
            value_arr.push(item[0]);
            year_arr.push(item[1]);


        });
 var temp_arr=[];
        var unique = year_arr.filter(onlyUnique);
        unique.map(function (item) {
           temp_arr.push({year:item,name:'test',data:[]});
        });
        result.map(function (item) {
    for(var i=0;i<temp_arr.length;i++){
            if (temp_arr[i]['year']==(item[1])){
                temp_arr[i]['data'].push(item[0]);
                var j=i;

                temp_arr[i]['name']=('c_name');

            }
    }
        });

    temp_arr.map(function (item) {
        series_arr.push({name:item['name'],data:item['data']});
    });
    console.log(series_arr);

        let series = series_arr;
        $('#container').highcharts({

            chart: {
                type: 'line',
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
            label: {
                connectorAllowed: false
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