let map;
let primary_overlay_layer;
let secondary_overlay_layer;
let primary_underlay_layer;
let secondary_underlay_layer;
let comparison_control;
let aoi_layer_left;
let aoi_layer_right;
let pilot_center=[-8.60436, -74.73243];

function add_option_by_id(selector, value, label) {
    let opt = document.createElement('option');
    opt.value = value;
    opt.innerHTML = label;
    selector.appendChild(opt);
}


function fill_years_selector(years) {
    let select = document.getElementById('selected_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year);
    }
}


function fill_comparison_years_selector(years) {
    let select = document.getElementById('comparison_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year);
    }
}


function clear_map_layers() {
    if (primary_overlay_layer != undefined) {
        map.removeLayer(primary_overlay_layer);
    }
    if (secondary_overlay_layer != undefined) {
        map.removeLayer(secondary_overlay_layer);
    }

    if (primary_overlay_layer != undefined) {
        map.removeLayer(primary_underlay_layer);
    }
    if (secondary_overlay_layer != undefined) {
        map.removeLayer(secondary_underlay_layer);
    }
    if (aoi_layer_left != undefined) {
        map.removeLayer(aoi_layer_left)
    }
    if (aoi_layer_right != undefined) {
        map.removeLayer(aoi_layer_right)
    }
    if (comparison_control != undefined) {
        document.getElementsByClassName('leaflet-sbs-range')[0].value = 1;
        let clipX = comparison_control._range.value;
        map.removeControl(comparison_control);
        comparison_control = undefined;
        let nw = map.containerPointToLayerPoint([0, 0]);
        let se = map.containerPointToLayerPoint(map.getSize());
        let clipLeft = 'rect(' + [nw.y, clipX, se.y, nw.x].join('px,') + 'px)';
        map.getPane('left').setAttribute('style', clipLeft);
    }
}

function whenClicked(e) {
    var layer = e.target;
    layer.setStyle({
        weight: 2,
        opacity: 1,
        color: 'cyan',  //Outline color
        fillOpacity: 0.4,
    });

    var name = e.target.feature.properties.NAME;
    $.ajax({
        type: 'POST',
        url: 'get-aoi-id/',
        data: {'aoi': name,'iso3':e.target.feature.properties.ISO3,'desig_eng':e.target.feature.properties.DESIG_ENG},
        success: function (data) {

            pa_selected_name = data.id;
            var zoomlevel = map.getZoom();


            if (zoomlevel >= 7) {
                window.location = window.location.origin + '/aoi/' + pa_selected_name + '/';
            } else {
                window.location = window.location.origin + '/aoi/1/';
            }
        }
    });
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
function  redraw_based_on_year(){
        document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();
    let selected_dataset_left = document.getElementById('selected_region').value;
     let selected_dataset_right = document.getElementById('comparing_region').value;

    let xhr = ajax_call("get-aoi/", {});
    xhr.done(function (result) {

        aoi_layer_left = L.geoJSON(result['data_pa'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            onEachFeature: onEachFeature,
            pane: 'left'
        });
        console.log("aftye lkl")
        aoi_layer_right = L.geoJSON(result['data_pa'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            onEachFeature: onEachFeature,
            pane: 'right'
        });

        aoi_layer_left.on('add', (e) => {
            document.getElementById("loading_spinner_map").style.display = "none";
        });
        aoi_layer_right.on('add', (e) => {
            document.getElementById("loading_spinner_map").style.display = "none";
        });
        let selected_year = document.getElementById('selected_year').value;
        let comparison_year = document.getElementById('comparison_year').value;
        let selected_dataset_left = document.getElementById('selected_region').value;
        let selected_dataset_right = document.getElementById('comparing_region').value;
        primary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_left}/${selected_dataset_left}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/crimsonbluegreen',
                pane: 'left'
            });

        primary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_right}/${selected_dataset_right}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/cwg',
                pane: 'left'
            })

        secondary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_right}/${selected_dataset_right}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/cwg',
                transparent: true,
                pane: 'right'
            })
        secondary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_left}/${selected_dataset_left}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/redblue',
                transparent: true,
                pane: 'right'
            });
        primary_underlay_layer.addTo(map);
        primary_overlay_layer.addTo(map);
        secondary_underlay_layer.addTo(map);
        secondary_overlay_layer.addTo(map);
        aoi_layer_left.addTo(map);
        aoi_layer_right.addTo(map);
        comparison_control = L.control.sideBySide([aoi_layer_left, primary_overlay_layer, primary_underlay_layer], [aoi_layer_right, secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()')
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()')
        map.on("zoomend", function () {
            var zoomlevel = map.getZoom();

            if (zoomlevel < 7) {
                if (map.hasLayer(aoi_layer_left)) {
                    map.removeLayer(aoi_layer_left);
                }
                if (map.hasLayer(aoi_layer_right)) {
                    map.removeLayer(aoi_layer_right);
                }
            } else {
                map.addLayer(aoi_layer_left);
                map.addLayer(aoi_layer_right);
            }
            console.log("Current Zoom Level = " + zoomlevel);
        });
        //  try {
        //      // pilot_center=[result.latitude, result.longitude];
        //     // map.panTo(new L.LatLng(result.latitude, result.longitude));
        //     // map.setZoom(result.zoom);
        // }
        // catch(except){
        //     console.log("err");
        // }
console.log("after err");
    });
}

