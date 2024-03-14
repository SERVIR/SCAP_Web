populateCollections();
$("#savetoDB").click(function (e) {
    e.preventDefault();


    var upload_form = $('#upload-file')[0];
    var form_data = new FormData(upload_form);
    form_data.append('boundaryFile', $('input[type=file]')[0].files[0]);
    form_data.append('boundaryFileName', $('#boundaryFile').val().replace(/.*(\/|\\)/, ''));
    form_data.append('coll_name', $('#coll_name').val());
    form_data.append('coll_desc', $('#coll_desc').val());
    var e = document.getElementById("access");
    var access = e.options[e.selectedIndex].text;
    form_data.append('access', access);
    if (document.getElementById("col_exists").innerHTML.length === 0) {
        let files = $('input[type=file]')[1].files;
        for (let i = 0; i < files.length; i++) {
            form_data.append('FC_tiffs[]', files[i]);
            form_data.append('FC_tiffs_OriginalNames[]', files[i].name);
            form_data.append('FC_tiffs_Name[]', "fc_" + $('#coll_name').val() + "_" + document.getElementsByClassName("years")[i].value + "_1ha.tif");
        }
        $.ajax({
            type: 'POST',
            url: '/savetomodel/',
            data: form_data,
            contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
            processData: false,
            success: function (data) {
                console.log(data);
                if (data.result == "success")
                    console.log('Success!');
                else {
                    document.getElementById("list").innerHTML = "";
                    alert(data.error_message)

                }
            },
        });
        let yrs = document.getElementsByClassName("years");
        for (var i = 0; i < yrs.length; i++) {
            yrs[i].value = '';
        }
        modal_new.style.display = "none";
    } else {
        alert("Change the collection name before submitting");
        modal_new.style.display = "none";
    }


});

function savetoLocalPath(btn) {
    if (btn.id === 'updatetoDB') {
        var upload_form = $('#upload-file')[0];
        var form_data = new FormData(upload_form);
        form_data.append('coll_name', $('#existing_list').find(":selected").val());
        let files = $('input[type=file]')[2].files;
        for (let i = 0; i < files.length; i++) {
            form_data.append('FC_tiffs_New[]', files[i]);
            form_data.append('FC_tiffs_New_OriginalNames[]', files[i].name);
            form_data.append('FC_tiffs_New_Name[]', "fc_" + $('#existing_list').find(":selected").val() + "_" + document.getElementsByClassName("years")[i].value + "_1ha.tif");
        }
        $.ajax({
            type: 'POST',
            url: '/updatetomodel/',
            data: form_data,
            contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
            processData: false,
            success: function (data) {
                console.log(data);
                if (data.result === "success")
                    console.log('Success!');
                else {
                    document.getElementById("existing_list").innerHTML = "";
                    alert(data.error_message)

                }
            },
        });

        // $('#myModal').hide();
        let yrs = document.getElementsByClassName("years");
        for (var i = 0; i < yrs.length; i++) {
            yrs[i].value = '';
        }
        modal.style.display = "none";
    }
}

$("#coll_name").on("keyup", function () {
    var coll = $(this).val().trim();
    $.ajax({
        type: 'POST',
        url: '/check_if_coll_exists/',
        data: {
            "coll_name": coll,
        },
        success: function (data) {
            if (data.result === "success") {
                document.getElementById("col_exists").innerHTML = "";
            } else {
                document.getElementById("col_exists").innerHTML = "Collection Exists, please choose a different name.";
            }
        }
    });
});
document.getElementById("tifffiles").onchange = () => {
    if (document.getElementById("list"))
        document.getElementById("list").innerHTML = "";
    let ul = document.getElementById("list");
    let files = document.getElementById("tifffiles").files;
    for (let i = 0; i < files.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode("Year for " + files[i].name));
        li.appendChild(document.createElement("br"));
        ul.appendChild(li);
        var input = document.createElement('input');
        input.className = "years form-control";
        input.type = "number";


        li.appendChild(input);
    }

}


document.getElementById("new_tifffiles").onchange = () => {
    if (document.getElementById("list_new_added"))
        document.getElementById("list_new_added").innerHTML = "";
    let ul = document.getElementById("list_new_added");
    let files = document.getElementById("new_tifffiles").files;
    for (let i = 0; i < files.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode("Enter the year for the file " + files[i].name + ':'));
        ul.appendChild(li);
        var input = document.createElement('input');
        input.className = "years";
        input.type = "text";
        li.appendChild(input);
    }
}

// function checkboxSelected(checkbox) {
//     if (checkbox.checked && checkbox.id === "new_c") {
//         document.getElementById("new_collection_info").style.display = "block";
//     } else {
//         document.getElementById("new_collection_info").style.display = "none";
//
//     }
//     if (checkbox.checked && checkbox.id === "existing_c") {
//         populateCollections();
//         document.getElementById("existing_coll").style.display = "block";
//     } else {
//         document.getElementById("existing_coll").style.display = "none";
//
//     }
// }

// Get the modal
var modal_new = document.getElementById("myModal");

