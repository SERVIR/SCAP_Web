// Ajax call to get the data using the parameters: ajax_url and ajax_data
function ajax_call(ajax_url, ajax_data) {
    //update database
    console.log(ajax_data);
    return $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        url: ajax_url.replace(/\/?$/, '/'),
        dataType: "json",
        data: ajax_data
    })
        .fail(function (xhr, status, error) {
        });
}

function ajax_call_with_progress(ajax_url, ajax_data) {
    return $.ajax({
        url: ajax_url.replace(/\/?$/, '/'),
        type: "POST",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: ajax_data,        
        dataType: "json",
        xhr: function() {
            // get the native XMLHttpRequest object
            var xhr = $.ajaxSettings.xhr();

            // set the onprogress event handler
            xhr.onprogress = function(evt) {
                // evt.loaded is the number of bytes that have been received
                // evt.total is the total number of bytes that are expected to be received
		let expected_len = evt.total;
                if(expected_len == 0){
                    evt.currentTarget.getResponseHeader('Uncompressed-File-Size');
                }
                console.log('progress', evt.loaded / expected_len * 100);
            };

            // return the customized object
            return xhr;
        }
    });
}

// Set the parent div for a html object
function set_parent(control, element) {
    document.getElementById(element)
        .appendChild(control.getContainer());
}

/**
 * Checks to see if the cookie is set
 * @param name
 * @returns {null}
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

