function stage_for_processing() {
    var name=$('#id_name').val();
    $.ajax({
        type: 'POST',
        url: 'stage-for-processing/',
        data: {'type':'aoi','coll_name': name},
        success: function (data) {
            location.href=window.location.protocol + "//" +location.host+'/aoi-collections/';
        }
    });

}
function check_progress_aoi(){

   if ($('#id_name').val().length>0 && $('#id_description').val().length>0) {
       var upload_form = $('#upload-aoi-new')[0];
       var form_data = new FormData(upload_form);
       let file = $("#id_source_file").prop('files')[0];
          if($("#id_source_file").prop('files')[0]===undefined){
              form_data.append('file', null);
         }
         else{
              form_data.append('file', file);
         }
       form_data.append('aoi_name', $('#id_name').val());
       form_data.append('aoi_desc', $('#id_description').val());
       form_data.append('metadata_link', $('#id_metadata_link').val());
       form_data.append('doi_link', $('#id_doi_link').val());
       var e = document.getElementById("id_access_level");
       var value = e.value;
       var text = e.options[e.selectedIndex].text;
       form_data.append('access', $('#id_access_level').val());
       $.ajax({
           type: 'POST',
           url: 'store-for-processing/',
           data: form_data,
           contentType: false,
           processData: false,
           xhr: function () {
               var xhr = new window.XMLHttpRequest();
               // Listen to the 'progress' event
               xhr.upload.addEventListener("progress", function (evt) {
                   if (evt.lengthComputable) {
                       // Calculate the percentage of the upload completed
                       var percentComplete = evt.loaded / evt.total * 100;
                       console.log('Upload progress: ' + percentComplete.toFixed(2) + '%');
                       document.getElementById("aoi_progress").innerHTML = percentComplete.toFixed(2) + '%';
                       document.getElementById("aoi_progress").style.width = percentComplete.toFixed(2) + '%';
                       if (percentComplete === 100.00) {
                           document.getElementById("aoi_progress_parent").style.display = "none";

                       } else {
                           document.getElementById("aoi_stage_processing").classList.add("disabled");
                           document.getElementById("aoi_progress_parent").style.display = "block";

                       }
                       // You can update a progress bar or do anything else with the progress information here
                   }
               }, false);
               return xhr;
           }, error: function (xhr, status, error) {
               console.log(xhr);
               console.log(status);
               console.log(error);
           },
           success: function (data) {
               if (data.error.length === 0) {
                   stage_for_processing();
                   location.href = window.location.protocol + "//" + location.host + '/aoi-collections/';

               } else {
                   alert(data.error)
               }
           },
       });
   }
   else{
       alert("Please check if you have entered AOI Name and Description.")
   }
}
document.getElementById('id_doi_link').onchange = function() {
    var doi=document.getElementById('id_doi_link').value;
    if(doi!=='') {


        $.ajax({
            type: 'POST',
            url: 'doi/',
            data: {'doi': doi},
            success: function (data) {
                if (data.error) {
                    alert('please enter a valid doi or leave blank');
                    document.getElementById('id_doi_link').value = "";
                } else {
                    console.log("valid doi");

                }
            }
        });
    }

};

function isUrlValid(userInput) {
    var res = userInput.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
    if (res == null)
        return false;
    else
        return true;
}
document.getElementById('id_metadata_link').onchange = function() {
    var metadata=document.getElementById('id_metadata_link').value;


   if(metadata===''){


   }
   else if(isUrlValid(metadata)){

   }
   else{
       alert("Please enter valid metadata link or leave blank")
   }

};