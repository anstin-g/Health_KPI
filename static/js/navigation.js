// navigation.js - Handles navigation functionality

document.addEventListener("DOMContentLoaded", function() {
    // Logo click navigation to home
    document.getElementById("logo").addEventListener("click", function() {
        window.location.href = "/home";  
    });
    
    // Logout functionality
    document.getElementById("logoutBtn").addEventListener("click", function() {
        window.location.href = "/";  
    });
});