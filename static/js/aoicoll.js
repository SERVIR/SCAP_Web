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