// Get the button that opens the modal
var btn_new = document.getElementById("review_new");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks the button, open the modal
btn_new.onclick = function () {
    var coll = $('#coll_name').val().trim();
    $.ajax({
        type: 'POST',
        url: '/check_if_coll_exists/',
        data: {
            "coll_name": coll,
        },
        success: function (data) {
            if (data.result === "success") {
                document.getElementById("col_exists").innerHTML = "";

                document.getElementById("c_tiffs").innerHTML = "";
                modal_new.style.display = "block";
                var coll_name = document.getElementById("coll_name").value;
                document.getElementById("c_name").innerHTML = coll_name;
                document.getElementById("c_desc").innerHTML = document.getElementById("coll_desc").value;
                document.getElementById("c_boundary_path").innerHTML = document.getElementById("boundaryFile").value;
                let files = document.getElementById("tifffiles").files;
                var ul = document.createElement('ul');
                for (let i = 0; i < files.length; i++) {
                    let li = document.createElement("li");
                    li.appendChild(document.createTextNode(files[i].name + " -> " + "fc_" + coll_name + "_" + document.getElementsByClassName("years")[i].value + "_1ha.tif"));
                    ul.appendChild(li);
                }
                var tiffs = document.getElementById("c_tiffs");
                tiffs.appendChild(ul);

                var e = document.getElementById("access");
                var text = e.options[e.selectedIndex].text;
                document.getElementById("c_access").innerHTML = text;
            } else {
                modal_new.style.display = "none";

                document.getElementById("col_exists").innerHTML = "Collection Exists, please choose a different name.";

            }
        }
    });


}

// When the user clicks on <span> (x), close the modal
span.onclick = function () {
    modal_new.style.display = "none";
}


// Get the modal
var modal = document.getElementById("mynewModal");

// Get the button that opens the modal
var btn = document.getElementById("review_existing");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[1];

// When the user clicks the button, open the modal
btn.onclick = function () {

    modal.style.display = "block";
    var coll_name = ($("#existing_list").find(":selected").val());

    document.getElementById("c_update_name").innerHTML = coll_name;

    let files = document.getElementById("new_tifffiles").files;
    var ul = document.createElement('ul');
    for (let i = 0; i < files.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(files[i].name + " -> " + "fc_" + coll_name + "_" + document.getElementsByClassName("years")[i].value + "_1ha.tif"));
        ul.appendChild(li);
    }
    var tiffs = document.getElementById("c_new_tiffs");
    tiffs.innerHTML = "";
    tiffs.appendChild(ul);
    var etiffs = document.getElementById("c_existing_tiffs");
    etiffs.appendChild(document.getElementById('list_existing'));

}


// When the user clicks on <span> (x), close the modal
span.onclick = function () {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }

}


function populateCollections() {
    document.getElementById("existing_list").innerHTML = "";
    var el = document.createElement("option");
    el.textContent = '--Select--';
    el.value = '--Select--';
    document.getElementById("existing_list").appendChild(el);
    $.ajax({
        type: 'POST',
        url: '/getcollections/',
        success: function (data) {
            console.log(data);
            var select = document.getElementById("existing_list");
            var options = data.coll;

            for (var i = 0; i < options.length; i++) {
                var opt = options[i];
                var el = document.createElement("option");
                el.textContent = opt;
                el.value = opt;
                select.appendChild(el);
            }
            console.log('Success!');
        },
    });
}

$('#existing_list').on('change', function () {
    // document.getElementById("lists").style.display="block";
    var x = document.getElementById('list_existing');
    if (x)
        x.remove();
    var coll_name = ($(this).find(":selected").val());
    console.log(coll_name);
    $.ajax({
        type: 'POST',
        url: '/getfilesfromcollection/', data: {"coll_name": coll_name},
        success: function (data) {
            console.log(data);
            var files = data.tiffs;

            var ul = document.createElement('ul');
            ul.id = 'list_existing';
            for (let i = 0; i < files.length; i++) {
                let li = document.createElement("li");
                li.appendChild(document.createTextNode(files[i]));
                ul.appendChild(li);
            }
            var parent = document.getElementById("lists");
            parent.appendChild(ul);
            console.log('Success!');
        },


    });

});

// function updatecollection(){
//      let files = document.getElementById("tifffiles").files;
//  var tiffs=[];
//     for (let i = 0; i < files.length; i++) {
//        tiffs.push("fc_"+$('#coll_name').val()+"_"+document.getElementsByClassName("years")[i].value+"_1ha.tif");
//     }
//     console.log(tiffs)
//     $.ajax({
//         type: 'POST',
//         url: '/updatecollection/',
//         data: {
//             "tiffs":tiffs
//
//
//         },
//
//         success: function (data) {
//             console.log('Success!');
//         },
//     });
// }

// function checkforduplicates(aoiuploads){
// return aoiuploads.find(function(existingFile) {
//     return (
//       existingFile.name         === file.name &&
//       existingFile.lastModified === file.lastModified &&
//       existingFile.size         === file.size &&
//       existingFile.type         === file.type
//     )
//   })
// }

function clearForm() {
    document.getElementById("list").innerHTML = "";

    document.getElementById("upload-file").reset();
}