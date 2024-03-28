function stage_for_processing() {
    console.log($('#id_agb_name').val());
    var name=$('#id_agb_name').val();
    $.ajax({
        type: 'POST',
        url: 'stage-for-processing/',
        data: {'type':'agb','coll_name': name},
        success: function (data) {
           // location.href=window.location.protocol + "//" +location.host+'/agb-data/';
        }
    });

}