function redraw_map_layers() {
    document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();
 let years = get_years(document.getElementById('selected_region').value);
    fill_years_selector(get_years_range(years[0], years[1]));
    let c_years = get_years(document.getElementById('comparing_region').value);
    fill_comparison_years_selector(get_years_range(c_years[0], c_years[1]));
    // document.getElementById('selected_year').value = years[0];
    // document.getElementById('comparison_year').value = c_years[0];
    let selected_dataset_left = document.getElementById('selected_region').value;
     let selected_dataset_right = document.getElementById('comparing_region').value;

    let xhr = ajax_call("get-aoi/", {});
    xhr.done(function (result) {
        // try {
        //     map.panTo(new L.LatLng(result.latitude, result.longitude));
        //     map.setZoom(result.zoom);
        // }
        // catch(except){
        //     console.log("err")
        // }

        aoi_layer_left = L.geoJSON(result['data_pa'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            onEachFeature: onEachFeature,
            pane: 'left'
        })
        aoi_layer_right = L.geoJSON(result['data_pa'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            onEachFeature: onEachFeature,
            pane: 'right'
        });

        aoi_layer_left.on('add', (e) => {
            document.getElementById("loading_spinner_map").style.display = "none";
        });
        aoi_layer_right.on('add', (e) => {
            document.getElementById("loading_spinner_map").style.display = "none";
        });
        let selected_year = document.getElementById('selected_year').value;
        let comparison_year = document.getElementById('comparison_year').value;
        let selected_dataset_left = document.getElementById('selected_region').value;
        let selected_dataset_right = document.getElementById('comparing_region').value;
        primary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_left}/${selected_dataset_left}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/crimsonbluegreen',
                pane: 'left'
            });

        primary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_right}/${selected_dataset_right}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/cwg',
                pane: 'left'
            })

        secondary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_right}/${selected_dataset_right}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/cwg',
                transparent: true,
                pane: 'right'
            })
        secondary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset_left}/${selected_dataset_left}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/redblue',
                transparent: true,
                pane: 'right'
            })
        primary_underlay_layer.addTo(map);
        primary_overlay_layer.addTo(map);
        secondary_underlay_layer.addTo(map);
        secondary_overlay_layer.addTo(map);
        aoi_layer_left.addTo(map);
        aoi_layer_right.addTo(map);
        comparison_control = L.control.sideBySide([aoi_layer_left, primary_overlay_layer, primary_underlay_layer], [aoi_layer_right, secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()')
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()')
        map.on("zoomend", function () {
            var zoomlevel = map.getZoom();

            if (zoomlevel < 7) {
                if (map.hasLayer(aoi_layer_left)) {
                    map.removeLayer(aoi_layer_left);
                }
                if (map.hasLayer(aoi_layer_right)) {
                    map.removeLayer(aoi_layer_right);
                }
            } else {
                map.addLayer(aoi_layer_left);
                map.addLayer(aoi_layer_right);
            }
            console.log("Current Zoom Level = " + zoomlevel);
        });
    });

}

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

