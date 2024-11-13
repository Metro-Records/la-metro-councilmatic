function styleInputs(element) {
    $(element).removeClass()
    let description_input = $("#id_description")

    description_input.removeClass()
    if (element.value != "") {
        $(element).addClass("alert alert-" + element.value)
        description_input.addClass("alert alert-" + element.value)
    }
}

$(document).ready(styleInputs($("#id_type")[0]));

$("#id_type").on('change', function() {
    styleInputs(this)
});

$(".rich-text-btn").on('click', function() {
    let input = document.getElementById("id_description")

    switch(this.id.split('-')[1]) {
        case "link":
            input.value += ("[this is a link!](https://url.com) ")
            break;
        case "bold":
            input.value += ("**this is bolded text!** ")
            break;
        case "italic":
            input.value += ("*this is italicized text!* ")
            break;
        case "break":
            input.value += ("\n<br>\n")
            break;
    }
});
