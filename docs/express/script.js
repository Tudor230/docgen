// API Documentation Interactive Features

document.addEventListener("DOMContentLoaded", function () {
  // Smooth scrolling for navigation links
  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href");
      console.log("Clicked link with href:", targetId); // Debug log
      const targetElement = document.querySelector(targetId);
      console.log("Found target element:", targetElement); // Debug log

      if (targetElement) {
        // Try multiple scrolling methods for better compatibility
        try {
          targetElement.scrollIntoView({
            behavior: "smooth",
            block: "start",
            inline: "nearest",
          });
        } catch (error) {
          // Fallback for older browsers
          console.log("Smooth scrolling not supported, using fallback");
          targetElement.scrollIntoView(true);
        }

        // Add a small delay before updating active state
        setTimeout(() => {
          updateActiveNavLink(this);
        }, 100);
      } else {
        console.error("Target element not found for:", targetId);
      }
    });
  });

  // Highlight active navigation item based on scroll position
  function updateActiveNavLink(activeLink = null) {
    navLinks.forEach((link) => {
      link.classList.remove("active");
    });

    if (activeLink) {
      activeLink.classList.add("active");
    }
  }

  // Intersection Observer for automatic active nav highlighting
  const endpoints = document.querySelectorAll(".endpoint");
  const observerOptions = {
    root: null,
    rootMargin: "-100px 0px -60% 0px",
    threshold: 0,
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        const correspondingNavLink = document.querySelector(`a[href="#${id}"]`);
        if (correspondingNavLink) {
          updateActiveNavLink(correspondingNavLink);
        }
      }
    });
  }, observerOptions);

  endpoints.forEach((endpoint) => {
    observer.observe(endpoint);
  });

  // Add copy functionality for endpoint paths
  const endpointPaths = document.querySelectorAll(".endpoint-path");
  endpointPaths.forEach((path) => {
    path.style.cursor = "pointer";
    path.title = "Click to copy";

    path.addEventListener("click", function () {
      navigator.clipboard.writeText(this.textContent).then(function () {
        // Show feedback
        const originalText = path.textContent;
        path.textContent = "Copied!";
        path.style.backgroundColor = "#48bb78";
        path.style.color = "white";

        setTimeout(() => {
          path.textContent = originalText;
          path.style.backgroundColor = "#f7fafc";
          path.style.color = "#2d3748";
        }, 1000);
      });
    });
  });

  // Search functionality (if we want to add it later)
  function initializeSearch() {
    // This could be implemented later for filtering endpoints
    console.log("Search functionality placeholder");
  }

  // Mobile menu toggle (if needed)
  function initializeMobileMenu() {
    const nav = document.querySelector(".navigation");
    if (window.innerWidth <= 768) {
      nav.style.maxHeight = "300px";
      nav.style.overflowY = "auto";
    }
  }

  // Initialize mobile optimizations
  initializeMobileMenu();

  // Handle window resize
  window.addEventListener("resize", function () {
    initializeMobileMenu();
  });

  // Add keyboard navigation
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      // Clear any active states
      updateActiveNavLink();
    }
  });
});

// Add active class styles
const style = document.createElement("style");
style.textContent = `
    .nav-link.active {
        background-color: #667eea !important;
        color: white !important;
    }
    
    .nav-link.active .method {
        background-color: rgba(255, 255, 255, 0.2);
    }
`;
document.head.appendChild(style);
