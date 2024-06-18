let map;
let primary_overlay_layer;
let secondary_overlay_layer;
let primary_underlay_layer;
let secondary_underlay_layer;
let comparison_control;
let aoi_layer_left;
let aoi_layer_right;let aoi_layer;
let country_layer;
let drawn_aoi;

let pilot_center=[-8.60436, -74.73243];
let map_modal_action="deforestation_targets";
function add_option_by_id(selector, value, label,defalt) {
    let opt = document.createElement('option');
    opt.value = value;
    if (value==defalt)
    {
        opt.selected=true;
    }
    opt.innerHTML = label;
    selector.appendChild(opt);
}
function getAllSiblings(elem, filter) {
    var sibs = [];
    elem = elem.parentNode.firstChild;
    do {
        if (elem.nodeType === 3) continue; // text node
        if (!filter || filter(elem)) sibs.push(elem);
    } while (elem = elem.nextSibling)
    return sibs;
}
function exampleFilter(elem) {
    switch (elem.nodeName.toUpperCase()) {
        case 'DIV':
            return true;
        default:
            return false;
    }
}
function set_map_action(anchor,text) {
    var div = anchor.parentNode;
    siblings = getAllSiblings(div, exampleFilter);
    for (var i = 0; i < siblings.length; i++) {

        siblings[i].classList.remove(('map-modal-action'));
    }
    div.classList.add('map-modal-action');
    localStorage.setItem('map_modal_action', text);
    map_modal_action=text;
}

function fill_dataset_selector(fc_data,agb_data) {
    let select = document.getElementById('selected_region');
    select.innerHTML = "";
    for (let i = 0; i < fc_data.length; i++) {
        let ds = fc_data[i];
        add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, 'nlcms');
    }
    if (agb_data != null) {
        select = document.getElementById('selected_agb');
        select.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, 'spawn-2010');
        }
    }
}

function fill_comparison_dataset_selector(fc_data,agb_data){
  let select = document.getElementById('comparing_region');
    select.innerHTML = "";
    for (let i = 0; i < fc_data.length; i++) {
        let ds = fc_data[i];
        add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds,'nlcms');
    }
    if(agb_data!=null) {
        select = document.getElementById('comparing_agb');
        select.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, 'spawn-2010');
        }
    }
}
function fill_years_selector(years) {
    let select = document.getElementById('selected_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year,years[0]);
    }
}


