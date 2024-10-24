var tmap;
var fc_name_for_email='';
var agb_name_for_email='';
var fc_filename_for_email='';
var username_for_email='';

function approve_fc_file(fc_file) {
    var year = fc_file.split('_')[0]
    var name = fc_file.split('_')[1]
    var pos1=fc_file.indexOf('_');
    var pos2=fc_file.indexOf('_',pos1+1);
    var coll = fc_file.substring(pos2+1)
    $.ajax({
        type: 'POST',
        url: 'approve-fc-file/',
        data: {'year': year, 'coll_name': coll},
        success: function (data) {
            if (data.success != undefined) {
                location.reload()
            } else {
                alert("There is an error approving the Forest Cover File " + name)
            }

        }
    });
}

function populate_tiff_table(tiff_files){
    document.getElementById('fc_tiffs_to_be_validated_body').innerHTML="";
    var tiff_files=JSON.parse(tiff_files);
        var tiff_table = document.getElementById("fc_tiffs_to_be_validated_body");
        for(var i=0;i<tiff_files.length;i++) {
            console.log(tiff_files[i])
            var tiff_file=tiff_files[i];
            var tr = document.createElement('tr');
            var td1 = document.createElement('td');
            var td2 = document.createElement('td');
            var td3 = document.createElement('td');
            var td4 = document.createElement('td');
            var td5 = document.createElement('td');
            var td6 = document.createElement('td');
            var td7 = document.createElement('td');
            var td8 = document.createElement('td');

            var text1 = document.createTextNode(tiff_file.year);
            var text3 = document.createTextNode(tiff_file.doi_link);
            var text4 = document.createTextNode(tiff_file.metadata_link);
            var text2 = document.createTextNode(tiff_file.file);
            var text5 = document.createTextNode(tiff_file.validation_status);

            var viewButton = document.createElement('button');
                    viewButton.textContent = 'View';
                    viewButton.type = "button";
                    viewButton.id=tiff_file.year+'_'+tiff_file.cid+'_'+tiff_file.cname;
                    viewButton.classList = "btn btn-primary";

                          viewButton.addEventListener("click", function (event) {
                              var pos1 = this.id.indexOf('_');
                              var pos2 = this.id.indexOf('_', pos1 + 1);
                              var coll = this.id.substring(pos2 + 1)
                               var user=this.parentNode.parentNode.cells[0].firstChild.innerHTML;
                              show_layers_on_map('fc', user,this.id.split('_')[1], coll, this.id.split('_')[0]);
                          });

        viewButton.style="margin: 10px;margin-top:0px";
        viewButton.className="btn-primary btn";
         var approveButton = document.createElement('button');
                    approveButton.textContent = 'Approve';
                    approveButton.type = "button";
                    approveButton.id=tiff_file.year+'_'+tiff_file.cid+'_'+tiff_file.cname;
                    approveButton.classList = "btn btn-primary";

                          approveButton.addEventListener("click", function (event) {
                              approve_fc_file(this.id);

                });

        approveButton.style="margin: 10px;margin-top:0px";
        approveButton.className="btn-primary btn";
         var denyButton = document.createElement('button');
                    denyButton.textContent = 'Deny';
                    denyButton.type = "button";
                    denyButton.id=tiff_file.year+'_'+tiff_file.cid+'_'+tiff_file.cname;
                    denyButton.classList = "btn btn-danger";

                          denyButton.addEventListener("click", function (event) {
                              fc_filename_for_email=this.id;
                              $('#text_for_email').html('');
    $('#email_message_modal').modal('show');
                              // notify_user('fc');
                });

        denyButton.style="margin: 10px;margin-top:0px";
        denyButton.className="btn-danger btn";

            td1.appendChild(text1);
            td2.appendChild(text2);
            td3.appendChild(text3);
            td4.appendChild(text4);
            td5.appendChild(text5);
            td6.appendChild(viewButton);
             td7.appendChild(approveButton);
              td8.appendChild(denyButton);

            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            tr.appendChild(td4);
            tr.appendChild(td5);
            tr.appendChild(td6);
                tr.appendChild(td7);
                    tr.appendChild(td8);
            console.log(tr)
            tiff_table.appendChild(tr);

        }

}

