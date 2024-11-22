ALERT_COLORS = {
	"primary": "#eb6864",
	"secondary": "#aaa",
	"success": "#22b24c",
	"danger": "#369",
	"warning": "#f5e625",
	"info": "#f57a00",
}

function styleParent(e) {
	if (e.target.classList.length > 0) {
		e.target.classList = ""
	}
	e.target.classList.add(`alert-${e.target.value}`);
}

// Callback function to execute when mutations are observed
const styleAlertTypeSelect = (mutationList, observer) => {
	mutationList.map(mu => {
		mu.addedNodes && mu.addedNodes.forEach(node => {
			if (node.id === "id_type") {
				styleParent({target: node})
				node.addEventListener("change", styleParent)
				observer.disconnect()
			}
		})
	})
};

// Create an observer instance linked to the callback function
const observer = new MutationObserver(styleAlertTypeSelect);

const config = {childList: true, subtree: true};

// Start observing the target node for configured mutations
observer.observe(document.body, config);