function fill_comparison_years_selector(years) {
    let select = document.getElementById('comparison_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year,years[years.length-1]);
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
    // if (aoi_layer_left != undefined) {
    //     map.removeLayer(aoi_layer_left)
    // }
    // if (aoi_layer_right != undefined) {
    //     map.removeLayer(aoi_layer_right)
    // }
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

    var name = e.target.feature.geometry.properties.name;
    $.ajax({
        type: 'POST',
        url: 'get-aoi-id/',
        data: {'aoi': name,'iso3':e.target.feature.geometry.properties.ISO3,'desig_eng':e.target.feature.geometry.properties.desig_eng},
        success: function (data) {

            pa_selected_name = data.id;
            var zoomlevel = map.getZoom();
            if(data.country_or_aoi==="country"){
                             window.location = window.location.origin + '/pilot/' + pa_selected_name + '/';

            }
            else{
                window.location = window.location.origin + '/aoi/' + pa_selected_name + '/';

            }

            // if (zoomlevel >= 7) {
            //     window.location = window.location.origin + '/aoi/' + pa_selected_name + '/';
            // } else {
            //     window.location = window.location.origin + '/aoi/1/';
            // }
        }
    });
}

function onEachFeature_aoi(feature, layer) {

    //bind click
    layer.on({
        click: whenClicked
    });

    layer.on('mouseover', function (e) {


        var name = e.target.feature.geometry.properties.name;


        var popupText = name;
        var tooltipText = "";
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
            fillOpacity: 0.5,
        });

    });

}
function onEachFeature_country(feature, layer) {

    //bind click
    layer.on({
        click: whenClicked
    });

    layer.on('mouseover', function (e) {


        var name = e.target.feature.geometry.properties.name;


        var popupText = name;
        var tooltipText = "";
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
            color: '#F9BD7C',  //Outline color
            fillOpacity: 0.5,
        });

    });

}
function  redraw_based_on_year() {
    document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();
    var thredds_dir="fc";
   map_modal_action=localStorage.getItem('map_modal_action');

    if (map_modal_action=='deforestation_targets' || map_modal_action=='deforestation_netzero') {
        thredds_dir="fc";
        scale_range = "0.5,1"

    }
    //carbon stock or emissions
    else if (map_modal_action=='carbon-stock' || map_modal_action=='emissions') {
        thredds_dir = map_modal_action;
        scale_range = "0,50000"


    }

    // aoi_layer_left = L.geoJSON(shp_obj['data_pa'], {
    //     style: {
    //         weight: 2,
    //         opacity: 1,
    //         color: 'cyan',  //Outline color
    //         fillOpacity: 0.4,
    //     },
    //     onEachFeature: onEachFeature,
    //     pane: 'left'
    // });
    // aoi_layer_right = L.geoJSON(shp_obj['data_pa'], {
    //     style: {
    //         weight: 2,
    //         opacity: 1,
    //         color: 'cyan',  //Outline color
    //         fillOpacity: 0.4,
    //     },
    //     onEachFeature: onEachFeature,
    //     pane: 'right'
    // });
    var hide_spinner_aoi=false;
    var hide_spinner_l1, hide_spinner_l1, hide_spinner_l1 =false;

    // aoi_layer_left.on('add', (e) => {
    //     // document.getElementById("loading_spinner_map").style.display = "none";
    //     hide_spinner_aoi=true;
    // });
    // aoi_layer_right.on('add', (e) => {
    //     // document.getElementById("loading_spinner_map").style.display = "none";
    //     hide_spinner_aoi=true;
    // });
    let selected_year = document.getElementById('selected_year').value;
    let comparison_year = document.getElementById('comparison_year').value;
    let selected_dataset_left = document.getElementById('selected_region').value;
    let selected_dataset_right = document.getElementById('comparing_region').value;
    let selected_dataset_left_agb ="";
    let selected_dataset_right_agb="";
    if(agb_colls!=undefined) {
         selected_dataset_left_agb = document.getElementById('selected_agb').value;
         selected_dataset_right_agb = document.getElementById('comparing_agb').value;
    }
      var base_thredds="https://thredds.servirglobal.net/thredds/wms/scap/public/"+thredds_dir+"/1";
        var layer_name=(thredds_dir=="fc")?
            "forest_cover":thredds_dir;

        primary_overlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`

        primary_overlay_layer = L.tileLayer.wms(primary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/crimsonbluegreen',
                pane: 'left'
            });
        primary_underlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`

        primary_underlay_layer = L.tileLayer.wms(primary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/cwg',
                pane: 'left'
            })
        secondary_overlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`

        secondary_overlay_layer = L.tileLayer.wms(secondary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/cwg',
                transparent: true,
                pane: 'right'
            })
        var style = 'boxfill/maize';
        if (selected_dataset_left === selected_dataset_right) {
            style = 'boxfill/redblue';
        }
             var  secondary_underlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`

        secondary_underlay_layer = L.tileLayer.wms(secondary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: style,
                transparent: true,
                pane: 'right'
            })
        // primary_underlay_layer.addTo(map);
        primary_overlay_layer.addTo(map);
        secondary_underlay_layer.addTo(map);
        secondary_overlay_layer.addTo(map);
    // aoi_layer_left.addTo(map);
    // aoi_layer_right.addTo(map);
          document.getElementById("loading_spinner_map").style.display = "none";

    comparison_control = L.control.sideBySide([ primary_overlay_layer], [ secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()')
    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()')
    map.on("zoomend", function () {
        var zoomlevel = map.getZoom();

        // if (zoomlevel < 7) {
        //     if (map.hasLayer(aoi_layer_left)) {
        //         map.removeLayer(aoi_layer_left);
        //     }
        //     if (map.hasLayer(aoi_layer_right)) {
        //         map.removeLayer(aoi_layer_right);
        //     }
        // } else {
        //     map.addLayer(aoi_layer_left);
        //     map.addLayer(aoi_layer_right);
        // }
        console.log("Current Zoom Level = " + zoomlevel);
    });
}

function add_aoi_polygons(shp_obj){
    // aoi_layer_left = L.geoJSON(shp_obj['data_pa'], {
    //     style: {
    //         weight: 2,
    //         opacity: 1,
    //         color: 'cyan',  //Outline color
    //         fillOpacity: 0.4,
    //     },
    //      onEachFeature: onEachFeature,
    //     pane: 'left'
    // });
    // aoi_layer_right = L.geoJSON(shp_obj['data_pa'], {
    //     style: {
    //         weight: 2,
    //         opacity: 1,
    //         color: 'cyan',  //Outline color
    //         fillOpacity: 0.4,
    //     },
    //     onEachFeature: onEachFeature,
    //     pane: 'right'
    // });
    // aoi_layer_left.addTo(map);
    // aoi_layer_right.addTo(map);
}

function add_thredds_wms_layers() {
    var thredds_dir = "fc";
    var layer_name = "forest_cover";
    var base_thredds = "";
    var primary_overlay_url = "";
    var primary_underlay_url = "";
    var secondary_overlay_url = "";
    var secondary_underlay_url = "";
    // years and datasets from dropdowns
    let selected_year = document.getElementById('selected_year').value;
    let comparison_year = document.getElementById('comparison_year').value;
    let selected_dataset_left = document.getElementById('selected_region').value;
    let selected_dataset_right = document.getElementById('comparing_region').value;
    let selected_dataset_left_agb ="";
    let selected_dataset_right_agb="";
    if(agb_colls!=undefined) {
         selected_dataset_left_agb = document.getElementById('selected_agb').value;
         selected_dataset_right_agb = document.getElementById('comparing_agb').value;
    }
    if (map_modal_action == 'deforestation_targets' || map_modal_action == 'deforestation_netzero') {
        thredds_dir = "fc";
        layer_name = "forest_cover";
        base_thredds = "https://thredds.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";

        primary_overlay_url = `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`;
        primary_underlay_url = `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`;
        secondary_overlay_url = `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`;
        secondary_underlay_url = `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`;
        scale_range = "0.5,1";
                 if ( document.getElementById('selected_agb')!=null)
    document.getElementById('selected_agb').style.display='none';
    if ( document.getElementById('comparing_agb')!=null)
     document.getElementById('comparing_agb').style.display='none';
     if ( document.getElementById('comparing_agb_label')!=null)
             document.getElementById('comparing_agb_label').style.display='none';
         if ( document.getElementById('selected_agb_label')!=null)
             document.getElementById('selected_agb_label').style.display='none';
    }
    //carbon stock or emissions
    else if (map_modal_action == 'carbon-stock' || map_modal_action == 'emissions') {
        thredds_dir = map_modal_action;
        layer_name = thredds_dir;
        base_thredds = "https://thredds.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";

        primary_overlay_url = `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`;
        primary_underlay_url = `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`;
        secondary_overlay_url = `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`;

        secondary_underlay_url = `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`;
        scale_range = "0,50000"

    }
    try {

        primary_overlay_layer = L.tileLayer.wms(primary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/crimsonbluegreen',
                pane: 'left'
            });
        primary_underlay_layer = L.tileLayer.wms(primary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: 'boxfill/cwg',
                pane: 'left'
            })
        secondary_overlay_layer = L.tileLayer.wms(secondary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: 'boxfill/cwg',
                transparent: true,
                pane: 'right'
            })
        var style = 'boxfill/maize';
        if (selected_dataset_left === selected_dataset_right) {
            style = 'boxfill/redblue';
        }

        secondary_underlay_layer = L.tileLayer.wms(secondary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: style,
                transparent: true,
                pane: 'right'
            })
        // primary_underlay_layer.addTo(map);
        primary_overlay_layer.addTo(map);
        secondary_underlay_layer.addTo(map);
        secondary_overlay_layer.addTo(map);
        comparison_control = L.control.sideBySide([ primary_overlay_layer], [ secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
    } catch (e) {
        console.log(e)
    }
}
    // aoi_layer_left.on('add', (e) => {
    //     document.getElementById("loading_spinner_map").style.display = "none";
    // });
    //
    // aoi_layer_right.on('add', (e) => {
    //     document.getElementById("loading_spinner_map").style.display = "none";
    // });
