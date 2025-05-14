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


function submitForm() {
    const profileForm = document.getElementById("addProfileForm");
    profileForm.submit();
}