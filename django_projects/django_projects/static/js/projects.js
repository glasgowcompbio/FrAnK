var images = new Array()
function preload() {
    for (i = 0; i < preload.arguments.length; i++) {
        images[i] = new Image()
        images[i].src = preload.arguments[i]
    }
}
preload(
    static_url + "img/PiMP_logo.gif"
)
$(function() {
    var loading = function() {
        // add the overlay with loading image to the page
        var over = '<div id="overlay">' +
            '<img id="loading_img" src="' + static_url + 'img/PiMP_logo.gif">' +
            '<p id="loading_text">Your data environment is being generated, please wait.<p>' +
            '</div>';
        $(over).appendTo('body');
    };
    $('.analysis_result_button').click(loading);
});
