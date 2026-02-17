document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault(); 

    let userid = document.getElementById("userid").value;
    let password = document.getElementById("password").value;

    fetch("", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ userid: userid, password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.redirect) {
            window.location.href = data.redirect; 
        } else {
            document.getElementById("message").textContent = data.message;
            document.getElementById("message").style.color = "red";
        }
    })
    .catch(error => console.error("Error:", error));
});


function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length, cookie.length);
            break;
        }
    }
    return cookieValue;
}
