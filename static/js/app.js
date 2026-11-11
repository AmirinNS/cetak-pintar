// CetakKira — Progressive enhancement form behavior
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("worksheet-form");
    if (!form) return;

    const seedInput = document.getElementById("input-seed");
    const btnNewSeed = document.getElementById("btn-new-seed");
    const btnShare = document.getElementById("btn-share");
    const shareToast = document.getElementById("share-toast");
    const shareFallbackContainer = document.getElementById("share-fallback-container");
    const shareUrlInput = document.getElementById("share-url-input");
    const btnCopyFallback = document.getElementById("btn-copy-fallback");
    const errorSummary = document.getElementById("error-summary");

    // Reveal progressive-enhancement-only controls
    document.querySelectorAll(".js-show").forEach((el) => {
        el.classList.remove("d-none");
    });

    // Focus error summary if present
    if (errorSummary) {
        errorSummary.focus();
    }

    // Generate new random seed
    if (btnNewSeed && seedInput) {
        btnNewSeed.addEventListener("click", () => {
            const newSeed = Math.floor(Math.random() * 2147483648);
            seedInput.value = newSeed;
        });
    }

    // Dynamic topic options toggle
    const topicCheckboxes = document.querySelectorAll(".topic-checkbox");

    function updateTopicFieldsets() {
        const checkedTopics = new Set();
        topicCheckboxes.forEach((cb) => {
            const card = cb.closest(".topic-select-card");
            if (cb.checked) {
                checkedTopics.add(cb.value);
                if (card) card.classList.add("border-primary", "bg-primary-subtle", "text-primary-emphasis", "active");
            } else {
                if (card) card.classList.remove("border-primary", "bg-primary-subtle", "text-primary-emphasis", "active");
            }
        });

        const topics = ["grid", "count", "add", "sub", "sifir", "div"];
        topics.forEach((t) => {
            const fieldset = document.getElementById(`group-topic-${t}`);
            if (!fieldset) return;
            const isChecked = checkedTopics.has(t);
            if (isChecked) {
                fieldset.classList.remove("d-none");
                fieldset.querySelectorAll("input, select").forEach((el) => {
                    el.disabled = false;
                });
            } else {
                fieldset.classList.add("d-none");
                fieldset.querySelectorAll("input, select").forEach((el) => {
                    el.disabled = true;
                });
            }
        });

        // Sifir tables reference group (shared between sifir_ref and sifir)
        const sifirRefFieldset = document.getElementById("group-topic-sifir_ref");
        if (sifirRefFieldset) {
            const hasSifir = checkedTopics.has("sifir_ref") || checkedTopics.has("sifir");
            if (hasSifir) {
                sifirRefFieldset.classList.remove("d-none");
                sifirRefFieldset.querySelectorAll("input, select").forEach((el) => {
                    el.disabled = false;
                });
            } else {
                sifirRefFieldset.classList.add("d-none");
                sifirRefFieldset.querySelectorAll("input, select").forEach((el) => {
                    el.disabled = true;
                });
            }
        }
    }

    // Initialize fieldset visibility and disabled state on DOM ready
    updateTopicFieldsets();

    topicCheckboxes.forEach((cb) => {
        cb.addEventListener("change", updateTopicFieldsets);
    });

    // Helper to serialize form into URLSearchParams preserving empty sentinels
    function serializeFormState(overrideLang = null) {
        const formData = new FormData(form);
        const searchParams = new URLSearchParams();

        // Topic multi-values
        const topics = [];
        formData.getAll("t").forEach((t) => {
            if (t.trim() !== "") topics.push(t.trim());
        });
        if (topics.length > 0) {
            searchParams.set("t", topics.join(","));
        } else {
            searchParams.set("t", "");
        }

        const checkedTopics = new Set(topics);

        // Language
        const currentLang = overrideLang || (formData.has("lang") ? formData.get("lang") : "ms");
        searchParams.set("lang", currentLang);

        // Seed
        if (formData.has("seed")) {
            searchParams.set("seed", formData.get("seed").trim());
        }

        // Single fields
        ["pages", "ans"].forEach((key) => {
            if (formData.has(key)) {
                searchParams.set(key, formData.get(key));
            }
        });

        if (checkedTopics.has("grid")) {
            ["grid_start", "grid_blanks"].forEach((key) => {
                if (formData.has(key)) searchParams.set(key, formData.get(key));
            });
        }

        if (checkedTopics.has("count")) {
            if (formData.has("count_max")) {
                searchParams.set("count_max", formData.get("count_max"));
            }
            const shapes = formData.getAll("count_shapes").filter((s) => s.trim() !== "");
            searchParams.set("count_shapes", shapes.join(","));
        }

        if (checkedTopics.has("add")) {
            ["add_digits", "add_regroup"].forEach((key) => {
                if (formData.has(key)) searchParams.set(key, formData.get(key));
            });
        }

        if (checkedTopics.has("sub")) {
            ["sub_digits", "sub_borrow"].forEach((key) => {
                if (formData.has(key)) searchParams.set(key, formData.get(key));
            });
        }

        if (checkedTopics.has("sifir_ref") || checkedTopics.has("sifir")) {
            const tables = formData.getAll("sifir_tables").filter((t) => t.trim() !== "");
            searchParams.set("sifir_tables", tables.join(","));
        }

        if (checkedTopics.has("sifir")) {
            if (formData.has("sifir_n")) {
                searchParams.set("sifir_n", formData.get("sifir_n"));
            }
        }

        if (checkedTopics.has("div")) {
            if (formData.has("div_digits")) {
                searchParams.set("div_digits", formData.get("div_digits"));
            }
            const divs = formData.getAll("div_divisors").filter((d) => d.trim() !== "");
            searchParams.set("div_divisors", divs.join(","));
            if (formData.has("div_rem")) {
                searchParams.set("div_rem", formData.get("div_rem"));
            }
        }

        return searchParams;
    }

    // Language switcher link handlers: serialize current form controls with target language
    document.querySelectorAll("a[data-lang]").forEach((link) => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetLang = link.getAttribute("data-lang");
            const searchParams = serializeFormState(targetLang);
            window.location.href = `/?${searchParams.toString()}`;
        });
    });

    // Share link serializer
    function buildCurrentShareUrl() {
        const searchParams = serializeFormState();
        const origin = window.location.origin;
        return `${origin}/?${searchParams.toString()}`;
    }

    function showShareFallback(url) {
        if (!shareFallbackContainer || !shareUrlInput) return;
        shareUrlInput.value = url;
        shareFallbackContainer.classList.remove("d-none");
        shareUrlInput.focus();
        shareUrlInput.select();
    }

    function showToastNotification() {
        if (!shareToast) return;
        shareToast.classList.remove("d-none");
        shareToast.classList.add("d-inline-flex");
        setTimeout(() => {
            shareToast.classList.remove("d-inline-flex");
            shareToast.classList.add("d-none");
        }, 3000);
    }

    if (btnShare) {
        btnShare.addEventListener("click", () => {
            const url = buildCurrentShareUrl();
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(url).then(() => {
                    showToastNotification();
                }).catch(() => {
                    showShareFallback(url);
                });
            } else {
                showShareFallback(url);
            }
        });
    }

    if (btnCopyFallback && shareUrlInput) {
        btnCopyFallback.addEventListener("click", () => {
            shareUrlInput.select();
            try {
                document.execCommand("copy");
                showToastNotification();
            } catch (err) {
                // Ignore fallback copy error
            }
        });
    }
});
