function stage_for_processing() {
    var name=$('#id_aoi_name').val();
    $.ajax({
        type: 'POST',
        url: 'stage-for-processing/',
        data: {'type':'aoi','coll_name': name},
        success: function (data) {
            location.href=window.location.protocol + "//" +location.host+'/user-data/';
        }
    });

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