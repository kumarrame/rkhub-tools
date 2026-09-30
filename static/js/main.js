/* ==========================================================================
   RKHUB Tools — main.js
   Theme toggle · Mobile nav · Ticker pause · Live search · Nav highlight
   Sticky header · Back-to-top
   ========================================================================== */

(function () {
  "use strict";

  var THEME_KEY = "rkhub-theme";

  /* ------------------------------------------------------------ helpers --- */

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  function normalize(str) {
    return (str || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")            // strip diacritics
      .replace(/[^\p{L}\p{N}\s]/gu, " ")          // drop punctuation
      .replace(/\s+/g, " ")
      .trim();
  }

  /* ============================================================= THEME === */

  function initTheme() {
    var root = document.documentElement;
    var btn = $("#themeToggle");
    if (!btn) return;

    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) { /* private mode */ }

    if (!saved) {
      saved = window.matchMedia &&
              window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    root.setAttribute("data-theme", saved);

    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* noop */ }
    });
  }

  /* ========================================================== MOBILE NAV === */

  function initNav() {
    var burger = $("#navBurger");
    var nav = $("#navMenu");
    if (!burger || !nav) return;

    function close() {
      nav.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
    }

    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.addEventListener("click", function (e) {
      if (e.target.closest(".nav__link")) close();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });

    document.addEventListener("click", function (e) {
      if (!nav.classList.contains("is-open")) return;
      if (!e.target.closest(".nav") && !e.target.closest(".nav-burger")) close();
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 900) close();
    });
  }

  /* ============================================================= TICKER === */

  function initTicker() {
    var track = $("#tickerTrack");
    var btn = $("#tickerBtn");
    var ticker = $(".ticker");
    if (!track || !btn || !ticker) return;

    // The track holds a duplicated list, so animating to -50% loops seamlessly.
    btn.addEventListener("click", function () {
      var paused = ticker.classList.toggle("is-paused");
      btn.setAttribute("aria-pressed", paused ? "true" : "false");
    });

    // Pause while the user is reading / hovering.
    ticker.addEventListener("mouseenter", function () { track.style.animationPlayState = "paused"; });
    ticker.addEventListener("mouseleave", function () {
      if (!ticker.classList.contains("is-paused")) track.style.animationPlayState = "running";
    });
  }

  /* ============================================================= SEARCH === */

  function initSearch() {
    var input = $("#toolSearch");
    var status = $("#searchStatus");
    if (!input) return;

    var cards = $$(".tool-card");
    var sections = $$("[data-section]");
    var resetBtn = null;

    if (status && !status.querySelector(".search-status__reset")) {
      resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.className = "btn btn--ghost search-status__reset";
      resetBtn.style.marginInlineStart = ".7rem";
      resetBtn.textContent = "Reset";
      resetBtn.addEventListener("click", function () {
        input.value = "";
        input.dispatchEvent(new Event("input"));
        input.focus();
      });
      status.appendChild(resetBtn);
    }

    function run() {
      var q = normalize(input.value);
      var matches = 0;

      cards.forEach(function (card) {
        var hay = normalize(card.getAttribute("data-search"));
        var hit = !q || hay.indexOf(q) !== -1;
        card.classList.toggle("is-hidden", !hit);
        if (hit) matches++;
      });

      sections.forEach(function (sec) {
        var any = sec.querySelectorAll(".tool-card:not(.is-hidden)").length > 0;
        sec.classList.toggle("is-hidden", !any);
      });

      if (!status) return;
      if (!q) {
        status.hidden = true;
        status.textContent = "";
        return;
      }
      status.hidden = false;
      status.textContent = matches
        ? matches + " tool(s) match \u201c" + input.value.trim() + "\u201d"
        : "No tool matched \u201c" + input.value.trim() + "\u201d \u2014 try a different keyword";
    }

    input.addEventListener("input", run);

    /* Pressing Enter must not submit the form.
       The template used to carry an inline onsubmit="return false;" but that
       needs 'unsafe-inline' in script-src, which the CSP forbids. The handler
       was dropped without being replaced here, so Enter performed a real form
       GET and reloaded the page, losing the filter. Bind it now instead. */
    var form = input.form || $("[data-search-form]");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        run();
        // Bring the first surviving result into view so Enter feels like it
        // did something, without yanking the page on an already-visible hit.
        var first = $(".tool-card:not(.is-hidden)");
        if (first) {
          var box = first.getBoundingClientRect();
          if (box.top < 0 || box.top > window.innerHeight) {
            first.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }
      });
    }

    // "/" focuses the search box.
    document.addEventListener("keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;
      if (e.key === "/" && !typing) {
        e.preventDefault();
        input.focus();
        input.select();
      }
      if (e.key === "Escape" && document.activeElement === input) {
        input.value = "";
        run();
        input.blur();
      }
    });

    run();
  }

  /* ======================================================= STICKY HEADER === */

  function initStickyHeader() {
    var nav = $("#navbar");
    var toTop = $("#toTop");
    if (!nav) return;

    function onScroll() {
      var y = window.scrollY || document.documentElement.scrollTop;
      nav.classList.toggle("is-stuck", y > 8);
      if (toTop) toTop.classList.toggle("is-visible", y > 420);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (toTop) {
      toTop.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }
  }

  /* ================================================== ACTIVE NAV HIGHLIGHT */

  function initNavHighlight() {
    var links = $$('.nav__link[href^="#"]');
    if (!links.length || !window.IntersectionObserver) return;

    var map = {};
    var targets = [];
    links.forEach(function (link) {
      var id = link.getAttribute("href").slice(1);
      var sec = document.getElementById(id);
      if (sec) { map[id] = link; targets.push(sec); }
    });
    if (!targets.length) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var link = map[entry.target.id];
        if (!link) return;
        if (entry.isIntersecting) {
          links.forEach(function (l) { l.classList.remove("is-active"); });
          link.classList.add("is-active");
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px", threshold: 0 });

    targets.forEach(function (t) { io.observe(t); });
  }

  /* ====================================================== SCROLL REVEAL === */

  function initReveal() {
    var targets = $$(".section-head, .contact-card, .howto, .result-box, .ws-stats, .privacy__inner");
    if (!targets.length) return;

    if (!window.IntersectionObserver) {
      targets.forEach(function (el) { el.classList.add("reveal", "is-in"); });
      return;
    }

    targets.forEach(function (el) { el.classList.add("reveal"); });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        // stagger siblings for a cascading feel
        var sibs = Array.prototype.slice.call(el.parentNode.children)
          .filter(function (n) { return n.classList && n.classList.contains("reveal"); });
        var i = Math.max(0, sibs.indexOf(el));
        el.style.transitionDelay = Math.min(i * 70, 350) + "ms";
        el.classList.add("is-in");
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });

    targets.forEach(function (el) { io.observe(el); });
  }

  /* ================================================ CARD INDEX STAGGER ==== */

  function initCardStagger() {
    $$(".card-grid").forEach(function (grid) {
      Array.prototype.slice.call(grid.children).forEach(function (card, i) {
        card.style.setProperty("--i", i);
      });
    });
  }

  /* ============================================ TOUCH TOOL-CARD RAIL ===== */

  /* The card's animated top rail is hover-driven on desktop. Touch devices
     never hover, so CSS keeps the rail visible but paused; resume it only for
     the cards actually on screen. All ~186 of them animating at once would
     repaint the whole grid on every frame. */
  /* ============================================= TOUCH / HOVER DETECTION === */

  /* The `(hover: none)` CSS feature is unreliable in practice — plenty of
     phones report `hover: hover`, and emulation can disagree with the real
     device. `maxTouchPoints` is the dependable signal, so decide once in JS
     and drive both the CSS and the observers off a class on <html>. */
  function isTouchDevice() {
    return (navigator.maxTouchPoints || 0) > 0 ||
           "ontouchstart" in window ||
           (window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
  }

  function initTouchFlag() {
    if (isTouchDevice()) document.documentElement.classList.add("is-touch");
  }

  /* An IntersectionObserver with no live reference is eligible for garbage
     collection, which silently kills its callbacks. Keep a module-level
     handle for the lifetime of the page. */
  var touchRailIO = null;

  function initTouchRail() {
    if (!document.documentElement.classList.contains("is-touch")) return;

    var cards = $$(".tool-card");
    if (!cards.length) return;

    if (!window.IntersectionObserver) {
      cards.forEach(function (c) { c.classList.add("is-visible"); });
      return;
    }

    touchRailIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.classList.toggle("is-visible", entry.isIntersecting);
      });
    }, { rootMargin: "80px 0px", threshold: 0 });

    cards.forEach(function (c) { touchRailIO.observe(c); });
  }

  /* ====================================================== TRUST SEAL ===== */

  function initTrustSeal() {
    var seal = document.getElementById("trustSeal");
    if (!seal) return;

    // reveal the whole block on scroll
    if (window.IntersectionObserver) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          seal.classList.add("is-in");
          io.unobserve(seal);
        });
      }, { threshold: 0.35 });
      io.observe(seal);
    } else {
      seal.classList.add("is-in");
    }

    // play the whole sequence once as soon as the user lands on the page
    setTimeout(function () { seal.classList.add("is-in"); }, 900);
  }

  /* ============================================================== BOOT ==== */

  function boot() {
    initTouchFlag();
    initTheme();
    initNav();
    initTicker();
    initSearch();
    initStickyHeader();
    initNavHighlight();
    initReveal();
    initCardStagger();
    initTouchRail();
    initTrustSeal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
