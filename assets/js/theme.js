(() => {
    const root = document.documentElement;
    const storageKey = "site-theme";
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

    let savedTheme = null;

    try {
        savedTheme = localStorage.getItem(storageKey);
    } catch {
        // The site still works if storage is unavailable.
    }

    root.dataset.theme =
        savedTheme === "dark" || savedTheme === "light"
            ? savedTheme
            : prefersDark.matches
              ? "dark"
              : "light";

    function saveTheme(theme) {
        try {
            localStorage.setItem(storageKey, theme);
        } catch {
            // Ignore storage failures and keep the theme for this page.
        }
    }

    function addThemeToggle() {
        const nav = document.querySelector(".site-header nav");

        if (!nav) {
            return;
        }

        const button = document.createElement("button");
        button.type = "button";
        button.className = "theme-toggle";

        button.innerHTML = `
            <span class="theme-icon theme-icon-moon" aria-hidden="true">
                <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
>
    <path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8a8.5 8.5 0 1 0 11.3 11.3Z"></path>
</svg>
            </span>

            <span class="theme-icon theme-icon-sun" aria-hidden="true">
                <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <circle cx="12" cy="12" r="3.5"></circle>
                    <path d="M12 2.5v2M12 19.5v2M4.5 4.5l1.4 1.4M18.1 18.1l1.4 1.4M2.5 12h2M19.5 12h2M4.5 19.5l1.4-1.4M18.1 5.9l1.4-1.4"></path>
                </svg>
            </span>
        `;

        function updateButton() {
            const isDark = root.dataset.theme === "dark";

            button.setAttribute(
                "aria-label",
                isDark ? "Switch to light theme" : "Switch to dark theme",
            );

            button.setAttribute(
                "title",
                isDark ? "Switch to light theme" : "Switch to dark theme",
            );

            button.setAttribute("aria-pressed", String(isDark));
        }

        button.addEventListener("click", () => {
            root.dataset.theme =
                root.dataset.theme === "dark" ? "light" : "dark";

            saveTheme(root.dataset.theme);
            updateButton();
        });

        updateButton();
        nav.appendChild(button);
    }

    document.addEventListener("DOMContentLoaded", addThemeToggle);
})();
