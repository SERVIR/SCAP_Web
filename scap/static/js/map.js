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
let from_map_modal=false;
let aoi_tooltip;
let aoi_nav_dict={};

window.onload = resetMapAction;
// reset map action to Forest Cover
function resetMapAction() {
    if (window.location.href.indexOf("/map/0/") > -1) {
        localStorage.clear();
        localStorage.setItem('map_modal_action', 'deforestation_targets');
    }
    console.log(localStorage.getItem('map_modal_action'));
        map_modal_action = localStorage.getItem('map_modal_action');
 if (window.location.href.indexOf("/map/") > -1) {
     if (map_modal_action == 'carbon-stock') {
         document.getElementById('usecase_name').innerHTML = 'Displaying: Carbon stock';
     } else if (map_modal_action == 'emissions') {
         document.getElementById('usecase_name').innerHTML = 'Displaying: Emission estimations';
     } else if (map_modal_action == 'deforestation_targets') {
         document.getElementById('usecase_name').innerHTML = 'Displaying: Forest cover';
     } else {
         document.getElementById('usecase_name').innerHTML = 'Displaying: Above Ground Biomass (AGB)';
     }
     ;
 }

    if (!$('#country_selection_modal').hasClass('show')) {
        get_available_years(map_modal_action);
    }
}
//method used to add dropdown selector options
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
//method used by set_map_action
function getAllSiblings(elem, filter) {
    var sibs = [];
    elem = elem.parentNode.firstChild;
    do {
        if (elem.nodeType === 3) continue; // text node
        if (!filter || filter(elem)) sibs.push(elem);
    } while (elem = elem.nextSibling)
    return sibs;
}
//method used by set_map_action
function divFilter(elem) {
    switch (elem.nodeName.toUpperCase()) {
        case 'DIV':
            return true;
        default:
            return false;
    }
}
// Method is called when a usecase is selected
function set_map_action(anchor,text,from_modal=false) {
    localStorage.setItem('map_modal_action', text);

    if (from_modal === true) {
        from_map_modal = true;
        console.log(localStorage.getItem('map_modal_action'));
    } else from_map_modal = false;
    if (anchor.className.includes('dropdown')) {
        document.getElementById('usecase_name').innerHTML = 'Displaying: ' + anchor.innerHTML
        if (!$('#country_selection_modal').hasClass('show')) {
            get_available_years(map_modal_action);

            redraw_map_layers();
        }
    } else {
        var div = anchor.parentNode;
        siblings = getAllSiblings(div, divFilter);
        for (var i = 0; i < siblings.length; i++) {
            siblings[i].classList.remove(('map-modal-action'));
        }
        div.classList.add('map-modal-action');
        map_modal_action = localStorage.getItem('map_modal_action');
        if (map_modal_action == 'carbon-stock') {
            document.getElementById('usecase_name').innerHTML = 'Displaying: Carbon stock';
        } else if (map_modal_action == 'emissions') {
            document.getElementById('usecase_name').innerHTML = 'Displaying: Emission estimations';
        } else if (map_modal_action == 'deforestation_targets') {
            document.getElementById('usecase_name').innerHTML = 'Displaying: Forest cover';
        } else {
            document.getElementById('usecase_name').innerHTML = 'Displaying: Above Ground Biomass (AGB)';
        }
        if (!$('#country_selection_modal').hasClass('show')) {
            get_available_years(map_modal_action);
            redraw_map_layers();
        }

    }
}
//AGB
function fill_agb_selector(agb_data) {
     let select = document.getElementById('selected_agb');
     let compare = document.getElementById('comparing_agb');
    if (agb_data != null) {
        select = document.getElementById('selected_agb');
        select.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, def_agb.toLowerCase().split(' ').join('-'));
        }
        compare = document.getElementById('comparing_agb');
        compare.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(compare, ds.split(' ').join('-').toLowerCase(), ds, def_agb.toLowerCase().split(' ').join('-'));
        }
    }
}
//Populate Fc/AGB in selection dropdown
function fill_dataset_selector(fc_data,agb_data) {
    let select = document.getElementById('selected_region');
    select.innerHTML = "";
    for (let i = 0; i < fc_data.length; i++) {
        let ds = fc_data[i];
        add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, def_lc.toLowerCase().split(' ').join('-'));
    }
    if (agb_data != null) {
        select = document.getElementById('selected_agb');
        select.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, def_agb.toLowerCase().split(' ').join('-'));
        }
    }
}
//Populate Fc/AGB in comparison dropdown
function fill_comparison_dataset_selector(fc_data,agb_data){

  let select = document.getElementById('comparing_region');
    select.innerHTML = "";
    for (let i = 0; i < fc_data.length; i++) {
        let ds = fc_data[i];
        add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds,def_lc.toLowerCase().split(' ').join('-'));
    }
    if(agb_data!=null) {
        select = document.getElementById('comparing_agb');
        select.innerHTML = "";
        for (let i = 0; i < agb_data.length; i++) {
            let ds = agb_data[i];
            add_option_by_id(select, ds.split(' ').join('-').toLowerCase(), ds, def_agb.toLowerCase().split(' ').join('-'));
        }
    }
}
// Populate selected year(left) in dropdown
function fill_years_selector(years) {
    let select = document.getElementById('selected_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year,years[0]);
    }
}

