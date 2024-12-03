document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("discussion-form");
    const postsContainer = document.getElementById("posts");

    // Load existing posts from localStorage
    function loadPosts() {
        const storedPosts = JSON.parse(localStorage.getItem("discussionPosts")) || [];
        storedPosts.forEach(post => addPostToDOM(post.username, post.content));
    }

    // Add a post to the DOM
    function addPostToDOM(username, content) {
        const postElement = document.createElement("div");
        postElement.classList.add("post");

        const usernameElement = document.createElement("h3");
        usernameElement.textContent = username;

        const contentElement = document.createElement("p");
        contentElement.textContent = content;

        postElement.appendChild(usernameElement);
        postElement.appendChild(contentElement);

        postsContainer.appendChild(postElement);
    }

    // Handle form submission
    form.addEventListener("submit", (e) => {
        e.preventDefault(); // Prevent form from reloading the page

        const username = document.getElementById("username").value.trim();
        const content = document.getElementById("post-content").value.trim();

        if (username && content) {
            addPostToDOM(username, content);

            // Save post to localStorage
            const storedPosts = JSON.parse(localStorage.getItem("discussionPosts")) || [];
            storedPosts.push({ username, content });
            localStorage.setItem("discussionPosts", JSON.stringify(storedPosts));

            // Clear form inputs
            form.reset();
        } else {
            alert("Please fill out both fields before submitting.");
        }
    });

    // Initial load of posts
    loadPosts();
});