function get_years_range(start, end) {
    var list = [];
    for (var i = start; i <= end; i++) {
        list.push(i);
    }
    return list
}

function get_available_years() {
    //let xhr = ajax_call("get-available-years", {});
    //xhr.done(function (result) {
    // let years = Object.values([2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020, 2021,2022]);
    let years = get_years(document.getElementById('selected_region').value);
    console.log(document.getElementById('selected_region').value);
    //console.log(result['data']);
    fill_years_selector(get_years_range(years[0], years[1]));
    let c_years = get_years(document.getElementById('comparing_region').value);
    fill_comparison_years_selector(get_years_range(c_years[0], c_years[1]));
    document.getElementById('selected_year').value = years[0];
    document.getElementById('comparison_year').value = c_years[1];
    redraw_map_layers();
    //})
}

function init_map() {
    // Initialize with map control with basemap and time slider
    if(document.getElementById("lat_from_db")){
        pilot_center = [parseFloat(document.getElementById("lat_from_db").innerHTML), parseFloat(document.getElementById("lon_from_db").innerHTML)];
    }
    var zoom=10;
   if(document.getElementById("zoom_from_db")){
       zoom = parseFloat(document.getElementById("zoom_from_db").innerHTML);
   }
    map = L.map('map_chart', {
        fullscreenControl: true, center: pilot_center, zoom: zoom
    });

    map.createPane('left');
    map.createPane('right');

    map.zoomControl.setPosition('topleft');
    satellite.addTo(map);

    // Add the Search Control to the map
    map.addControl(new GeoSearch.GeoSearchControl({
        provider: new GeoSearch.OpenStreetMapProvider(),
        showMarker: false, // optional: true|false  - default true
        showPopup: false,
        autoClose: true
    }));

    var wmsLayer = L.tileLayer.wms('https://thredds.servirglobal.net/geoserver/ows?', {
        layers: 's-cap:watermask_2',
        format: 'image/png',
        transparent: true
    }).addTo(map);


    get_available_years();
}


function removeLayers() {
    satellite.remove();
    gSatLayer.remove();
    darkGrayLayer.remove();
    osm.remove();
    OpenTopoMap.remove();
    terrainLayer.remove();
    deLormeLayer.remove();
    gSatLayer.remove();
}


function add_basemap(map_name) {
    removeLayers();
    switch (map_name) {
        case "osm":
            osm.addTo(map);
            break;
        case "delorme":
            deLormeLayer.addTo(map);
            break;
        case "satellite":
            satellite.addTo(map);
            break;
        case "terrain":
            terrainLayer.addTo(map);
            break;
        case "topo":
            OpenTopoMap.addTo(map);
            break;
        case "gsatellite":
            gSatLayer.addTo(map);
            break;
        case "darkgray":
            darkGrayLayer.addTo(map);
            break;
        default:
            osm.addTo(map);
    }
}


$(function () {
    init_map();
 // let years = get_years(document.getElementById('selected_region').value);
 //    fill_years_selector(get_years_range(years[0], years[1]));
 //    let c_years = get_years(document.getElementById('comparing_region').value);
 //    fill_comparison_years_selector(get_years_range(c_years[0], c_years[1]));
});