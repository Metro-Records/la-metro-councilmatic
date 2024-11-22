ALERT_COLORS = {
	"primary": "#eb6864",
	"secondary": "#aaa",
	"success": "#22b24c",
	"danger": "#369",
	"warning": "#f5e625",
	"info": "#f57a00",
}

function styleParent(e) {
	console.log(e.target.classList)
	if (e.target.classList.length > 0) {
		e.target.classList = ""
	}
	e.target.classList.add(`alert-${e.target.value}`);
	//e.target.style.backgroundColor = ALERT_COLORS[e.target.value] || "unset"
	//e.target.style.color = "#333"
	//e.target.style.opacity = "0.5"
	//e.target.style.fontWeight = "700"
}

// Select the node that will be observed for mutations
const targetNode = document.body;

console.log(targetNode)

// Options for the observer (which mutations to observe)
const config = { childList: true, subtree: true };

// Callback function to execute when mutations are observed
const callback = (mutationList, observer) => {
	mutationList.map(mu => {
		mu.addedNodes && mu.addedNodes.forEach(node => {
			if (node.id === "id_type") {
				styleParent({target: node})
				node.addEventListener("change", styleParent)
				console.log("listening for changes")
			}
		})
	})
};

// Create an observer instance linked to the callback function
const observer = new MutationObserver(callback);

// Start observing the target node for configured mutations
observer.observe(targetNode, config);
