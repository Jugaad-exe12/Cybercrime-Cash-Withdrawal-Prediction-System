document.addEventListener("DOMContentLoaded", function () {

    const loginBtn = document.getElementById("loginBtn");
    const loginForm = document.getElementById("loginForm");
    const closeLogin = document.getElementById("closeLogin");

    loginBtn.addEventListener("click", function (event) {
        event.preventDefault();
        loginForm.style.display = "block";
    });

    closeLogin.addEventListener("click", function () {
        loginForm.style.display = "none";
    });

    loginForm.addEventListener("submit", function (event){
        event.preventDefault();
        alert("Login Successfull");
        loginForm.style.display = "none";
    });

    const aboutBtn = document.getElementById("aboutBtn");
    const aboutSection = document.getElementById("aboutSection");
    const closeAbout = document.getElementById("closeAbout");
    
    aboutBtn.addEventListener("click", function (event) {
        event.preventDefault();
        aboutSection.style.display = "block";
        aboutSection.scrollIntoView({
            behavior : smooth
        });

        


    });

    closeAbout.addEventListener("click",function() {
        aboutSection.style.display = "none";
    })



});