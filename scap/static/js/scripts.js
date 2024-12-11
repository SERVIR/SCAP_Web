/*!
* Start Bootstrap - Agency v7.0.12 (https://startbootstrap.com/theme/agency)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-agency/blob/master/LICENSE)
*/
//
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink function
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
        }

    };

    // Shrink the navbar 
    navbarShrink();

    // Shrink the navbar when page is scrolled
    document.addEventListener('scroll', navbarShrink);

    //  Activate Bootstrap scrollspy on the main nav element
    const mainNav = document.body.querySelector('#mainNav');
    if (mainNav) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#mainNav',
            rootMargin: '0px 0px -40%',
        });
    }
    ;

    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });

});


var table = document.getElementById("myTable");
for (var i = 1;i<=table.rows.length; i++) {

    //iterate through rows
    var mainrow = table.rows[i];
    if (mainrow !== undefined) {
        var ch1 = mainrow.getElementsByTagName('td')[0];

        var ch2 = ch1.children[0];
        if (window.location.href.indexOf("/aoi-collections/") > -1) {
            $.ajax({
                type: 'POST',
                url: 'get-aoi-ids/', data: {'aoi_name': ch2.textContent},
                success: function (data) {
                    console.log(data)

                    const ul = document.getElementById("list_of_aois" + "_" + data.aoi_coll_id);

                    for (var j = 0; j < data.aois.length; j++) {
                        var aoi_id = data.aois[j].id;
                        var aoi_name = data.aois[j].name;
                        if (aoi_id > 0) {


// Create a new LI element
                            const newLi = document.createElement("li");
                            newLi.style.width = '200px';

                            const anchor = document.createElement('a');

                            // Set the href attribute
                            anchor.href = window.location.origin + '/aoi/' + aoi_id + '/';
                            anchor.target = '_blank';
                            if (aoi_name.length < 13) {
                                // Set the text content of the anchor
                                anchor.textContent = "Go to AOI: " + aoi_name;
                            } else {
                                // Set the text content of the anchor
                                anchor.textContent = "Go to AOI: " + aoi_name.substr(0, 13) + '...';
                            }


                            // Append the anchor element to the li element
                            newLi.appendChild(anchor);

// Append the new LI element to the UL element
                            if (ul !== null)
                                ul.appendChild(newLi);
                        }
                    }

                }
            });
        }
    }


}




//
// const ul = document.getElementById("list_of_aois");
//
// // Create a new LI element
// const newLi = document.createElement("li");
//
// const anchor = document.createElement('a');
//
//   // Set the href attribute
//   anchor.href = '#'; // Replace with the actual URL you want to link to
//   anchor.target='_blank';
//
//   // Set the text content of the anchor
//   anchor.textContent = newLi.textContent;
//
//   // Clear the existing content of the li element
//   newLi.innerHTML = '';
//
//   // Append the anchor element to the li element
//   newLi.appendChild(anchor);
//
// // Append the new LI element to the UL element
// ul.appendChild(newLi);