try {
  document.documentElement.dataset.theme =
    localStorage.getItem("cirrus-theme") || "light";
} catch (_) {}
document
  .getElementById("print-label")
  ?.addEventListener("click", () => window.print());
document
  .getElementById("sidebar-scrim")
  ?.addEventListener("click", () => document.body.classList.remove("nav-open"));
document.querySelector(".password-toggle")?.addEventListener("click", (e) => {
  const field = document.querySelector("input[name=password]");
  field.type = field.type === "password" ? "text" : "password";
  e.currentTarget.setAttribute(
    "aria-label",
    field.type === "password" ? "Show password" : "Hide password",
  );
});
for (const button of document.querySelectorAll("[data-refresh-page]"))
  button.addEventListener("click", () => location.reload());
for (const form of document.querySelectorAll("form"))
  form.addEventListener("submit", () => {
    form.classList.add("is-submitting");
    form.setAttribute("aria-busy", "true");
  });
if (
  !matchMedia("(prefers-reduced-motion: reduce)").matches &&
  matchMedia("(pointer: fine)").matches
) {
  for (const art of document.querySelectorAll(
    ".pulse-hero,.asset-hero,.login-art",
  )) {
    art.addEventListener("pointermove", (e) => {
      const r = art.getBoundingClientRect();
      art.style.setProperty(
        "--mx",
        `${(e.clientX - r.left - r.width / 2) / 40}px`,
      );
      art.style.setProperty(
        "--my",
        `${(e.clientY - r.top - r.height / 2) / 40}px`,
      );
    });
    art.addEventListener("pointerleave", () => {
      art.style.setProperty("--mx", "0px");
      art.style.setProperty("--my", "0px");
    });
  }
}

const navigation = document.querySelector(".sidebar");
const compactNavigation = matchMedia("(max-width: 760px)");
function syncNavigation() {
  if (navigation)
    navigation.inert =
      compactNavigation.matches &&
      !document.body.classList.contains("nav-open");
}
syncNavigation();
compactNavigation.addEventListener("change", syncNavigation);
document
  .getElementById("sidebar-scrim")
  ?.addEventListener("click", syncNavigation);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.body.classList.remove("nav-open");
    syncNavigation();
  }
});