function show_layers_on_map(type,user,cid,coll,year=0,yrs="[]") {
    document.getElementById('file_summary').style.display='block';


    // populate_tiff_table(tiff_files);

        var years_list = JSON.parse(yrs);
        var years = [];

        console.log(years_list)
        for (var j = 0; j < years_list.length; j++) {
            if (parseInt(cid) === years_list[j].cid) {
                years = years_list[j].years;
                break;
            }
        }
            if(year>0){
        years=[year];
    }
        document.getElementById('show_on_map').style.display = 'block';
        document.getElementById('preview_coll').innerText = coll;
        if (tmap != undefined) {
            tmap.eachLayer(function (layer) {
                tmap.removeLayer(layer);
            });
            darkmap.addTo(tmap);
        }

        if (tmap === undefined) {
            init_maps();
        }

        // L.geoJSON(boundary_geojson).addTo(tmap);
        console.log(years)

        for (var i = 0; i < years.length; i++) {
                if(type==='fc') {
     layer_name = 'preview.fc.'+user+'.' + coll + '.' + years[i];
     console.log(layer_name)
    }
    else if(type == 'agb'){
        layer_name = 'preview.agb.'+user+'.'  + coll + '.' + years[i];
    }

            console.log(layer_name);
            var xmlString = "https://geodata.servirglobal.net/geoserver/s-cap/wms?service=wms&version=1.1.1&request=GetCapabilities"
            fetch(xmlString)
                .then((response) => response.text())
                .then((text) => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(text, "text/xml");
                    var floor = doc.getElementsByTagName("Layer");
                    for (var i = 0; i < floor.length; i++) {
                        if (floor[i].childNodes[1].textContent === layer_name) {
                            const param = floor[i].childNodes[11];
                            var minx = param.getAttribute('minx');
                            var miny = param.getAttribute('miny');
                            var maxx = param.getAttribute('maxx');
                            var maxy = param.getAttribute('maxy');
                            // break;
                        }
                    }

                    var mywms = L.tileLayer.wms("https://geodata.servirglobal.net/geoserver/s-cap/wms", {
                        layers: layer_name,
                        format: 'image/png',
                        transparent: true,
                        version: '1.1.0',
                        attribution: "myattribution"
                    });

                    mywms.addTo(tmap);
                    var bounds = [
                        [miny, minx],
                        [maxy, maxx]
                    ];
                    // var rectangle = L.rectangle(bounds, {color: "#ff7800", weight: 3}).addTo(tmap);
                    tmap.fitBounds(bounds);
                });
            $.ajax({
              type: 'POST',
              url: 'get-forestcoverfile-stats/',
              data: {'year':years[i],'coll_name':coll,'type':type},
              success: function (data) {
                  document.getElementById('tif_shape').innerText=data.shape;
                   document.getElementById('tif_crs').innerText=data.crs;
                    document.getElementById('tif_min').innerText=data.min;
                     document.getElementById('tif_max').innerText=data.max;
                     document.getElementById('tif_extent').innerText=data.extent;
                      document.getElementById('tif_filename').innerText=data.filename;

              }
          });

        }


}
function init_maps(){

var darkmap = L.tileLayer(' https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:  '<a href="http://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
});


// Dark basemap
 darkmap = L.tileLayer(' https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:  '<a href="http://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
});
      tmap = L.map('tfile_validate', {
        fullscreenControl: true,center:[-8.60436, -74.73243],zoom:9
    });

  darkmap.addTo(tmap);
}

function stage_for_processing(type,name="") {
    console.log(name)
    var nm=$('#preview_coll').html();
    // if(name==undefined){
    //     alert("Please save collection first")
    // }
    // else {
    var json_obj={};
     if(type=='fc')
                json_obj={'type': type, 'coll_name': name};
                else if(type='agb')
                     json_obj={'type': type, 'agb_name': name};
                else
                     json_obj={'type': type, 'aoi_name': name};
        $.ajax({
            type: 'POST',
            url: 'stage-for-processing/',
            data: json_obj,
            success: function (data) {
                if (data.success != undefined) {
                    if (type == 'fc')
                        location.href = window.location.protocol + "//" + location.host + '/forest-cover-collections/';
                    else if (type = 'agb')
                        location.href = window.location.protocol + "//" + location.host + '/agb-collections/';
                    else
                        location.href = window.location.protocol + "//" + location.host + '/aoi-collections/';
                } else if (data.error != undefined) {
                    alert(data.error)
                }
            }

            });
    // }

}
var email_content="";
function notify_user(type){
    // alert("An email will be sent to the user.");
    // location.href = window.location.protocol + "//" + location.host + '/forest-cover-collections/';
    var message=email_content+ "\n"+document.getElementById('text_for_email').value;
    var user=username_for_email;
      var name=type==='fc'?(fc_filename_for_email.length>0?fc_filename_for_email:fc_name_for_email):agb_name_for_email;
      if(message.length==0 && document.getElementById('text_for_email').value==""){
          alert("Please enter a message or select an option for the email");
      }
      else {
          $.ajax({
              type: 'POST',
              url: 'deny-notify-user/',
              data: {'type': type, 'coll_name': name, 'message': message, 'user': user},
              success: function (data) {
                  if (data.msg === 'success')
                      location.reload();
                  else {
                      alert(data.msg);
                      location.reload();

                  }
              }
          });
      }
}


$('.fc_deny').click(function(){
$('#text_for_email').val('');
    $('#email_message_modal').modal('show');
 fc_name_for_email=this.parentNode.parentNode.cells[1].firstChild.innerHTML;
 username_for_email=this.parentNode.parentNode.cells[0].firstChild.innerHTML;
});

$('#agb_deny').click(function(){
    $('#text_for_email').val('');
    $('#email_message_modal').modal('show');
       agb_name_for_email=this.parentNode.parentNode.cells[1].firstChild.innerHTML;
       username_for_email=this.parentNode.parentNode.cells[0].firstChild.innerHTML;
});


$("#email_opt1").change(function() {
    if(this.checked) {
        //Do
        email_content=email_content+' '+$("#email_opt1_label").html();
    }
});
$("#email_opt2").change(function() {
    if(this.checked) {
        //Do stuff
        email_content=email_content+' '+$("#email_opt2_label").html();
    }
});
$("#email_opt3").change(function() {
    if(this.checked) {
        //Do stuff
        $('#text_for_email').show();

    }
         else{
                   $('#text_for_email').hide();
                      $('#text_for_email').val('');
         }

});