// Admin view: Helper functions for manually uploading event documents via a URL or PDF.
function full_text_doc_url_js(url, base_url) {
    encoded_url = encodeURIComponent(url)
    doc_url = base_url + '?filename=agenda&document_url=' + encoded_url

    return doc_url
};

function previewPDF(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            // Show buttons and preview
            $('#pdf-form-message, #pdf-check-viewer-test, #pdf-form-cancel, #pdf-form-submit').removeClass('hidden');
            document.getElementById('pdf-check-viewer-test').src = e.target.result
        }

        reader.readAsDataURL(input.files[0]);
    }
};

function getCookie(name) {
    // Get value of a cookie by name
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function contactTranslationAPI(document_id, entity_type) {
    // Hit our own api to ask the translation suite for available links
    return fetch(`/api/translations/${document_id}/`, {
            headers: { "X-CSRFToken": getCookie("csrftoken"), "Content-Type": "application/x-www-form-urlencoded" },
            method: "POST",
            body: new URLSearchParams({ "entity_type": entity_type }),
        })
        .then(r => r.json())
}

class IndexTranslationUtils {
    static renderLinks(linksArr, file_format, meeting_id) {
        // Display links to translations as li's within a bootstrap accordion element
        if (linksArr.length > 0) {
            const agendaList = document.getElementById(`agenda-${file_format}-list-${meeting_id}`)
            const agendaDisplay = document.getElementById(`agenda-${file_format}s-display-${meeting_id}`)

            const fileLinks = linksArr.map(file => {
                const linkEl = document.createElement("li")
                linkEl.classList.add("list-group-item")
                linkEl.innerHTML = `<a href="${file.url}" target="_blank">${file.link_text}</a>`
                agendaList.appendChild(linkEl)
            })
            agendaDisplay.classList.remove("d-none")
        }
    }

    static findTranslations(document_id, meeting_id) {
        // Either show translations if any are available, or tell user none exist.
        contactTranslationAPI(document_id, "event")
        .then(data => {
            const messageEl = document.getElementById(`checking-message-${meeting_id}`)
            if (data.document_pdfs.length == 0 && data.document_rtfs.length == 0) {
                messageEl.innerHTML = `<p><em>No translations found for this agenda.</em></p>`
            } else {
                messageEl.classList.add("d-none")
                this.renderLinks(data.document_pdfs, "pdf", meeting_id)
                this.renderLinks(data.document_rtfs, "rtf", meeting_id)
            }
        })
    }
}

class DetailPageTranslationUtils {
    static renderLinks(linksArr, file_format, document_type) {
        // Display links to translations as consecutive anchor tags,
        // with a separator in between each
        if (linksArr.length > 0) {
            // Special treatment for English RTF
            // Languages are ordered so English will always be first
            if (file_format === "rtf") {
                const [engFile] = linksArr.splice(0,1)
                const rtfDisplay = document.getElementById(`english-${document_type}-rtf-display`)
                const linkEl = document.createElement("a")
                linkEl.href = engFile.url
                linkEl.target = "_blank"
                linkEl.innerHTML = engFile.link_text + "(RTF)"
                rtfDisplay.appendChild(linkEl)
                rtfDisplay.classList.remove("d-none")
            }

            const translationList = document.getElementById(`${document_type}-${file_format}s`)
            const translationDisplay = document.getElementById(`${document_type}-${file_format}-display`)
            const separator = document.createElement("span")
            separator.classList.add("mx-1")
            separator.innerHTML = "|"

            linksArr.map((file, index, array) => {

                const linkEl = document.createElement("a")
                linkEl.href = file.url
                linkEl.target = "_blank"
                linkEl.innerHTML = file.link_text
                translationList.appendChild(linkEl)
                if (index < array.length - 1) {
                    translationList.appendChild(separator.cloneNode(true))
                }
            })
            translationDisplay.classList.remove("d-none")
        }
    }

    static findTranslations(document_id, entity_type) {
        // Either show translations if any are available, or tell user none exist.
        const document_type = entity_type == "event" ? "agenda" : "board-report"

        contactTranslationAPI(document_id, entity_type)
        .then(data => {
            const messageEl = document.getElementById(`checking-message`)
            if (data.document_pdfs.length == 0 && data.document_rtfs.length == 0) {
                messageEl.innerHTML = `<p><em>No translations found for this ${document_type}.</em></p>`
            } else {
                messageEl.classList.add("d-none")
                this.renderLinks(data.document_pdfs, "pdf", document_type)
                this.renderLinks(data.document_rtfs, "rtf", document_type)
            }
        })
    }
}