// Populate comparison year(right) in dropdown
function fill_comparison_years_selector(years) {
    let select = document.getElementById('comparison_year');
    select.innerHTML = "";
    for (let i = 0; i < years.length; i++) {
        let year = years[i];
        add_option_by_id(select, year, year,years[years.length-1]);
    }
}
// Clear layers added on map
function clear_map_layers() {
    if (primary_overlay_layer != undefined) {
        map.removeLayer(primary_overlay_layer);
    }
    if (secondary_overlay_layer != undefined) {
        map.removeLayer(secondary_overlay_layer);
    }
    if (secondary_overlay_layer != undefined) {
        map.removeLayer(secondary_underlay_layer);
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
// when a protected area is clicked on the map
function whenClicked(e) {
    var layer = e.target;
    layer.setStyle({
        weight: 2,
        opacity: 1,
        color: 'cyan',  //Outline color
        fillOpacity: 0.4,
    });

    var name = e.target.feature.geometry.properties.name; // layer name
    // AJAX call to get the protected area details and redierct to corresponding AOI page
    $.ajax({
        type: 'POST',
        url: 'get-aoi-id/',
        data: {
            'aoi': name,
            'iso3': e.target.feature.geometry.properties.ISO3,
            'desig_eng': e.target.feature.geometry.properties.desig_eng
        },
        success: function (data) {
            pa_selected_name = data.id;
            if (data.country_or_aoi === "country") {
                window.location = window.location.origin + '/pilot/' + pa_selected_name + '/';
            } else {
                window.location = window.location.origin + '/aoi/' + pa_selected_name + '/';
            }
        }
    });
}
// This method is called when protected area layer is added on map
function onEachFeature_aoi(feature, layer) {

    //on layer click
    layer.on({
        click: whenClicked
    });
    //on layer mouseover
    layer.on('mouseover', function (e) {
        var name = e.target.feature.geometry.properties.name; // layer name
        var popupText = name;
        var tooltipText = name;
        layer.bindTooltip(tooltipText);
        this.getTooltip().setOpacity(0.9);
        layer.setStyle({
            weight: 2,
            opacity: 1,
            color: 'yellow',  //Outline color
            fillOpacity: 0.4,
        });
    });
    // on layer mouse out
    layer.on('mouseout', function (e) {
        layer.closePopup();
        layer.setStyle({
            weight: 2,
            opacity: 1,
            color: 'cyan',  //Outline color
            fillOpacity: 0,
        });

    });
}

// Redraw map layers when year dropdowns are changed
function  redraw_based_on_year() {
    console.log(map_modal_action)

    console.log(localStorage.getItem('map_modal_action'))
    document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();
    map_modal_action=localStorage.getItem('map_modal_action');
    var thredds_dir="fc";
    var pri_over_style = '';
    var sec_under_style = '';
    var sec_over_style = '';
    let selected_dataset_left = document.getElementById('selected_region').value;
    let selected_dataset_right = document.getElementById('comparing_region').value;
    let selected_dataset_left_agb ="";
    let selected_dataset_right_agb="";
    if(agb_colls!=undefined) {
         selected_dataset_left_agb = document.getElementById('selected_agb').value;
         selected_dataset_right_agb = document.getElementById('comparing_agb').value;
    }
    var scale_range="0.5,1";
    var fc_scale_range_left = "";
    var fc_scale_range_right="";
    if (map_modal_action=='deforestation_targets') { //ForestCover use case
        thredds_dir = "fc";
        if(selected_dataset_left=='esri')
            fc_scale_range_left="0.5,2";
        else
            fc_scale_range_left="0.5,1";
        if(selected_dataset_right=='esri')
            fc_scale_range_right="0.5,2"
        else fc_scale_range_right="0.5,1"
        if (selected_dataset_left === selected_dataset_right) {
            pri_over_style = 'boxfill/crimsonbluegreen';
            sec_over_style = 'boxfill/cwg';
            sec_under_style = 'boxfill/redblue';
        } else {
            pri_over_style = 'boxfill/crimsonbluegreen';
            sec_over_style = 'boxfill/cwg';
            sec_under_style = 'boxfill/maize';
        }
    }
    else if (map_modal_action=='carbon-stock' || map_modal_action=='emissions') { //Carbon Stock or Emissions usecase
        thredds_dir = map_modal_action;
        scale_range = "0,50000"
        if (map_modal_action == 'carbon-stock') {
            pri_over_style = 'boxfill/crimsonyellowred';
            sec_over_style = 'boxfill/crimsonyellowred';
        } else {
            pri_over_style = 'boxfill/scap-agb';
            sec_over_style = 'boxfill/scap-agb';
        }

    }
    let selected_year = document.getElementById('selected_year').value;
    let comparison_year = document.getElementById('comparison_year').value;
    var base_thredds="https://scapwms.servirglobal.net/thredds/wms/scap/public/"+thredds_dir+"/1";
    var layer_name=(thredds_dir=="fc")?"forest_cover":thredds_dir;
    primary_overlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`

    primary_overlay_layer = L.tileLayer.wms(primary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: (thredds_dir=="fc")?fc_scale_range_left:scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: pri_over_style,
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
                colorscalerange: (thredds_dir=="fc")?fc_scale_range_right:scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: sec_over_style,
                transparent: true,
                pane: 'right'
            });

    var  secondary_underlay_url=(thredds_dir=="fc")?
            `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`
            :
                        `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`

    secondary_underlay_layer = L.tileLayer.wms(secondary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: (thredds_dir=="fc")?fc_scale_range_right:scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: sec_under_style,
                transparent: true,
                pane: 'right'
            })
        // Add layers based on usecase
        if (map_modal_action == 'deforestation_targets') { // Forest Cover usecase
            console.log(primary_overlay_layer)
            primary_overlay_layer.addTo(map);
            secondary_underlay_layer.addTo(map);
            secondary_overlay_layer.addTo(map);
            comparison_control = L.control.sideBySide([primary_overlay_layer], [secondary_overlay_layer, secondary_underlay_layer]).addTo(map);
        } else if (map_modal_action == 'carbon-stock' || map_modal_action == 'emissions') { // Carbon Stock or Emissions usecase
            primary_overlay_layer.addTo(map);
            secondary_overlay_layer.addTo(map);
            comparison_control = L.control.sideBySide([primary_overlay_layer], [secondary_overlay_layer]).addTo(map);
        }
        else{ // AGB usecase
            thredds_dir = map_modal_action;
            layer_name = thredds_dir;
            base_thredds = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";
            scale_range = "1,550";
            primary_overlay_url = `${base_thredds}/${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left_agb}.nc4?service=WMS`;
            secondary_overlay_url = `${base_thredds}/${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right_agb}.nc4?service=WMS`;
             pri_over_style = 'boxfill/scap-agb';
            sec_over_style = 'boxfill/scap-agb';
            comparison_control = L.control.sideBySide([primary_overlay_layer], [secondary_overlay_layer]).addTo(map);

    }
    // display order of layers via panes on map
    map.getPane("left").style.zIndex = "360";
    map.getPane("right").style.zIndex = "360";
    map.getPane("top").style.zIndex = "500";
    map.getPane("topmost").style.zIndex = "600";

    document.getElementById("loading_spinner_map").style.display = "none";

    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()')
    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()')
    // get statitcics fot info modal
    get_stats_for_map();
}

// This method adds the THREDDS WMS layers on the left and right panes of the map based on dropdown selections
function add_thredds_wms_layers(map_modal_action) {


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
    let selected_dataset_left_agb = "";
    let selected_dataset_right_agb = "";
    console.log(agb_colls)
    if (agb_colls != undefined) {
        selected_dataset_left_agb = document.getElementById('selected_agb').value;
        selected_dataset_right_agb = document.getElementById('comparing_agb').value;
    }
    // Defining styles/palettes based on dataset selections
    var pri_over_style = '';
    var sec_under_style = '';
    var sec_over_style = '';
    var scale_range = "0.5,1";
    var fc_scale_range_left = "";
    var fc_scale_range_right = "";
    if (map_modal_action == 'deforestation_targets') { // Forest Cover usecase
        thredds_dir = "fc";
        layer_name = "forest_cover";
        base_thredds = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";
        //Generate the WMS URLs from available data
        primary_overlay_url = `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`;
        primary_underlay_url = `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`;
        secondary_overlay_url = `${base_thredds}/${selected_dataset_right}/${thredds_dir}.1.${selected_dataset_right}.${comparison_year}.nc4?service=WMS`;
        secondary_underlay_url = `${base_thredds}/${selected_dataset_left}/${thredds_dir}.1.${selected_dataset_left}.${selected_year}.nc4?service=WMS`;
        // Range is 0.5,2 for ESRI datasets and 0.5,1 for other datasets
        if (selected_dataset_left == 'esri')
            fc_scale_range_left = "0.5,2";
        else
            fc_scale_range_left = "0.5,1";
        if (selected_dataset_right == 'esri')
            fc_scale_range_right = "0.5,2";
        else fc_scale_range_right = "0.5,1";
        // Defining styles/palettes based on dataset selections
        if (selected_dataset_left === selected_dataset_right) {
            pri_over_style = 'boxfill/crimsonbluegreen';
            sec_over_style = 'boxfill/cwg';
            sec_under_style = 'boxfill/redblue';
        } else {
            pri_over_style = 'boxfill/crimsonbluegreen';
            sec_over_style = 'boxfill/cwg';
            sec_under_style = 'boxfill/maize';
        }

    } else if (map_modal_action == 'carbon-stock' || map_modal_action == 'emissions') {     //Carbon Stock or Emissions usecase
        thredds_dir = map_modal_action;
        layer_name = thredds_dir;
        //Generate the WMS URLs from available data
        base_thredds = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";
          selected_dataset_left_agb = document.getElementById('selected_agb').value;
        selected_dataset_right_agb = document.getElementById('comparing_agb').value;
        primary_overlay_url = `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`;
        primary_underlay_url = `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`;
        secondary_overlay_url = `${base_thredds}/${selected_dataset_right}_${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right}_${selected_dataset_right_agb}.${comparison_year}.nc4?service=WMS`;
        secondary_underlay_url = `${base_thredds}/${selected_dataset_left}_${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left}_${selected_dataset_left_agb}.${selected_year}.nc4?service=WMS`;
        scale_range = "0,50000";
        // Defining styles/palettes based on dataset selections
        if (map_modal_action == 'carbon-stock') {
            pri_over_style = 'boxfill/crimsonyellowred';
            sec_over_style = 'boxfill/crimsonyellowred';
        } else {
            pri_over_style = 'boxfill/scap-agb';
            sec_over_style = 'boxfill/scap-agb';
        }

    } else {// AGB usecase
        thredds_dir = map_modal_action;
        layer_name = thredds_dir;
        scale_range = "1,550";
        //Generate the WMS URLs from available data
        base_thredds = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + thredds_dir + "/1";
        selected_dataset_left_agb = document.getElementById('selected_agb').value;
        selected_dataset_right_agb = document.getElementById('comparing_agb').value;
        console.log(selected_dataset_left_agb);
        console.log(selected_dataset_right_agb);
        primary_overlay_url = `${base_thredds}/${selected_dataset_left_agb}/${thredds_dir}.1.${selected_dataset_left_agb}.nc4?service=WMS`;
        secondary_overlay_url = `${base_thredds}/${selected_dataset_right_agb}/${thredds_dir}.1.${selected_dataset_right_agb}.nc4?service=WMS`;
        // Defining styles/palettes based on dataset selections
        pri_over_style = 'boxfill/scap-agb';
        sec_over_style = 'boxfill/scap-agb';
        console.log(primary_overlay_url);
        console.log(secondary_overlay_url);
        console.log(layer_name)
    }
    // Create Leaflet WMS Urls to add to the panes on the map from the above set variables
    try {
        primary_overlay_layer = L.tileLayer.wms(primary_overlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: (thredds_dir == "fc") ? fc_scale_range_left : scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                transparent: true,
                styles: pri_over_style,
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
                colorscalerange: (thredds_dir == "fc") ? fc_scale_range_right : scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: sec_over_style,
                transparent: true,
                pane: 'right'
            })

        secondary_underlay_layer = L.tileLayer.wms(secondary_underlay_url,
            {
                layers: [layer_name],
                format: "image/png",
                colorscalerange: (thredds_dir == "fc") ? fc_scale_range_right : scale_range,
                abovemaxcolor: 'transparent',
                belowmincolor: 'transparent',
                styles: sec_under_style,
                transparent: true,
                pane: 'right'
            })

        // Add secondary underlay layer only for Forest Cover usecase
        if (map_modal_action == 'deforestation_targets') {
            primary_overlay_layer.addTo(map);
            secondary_underlay_layer.addTo(map);
            secondary_overlay_layer.addTo(map);
            comparison_control = L.control.sideBySide([primary_overlay_layer], [secondary_overlay_layer, secondary_underlay_layer]).addTo(map);

        } else {
            primary_overlay_layer.addTo(map);
            secondary_overlay_layer.addTo(map);
            comparison_control = L.control.sideBySide([primary_overlay_layer], [secondary_overlay_layer]).addTo(map);
        }
    } catch (e) {
        console.log(e)
    }
}

// This method adds WMS layers when dropdown selections change
function redraw_map_layers() {
    map_modal_action = localStorage.getItem('map_modal_action');

    console.log(map_modal_action);
        console.log(document.getElementById('usecase_name'))

    document.getElementById("loading_spinner_map").style.display = "block";
    clear_map_layers();
    if (map_modal_action == 'deforestation_targets') { // Forest Cover usecase
        /* Display the dropdowns that are required for the usecase and hide the rest */
        if (document.getElementById('selected_agb') != null)
            document.getElementById('selected_agb').style.display = 'none';
        if (document.getElementById('comparing_agb') != null)
            document.getElementById('comparing_agb').style.display = 'none';
        if (document.getElementById('comparing_agb_label') != null)
            document.getElementById('comparing_agb_label').style.display = 'none';
        if (document.getElementById('selected_agb_label') != null)
            document.getElementById('selected_agb_label').style.display = 'none';
        if (document.getElementById('selected_year') != null)
            document.getElementById('selected_year').style.display = 'block';
        if (document.getElementById('selected_year_label') != null)
            document.getElementById('selected_year_label').style.display = 'block';
        if (document.getElementById('comparison_year') != null)
            document.getElementById('comparison_year').style.display = 'block';
        if (document.getElementById('comparison_year_label') != null)
            document.getElementById('comparison_year_label').style.display = 'block';
        if (document.getElementById('comparing_region') != null)
            document.getElementById('comparing_region').style.display = 'block';
        if (document.getElementById('comparing_region_label') != null)
            document.getElementById('comparing_region_label').style.display = 'block';
        if (document.getElementById('selected_region_label') != null)
            document.getElementById('selected_region_label').style.display = 'block';
        if (document.getElementById('selected_region') != null)
            document.getElementById('selected_region').style.display = 'block';
        // Populate the years for FC on both sides
        let years = get_years_for_name_no_agb(fc_colls, document.getElementById('selected_region').value);
        fill_years_selector(years);
        let c_years = get_years_for_name_no_agb(fc_colls, document.getElementById('comparing_region').value);
        fill_comparison_years_selector(c_years);
        // Set the default year
        document.getElementById('selected_year').value = years[0];
        document.getElementById('comparison_year').value = c_years[c_years.length - 1];
    } else if (map_modal_action == 'carbon-stock' || map_modal_action == 'emissions') { // Carbon Stock or Emissions usecase
        /* Display the dropdowns that are required for the usecase and hide the rest */

        if (document.getElementById('selected_agb') != null)
            document.getElementById('selected_agb').style.display = 'block';
        if (document.getElementById('comparing_agb') != null)
            document.getElementById('comparing_agb').style.display = 'block';
        if (document.getElementById('comparing_agb_label') != null)
            document.getElementById('comparing_agb_label').style.display = 'block';
        if (document.getElementById('selected_agb_label') != null)
            document.getElementById('selected_agb_label').style.display = 'block';
        if (document.getElementById('selected_year') != null)
            document.getElementById('selected_year').style.display = 'block';
        if (document.getElementById('selected_year_label') != null)
            document.getElementById('selected_year_label').style.display = 'block';

        if (document.getElementById('comparison_year') != null)
            document.getElementById('comparison_year').style.display = 'block';
        if (document.getElementById('comparison_year_label') != null)
            document.getElementById('comparison_year_label').style.display = 'block';
        if (document.getElementById('comparing_region') != null)
            document.getElementById('comparing_region').style.display = 'block';
        if (document.getElementById('comparing_region_label') != null)
            document.getElementById('comparing_region_label').style.display = 'block';
        if (document.getElementById('selected_region_label') != null)
            document.getElementById('selected_region_label').style.display = 'block';
        if (document.getElementById('selected_region') != null)
            document.getElementById('selected_region').style.display = 'block';
        // Populate years based on FC and AGB selections
        let years = get_years_for_name(fc_colls, document.getElementById('selected_region').value);
        fill_years_selector(years);
        let c_years = get_years_for_name(fc_colls, document.getElementById('comparing_region').value);
        fill_comparison_years_selector(c_years);
        // Set the default year
        document.getElementById('selected_year').value = years[0];
        document.getElementById('comparison_year').value = c_years[c_years.length - 1];
    } else { // AGB usecase
        /* Display the dropdowns that are required for the usecase and hide the rest */

        if (document.getElementById('comparing_agb') != null)
            document.getElementById('comparing_agb').style.display = 'block';
        if (document.getElementById('comparing_agb_label') != null)
            document.getElementById('comparing_agb_label').style.display = 'block';
        if (document.getElementById('selected_agb_label') != null)
            document.getElementById('selected_agb_label').style.display = 'block';
        if (document.getElementById('selected_agb') != null)
            document.getElementById('selected_agb').style.display = 'block';

        if (document.getElementById('comparing_region') != null)
            document.getElementById('comparing_region').style.display = 'none';
        if (document.getElementById('comparing_region_label') != null)
            document.getElementById('comparing_region_label').style.display = 'none';
        if (document.getElementById('selected_region_label') != null)
            document.getElementById('selected_region_label').style.display = 'none';
        if (document.getElementById('selected_region') != null)
            document.getElementById('selected_region').style.display = 'none';

        if (document.getElementById('selected_year') != null)
            document.getElementById('selected_year').style.display = 'none';
        if (document.getElementById('selected_year_label') != null)
            document.getElementById('selected_year_label').style.display = 'none';

        if (document.getElementById('comparison_year') != null)
            document.getElementById('comparison_year').style.display = 'none';
        if (document.getElementById('comparison_year_label') != null)
            document.getElementById('comparison_year_label').style.display = 'none';
    }
    // Add the THREDDS WMS layers based on usecase, year and dataset selection
    add_thredds_wms_layers(map_modal_action);

    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseover', 'map.dragging.disable()');
    document.getElementsByClassName('leaflet-sbs-range')[0].setAttribute('onmouseout', 'map.dragging.enable()');
    document.getElementById("loading_spinner_map").style.display = "none";

    // Get the statistics on every dropdown change in order to update the info modal
    if (window.location.href.indexOf("/map/") > -1)
        get_stats_for_map();
}
//Get dataset names
function get_names_from_obj(obj){
        if(obj===undefined)
        return null;
    let names=[];
    for(var i=0;i<obj.length;i++){
        names.push(obj[i].name);
    }
    return names;
}
// Get list of years based on FC selection
function get_years_for_name_no_agb(obj,name){
     let years = [];
        for (var i = 0; i < obj.length; i++) {
            if (name.toLowerCase() === obj[i].name.split(' ').join('-').toLowerCase())
                return obj[i].years.sort();
        }
}
// Get list of years based on FC/AGB selection
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
//populate data in dropdowns
function get_available_years(map_modal_action) {
    console.log(map_modal_action);
    map_modal_action=localStorage.getItem('map_modal_action');
    // Forest Cover: Populate years and FC dropdowns
    if (map_modal_action=='deforestation_targets') {
        fill_dataset_selector(get_names_from_obj(fc_colls), get_names_from_obj(agb_colls));
        let years = get_years_for_name_no_agb(fc_colls, document.getElementById('selected_region').value);
        fill_years_selector(years);
        fill_comparison_dataset_selector(get_names_from_obj(fc_colls), get_names_from_obj(agb_colls));
        let c_years = get_years_for_name_no_agb(fc_colls, document.getElementById('comparing_region').value);
        fill_comparison_years_selector(c_years);

        document.getElementById('selected_year').value = years[0];
        document.getElementById('comparison_year').value = c_years[c_years.length - 1];
    }
    // Carbon Stock or Emissions:Populate years, FC dropdowns and AGB dropdowns
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
    else{
        fill_agb_selector(get_names_from_obj(agb_colls));
    }
}
// Get selected LCs when user draws AOI
function get_checked_lcs() {
    var lcs = [];
    $('.LC_checkboxlist input[type="checkbox"]:checked').each(function () {

        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        lcs.push(temp.replace('L', '').replace('C', ''));
    });
    return lcs;
}
// Get selected AGBS when user draws AOI
function get_checked_agbs() {
    var agbs = [];
    $('.AGB_checkboxlist input[type="checkbox"]:checked').each(function () {
        var temp = $(this).val().split(' ').pop().replace('(', '').replace(')', '');
        agbs.push(temp.replace('A', '').replace('G', '').replace('B', ''));
    });
    return agbs;
}

// Send user drawn AOI along with selected LCs and AGBs to database and redirect to the AOI page
function send_to_backend(){
    var lcss = get_checked_lcs();
    var agbss = get_checked_agbs();
    if(lcss.length>0 && agbss.length>0) {
        $.ajax({
            type: 'POST',
            url: 'upload-drawn-aoi/',
            data: {'lcs': lcss, 'agbs': agbss, 'geometry': JSON.stringify(drawn_aoi)},
            success: function (data) {
                if('error' in data){
                    alert('Please login to continue')
                }
                else{
                    window.location = window.location.origin + '/aoi/' + data.aoi_id + '/custom/';
                }
            }
        });
    }
    else{
        alert("Please select atleast one Land Cover and one Above Ground Biomass dataset");
    }
}

// Get statistics for map info modal
function get_stats_for_map() {
    // Get all the selected values
    var fc_name_left = document.getElementById('selected_region').value;
    var fc_name_right = document.getElementById('comparing_region').value;
    var agb_name_left = document.getElementById('selected_agb').value;
    var agb_name_right = document.getElementById('comparing_agb').value;
    var year_left = document.getElementById('selected_year').value;
    var year_right = document.getElementById('comparison_year').value;
    // AJAX call to return data from database
    $.ajax({
        type: 'POST',
        url: 'get_statistics_for_map/',
        data: {
            'fc_name_left': fc_name_left,
            'fc_name_right': fc_name_right,
            'agb_name_left': agb_name_left,
            'agb_name_right': agb_name_right,
            'year_left': year_left,
            'year_right': year_right,
            'map_action': map_modal_action
        },
        success: function (data) {
            var type = "deforestation_targets";
            var thredds_url_left = "";
            var thredds_url_right = "";
            var min_left, min_right = 0;
            var max_left, max_right = 1;
            var palette = "cwg";
            var title = "";
            var text_between = "";
            // Display data on the modal based on use case selection
            if (map_modal_action == 'deforestation_targets') {
                title = "Forest Cover Analysis";
                document.getElementById('other_3_usecases').style.display = 'none';
                document.getElementById('fc_usecase').style.display = 'block';
            } else {
                document.getElementById('other_3_usecases').style.display = 'flex';
                document.getElementById('fc_usecase').style.display = 'none';
            }
            if (map_modal_action == 'emissions') {
                document.getElementById('left_source').innerHTML = fc_name_left.split('-').join(' ').toUpperCase() + ' (FC), ' + agb_name_left.split('-').join(' ').toUpperCase() + ' (AGB)';
                document.getElementById('right_source').innerHTML = fc_name_right.split('-').join(' ').toUpperCase() + ' (FC), ' + agb_name_right.split('-').join(' ').toUpperCase() + ' (AGB)';
                type = map_modal_action;
                if (data.em_left.length > 0) {
                    min_left = data.em_left[0].min;
                    max_left = data.em_left[0].max;
                    min_right = data.em_right[0].min;
                    max_right = data.em_right[0].max;
                } else {
                    min_left = -1;
                    min_right = -1;
                    max_left = 32767;
                    max_right = 32767;

                }
                if (min_left == 0 && min_right == 0) {
                    min_left = -1
                    min_right = -1

                }
                if (max_left == 0 && max_right == 0) {
                    max_left = 32767
                    max_right = 32767

                }
                palette = "scap-agb";
                title = "Carbon Emission Estimations";
                document.getElementById('modal_usecase_title').innerHTML = title;
                document.getElementById('right_doi_fc').innerHTML = data.fc_doi_right;
                document.getElementById('right_doi_agb').innerHTML = data.agb_doi_right;
                document.getElementById('left_doi_fc').innerHTML = data.fc_doi_left;
                document.getElementById('left_doi_agb').innerHTML = data.agb_doi_left;
                document.getElementById('emissions_img').style.display = 'inline';
                document.getElementById('cs_img').style.display = 'none';
                document.getElementById('agb_img').style.display = 'none';

                text_between = "The color scales for the <strong>Carbon Emission</strong> estimations you have selected, are:";
                thredds_url_left = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + fc_name_left + '_' + agb_name_left + "/" + type + ".1." + fc_name_left + '_' + agb_name_left + "." + year_left +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_left + "," + max_left + "&PALETTE=" + palette;
                thredds_url_right = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + fc_name_right + '_' + agb_name_right + "/" + type + ".1." + fc_name_right + '_' + agb_name_right + "." + year_right +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_right + "," + max_right + "&PALETTE=" + palette;

            }
            if (map_modal_action == 'carbon-stock') {
                document.getElementById('left_source').innerHTML = fc_name_left.split('-').join(' ').toUpperCase() + ' (FC), ' + agb_name_left.split('-').join(' ').toUpperCase() + ' (AGB)';
                document.getElementById('right_source').innerHTML = fc_name_right.split('-').join(' ').toUpperCase() + ' (FC), ' + agb_name_right.split('-').join(' ').toUpperCase() + ' (AGB)';
                type = map_modal_action;
                if (data.cs_left.length > 0) {
                    min_left = data.cs_left[0].min;
                    max_left = data.cs_left[0].max;
                    min_right = data.cs_right[0].min;
                    max_right = data.cs_right[0].max;
                } else {
                    min_left = -1;
                    min_right = -1;
                    max_left = 32767;
                    max_right = 32767;
                }
                if (min_left == 0 && min_right == 0) {
                    min_left = -1
                    min_right = -1
                }
                if (max_left == 0 && max_right == 0) {
                    max_left = 32767
                    max_right = 32767

                }
                palette = "crimsonyellowgreen";
                title = "Carbon Stock Emissions";
                document.getElementById('modal_usecase_title').innerHTML = title;
                text_between = "The color scales for the <strong>Carbon Stock</strong> estimations you have selected, are:";
                document.getElementById('right_doi_fc').innerHTML = data.fc_doi_right;
                document.getElementById('right_doi_agb').innerHTML = data.agb_doi_right;
                document.getElementById('left_doi_fc').innerHTML = data.fc_doi_left;
                document.getElementById('left_doi_agb').innerHTML = data.agb_doi_left;

                document.getElementById('cs_img').style.display = 'inline';
                document.getElementById('emissions_img').style.display = 'none';
                document.getElementById('agb_img').style.display = 'none';

                thredds_url_left = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + fc_name_left + '_' + agb_name_left + "/" + type + ".1." + fc_name_left + '_' + agb_name_left + "." + year_left +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_left + "," + max_left + "&PALETTE=" + palette;
                thredds_url_right = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + fc_name_right + '_' + agb_name_right + "/" + type + ".1." + fc_name_right + '_' + agb_name_right + "." + year_right +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_right + "," + max_right + "&PALETTE=" + palette;

            }
            if (map_modal_action == 'agb') {
                document.getElementById('left_source').innerHTML = agb_name_left.split('-').join(' ').toUpperCase() + ' (AGB)';
                document.getElementById('right_source').innerHTML = agb_name_right.split('-').join(' ').toUpperCase() + ' (AGB)';
                console.log('agb')

                type = map_modal_action;
                if (data.agb_left.length > 0) {
                    min_left = data.agb_left[0].min;
                    max_left = data.agb_left[0].max;
                    min_right = data.agb_right[0].min;
                    max_right = data.agb_right[0].max;
                } else {
                    min_left = 1;
                    min_right = 1;
                    max_left = 550;
                    max_right = 550;
                }
                if (min_left == 0 && min_right == 0) {
                    min_left = 1
                    min_right = 1
                }
                if (max_left == 0 && max_right == 0) {
                    max_left = 550
                    max_right = 550

                }
                palette = "scap-agb";
                title = "Above Ground Biomass Estimation Comparison";
                document.getElementById('modal_usecase_title').innerHTML = title;
                text_between = "The color scales for the <strong>Above Ground Biomass (AGB)</strong> estimation source you have selected, are:";

                document.getElementById('right_doi_agb').innerHTML = data.agb_doi_right;
                document.getElementById('left_doi_agb').innerHTML = data.agb_doi_left;
                document.getElementById('right_doi_fc').innerHTML = "";
                document.getElementById('left_doi_fc').innerHTML = "";
                console.log("after fc empty")
                document.getElementById('agb_img').style.display = 'inline';
                document.getElementById('cs_img').style.display = 'none';
                document.getElementById('emissions_img').style.display = 'none';
                thredds_url_left = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + agb_name_left + "/" + type + ".1." + agb_name_left +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_left + "," + max_left + "&PALETTE=" + palette;
                thredds_url_right = "https://scapwms.servirglobal.net/thredds/wms/scap/public/" + type + "/1/" + agb_name_right + "/" + type + ".1." + agb_name_right +
                    ".nc4?service=WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=" + type + "&colorscalerange=" + min_right + "," + max_right + "&PALETTE=" + palette;

            }
            if (map_modal_action != 'deforestation_targets') {
                document.getElementById('left_min').innerHTML = min_left;
                document.getElementById('left_max').innerHTML = max_left;
                document.getElementById('right_min').innerHTML = min_right;
                document.getElementById('right_max').innerHTML = max_right;
                document.getElementById('text_between').innerHTML = text_between;
                var div = document.getElementById("primary_overlay_legend");
                div.innerHTML = "";
                div.innerHTML +=
                    '<img src="' + thredds_url_left + '" alt="legend">';
                div = document.getElementById("secondary_overlay_legend");
                div.innerHTML = "";
                div.innerHTML +=
                    '<img src="' + thredds_url_right + '" alt="legend">';
            }

        }
    });
}


function clickAOITag(html_id){
    aoi_values = aoi_nav_dict[html_id]
    $.ajax({
        type: 'POST',
        url: 'get-aoi-id/',
        data: {
            'aoi': aoi_values.NAME,
            'iso3': aoi_values.ISO3,
            'desig_eng': aoi_values.DESIG_ENG
        },
        success: function (data) {
            pa_selected_name = data.id;
            if (data.country_or_aoi === "country") {
                window.location = window.location.origin + '/pilot/' + pa_selected_name + '/';
            } else {
                window.location = window.location.origin + '/aoi/' + pa_selected_name + '/';
            }
        }
    });

}


/**
 * getFeatureInfoUrl
 * Builds and returns the url needed to make the feature info call
 * for the selected admin layer
 * @param {object} map - the map object
 * @param {object} layer - L.tileLayer.wms
 * @param {object} latlng - location clicked
 * @param {object} params - special parameters
 * @returns string url
 */
function getFeatureInfoUrl(map, layer, latlng, params) {
    if(layer === undefined){ return; }

    const point = map.latLngToContainerPoint(latlng, map.getZoom());
    const size = map.getSize();
    const bounds = map.getBounds();
    let sw = bounds.getSouthWest();
    let ne = bounds.getNorthEast();
    sw = L.CRS.EPSG4326.project(new L.LatLng(sw.lat, sw.lng));
    ne = L.CRS.EPSG4326.project(new L.LatLng(ne.lat, ne.lng));

    const bb = sw.x + "," + sw.y + "," + ne.x + "," + ne.y;

    const defaultParams = {
        request: "GetFeatureInfo",
        service: "WMS",
        srs: "EPSG:4326",
        styles: "",
        version: layer._wmsVersion,
        format: layer.options.format,
        bbox: bb,
        height: size.y,
        width: size.x,
        layers: layer.options.layers,
        query_layers: layer.options.layers,
        info_format: "text/html",
        FEATURE_COUNT: 50
    };

    params = L.Util.extend(defaultParams, params || {});
    params[params.version === "1.3.0" ? "i" : "x"] = point.x;
    params[params.version === "1.3.0" ? "j" : "y"] = point.y;
    return layer._url + L.Util.getParamString(params, layer._url, true);
}


// This method initializes the map with list of basemaps, overlays, watermask and sets default view. Also creates panes and controls.
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
    // list of overlays based on the URL
    if(country_id===0) { // if the map is loaded on map page without any pilot country selected
        overlays = {
            'Watermask': watermaskLayer,
        };
    }
    else if (window.location.href.indexOf("/pilot/") > -1) { // if the map is loaded on pilot country page
         country_layer = L.geoJSON(shp_obj['data_country'], {
            style: {
                weight: 2,
                opacity: 1,
                color: '#D3D3D3',  //Outline color
                fillOpacity: 0.2,
                 strokeWidth: 0,
            },
             pane:'topmost'
        });

           aoi_layer = L.tileLayer.wms('https://esa-rdst-data.servirglobal.net/geoserver/s-cap/wms?service=WMS',
            {
                layers: ['s-cap:ProtectedAreas'],
                format: "image/png",
                styles: '',
		transparent: true,
                pane: 'top'
            });

        overlays = {
            'Watermask': watermaskLayer,
            'Protected Areas': aoi_layer,
            'Country Outline': country_layer,
        };
        localStorage.setItem('map_modal_action','deforestation_targets')
    }
    else if (window.location.href.indexOf("/aoi/") > -1) { // if the map is loaded on protected area page
        aoi_layer = L.geoJSON(shp_obj['data_pa'], {
            style: {
                weight: 2,
                opacity: 1.0,
                color: 'cyan',  //Outline color
                fillOpacity: 0.0,
            },
            onEachFeature: onEachFeature_aoi,
            pane:'top'
        });
              // list of overlays
        overlays = {
            'Watermask': watermaskLayer,
            'Protected Areas': aoi_layer,

        };
                localStorage.setItem('map_modal_action','deforestation_targets')

    }
    else { // if the map is loaded on map explorer page
        aoi_layer = L.geoJSON(shp_obj['data_pa'], {
            style: {
                weight: 2,
                opacity: 1.0,
                color: 'cyan',  //Outline color
                fillOpacity: 0.0,
            },
            onEachFeature: onEachFeature_aoi,
            pane: 'top'
        });
        country_layer = L.geoJSON(shp_obj['data_country'], {
            style: {
                weight: 2,
                opacity: 1,
                color: '#D3D3D3',  //Outline color
                fillOpacity: 0.2,
                strokeWidth: 0,
            },
            pane: 'topmost'
        });
        overlays = {
            'Watermask': watermaskLayer,
            'Protected Areas': aoi_layer,
            'Country Outline': country_layer,
        };
    }

    //get center(lat, lon) and zoom from PilotCountry object
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
    map.createPane('top');
    map.createPane('topmost');
    map.zoomControl.setPosition('topleft');
    //add the default layers to show
    darkmap.addTo(map);
    // button added at the bottom left to switch usecase
    var usecasebutton = L.control({position: 'bottomleft'});
    usecasebutton.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = '<div class="btn-group dropend">\n' +
            '  <button type="button" id="usecase_name" class="btn btn-primary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">\n' +
            '    Displaying: Forest cover\n' +
            '  </button>\n' +
            '  <ul class="dropdown-menu">\n' +
            '    <li><a class="dropdown-item text-secondary" href="#" onclick="set_map_action(this,\'deforestation_targets\')">Forest cover</a></li>\n' +
            '    <li><a class="dropdown-item text-secondary" href="#" onclick="set_map_action(this,\'agb\')">Above Ground Biomass (AGB)</a></li>\n' +
            '    <li><a class="dropdown-item text-secondary" href="#"  onclick="set_map_action(this,\'emissions\')">Emission estimations</a></li>\n' +
            '    <li><a class="dropdown-item text-secondary" href="#" onclick="set_map_action(this,\'carbon-stock\')">Carbon stock</a></li>\n' +
            '  </ul>\n' +
            '</div>';
        div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
        return div;
    };
    // adding the usecase button only if we are on map page
    if(window.location.href.indexOf("/map/") > -1) {
        usecasebutton.addTo(map);
    }

    // addind the layer selection control to bottom left
    var layerControl = L.control.layers(baseMaps, overlays, {position: 'bottomleft'}).addTo(map);
    // Layer for user drawn polygons
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
            featureGroup: editableLayers,
            remove: true
        }
    };
    var drawControl = new L.Control.Draw(drawPluginOptions);
    // add draw polygon control to the map
    map.addControl(drawControl);
    map.on('draw:created', function (e) {
        var type = e.layerType,
            layer = e.layer;
        editableLayers.addLayer(layer);
        var json = editableLayers.toGeoJSON();
        $('#drawing_modal').modal('show');
        drawn_aoi = json;
    });

    map.on("click", function (e) {
        const url = getFeatureInfoUrl(map, aoi_layer, e.latlng, {
            info_format: "application/json",
            propertyName: "NAME,DESIG_ENG,ISO3",
        });

        if( url === undefined ){ return; }

        $.ajax({
            type: "GET",
            async: true,
            url: url,
            crossDomain: true,
            success: function (response) {
                if (response) {
		    console.log(response)
                    if (aoi_tooltip) {
                        aoi_tooltip.remove()
                    }
                    if (aoi_nav_dict) {
                        aoi_nav_dict = {}
                    }
                    if (response.features.length === 0){
                        aoi_tooltip = L.popup().setLatLng(e.latlng).setContent("<p>No AOIs found in specified location").openOn(map)
                        return;
                    }
                    let tooltip_content = "<table>"
                    for (const feat of response.features){
                        aoi_nav_dict[feat.id] = feat.properties
                        aoi_nav_dict[feat.id].NAME = decodeURIComponent(escape(aoi_nav_dict[feat.id].NAME))
                        tooltip_content += "<tr><td id='" + feat.id + "' onClick='clickAOITag(this.id)' class='aoi_link'>" + feat.properties.NAME + "</td></tr>"
                    }
                    tooltip_content += "</table>"
                    aoi_tooltip = L.popup().setLatLng(e.latlng).setContent(tooltip_content).openOn(map)
                }
            },
        });
    });    
    // add info modal control to the map
    L.easyButton('fa-info', function (btn, map) {
        $('#info_modal').modal('show');
    }, 'Info').addTo(map);

    // Add the search control to the map
    map.addControl(new GeoSearch.GeoSearchControl({
        provider: new GeoSearch.OpenStreetMapProvider(),
        showMarker: false,
        showPopup: false,
        autoClose: true
    }));

    // Which layers to show by default based on the page
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
    // load the usecase based on local storage value. If not set, default is to show forest cover layer
    map_modal_action=localStorage.getItem('map_modal_action');
    if(map_modal_action==null)
    {
        map_modal_action='deforestation_targets';
    }
    //populate the dropdowns based on the map modal action that is set above
    get_available_years(map_modal_action);
}

//zoom to selected pilot country
function zoomtoArea(id){
        console.log(localStorage.getItem('map_modal_action'));
    if (id!==0) {
        window.location = window.location.origin + "/map/" + id + "/";
        $('#country_selection_modal').modal('hide');
    }
}

// Starts here
$(function () {
    //Map Initialization
    init_map()
     map_modal_action=localStorage.getItem('map_modal_action');
       // if (map_modal_action == 'carbon-stock') {
       //      document.getElementById('usecase_name').innerHTML = 'Displaying: Carbon stock';
       //  } else if (map_modal_action == 'emissions') {
       //      document.getElementById('usecase_name').innerHTML = 'Displaying: Emission estimations';
       //  } else if (map_modal_action == 'deforestation_targets') {
       //      document.getElementById('usecase_name').innerHTML = 'Displaying: Forest cover';
       //  } else {
       //      document.getElementById('usecase_name').innerHTML = 'Displaying: Above Ground Biomass (AGB)';
       //  };
 if (window.location.href.indexOf("/map/0/") > -1)
     {
         // localStorage.clear();
         // localStorage.setItem('map_modal_action','deforestation_targets');

     }
     else{
         map_modal_action=localStorage.getItem('map_modal_action');
         redraw_map_layers();
    }

    var id = window.location.pathname.split('/')[2];
    // if usecase and country are selected from the modal, zoom to that country and load the map layers
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



