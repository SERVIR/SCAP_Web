function validate_all_fields(year, doi_link) {
    if (year.length < 4) {
        alert("please enter a valid year");
        return false;
    }
    $.ajax({
        type: 'POST',
        crossDomain: true,
        dataType: 'jsonp',
        url: 'http://api.datacite.org/dois',
        data: {'query': doi_link},
        success: function (result) {
            console.log(result.data.length);
            if (result.data.length <= 0) {
                return false;

            }

        },
    });
    return true;

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
    form_data.append('coll_name', $('#id_collection_name').val());


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
                alert(data.error_message)

            }
        },
    });
}

function addFields(user) {
    var validated = false;
    var year = $('#tiff_year').val();
    var doi_link = $('#tiff_doi').val();
    var metadata_link = $('#tiff_metadata').val();
    validated = validate_all_fields(year, doi_link);
    var doi_url = "";
    if (validated) {


        $.ajax({
            type: 'POST',
            url: 'doi/',
            data: {'doi': $('#tiff_doi').val()},
            success: function (data) {
                if (data.url != "") {
                    // display success message and reset values in the form fields
                    console.log(data.url);
                    doi_url = data.url;
                    var tiff_table = document.getElementById("tifffTableBody");
                    var tbodyRowCount = tiff_table.rows.length; // 3

                    var tr = document.createElement('tr');

                    var td1 = document.createElement('td');
                    var td2 = document.createElement('td');
                    var td3 = document.createElement('td');
                    var td4 = document.createElement('td');
                    var td5 = document.createElement('td');

                    var text1 = document.createTextNode(user);
                    var text2 = document.createTextNode($('#tiff_year').val());
                    var text3 = document.createTextNode($('#tiff_new_file').val().replace(/.*(\/|\\)/, ''));
                    var doi = document.createElement('a');
                    var link = document.createTextNode('Link');
                    doi.href = doi_url;
                    doi.target = "_blank";
                    doi.appendChild(link);
                    var metadata = document.createElement('a');
                    link = document.createTextNode('Link');
                    metadata.href = $('#tiff_metadata').val();
                    metadata.target = "_blank";
                    metadata.appendChild(link);
                    td1.appendChild(text1);
                    td2.appendChild(text2);
                    td3.appendChild(text3);
                    td4.appendChild(doi);
                    td5.appendChild(metadata);

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
                } else {
                    alert('Please enter a valid DOI or leave blank');
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log(textStatus);
            }

        });


    } else {
        $("#tifffTableBody").html('<tr id="no-records" class="text-center"><td colspan="5">No tiff files added yet.</td></tr>');
    }


}