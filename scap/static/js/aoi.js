update_aois();
document.getElementById("aoifiles").onchange = () => {
    console.log("uplaoded")
    if (document.getElementById("aoi_list"))
        document.getElementById("aoi_list").innerHTML = "";
    let ul = document.getElementById("aoi_list");
    let files = document.getElementById("aoifiles").files;
    console.log(files)
    for (let i = 0; i < files.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode("Enter the  name for the file " + files[i].name + ':'));
        ul.appendChild(li);
        var input = document.createElement('input');
        input.className = "aoi_names";
        input.type = "text";
        li.appendChild(input);
    }
}

// Get the modal
var modal_aoi = document.getElementById("aoiModal");

// Get the button that opens the modal
var btn_aoi = document.getElementById("review_aois");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks the button, open the modal
btn_aoi.onclick = function () {
    document.getElementById("c_aoi_names").innerHTML = "";
    modal_aoi.style.display = "block";


    let files = document.getElementById("aoifiles").files;
    // alert(checkforduplicates(files);
    var ul = document.createElement('ul');
    for (let i = 0; i < files.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(files[i].name + " -> " + document.getElementsByClassName("aoi_names")[i].value + ".zip"));
        ul.appendChild(li);
    }
    var aoi_names = document.getElementById("c_aoi_names");
    aoi_names.appendChild(ul);


}
span.onclick = function () {
    modal_aoi.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
    if (event.target == modal_aoi) {
        modal_aoi.style.display = "none";
    }

}
$("#storeAOI").click(function (e) {
    e.preventDefault();
    var upload_form = $('#upload-aoi')[0];
    var form_data = new FormData(upload_form);
        let files = $('input[type=file]')[0].files;
        for (let i = 0; i < files.length; i++) {
            form_data.append('aois[]', files[i]);
            form_data.append('aoi_names[]',  document.getElementsByClassName("aoi_names")[i].value);
        }
        $.ajax({
            type: 'POST',
            url: '/saveAOItomodel/',
            data: form_data,
            contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
            processData: false,
            success: function (data) {
                console.log(data);
                if (data.result == "success") {
                    console.log('Success!');
                            modal_aoi.style.display = "none";
        update_aois();

                }
                else
                    alert(data.error_message)
            },
        });
        let yrs = document.getElementsByClassName("aoi_names");
        for (var i = 0; i < yrs.length; i++) {
            yrs[i].value = '';
        }
                          document.getElementById("aoi_list").innerHTML="";


});

function clearForm(){
                        document.getElementById("aoi_list").innerHTML="";

    document.getElementById("upload-aoi").reset();
}

function update_aois(){
    document.getElementById("aoi_table").innerHTML="";
      var newRow = document.createElement("tr");
                var td = document.createElement("th");
                td.innerHTML = "AOI Name";
                newRow.appendChild(td);
                 td = document.createElement("th");
                td.innerHTML = "Last Accessed On";
                                newRow.appendChild(td);

                td = document.createElement("th");
                td.innerHTML = "Delete AOI"
                ;
                newRow.appendChild(td);
                document.getElementById('aoi_table').appendChild(newRow);


    $.ajax({
        type: 'POST',
        url: '/get_aoi_list/', data: {},
        success: function (data) {
            console.log(data);
            var aois=data.names;

            var dates=data.last_accessed_on;

            for (var i = 0; i < aois.length; i++) {
                            var btn = document.createElement('input');

                btn.type = "button";
                btn.className = "btn_del";
                btn.value = "Delete";
                btn.id=aois[i];
                btn.addEventListener("click", deleteAOI);



                var td = document.createElement("td");
                td.appendChild(btn);
                var newRow = document.createElement("tr");
                var td_aoi = document.createElement("td");
                td_aoi.innerHTML = aois[i];
                var td_date = document.createElement("td");
                td_date.innerHTML = dates[i];
                newRow.appendChild(td_aoi);
                newRow.appendChild((td_date));
                newRow.appendChild(td);
                document.getElementById('aoi_table').appendChild(newRow);
            }

            console.log('Success!');
        },


    });
}
const deleteAOI = e => {
        $.ajax({
            type: 'POST',
            url: '/delete_AOI/', data: {'aoi_name':e.target.id},
            success: function (data) {
                console.log("msg")
                update_aois();
            }
        });
}