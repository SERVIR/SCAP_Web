function stage_for_processing() {
    var name=$('#current_coll').html();
    $.ajax({
        type: 'POST',
        url: 'stage-for-processing/',
        data: {'type':'fc','coll_name': name},
        success: function (data) {
            location.href=window.location.protocol + "//" +location.host+'/user-data/';
        }
    });

}

function validate_all_fields(year, file,doi_link) {
    var res = true;
    if (file === '' || file === undefined) {
        alert("Please select a file");
        res = false;
    }
    if (year.length < 4) {
        alert("Please enter a valid year");
        res = false;
    }

    // if (doi_link.length > 0) {
    //     // $.ajax({
    //     //     type: 'POST',
    //     //     crossDomain: true,
    //     //     dataType: 'jsonp',
    //     //     url: 'http://api.datacite.org/dois',
    //     //     data: {'query': doi_link},
    //     //     success: function (result) {
    //     //         console.log(result.data.length);
    //     //         if (result.data.length === 0) {
    //     //             res = false;
    //     //
    //     //         }
    //     //
    //     //     },
    //     // });
    //     if (res === false) {
    //         alert("please enter a valid DOi or leave blank");
    //         return res;
    //     }

    // }
        return res;

}

function clear_fields() {
    $('#tiff_year').val('');
    $('#tiff_metadata').val('');
    $('#tiff_doi').val('');
    $('#tiff_new_file').val('');
}

function storeTiffs() {

    var upload_form = $('#upload-file-new')[0];
    var form_data = new FormData(upload_form);
    let file = $("#tiff_new_file").prop('files')[0];
    form_data.append('FC_tiff', file);
    form_data.append('year', $('#tiff_year').val());
    form_data.append('doi', $('#tiff_doi').val());
    form_data.append('metadata', $('#tiff_metadata').val());
    form_data.append('coll_name', $('#current_coll').html());


    $.ajax({
        type: 'POST',
        url: '/savetomodel/',
        data: form_data,
        contentType: false,
        processData: false,
        success: function (data) {
            console.log(data);
            if (data.result == "success")
                console.log('Success!');
            else {
                alert(data.error_message);

            }
        },
    });
}

function show_tiffs(col) {
    $.ajax({
            type: 'POST',
            url: 'get-tiff-data/',
            data: {'coll_name': col},
            success: function (result) {
                                    var tiff_table = document.getElementById("tifffTableBody");
                        var data=result.data;
                        if (data.length>0){
                            $("#tifffTableBody").html('');
                        }
                for (var i=0;i<data.length;i++) {

                    var userId = data[i].userId;
                    var year = data[i].year;
                    var filename = data[i].filename;
                    var doi_link = data[i].doi;
                    var metadata_link = data[i].metadata;

                    var tr = document.createElement('tr');

                    var td1 = document.createElement('td');
                    var td2 = document.createElement('td');
                    var td3 = document.createElement('td');
                    var td4 = document.createElement('td');
                    var td5 = document.createElement('td');

                    var text1 = document.createTextNode(userId);
                    var text2 = document.createTextNode(year);
                    var text3 = document.createTextNode(filename);
                     if(doi_link.length>0) {
                        var doi = document.createElement('a');
                        var link = document.createTextNode('Link');
                        doi.href = doi_link;
                        doi.target = "_blank";
                        doi.appendChild(link);
                        td4.appendChild(doi);
                    }
                    else{
                      td4.appendChild( document.createTextNode(''));
                    }
                    if(metadata_link.length>0) {
                        var metadata = document.createElement('a');
                        mlink = document.createTextNode('Link');
                        metadata.href = metadata_link;
                        metadata.target = "_blank";
                        metadata.appendChild(mlink);
                         td5.appendChild(metadata);
                    }
                    else{
                         td5.appendChild( document.createTextNode(''));
                    }
                    td1.appendChild(text1);
                    td2.appendChild(text2);
                    td3.appendChild(text3);


                    tr.appendChild(td1);
                    tr.appendChild(td2);
                    tr.appendChild(td3);
                    tr.appendChild(td4);
                    tr.appendChild(td5);

                    tiff_table.appendChild(tr);
                }
                var tbodyRowCount = tiff_table.rows.length; // 3
                if (tbodyRowCount > 0) {
                    if (document.getElementById("no-records"))
                        document.getElementById("no-records").remove();
                }
            }
            });


}
// console.log({{operation}});
if(opn==='EDIT'){
        show_tiffs($('#current_coll').html());
    }
function addFields(user,opn) {
    var tiff_table = document.getElementById("tifffTableBody");

    var validated = true;
    var year = $('#tiff_year').val();
    var doi_link = $('#tiff_doi').val();
    var metadata_link = $('#tiff_metadata').val();
    validated = validate_all_fields(year, $('#tiff_new_file').val(), doi_link);
    var doi_url = "";
    console.log(validated);
    if (validated) {


        $.ajax({
            type: 'POST',
            url: 'doi/',
            data: {'doi': $('#tiff_doi').val()},
            success: function (data) {
                // display success message and reset values in the form fields


                var tbodyRowCount = tiff_table.rows.length; // 3

                var tr = document.createElement('tr');

                var td1 = document.createElement('td');
                var td2 = document.createElement('td');
                var td3 = document.createElement('td');
                var td4 = document.createElement('td');
                var td5 = document.createElement('td');

                var text1 = document.createTextNode(user);
                var text2 = document.createTextNode($('#tiff_year').val());
                var text3 = document.createTextNode('fc_'+user+'_'+$('#current_coll').html()+'_'+year+'_1ha.tif');
                console.log(data.error);
                   if(data.error!==undefined) {
                       doi_url = $('#tiff_doi').val();
                       td4.appendChild(document.createTextNode(doi_url));
                   }
                else {
                    console.log("in else")
                    if(data.url.length>0) {
                        doi_url = data.url;
                        var doi = document.createElement('a');
                        var link = document.createTextNode('Link');
                        doi.href = doi_url;
                        doi.target = "_blank";
                        doi.appendChild(link);
                        td4.appendChild(doi);
                    }
                    else{
                        td4.appendChild(document.createTextNode(''));
                    }
                   }


                if (metadata_link.length > 0) {
                    var metadata = document.createElement('a');
                    var mlink = document.createTextNode('Link');
                    metadata.href = $('#tiff_metadata').val();
                    metadata.target = "_blank";
                    metadata.appendChild(mlink);
                    td5.appendChild(metadata);

                } else {
                    td5.appendChild( document.createTextNode(''));

                }
                td1.appendChild(text1);
                td2.appendChild(text2);

                td3.appendChild(text3);


                tr.appendChild(td1);
                tr.appendChild(td2);
                tr.appendChild(td3);
                tr.appendChild(td4);
                tr.appendChild(td5);

                tiff_table.appendChild(tr);
                storeTiffs();
                if (tbodyRowCount > 0) {
                    if (document.getElementById("no-records"))
                        document.getElementById("no-records").remove();
                }
                clear_fields();

            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(errorThrown);
            }

        });
    } else {
        var tbodyRowCount = tiff_table.rows.length; // 3
        if (tbodyRowCount > 0) {
            if (document.getElementById("no-records"))
                document.getElementById("no-records").remove();
        } else {
            $("#tifffTableBody").html('<tr id="no-records" class="text-center"><td colspan="5">No tiff files added yet.</td></tr>');

        }
    }


}