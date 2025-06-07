// carousels don't work on Opera
if (navigator.userAgent.includes("OPR")) {
    alert("You are using an unsupported browser!\nFor the best experience, we recommend Chrome, Firefox, or Edge.")
}

// Global vars needed for listeners
let navDropdownBtn;
let navDropdownContainer;

// These functions are for the nav dropdown
function handleOutsideClick(e) {
    if (
        !navDropdownContainer.contains(e.target)
        & !navDropdownBtn.contains(e.target)
    ) {
        toggleNavDropdown();
    }
}


function addClickListener() {
    document.addEventListener("click", handleOutsideClick);
}


function removeClickListener() {
    document.removeEventListener("click", handleOutsideClick);
}


function toggleNavDropdown(elem=false) {
    if (elem) {
        navDropdownBtn = elem;
        navDropdownContainer = document.getElementById("navDropdown");
    }

    navDropdownContainer.classList.toggle("d-none");
    
    if (!navDropdownContainer.classList.contains("d-none")) {
        navDropdownBtn.setAttribute("aria-expanded", "true");
        // using setTimeout to avoid double toggle from a mouseup event
        // being sent as click event on some browsers
        setTimeout(addClickListener, 25);
    }
    else {
        navDropdownBtn.setAttribute("aria-expanded", "false");
        removeClickListener();
    }
}


// These functions are for profile to toggle show/hide the ProfileForm
function toggleProfileForm(focus) {
    const addProfileBtn = document.getElementById("addProfileBtn");
    const addProfileFormDiv = document.getElementById("addProfileFormDiv");
    addProfileBtn.classList.toggle("d-none");
    addProfileFormDiv.classList.toggle("d-none");
    
    if (focus) {
        const nameElement = document.getElementById("id_profile_name");
        nameElement.focus();
    }
}


function submitForm(formId) {
    const profileForm = document.getElementById(formId);
    profileForm.submit();
}


// Select profile radio button from icon
function selectIcon(selectedIconBtn) {
    // Finds current selection & new selection
    // Toggles color of btn to white & blue respectively
    // Switches checked attribute to input for new selection
    //
    const targetInputId = selectedIconBtn.getAttribute("id").split("-")[0];
    const targetInput = document.getElementById(targetInputId);
    // if user clicked on current selection, do nothing
    if (targetInput.getAttribute("checked")) {
        return false;
    }
    const currentIconBtn = document.querySelector(".btn-outline-primary");
    const currentInputId = currentIconBtn.getAttribute("id").split("-")[0];
    const currentInput = document.getElementById(currentInputId);
    // toggle checked first, then update colors
    currentInput.toggleAttribute("checked");
    targetInput.toggleAttribute("checked");
    currentIconBtn.classList.remove("btn-outline-primary");
    currentIconBtn.classList.add("btn-outline-light");
    selectedIconBtn.classList.remove("btn-outline-light");
    selectedIconBtn.classList.add("btn-outline-primary");
}

// toggle show/hide watch & view content icons on hover
function toggleIcons(elem) {
    // if image is clipped, do nothing
    if (
        elem.getBoundingClientRect().right > 
        elem.parentElement.getBoundingClientRect().right
        || elem.getBoundingClientRect().left <
        elem.parentElement.getBoundingClientRect().left
    ) {
        return;
    }
    const watchEl = document.getElementById(elem.getAttribute("id") + "-watch");
    const viewEl = document.getElementById(elem.getAttribute("id") + "-view");
    watchEl.classList.toggle("d-none");
    viewEl.classList.toggle("d-none");
}

//toggle favorite
function toggleFavorite(element) {
    contentId = element.getAttribute("id");
    console.log("toggling favorite");
    // POST to /djangoflix/favorite/<id>
}

// Season select
function toggleEpisodes(elem) {
    seasonId = elem.value;
    console.log(`seasonId: ${seasonId}`);
    current = document.querySelector(".selected");
    console.log(`current: ${current}`);
    selected = document.getElementById(seasonId + "Episodes");
    console.log(`selected ${selected}`);
    current.classList.remove("selected");
    current.classList.add("d-none");
    selected.classList.remove("d-none");
    selected.classList.add("selected");
}

// toggle watch icon for Episodes on view_details.html
function toggleWatchIcon(elem) {
    const watchEl = document.getElementById(elem.getAttribute("id") + "-watch");
    watchEl.classList.toggle("d-none");
}