function redraw_map_layers(map_modal_action) {
    document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();

if (map_modal_action=='deforestation_targets' || map_modal_action=='deforestation_netzero') {
        if ( document.getElementById('selected_agb')!=null)
    document.getElementById('selected_agb').style.display='none';
    if ( document.getElementById('comparing_agb')!=null)
     document.getElementById('comparing_agb').style.display='none';
     if ( document.getElementById('comparing_agb_label')!=null)
             document.getElementById('comparing_agb_label').style.display='none';
         if ( document.getElementById('selected_agb_label')!=null)
             document.getElementById('selected_agb_label').style.display='none';
    let years = get_years_for_name_no_agb(fc_colls, document.getElementById('selected_region').value);
    fill_years_selector(years);
    let c_years = get_years_for_name_no_agb(fc_colls, document.getElementById('comparing_region').value);
    fill_comparison_years_selector(c_years);
     document.getElementById('selected_year').value = years[0];
    document.getElementById('comparison_year').value = c_years[c_years.length - 1];


}
else{
    let years = get_years_for_name(fc_colls, document.getElementById('selected_region').value);

    fill_years_selector(years);
    let c_years = get_years_for_name(fc_colls, document.getElementById('comparing_region').value);
    fill_comparison_years_selector(c_years);
     document.getElementById('selected_year').value = years[0];
    document.getElementById('comparison_year').value = c_years[c_years.length - 1];
             if ( document.getElementById('selected_agb')!=null)

        document.getElementById('selected_agb').style.display='block';
                 if ( document.getElementById('comparing_agb')!=null)

             document.getElementById('comparing_agb').style.display='block';
                      if ( document.getElementById('comparing_agb_label')!=null)

                          document.getElementById('comparing_agb_label').style.display='block';
                               if ( document.getElementById('selected_agb_label')!=null)

             document.getElementById('selected_agb_label').style.display='block';



}


    add_aoi_polygons(shp_obj);
    add_thredds_wms_layers();
    // document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()');
    // document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()');
    // display protected areas based on zoom level
    map.on("zoomend", function () {
        var zoomlevel = map.getZoom();
        // if (zoomlevel < 5) {
        //     if (map.hasLayer(aoi_layer_left)) {
        //         map.removeLayer(aoi_layer_left);
        //     }
        //     if (map.hasLayer(aoi_layer_right)) {
        //         map.removeLayer(aoi_layer_right);
        //     }
        // } else {
        //     map.addLayer(aoi_layer_left);
        //     map.addLayer(aoi_layer_right);
        // }
        console.log("Current Zoom Level = " + zoomlevel);
    });
    document.getElementById("loading_spinner_map").style.display = "none";
}
function get_names_from_obj(obj){
        if(obj===undefined)
        return null;
    let names=[];
    for(var i=0;i<obj.length;i++){
        names.push(obj[i].name);
    }
    return names;
}
function get_years_for_name_no_agb(obj,name){
     let years = [];
        for (var i = 0; i < obj.length; i++) {
            if (name.toLowerCase() === obj[i].name.split(' ').join('-').toLowerCase())
                return obj[i].years.sort();
        }
}
function get_years_for_name(obj,name) {
    let years = [];
    var temp=[]
    if (document.getElementById('selected_agb')!=null&&document.getElementById('selected_agb').style.display != 'none') {
        years=[]
        for (var i = 0; i < obj.length; i++) {
            if (name.toLowerCase() === obj[i].name.split(' ').join('-').toLowerCase()) {
                temp = obj[i].years;
                break;
            }
        }
        for (var i = 0; i < agb_colls.length; i++) {
            name=document.getElementById('selected_agb').value;
            if (name.toLowerCase() === agb_colls[i].name.split(' ').join('-').toLowerCase()) {
                agb_year=agb_colls[i].years[0];
                break;
            }
        }
        for (var x = 0; x < temp.length; x++) {
            if (temp[x] < agb_year) {
                continue;
            } else {
                years.push(temp[x]);
            }
        }
    } else {
        years = [];
        for (var i = 0; i < obj.length; i++) {
            if (name.toLowerCase() === obj[i].name.split(' ').join('-').toLowerCase())
                return obj[i].years.sort();
        }
    }

    return years.sort();
}
//first populate data in dropdowns
function get_available_years(map_modal_action) {
    //land cover

    console.log(map_modal_action);
    if (map_modal_action=='deforestation_targets' || map_modal_action=='deforestation_netzero') {
            fill_dataset_selector(get_names_from_obj(fc_colls), get_names_from_obj(agb_colls));
            let years = get_years_for_name_no_agb(fc_colls, document.getElementById('selected_region').value);
            fill_years_selector(years);
            fill_comparison_dataset_selector(get_names_from_obj(fc_colls), get_names_from_obj(agb_colls));
            let c_years = get_years_for_name_no_agb(fc_colls, document.getElementById('comparing_region').value);
            fill_comparison_years_selector(c_years);


        document.getElementById('selected_year').value = years[0];
        document.getElementById('comparison_year').value = c_years[c_years.length - 1];
    }
    //carbon stock or emissions
    else if (map_modal_action=='carbon-stock' || map_modal_action=='emissions'){
        fill_dataset_selector(get_names_from_obj(fc_colls),get_names_from_obj(agb_colls));
        let years = get_years_for_name(fc_colls, document.getElementById('selected_region').value);
        fill_years_selector(years);

        fill_comparison_dataset_selector(get_names_from_obj(fc_colls),get_names_from_obj(agb_colls));
        let c_years = get_years_for_name(fc_colls, document.getElementById('comparing_region').value);
        fill_comparison_years_selector(c_years);

        document.getElementById('selected_year').value = years[0];
        document.getElementById('comparison_year').value = c_years[c_years.length - 1];
    }


     redraw_map_layers(map_modal_action);
}
function get_checked_lcs() {
    var lcs = [];
    $('.LC_checkboxlist input[type="checkbox"]:checked').each(function () {

        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        // console.log(temp.replace('L', '').replace('C', ''));
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
function send_to_backend(){
    var lcss = get_checked_lcs();
    var agbss = get_checked_agbs();
    if(lcss.length>0 && agbss.length>0) {
        $.ajax({
            type: 'POST',
            url: 'upload-drawn-aoi/',
            data: {'lcs': lcss, 'agbs': agbss, 'geometry': JSON.stringify(drawn_aoi)},
            success: function (data) {
                window.location = window.location.origin + '/aoi/' + data.aoi_id + '/';
            }
        });
    }
    else{
        alert("Please select atleast one Land Cover and one Above Ground Biomass dataset");
    }
}

function init_map() {
    // list of basemaps
    var baseMaps = {
        "Gray": darkGrayLayer,
        "OpenTopo": OpenTopoMap,
        "Streets": streets,
        "Satellite": satellite,
        "Keep Default": darkmap
    };


            var overlays ;
            console.log(country_id)
        if(country_id===0) {
            overlays = {
                'Watermask': watermaskLayer,


            };
        }
        else   if (window.location.href.indexOf("/pilot/") > -1) {
             country_layer = L.geoJSON(shp_obj['data_country'], {
                style: {
                    weight: 2,
                    opacity: 1,
                    color: '#D3D3D3',  //Outline color
                    fillOpacity: 0.2,
                     strokeWidth: 0,
                },
                // onEachFeature: onEachFeature_country,
            });
               aoi_layer = L.geoJSON(shp_obj['data_pa'], {
                style: {
                    weight: 2,
                    opacity: 1,
                    color: 'cyan',  //Outline color
                    fillOpacity: 0.4,
                },
                onEachFeature: onEachFeature_aoi,
            });
                   // list of overlays
            overlays = {
                'Watermask': watermaskLayer,
                'Protected Areas': aoi_layer,
                'Country Outline': country_layer,


            };

        }
        else   if (window.location.href.indexOf("/aoi/") > -1) {
            aoi_layer = L.geoJSON(shp_obj['data_pa'], {
                style: {
                    weight: 2,
                    opacity: 1,
                    color: 'cyan',  //Outline color
                    fillOpacity: 0.4,
                },
                onEachFeature: onEachFeature_aoi,
            });
                  // list of overlays
            overlays = {
                'Watermask': watermaskLayer,
                'Protected Areas': aoi_layer,


            };
        }
        else {
            aoi_layer = L.geoJSON(shp_obj['data_pa'], {
                style: {
                    weight: 2,
                    opacity: 1,
                    color: 'cyan',  //Outline color
                    fillOpacity: 0.4,

                },
                onEachFeature: onEachFeature_aoi,
            });
            country_layer = L.geoJSON(shp_obj['data_country'], {
                style: {
                    weight: 2,
                    opacity: 1,
                    color: '#D3D3D3',  //Outline color
                    fillOpacity: 0.2,
                     strokeWidth: 0,
                },
                // onEachFeature: onEachFeature_country,
            });

            // list of overlays
            overlays = {
                'Watermask': watermaskLayer,
                'Protected Areas': aoi_layer,
                'Country Outline': country_layer,


            };
        }


    //get lat, lon and zoom from PilotCountry db object
    if (document.getElementById("lat_from_db")) {
        pilot_center = [parseFloat(document.getElementById("lat_from_db").innerHTML), parseFloat(document.getElementById("lon_from_db").innerHTML)];
    }
    var zoom = 10;
    if (document.getElementById("zoom_from_db")) {
        zoom = parseFloat(document.getElementById("zoom_from_db").innerHTML);
    }
    // load the leaflet map
    map = L.map('map_chart', {
        fullscreenControl: true, center: pilot_center, zoom: zoom
    });
    //creates panes with labels
    map.createPane('left');
    map.createPane('right');
    map.zoomControl.setPosition('topleft');
    //add the default layers to show
    darkmap.addTo(map);
    // watermaskLayer.addTo(map);
    //add tje
    var layerControl = L.control.layers(baseMaps, overlays, {position: 'bottomleft'}).addTo(map);

    var editableLayers = new L.FeatureGroup();
    map.addLayer(editableLayers);
    var drawPluginOptions = {
        draw: {
            polygon: {
                allowIntersection: false, // Restricts shapes to simple polygons
                drawError: {
                    color: '#660778', // Color the shape will turn when intersects
                    message: '<strong>Oh snap!<strong> you can\'t draw that!' // Message that will show when intersect
                },
                shapeOptions: {
                    color: '#ffc800'
                }
            },
            // disable toolbar item by setting it to false
            polyline: false,
            circle: false, // Turns off this drawing tool
            rectangle: false,
            marker: false,
            circlemarker: false,
        },
        edit: {
            featureGroup: editableLayers, //REQUIRED!!
            remove: true
        }
    };
    var drawControl = new L.Control.Draw(drawPluginOptions);
    // draw polygon control
    map.addControl(drawControl);
   if(country_layer!=undefined && window.location.href.indexOf("/pilot/") > -1){
        country_layer.addTo(map);
    }
     if(country_layer!=undefined && window.location.href.indexOf("/map/") > -1){
        country_layer.addTo(map);
    }
    if (aoi_layer!=undefined && window.location.href.indexOf("/aoi/") > -1) {
        aoi_layer.addTo(map);

    }
    if (aoi_layer!=undefined && window.location.href.indexOf("/map/") > -1) {
        aoi_layer.addTo(map);

    }

    map.on('draw:created', function (e) {
        var type = e.layerType,
            layer = e.layer;
        editableLayers.addLayer(layer);
        var json = editableLayers.toGeoJSON();
        $('#drawing_modal').modal('show');
        drawn_aoi = json;
    });


    // info modal control
    L.easyButton('fa-info', function (btn, map) {
        $('#info_modal').modal('show');
    }, 'Info').addTo(map);


    // Add the Search Control to the map
    map.addControl(new GeoSearch.GeoSearchControl({
        provider: new GeoSearch.OpenStreetMapProvider(),
        showMarker: false, // optional: true|false  - default true
        showPopup: false,
        autoClose: true
    }));
    map_modal_action=localStorage.getItem('map_modal_action');
    if(map_modal_action==null)
    {
        map_modal_action='deforestation_targets';
    }
    get_available_years(map_modal_action);
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

//clicked on modal to select country
function zoomtoArea(id){
    if (id!==0) {
        window.location = window.location.origin + "/map/" + id + "/";
        $('#country_selection_modal').modal('hide');
    }
}

// Starts here
$(function () {
    init_map();
    var id = window.location.pathname.split('/')[2];
    // if action and country are selected, zoom to that country and load the map layers
    if (id <= 0) {
        $('#country_selection_modal').modal('show');
    } else {
        try {
            map.setView([document.getElementById('lat_from_db').innerHTML, document.getElementById("lon_from_db").innerHTML], document.getElementById("zoom_from_db").innerHTML);

        } catch (e) {
            console.log(e)
        }
    }
});