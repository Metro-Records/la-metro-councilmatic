const { IndexTranslationUtils, DetailPageTranslationUtils } = require("./utils")

describe("IndexTranslationUtils.renderLinks", () => {
    const fileFormat = "pdf"
    const meetingId = "123"

    beforeEach(() => {
        document.body.innerHTML = `
            <ul id="agenda-${fileFormat}-list-${meetingId}"></ul>
            <div id="agenda-${fileFormat}s-display-${meetingId}" class="d-none"></div>
        `
    })

    it("does nothing when linksArr is empty", () => {
        IndexTranslationUtils.renderLinks([], fileFormat, meetingId)

        const list = document.getElementById(`agenda-${fileFormat}-list-${meetingId}`)
        const display = document.getElementById(`agenda-${fileFormat}s-display-${meetingId}`)

        expect(list.children.length).toBe(0)
        expect(display.classList.contains("d-none")).toBe(true)
    })

    it("appends a list item per link and reveals the display", () => {
        const linksArr = [
            { url: "http://example.com/a.pdf", link_text: "English" },
            { url: "http://example.com/b.pdf", link_text: "Spanish" },
        ]

        IndexTranslationUtils.renderLinks(linksArr, fileFormat, meetingId)

        const list = document.getElementById(`agenda-${fileFormat}-list-${meetingId}`)
        const display = document.getElementById(`agenda-${fileFormat}s-display-${meetingId}`)

        expect(list.children.length).toBe(2)

        linksArr.forEach((file, index) => {
            const li = list.children[index]
            expect(li.classList.contains("list-group-item")).toBe(true)

            const anchor = li.querySelector("a")
            expect(anchor.getAttribute("href")).toBe(file.url)
            expect(anchor.getAttribute("target")).toBe("_blank")
            expect(anchor.textContent).toBe(file.link_text)
        })

        expect(display.classList.contains("d-none")).toBe(false)
    })
})

describe("DetailPageTranslationUtils.renderLinks", () => {
    const documentType = "agenda"

    function setupDom(fileFormat) {
        document.body.innerHTML = `
            <div id="${documentType}-${fileFormat}s"></div>
            <div id="${documentType}-${fileFormat}-display" class="d-none"></div>
            <div id="english-${documentType}-rtf-display" class="d-none"></div>
        `
    }

    it("does nothing when linksArr is empty", () => {
        setupDom("pdf")

        DetailPageTranslationUtils.renderLinks([], "pdf", documentType)

        const list = document.getElementById(`${documentType}-pdfs`)
        const display = document.getElementById(`${documentType}-pdf-display`)

        expect(list.children.length).toBe(0)
        expect(display.classList.contains("d-none")).toBe(true)
    })

    it("appends anchors with separators between links for non-rtf formats", () => {
        setupDom("pdf")

        const linksArr = [
            { url: "http://example.com/a.pdf", link_text: "English" },
            { url: "http://example.com/b.pdf", link_text: "Spanish" },
            { url: "http://example.com/c.pdf", link_text: "Chinese" },
        ]

        DetailPageTranslationUtils.renderLinks(linksArr, "pdf", documentType)

        const list = document.getElementById(`${documentType}-pdfs`)
        const display = document.getElementById(`${documentType}-pdf-display`)

        // 3 anchors + 2 separators
        expect(list.children.length).toBe(5)

        const anchors = list.querySelectorAll("a")
        expect(anchors.length).toBe(3)
        anchors.forEach((anchor, index) => {
            expect(anchor.getAttribute("href")).toBe(linksArr[index].url)
            expect(anchor.getAttribute("target")).toBe("_blank")
            expect(anchor.textContent).toBe(linksArr[index].link_text)
        })

        const separators = list.querySelectorAll("span.mx-1")
        expect(separators.length).toBe(2)
        separators.forEach(separator => expect(separator.textContent).toBe("|"))

        // No trailing separator after the last anchor
        expect(list.lastElementChild.tagName).toBe("A")

        expect(display.classList.contains("d-none")).toBe(false)
    })

    it("renders the English file separately and the rest normally for rtf format", () => {
        setupDom("rtf")

        const linksArr = [
            { url: "http://example.com/en.rtf", link_text: "English" },
            { url: "http://example.com/es.rtf", link_text: "Spanish" },
            { url: "http://example.com/zh.rtf", link_text: "Chinese" },
        ]

        DetailPageTranslationUtils.renderLinks(linksArr, "rtf", documentType)

        const englishDisplay = document.getElementById(`english-${documentType}-rtf-display`)
        const englishAnchor = englishDisplay.querySelector("a")
        expect(englishAnchor.getAttribute("href")).toBe("http://example.com/en.rtf")
        expect(englishAnchor.textContent).toBe("English(RTF)")
        expect(englishDisplay.classList.contains("d-none")).toBe(false)

        const list = document.getElementById(`${documentType}-rtfs`)
        const display = document.getElementById(`${documentType}-rtf-display`)

        // Remaining 2 anchors + 1 separator between them
        const anchors = list.querySelectorAll("a")
        expect(anchors.length).toBe(2)
        expect(anchors[0].textContent).toBe("Spanish")
        expect(anchors[1].textContent).toBe("Chinese")
        expect(list.querySelectorAll("span.mx-1").length).toBe(1)

        expect(display.classList.contains("d-none")).toBe(false)
    })
})
