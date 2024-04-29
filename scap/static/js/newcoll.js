var coll_doi=false;
var coll_metadata=false;
var tiff_doi=false;
var year_exists=true;
var doi_metadata=false;
function  remove_boundary_file (){
       $.ajax({
            type: 'POST',
            url: 'update-boundary-file/',
            data: {'type':'fc'},
            success: function (data) {
                window.location.reload();
            }
        });
}
function sortTable(table, col, reverse) {
    var tb = table.tBodies[0], // use `<tbody>` to ignore `<thead>` and `<tfoot>` rows
        tr = Array.prototype.slice.call(tb.rows, 0), // put rows into array
        i;
    reverse = -((+reverse) || -1);
    tr = tr.sort(function (a, b) { // sort rows
        return reverse // `-1 *` if want opposite order
            * (a.cells[col].textContent.trim() // using `.textContent.trim()` for test
                .localeCompare(b.cells[col].textContent.trim())
               );
    });
    for(i = 0; i < tr.length; ++i) tb.appendChild(tr[i]); // append each row in order
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
                    coll_doi=false;
                    document.getElementById('id_doi_link').value = "";
                } else {
                    coll_doi=true;
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
document.getElementById('tiff_metadata').onchange = function() {
    var metadata=document.getElementById('tiff_metadata').value;


   if(metadata===''){


   }
   else if(isUrlValid(metadata)){

   }
   else{
       alert("Please enter valid metadata link or leave blank")
   }

};
document.getElementById('tiff_year').onchange = function() {
  var year=document.getElementById('tiff_year').value;
 var current_year=new Date().getFullYear();
    if (year.length < 4 || year<=1979 ||year>current_year) {
        alert("Please enter a valid year between 1980 and "+current_year);
    }
};
document.getElementById('tiff_doi').onchange = function() {
    var doi=document.getElementById('tiff_doi').value;


        $.ajax({
            type: 'POST',
            url: 'doi/',
            data: {'doi': doi},
            success: function (data) {
                if(data.error){
                    alert('please enter a valid doi');
                                        tiff_doi=false;

                    document.getElementById('tiff_doi').value="";
                }
                else{
                    tiff_doi=true;
                    console.log("valid doi");

                }
            }
        });

};
function stage_for_processing() {
    var name=$('#current_coll').html();
    if(name==undefined){
        alert("Please save collection first")
    }
    else {
        $.ajax({
            type: 'POST',
            url: 'stage-for-processing/',
            data: {'type': 'fc', 'coll_name': name},
            success: function (data) {
                location.href = window.location.protocol + "//" + location.host + '/forest-cover-collections/';
            }
        });
    }

}

function validate_all_fields(year, file,doi_link) {
    var res = true;
    if (file === '' || file === undefined) {
        alert("Please select a file");
        res = false;
    }
    var current_year=new Date().getFullYear();
    if (year.length < 4 || year<=1979 ||year>current_year) {
        alert("Please enter a valid year between 1980 and "+current_year);
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
    form_data.append('file', file);
    form_data.append('year', $('#tiff_year').val());
    form_data.append('doi_link', $('#tiff_doi').val());
    form_data.append('metadata_link', $('#tiff_metadata').val());
    form_data.append('coll_name', $('#current_coll').html());


    $.ajax({
        type: 'POST',
        url: 'add-tiff-record/',
        data: form_data,
        contentType: false,
        processData: false,
        xhr: function() {
                var xhr = new window.XMLHttpRequest();
                var parent_div=document.createElement("div");
                parent_div.className="progress";
                parent_div.style.marginBottom="10px";
                var label=document.createElement('span');

                label.innerHTML="Uploading "+file.name;;

                         var progress_div=document.createElement("div");
                            progress_div.className='progress-bar progress-bar-striped progress-bar-animated';
                        progress_div.role='progressbar';
                        progress_div.id= "id" + Math.random().toString(16).slice(2);
                        parent_div.appendChild(progress_div);
                        document.getElementById("fc_progress_parent").appendChild(label);
                        document.getElementById("fc_progress_parent").appendChild(parent_div);

                // Listen to the 'progress' event
                xhr.upload.addEventListener("progress", function(evt) {
                    if (evt.lengthComputable) {
                        // Calculate the percentage of the upload completed
                        var percentComplete = evt.loaded / evt.total * 100;
                        console.log('Upload progress: ' + percentComplete.toFixed(2) + '%');

                        progress_div.innerHTML=percentComplete.toFixed(2) + '%';
                        progress_div.style.width=percentComplete.toFixed(2) + '%';

                        // document.getElementById("fc_progress").innerHTML=percentComplete.toFixed(2) + '%';
                        // document.getElementById("fc_progress").style.width=percentComplete.toFixed(2) + '%';
                        if(percentComplete===100.00){
                            document.getElementById("fc_progress_parent").style.display="none";
                            document.getElementById("stage_processing").classList.remove("disabled");

                        }
                        else{
                            document.getElementById("fc_progress_parent").style.display="flex";
                            document.getElementById("stage_processing").classList.add("disabled");

                        }
                        // You can update a progress bar or do anything else with the progress information here
                    }
                }, false);
                return xhr;
            },error: function(xhr, status, error) {
               console.log(xhr);
               console.log(status);
               console.log(error);
            },
        success: function (data) {
            console.log(data.error);
            if(data.error.length>0) {
                alert("Year exists, please change year");
                show_tiffs($('#current_coll').html());
            }
            else {
                year_exists = true;
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
            var data = result.data;
            console.log(result);
            if (data.length > 0) {
                $("#tifffTableBody").html('');

                for (var i = 0; i < data.length; i++) {

                    var year = data[i].year;
                    var filename = data[i].filename;
                    var doi_link = data[i].doi_full_link;
                    var metadata_link = data[i].metadata;

                    var tr = document.createElement('tr');

                    var td2 = document.createElement('td');
                    var td3 = document.createElement('td');
                    var td4 = document.createElement('td');
                    var td5 = document.createElement('td');
                    var td6 = document.createElement('td');
                    var td7 = document.createElement('td');

                    var text2 = document.createTextNode(year);
                    var text3 = document.createTextNode(filename);
                    if (doi_link.length > 0) {
                        var doi = document.createElement('a');
                        var link = document.createTextNode('Link');
                        doi.href = doi_link;
                        doi.target = "_blank";
                        doi.appendChild(link);
                        td4.appendChild(doi);
                    } else {
                        td4.appendChild(document.createTextNode(''));
                    }
                    if (metadata_link.length > 0) {
                        var metadata = document.createElement('a');
                        mlink = document.createTextNode('Link');
                        metadata.href = metadata_link;
                        metadata.target = "_blank";
                        metadata.appendChild(mlink);
                        td5.appendChild(metadata);
                    } else {
                        td5.appendChild(document.createTextNode(''));
                    }
                    td2.appendChild(text2);
                    td3.appendChild(text3);
                    var editButton = document.createElement('button');
                    editButton.textContent = 'Edit';
                    editButton.type = "button";
                    editButton.classList = "btn btn-primary";
                    editButton.onclick = function () {
                        var row = this.parentElement.parentElement;


                        populateTiffForm(row);
                    };
                    var deleteButton = document.createElement('button');
                    deleteButton.textContent = 'Delete';
                    deleteButton.type = "button";
                    deleteButton.classList = "btn btn-danger";
                    td6.appendChild(editButton);
                    td7.appendChild(deleteButton);
                    deleteButton.onclick = function () {
                        var row = this.parentElement.parentElement;

                        var id = parseInt(window.location.pathname.split('/')[3]);
                        deleteTiffFile(id, row);

                    };


                    tr.appendChild(td2);
                    tr.appendChild(td3);
                    tr.appendChild(td4);
                    tr.appendChild(td5);
                    tr.appendChild(td6);
                    tr.appendChild(td7);
                    tiff_table.appendChild(tr);
                }
                var tbodyRowCount = tiff_table.rows.length; // 3
                if (tbodyRowCount > 0) {
                    if (document.getElementById("no-records"))
                        document.getElementById("no-records").remove();
                }
                sortTable(document.getElementById("tifffTable"), 0, false);
                                document.getElementById("stage_processing").classList.remove("disabled");

            } else {
                $("#tifffTableBody").html('<tr id="no-records" class="text-center"><td colspan="6">No tiff files added yet.</td></tr>');
                document.getElementById("stage_processing").classList.add("disabled");
            }
        }
    });

}
if(opn==='EDIT') {
    show_tiffs($('#current_coll').html());
}

function deleteTiffFile(id,row) {
    console.log(id);
      var tds = row.getElementsByTagName("td");   // Finds all children <td> elements
        var year=tds[0].textContent;
    $.ajax({
         type: 'POST',
         url: 'delete-tiff-record/',
         data: {'year':year,'coll_name':$('#current_coll').html()},
         success: function (data) {

            row.parentNode.removeChild(row);
             var tiff_table = document.getElementById("tifffTableBody");
             var tbodyRowCount = tiff_table.rows.length; // 3
        if (tbodyRowCount > 0) {
            if (document.getElementById("no-records"))
                document.getElementById("no-records").remove();
            document.getElementById("stage_processing").classList.remove("disabled");

        } else {
            $("#tifffTableBody").html('<tr id="no-records" class="text-center"><td colspan="6">No tiff files added yet.</td></tr>');
            document.getElementById("stage_processing").classList.add("disabled");
        }
         }
     });

}

function updateFields(button,pk) {


    var tiff_id = document.getElementById("tiff_id_to_update").value;
    $.ajax({
        type: 'POST',
        url: 'doi/',
        data: {'doi': $('#tiff_doi').val()},
        success: function (data) {
            var upload_form = $('#upload-file-new')[0];
            var form_data = new FormData(upload_form);
            let file = $("#tiff_new_file").prop('files')[0];
            form_data.append('file', file);
            form_data.append('year', $('#tiff_year').val());
            if ($('#tiff_doi').val() !== '') {

                if (data.url && data.url.length > 0) {
                    var rowIndex = document.getElementById("row_to_update").value;
                    var a = document.getElementById('tifffTable').rows[rowIndex].cells[2].firstChild;
                    console.log(data.url)
                   a.href= data.url;
                } else {
                    alert('Please enter a valid doi or leave blank');
                }
            } else {
                form_data.append('doi_link', $('#tiff_doi').val());

            }


            form_data.append('metadata_link', $('#tiff_metadata').val());
            form_data.append('coll_name', $('#current_coll').html());
            form_data.append('id', parseInt(tiff_id));


            $.ajax({
                type: 'POST',
                url: 'update-tiff-record/',
                data: form_data,
                contentType: false,
                processData: false,
                success: function (data1) {
                    if (data1.error) {
                        alert(data1.error);

                    } else {
                        console.log("updated tiff record");
                        document.getElementById("update_tiff").type = "hidden";
                        document.getElementById("label_edit_tiff").style.display = "none";
                        document.getElementById("save_year").type = "button";
                        document.location.reload(true);
                    }
                }
            });
        }
    });

}
function populateTiffForm(row) {
    document.getElementById("row_to_update").value=row.rowIndex;

                     var tds = row.getElementsByTagName("td");   // Finds all children <td> elements
        var year=tds[0].textContent;
        // var doi=tds[2].getElementsByTagName("a")[0]?tds[2].getElementsByTagName("a")[0].getAttribute('href'):"";
        var metadata=tds[3].getElementsByTagName("a")[0]?tds[3].getElementsByTagName("a")[0].getAttribute('href'):"";
        var curr_file=tds[1].textContent;

     $.ajax({
         type: 'POST',
         url: 'get-tiff-id/',
         data: {'year':year,'coll_name':$('#current_coll').html()},
         success: function (data) {
            document.getElementById("tiff_id_to_update").value=data.id;
            document.getElementById("tiff_doi").value=data.doi;

        document.getElementById("tiff_year").value=year;
        // document.getElementById("tiff_doi").value=doi;
        document.getElementById("tiff_metadata").value=metadata;
        document.getElementById("update_tiff").type="button";
        document.getElementById("label_edit_tiff").style.display="block";
        document.getElementById("current_tiff_name").innerHTML=curr_file;
        document.getElementById("save_year").type="hidden";
         }
     });

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

                var td2 = document.createElement('td');
                var td3 = document.createElement('td');
                var td4 = document.createElement('td');
                var td5 = document.createElement('td');
     var td6 = document.createElement('td');
                    var td7 = document.createElement('td');
                var text2 = document.createTextNode($('#tiff_year').val());
                var text3 = document.createTextNode($("#tiff_new_file").prop('files')[0].name);
                text3.id='fc_'+user+'_'+$('#current_coll').html()+'_'+year+'_1ha';
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
                        // doi.onclick=go_to_doi();
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
                td2.appendChild(text2);

                td3.appendChild(text3);
                    var editButton = document.createElement('button');
editButton.textContent = 'Edit';
editButton.type="button";
editButton.classList="btn btn-primary";
editButton.onclick=function (){
    var row=this.parentElement.parentElement;


populateTiffForm(row);
};
                    var deleteButton = document.createElement('button');
deleteButton.textContent = 'Delete';
deleteButton.type="button";
deleteButton.classList="btn btn-danger";
td6.appendChild(editButton);
td7.appendChild(deleteButton);
deleteButton.onclick=function (){
    var row=this.parentElement.parentElement;

var id=parseInt(window.location.pathname.split('/')[3]);
deleteTiffFile(id,row);

};

                tr.appendChild(td2);
                tr.appendChild(td3);
                tr.appendChild(td4);
                tr.appendChild(td5);
       tr.appendChild(td6);
                    tr.appendChild(td7);
                    // if (tiff_doi) {

                      storeTiffs();

                             tiff_table.appendChild(tr);
                                                      clear_fields();


                    // }




                if (tbodyRowCount > 0) {
                    if (document.getElementById("no-records"))
                        document.getElementById("no-records").remove();
                }


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
            document.getElementById("stage_processing").classList.remove("disabled");

        } else {
            $("#tifffTableBody").html('<tr id="no-records" class="text-center"><td colspan="6">No tiff files added yet.</td></tr>');
            document.getElementById("stage_processing").classList.add("disabled");
        }
    }


}