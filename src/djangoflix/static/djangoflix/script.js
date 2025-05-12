console.log("JS is connected")

function showProfileForm() {
    const addProfileBtn = document.getElementById("addProfileBtn")
    const addProfileForm = document.getElementById("addProfileForm")
    addProfileBtn.classList.toggle("d-none")
    addProfileForm.classList.toggle("d-none")

}