var pa_selected_name;
var mapOptions = {
    center: [-10.4, -75.3],
    zoom: 8
}

// init_map();
var first_layer;
var second_layer;

function get_years(ds) {
    var json_obj = [{'ds': 'mapbiomas', 'start': 2000, 'end': 2021},
        {'ds': 'cci', 'start': 2000, 'end': 2020},
        {'ds': 'esri', 'start': 2017, 'end': 2021},
        {'ds': 'jaxa', 'start': 2007, 'end': 2016},
        {'ds': 'modis', 'start': 2001, 'end': 2022},
        {'ds': 'worldcover', 'start': 2020, 'end': 2021},
    ]
    for (var i = 0; i < json_obj.length; i++) {
        if (json_obj[i].ds === ds) {
            return [json_obj[i].start, json_obj[i].end];
        }
    }
}

$('#datasource_select').on('change', function () {
    console.log("jhfjdh")
var bounds = L.latLng(40.737, -73.923).toBounds();
    console.log("kshjkdhsds")
map.fitBounds(bounds, {animation: false});
    console.log("kdlhfkjd")
    if (first_layer !== undefined) {
        map.removeLayer(first_layer);
    }
    if (second_layer !== undefined) {
        map.removeLayer(second_layer);
    }
    var ds = document.getElementById("datasource_select");
    var ds_name = ds.options[ds.selectedIndex].text.toLowerCase();

    var first_year = get_years(ds_name)[0];
    var last_year = get_years(ds_name)[1];
    first_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${ds_name}/${ds_name}.${first_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
        {
            layers: ["forest_cover"],
            format: "image/png",
            colorscalerange: "0.5,1",
            abovemaxcolor: 'transparent',
            belowmincolor: 'transparent',
            transparent: true,
            styles: 'boxfill/crimsonbluegreen',
        })
    second_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${ds_name}/${ds_name}.${last_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
        {
            layers: ["forest_cover"],
            format: "image/png",
            colorscalerange: "0.5,1",
            abovemaxcolor: 'transparent',
            belowmincolor: 'transparent',
            transparent: true,
            styles: 'boxfill/ferret',
        })

    second_layer.addTo(map);
    first_layer.addTo(map);
});

function whenClicked(e) {
    var name = e.target.feature.properties.NAME;
    pa_selected_name = name;
    if (name !== undefined) {
        let req_to_update = ajax_call("get-updated-series", {'pa_name': pa_selected_name});
        req_to_update.done(function (result) {
            document
                .getElementById("region_country").innerHTML = result.region_country;
            var updated_emissions_chart = JSON.parse(result.chart_epa);
            var updated_forestchange_chart = JSON.parse(result.chart_fcpa);
            getMMA(pa_selected_name, updated_emissions_chart);
            getFC(pa_selected_name, updated_forestchange_chart);
        });


        window.location.hash = "";
        window.location.hash = "Emissions_PA";
    }
}

function onEachFeature(feature, layer) {
    //bind click
    layer.on({
        click: whenClicked
    });

    layer.on('mouseover', function (e) {
        var name = e.target.feature.properties.NAME;
        var popupText = name
        var tooltipText = "blabla";
        layer.bindPopup(popupText, {
            closeButton: false
        });
        layer.bindTooltip(tooltipText);
        layer.openPopup();
        this.getTooltip().setOpacity(0);
        layer.setStyle({
            weight: 2,
            opacity: 1,
            color: 'yellow',  //Outline color
            fillOpacity: 0.4,
        })

        layer.on('mouseover', function () {
            this.getTooltip().setOpacity(this.isPopupOpen() ? 0 : .9);
        });
    });
    layer.on('mouseout', function (e) {
        layer.closePopup();
        layer.setStyle({
            weight: 2,
            opacity: 1,
            color: 'cyan',  //Outline color
            fillOpacity: 0.4,
        })
    });
}

let req = ajax_call("get-aoi", {});
req.done(function (result) {

    var aoi_layer = L.geoJSON(result['data'], {
        style: {
            weight: 2,
            opacity: 1,
            color: 'cyan',  //Outline color
            fillOpacity: 0.4,

        },
        onEachFeature: onEachFeature,
    });
    aoi_layer.on('add', (e) => {
// document.getElementById("loading_spinner").style.display="none";
    });


    aoi_layer.addTo(map);


});
$("#datasource_select") .trigger('change');