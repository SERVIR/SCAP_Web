let map;
let primary_overlay_layer;
let secondary_overlay_layer;
let primary_underlay_layer;
let secondary_underlay_layer;
let comparison_control;
let aoi_layer_left;
let aoi_layer_right;

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
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year);
    }
}


function clear_map_layers(){
    if(primary_overlay_layer != undefined){
        map.removeLayer(primary_overlay_layer);
    }
    if(secondary_overlay_layer != undefined){
        map.removeLayer(secondary_overlay_layer);
    }

    if(primary_overlay_layer != undefined){
        map.removeLayer(primary_underlay_layer);
    }
    if(secondary_overlay_layer != undefined){
        map.removeLayer(secondary_underlay_layer);
    }
    if(aoi_layer_left != undefined){
        map.removeLayer(aoi_layer_left)
    }
    if(aoi_layer_right != undefined){
        map.removeLayer(aoi_layer_right)
    }
    if(comparison_control != undefined){
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

function redraw_map_layers(){
    clear_map_layers();

    let selected_year = document.getElementById('selected_year').value
    let comparison_year = document.getElementById('comparison_year').value
    let selected_dataset = document.getElementById('selected_region').value

    let xhr = ajax_call("get-aoi", {});
    xhr.done(function (result) {
        aoi_layer_left = L.geoJSON(result['data'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            pane: 'left'
        })
        aoi_layer_right = L.geoJSON(result['data'], {
            style: {
                weight: 2,
                opacity: 1,
                color: 'cyan',  //Outline color
                fillOpacity: 0.4,
            },
            pane: 'right'
        })

        primary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset}/${selected_dataset}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
            {
                layers: ["forest_cover"],
                format: "image/png",
                colorscalerange: "0.5,1",
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/crimsonbluegreen',
                pane: 'left'
            })

        primary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset}/${selected_dataset}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
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

        secondary_overlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset}/${selected_dataset}.${comparison_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
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
        secondary_underlay_layer = L.tileLayer.wms(`https://thredds.servirglobal.net/thredds/wms/scap/fc/${selected_dataset}/${selected_dataset}.${selected_year}0101T000000Z.global.1ha.yearly.nc4?service=WMS`,
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
        primary_underlay_layer.addTo(map)
        primary_overlay_layer.addTo(map)
        secondary_underlay_layer.addTo(map)
        secondary_overlay_layer.addTo(map)
        aoi_layer_left.addTo(map)
        aoi_layer_right.addTo(map)

        comparison_control = L.control.sideBySide([aoi_layer_left, primary_overlay_layer, primary_underlay_layer], [aoi_layer_right, secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()')
        document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()')
    });
}

function get_available_years(){
    //let xhr = ajax_call("get-available-years", {});
    //xhr.done(function (result) {
    let years = Object.values([2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020, 2021,2022]);
    //console.log(result['data']);
    fill_years_selector(years);
    fill_comparison_years_selector(years);
    document.getElementById('selected_year').value=2017;
    document.getElementById('comparison_year').value=2020;
    redraw_map_layers();
    //})
}

function init_map(){
    // Initialize with map control with basemap and time slider
    map = L.map('map_chart', {
        fullscreenControl: true, center: [-8.60436, -74.73243], zoom: 10
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

    get_available_years();
}


function removeLayers(){
    satellite.remove();
    gSatLayer.remove();
    darkGrayLayer.remove();
    osm.remove();
    OpenTopoMap.remove();
    terrainLayer.remove();
    deLormeLayer.remove();
    gSatLayer.remove();
}


function add_basemap(map_name){
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
});