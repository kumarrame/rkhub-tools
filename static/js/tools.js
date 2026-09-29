/* ==========================================================================
   RKHUB Tools — tools.js
   Every engine runs entirely in the browser (FileReader + Canvas + Blob).
   NOTHING is ever uploaded to the server.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.getElementById("workspace");
  if (!root) return;

  var SLUG = root.getAttribute("data-tool");

  /* ======================================================== helpers ======= */

  function $(id) { return document.getElementById(id); }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) return resolve();
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("Failed to load " + src)); };
      document.head.appendChild(s);
    });
  }

  function fmtBytes(n) {
    if (!isFinite(n) || n < 0) return "—";
    if (n === 0) return "0 B";
    var units = ["B", "KB", "MB", "GB", "TB"];
    var i = Math.floor(Math.log(n) / Math.log(1024));
    i = Math.min(i, units.length - 1);
    return (n / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 2) + " " + units[i];
  }

  function inr(n) {
    if (!isFinite(n)) return "—";
    return "₹" + Math.round(n).toLocaleString("en-IN");
  }

  function downloadURL(url, filename) {
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  function downloadCanvas(canvas, filename, type, quality) {
    canvas.toBlob(function (blob) {
      var url = URL.createObjectURL(blob);
      downloadURL(url, filename);
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }, type || "image/png", quality);
  }

  function readImage(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () { resolve({ img: img, url: url }); };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error("Image load failed")); };
      img.src = url;
    });
  }

  function readBuffer(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = function () { reject(fr.error); };
      fr.readAsArrayBuffer(file);
    });
  }

  function readDataURL(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = function () { reject(fr.error); };
      fr.readAsDataURL(file);
    });
  }

  /* cssFilter string from brightness/contrast percentages */
  function cssFilter(brightness, contrast) {
    return "brightness(" + brightness + "%) contrast(" + contrast + "%)";
  }

  function mountCanvas(container, w, h) {
    container.innerHTML = "";
    var c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    container.appendChild(c);
    return c;
  }

  /* letterbox an image into a target box (cover-fit) */
  function drawCover(ctx, img, tx, ty, tw, th) {
    var scale = Math.max(tw / img.naturalWidth, th / img.naturalHeight);
    var w = img.naturalWidth * scale;
    var h = img.naturalHeight * scale;
    ctx.drawImage(img, tx + (tw - w) / 2, ty + (th - h) / 2, w, h);
  }

  function bindRange(id, outId, format) {
    var el = $(id), out = $(outId);
    if (!el || !out) return function () { return parseFloat(el.value); };
    function sync() { out.textContent = format(parseFloat(el.value)); }
    el.addEventListener("input", sync);
    sync();
    return function () { return parseFloat(el.value); };
  }

  function show(el) { if (el) el.hidden = false; }
  function hide(el) { if (el) el.hidden = true; }

  function panelFor(slug) {
    return root.querySelector('[data-panel="' + slug + '"]');
  }

  /* ======================================================================
     FILE PICKER + DRAG & DROP  (shared by all file-based tools)
     ==================================================================== */

  function initFileInput(accept, onFiles) {
    var input = $("fileInput");
    var drop = $("dropZone");
    var pick = $("pickBtn");
    if (!input || !pick) return;

    if (accept) input.setAttribute("accept", accept);

    pick.addEventListener("click", function () { input.click(); });

    input.addEventListener("change", function () {
      if (input.files && input.files.length) onFiles(input.files);
    });

    if (!drop) return;

    ["dragenter", "dragover"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        drop.classList.add("is-drag");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        drop.classList.remove("is-drag");
      });
    });
    drop.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) onFiles(files);
    });

    // Prevent the browser from navigating away when a file is dropped
    // outside the zone.
    window.addEventListener("dragover", function (e) { e.preventDefault(); });
    window.addEventListener("drop", function (e) { e.preventDefault(); });
  }

  function bindReset(fn) {
    var btn = $("resetBtn");
    if (btn) btn.addEventListener("click", fn);
  }

  /* ======================================================================
     1. PASSPORT PHOTO MAKER  —  3.5 x 4.5 cm @ 300 DPI = 413 x 531 px
     ==================================================================== */

  function enginePassport() {
    var panel = panelFor("passport-photo");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var current = null;

    var PP_W = 413, PP_H = 531;
    var gBrightness = bindRange("ppBrightness", "ppBrightnessOut", function (v) { return v + "%"; });
    var gContrast = bindRange("ppContrast", "ppContrastOut", function (v) { return v + "%"; });
    var gZoom = bindRange("ppZoom", "ppZoomOut", function (v) { return v + "%"; });

    function bgColor() {
      var r = root.querySelector('input[name="ppBg"]:checked');
      return r ? r.value : "#FFFFFF";
    }

    function render() {
      if (!current) return;
      var canvas = mountCanvas(canvasWrap, PP_W, PP_H);
      var ctx = canvas.getContext("2d");
      var bg = bgColor();

      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, PP_W, PP_H);

      var img = current;
      var zoom = gZoom() / 100;
      var inner = { w: PP_W, h: PP_H };

      ctx.save();
      // zoom about the centre
      ctx.translate(PP_W / 2, PP_H / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-PP_W / 2, -PP_H / 2);
      ctx.filter = cssFilter(gBrightness(), gContrast());
      drawCover(ctx, img, 0, 0, inner.w, inner.h);
      ctx.restore();

      // thin border so the print sheet reads clearly
      ctx.strokeStyle = "rgba(0,0,0,.28)";
      ctx.lineWidth = 2;
      ctx.strokeRect(1, 1, PP_W - 2, PP_H - 2);
    }

    function rebuild() {
      var canvas = mountCanvas(canvasWrap, PP_W, PP_H);
      canvas.getContext("2d").fillStyle = "#FFFFFF";
      canvas.getContext("2d").fillRect(0, 0, PP_W, PP_H);
    }

    initFileInput("image/*", function (files) {
      readImage(files[0]).then(function (r) {
        current = r.img;
        show(panel);
        hide($("dropZone"));
        render();
        if (dl) dl.disabled = false;
      });
    });

    ["ppBrightness", "ppContrast", "ppZoom"].forEach(function (id) {
      $(id).addEventListener("input", render);
    });
    root.querySelectorAll('input[name="ppBg"]').forEach(function (r) {
      r.addEventListener("change", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (c) downloadCanvas(c, "passport-photo-3.5x4.5.png", "image/png");
      });
    }

    bindReset(function () {
      current = null;
      hide(panel);
      show($("dropZone"));
      rebuild();
      if (dl) dl.disabled = false;
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     2. PDF COMPRESSOR  —  pdf-lib: render pages, re-pack at lower DPI
     ==================================================================== */

  function enginePdfCompressor() {
    var panel = panelFor("pdf-compressor");
    var drop = $("dropZone");
    var btn = $("compressBtn");
    var pdfFile = null;
    var outBlob = null;

    var LEVELS = { light: 1.0, medium: 0.72, strong: 0.5 };
    var JPEGS = { light: 0.82, medium: 0.6, strong: 0.42 };

    function setStat(id, val) { var e = $(id); if (e) e.textContent = val; }

    initFileInput("application/pdf", function (files) {
      pdfFile = files[0];
      show(panel);
      setStat("pcOrig", fmtBytes(pdfFile.size));
      setStat("pcNew", "—");
      setStat("pcSaved", "—");
      setStat("pcPages", "—");
      if (btn) btn.disabled = false;
      if (drop) {
        var t = drop.querySelector(".ws-drop__sub");
        if (t) t.textContent = pdfFile.name + " — " + fmtBytes(pdfFile.size);
      }
    });

    if (btn) {
      btn.addEventListener("click", function () {
        if (!pdfFile) return;
        var level = ($("pcLevel") || {}).value || "medium";
        var scale = LEVELS[level];
        var quality = JPEGS[level];

        btn.disabled = true;
        var label = btn.innerHTML;
        btn.textContent = "Compressing…";

        loadScript("https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js")
          .then(function () {
            var PDFLib = window.PDFLib;
            if (!PDFLib) throw new Error("pdf-lib unavailable");

            return readBuffer(pdfFile).then(function (buf) {
              return PDFLib.PDFDocument.load(buf, { ignoreEncryption: true });
            }).then(function (src) {
              var out = PDFLib.PDFDocument.create();
              var pages = src.getPages();
              var chain = Promise.resolve();

              pages.forEach(function (page) {
                chain = chain.then(function () {
                  var vp0 = page.getViewport({ scale: 1 });
                  var vp = page.getViewport({ scale: scale });

                  var c = document.createElement("canvas");
                  c.width = Math.max(1, Math.floor(vp.width));
                  c.height = Math.max(1, Math.floor(vp.height));
                  var ctx = c.getContext("2d");
                  ctx.fillStyle = "#FFFFFF";
                  ctx.fillRect(0, 0, c.width, c.height);

                  return c.toBlob(function (blob) {
                    return readDataURL(blob).then(function (dataUrl) {
                      return out.embedJpg(dataUrl).then(function (jpg) {
                        var p = out.addPage([vp0.width, vp0.height]);
                        p.drawImage(jpg, { x: 0, y: 0, width: vp0.width, height: vp0.height });
                      });
                    });
                  }, "image/jpeg", quality);
                });
              });

              return chain.then(function () {
                setStat("pcPages", String(pages.length));
                return out.save();
              });
            });
          })
          .then(function (bytes) {
            outBlob = new Blob([bytes], { type: "application/pdf" });
            setStat("pcNew", fmtBytes(outBlob.size));
            var saved = pdfFile.size - outBlob.size;
            var pct = pdfFile.size ? (saved / pdfFile.size) * 100 : 0;
            setStat("pcSaved", (saved >= 0 ? fmtBytes(saved) + " (" + pct.toFixed(1) + "%)"
                                          : "GREW " + fmtBytes(-saved)));
          })
          .catch(function (err) {
            setStat("pcNew", "Failed");
            setStat("pcSaved", err && err.message ? err.message : "Error");
          })
          .then(function () {
            btn.disabled = false;
            btn.innerHTML = label;
          });
      });

      // second click downloads the already-compressed result
      btn.addEventListener("dblclick", function () {
        if (!outBlob) return;
        var url = URL.createObjectURL(outBlob);
        downloadURL(url, (pdfFile.name || "document").replace(/\.pdf$/i, "") + "-compressed.pdf");
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
      });
    }

    bindReset(function () {
      pdfFile = null; outBlob = null;
      hide(panel); show(drop);
      ["pcOrig", "pcNew", "pcSaved", "pcPages"].forEach(function (i) { setStat(i, "—"); });
      if (btn) btn.disabled = true;
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     3. IMAGE TO PDF  —  jsPDF
     ==================================================================== */

  function engineImageToPdf() {
    var panel = panelFor("image-to-pdf");
    var list = $("ipList");
    var btn = $("convertBtn");
    var files = [];

    var gMargin = bindRange("ipMargin", "ipMarginOut", function (v) { return v + " mm"; });

    function refreshList() {
      if (!list) return;
      list.innerHTML = "";
      files.forEach(function (f) {
        var li = document.createElement("li");
        var a = document.createElement("span");
        a.textContent = f.name;
        var b = document.createElement("span");
        b.textContent = fmtBytes(f.size);
        li.appendChild(a); li.appendChild(b);
        list.appendChild(li);
      });
      var c = $("ipCount");
      if (c) c.textContent = String(files.length);
      if (btn) btn.disabled = files.length === 0;
    }

    initFileInput("image/*", function (f) {
      files = Array.prototype.slice.call(f);
      show(panel);
      refreshList();
    });

    if (btn) {
      btn.addEventListener("click", function () {
        if (!files.length) return;
        var size = ($("ipPageSize") || {}).value || "a4";
        var orient = ($("ipOrientation") || {}).value || "p";
        var margin = gMargin();

        btn.disabled = true;
        var label = btn.innerHTML;
        btn.textContent = "Creating PDF…";

        loadScript("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js")
          .then(function () {
            var jsPDFctor = window.jspdf && window.jspdf.jsPDF;
            if (!jsPDFctor) throw new Error("jsPDF unavailable");

            var first = null;
            return readImage(files[0]).then(function (r) {
              first = r.img;
              if (size === "auto") {
                var w = first.naturalWidth, h = first.naturalHeight;
                var o = w > h ? "l" : "p";
                return createDoc(jsPDFctor, o, margin).then(function (doc) {
                  return addImages(doc, files, margin, true);
                });
              }
              return createDoc(jsPDFctor, orient, margin).then(function (doc) {
                return addImages(doc, files, margin, false);
              });
            });
          })
          .then(function (doc) {
            var blob = doc.output("blob");
            var url = URL.createObjectURL(blob);
            downloadURL(url, "rkhub-image-to-pdf.pdf");
            setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
          })
          .catch(function (err) {
            alert("PDF create failed: " + (err && err.message ? err.message : "unknown error"));
          })
          .then(function () {
            btn.disabled = files.length === 0;
            btn.innerHTML = label;
          });
      });
    }

    function createDoc(jsPDFctor, orient, margin) {
      var unit = "mm";
      var format = orient === "l" ? "a4" : "a4";
      var doc = new jsPDFctor({ unit: unit, format: format, orientation: orient });
      doc.setMargins(margin, margin, margin);
      return doc;
    }

    function addImages(doc, list, margin, autoSize) {
      var chain = Promise.resolve();
      var firstPage = true;
      list.forEach(function (f, idx) {
        chain = chain.then(function () {
          return readImage(f).then(function (r) {
            var img = r.img;
            var pw = doc.internal.pageSize.getWidth();
            var ph = doc.internal.pageSize.getHeight();
            var availW = pw - margin * 2;
            var availH = ph - margin * 2;
            var ratio = img.naturalWidth / img.naturalHeight;
            var w = availW;
            var h = w / ratio;
            if (h > availH) { h = availH; w = h * ratio; }
            var x = (pw - w) / 2;
            var y = (ph - h) / 2;
            if (!firstPage) doc.addPage();
            doc.addImage(img, "JPEG", x, y, w, h);
            firstPage = false;
            URL.revokeObjectURL(r.url);
          });
        });
      });
      return chain.then(function () { return doc; });
    }

    bindReset(function () {
      files = [];
      refreshList();
      hide(panel); show($("dropZone"));
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     4. SIGNATURE & THUMB EXTRACTOR  —  B&W via threshold
     ==================================================================== */

  function engineSignature() {
    var panel = panelFor("signature-extractor");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var current = null;

    var gBrightness = bindRange("seBrightness", "seBrightnessOut", function (v) { return String(v); });
    var gContrast = bindRange("seContrast", "seContrastOut", function (v) { return String(v); });
    var gThreshold = bindRange("seThreshold", "seThresholdOut", function (v) { return String(v); });

    function invert() {
      var e = $("seInvert");
      return !!(e && e.checked);
    }

    function render() {
      if (!current) return;
      var w = current.naturalWidth, h = current.naturalHeight;
      var canvas = mountCanvas(canvasWrap, w, h);
      var ctx = canvas.getContext("2d");

      var off = document.createElement("canvas");
      off.width = w; off.height = h;
      var octx = off.getContext("2d");
      octx.filter = cssFilter(100 + gBrightness(), gContrast());
      octx.drawImage(current, 0, 0, w, h);

      var data = octx.getImageData(0, 0, w, h);
      var px = data.data;
      var thr = gThreshold();
      var flip = invert();

      for (var i = 0; i < px.length; i += 4) {
        var lum = 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2];
        var v = lum >= thr ? 255 : 0;
        if (flip) v = 255 - v;
        px[i] = px[i + 1] = px[i + 2] = v;
        px[i + 3] = 255;
      }
      ctx.putImageData(data, 0, 0);
    }

    initFileInput("image/*", function (files) {
      readImage(files[0]).then(function (r) {
        current = r.img;
        show(panel);
        hide($("dropZone"));
        render();
        if (dl) dl.disabled = false;
      });
    });

    ["seBrightness", "seContrast", "seThreshold", "seInvert"].forEach(function (id) {
      var e = $(id);
      if (e) e.addEventListener("input", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (c) downloadCanvas(c, "signature-bw.png", "image/png");
      });
    }

    bindReset(function () {
      current = null;
      hide(panel); show($("dropZone"));
      canvasWrap.innerHTML = "";
      if (dl) dl.disabled = true;
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     5. DOCUMENT CROP & AUTO-ENHANCE
     ==================================================================== */

  function engineDocCrop() {
    var panel = panelFor("document-crop");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var current = null;

    var gTop = bindRange("dcTop", "dcTopOut", function (v) { return v + "%"; });
    var gBottom = bindRange("dcBottom", "dcBottomOut", function (v) { return v + "%"; });
    var gLeft = bindRange("dcLeft", "dcLeftOut", function (v) { return v + "%"; });
    var gRight = bindRange("dcRight", "dcRightOut", function (v) { return v + "%"; });

    function enhance() {
      var e = $("dcEnhance");
      return !!(e && e.checked);
    }

    function render() {
      if (!current) return;
      var W = current.naturalWidth, H = current.naturalHeight;
      var sx = Math.round(W * gLeft() / 100);
      var sy = Math.round(H * gTop() / 100);
      var sw = Math.max(1, Math.round(W * (1 - gLeft() / 100 - gRight() / 100)));
      var sh = Math.max(1, Math.round(H * (1 - gTop() / 100 - gBottom() / 100)));

      var canvas = mountCanvas(canvasWrap, sw, sh);
      var ctx = canvas.getContext("2d");
      ctx.imageSmoothingQuality = "high";
      ctx.filter = enhance() ? "contrast(1.22) brightness(1.06) saturate(1.1)" : "none";
      ctx.drawImage(current, sx, sy, sw, sh, 0, 0, sw, sh);
      ctx.filter = "none";
    }

    initFileInput("image/*", function (files) {
      readImage(files[0]).then(function (r) {
        current = r.img;
        show(panel);
        hide($("dropZone"));
        render();
        if (dl) dl.disabled = false;
      });
    });

    ["dcTop", "dcBottom", "dcLeft", "dcRight", "dcEnhance"].forEach(function (id) {
      var e = $(id);
      if (e) e.addEventListener("input", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (c) downloadCanvas(c, "document-cropped.jpg", "image/jpeg", 0.92);
      });
    }

    bindReset(function () {
      current = null;
      hide(panel); show($("dropZone"));
      canvasWrap.innerHTML = "";
      if (dl) dl.disabled = true;
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     6. FORMAT CONVERTER  (PNG / JPG / WebP)
     ==================================================================== */

  function engineFormatConverter() {
    var panel = panelFor("format-converter");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var current = null;
    var origSize = 0;

    var gQuality = bindRange("fcQuality", "fcQualityOut", function (v) { return (v / 100).toFixed(2); });
    var gMaxW = bindRange("fcMaxWidth", "fcMaxWidthOut", function (v) {
      return v === 0 ? "0 = original" : v + " px";
    });

    function fmt() { var e = $("fcFormat"); return e ? e.value : "image/png"; }
    function quality() { return gQuality() / 100; }

    function setStat(id, v) { var e = $(id); if (e) e.textContent = v; }

    function ext() {
      var m = { "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp" };
      return m[fmt()] || "png";
    }

    function render() {
      if (!current) return;
      var W = current.naturalWidth, H = current.naturalHeight;
      var maxW = gMaxW();
      var scale = (maxW > 0 && W > maxW) ? maxW / W : 1;
      var w = Math.max(1, Math.round(W * scale));
      var h = Math.max(1, Math.round(H * scale));

      var canvas = mountCanvas(canvasWrap, w, h);
      var ctx = canvas.getContext("2d");
      ctx.imageSmoothingQuality = "high";

      // JPEG has no alpha — flatten onto white.
      if (fmt() === "image/jpeg") {
        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(0, 0, w, h);
      }
      ctx.drawImage(current, 0, 0, w, h);

      canvas.toBlob(function (blob) {
        setStat("fcOrig", fmtBytes(origSize));
        setStat("fcNew", fmtBytes(blob ? blob.size : 0));
        setStat("fcDims", w + " × " + h);
      }, fmt(), quality());
    }

    initFileInput("image/*", function (files) {
      readImage(files[0]).then(function (r) {
        current = r.img;
        origSize = files[0].size;
        show(panel);
        hide($("dropZone"));
        render();
        if (dl) dl.disabled = false;
      });
    });

    ["fcFormat", "fcQuality", "fcMaxWidth"].forEach(function (id) {
      var e = $(id);
      if (e) e.addEventListener("input", render);
      if (e) e.addEventListener("change", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (!c) return;
        var base = (current && current.name) || "rkhub-image";
        downloadCanvas(c, base.replace(/\.[^.]+$/, "") + "." + ext(), fmt(), quality());
      });
    }

    bindReset(function () {
      current = null; origSize = 0;
      hide(panel); show($("dropZone"));
      canvasWrap.innerHTML = "";
      ["fcOrig", "fcNew", "fcDims"].forEach(function (i) { setStat(i, "—"); });
      if (dl) dl.disabled = true;
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });
  }

  /* ======================================================================
     6b. PHOTO SHEET PRINTER  —  4 to 36 photos on one A4 @ 300 DPI
     ==================================================================== */

  function enginePhotoSheet() {
    var panel = panelFor("photo-sheet");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var pdfBtn = $("downloadPdfBtn");
    var current = null;

    var A4_W = 2480, A4_H = 3508;                 // 300 DPI
    var GAP = 20;                                  // gutter between photos (px)
    var MARGIN = 90;                               // sheet margin (px)

    var SIZES = {
      "35x45": { w: 413, h: 531, label: "35 × 45 mm" },
      "25x35": { w: 295, h: 413, label: "25 × 35 mm" },
      "20x25": { w: 236, h: 295, label: "20 × 25 mm" },
      "50x65": { w: 591, h: 768, label: "50 × 65 mm" },
      "30x40": { w: 354, h: 472, label: "30 × 40 mm" }
    };

    var gBright = bindRange("psBrightness", "psBrightnessOut", function (v) { return v + "%"; });
    var gContrast = bindRange("psContrast", "psContrastOut", function (v) { return v + "%"; });

    function size() { return SIZES[($("psSize") || {}).value] || SIZES["35x45"]; }
    function layout() {
      var raw = (($("psLayout") || {}).value || "4x3").split("x");
      return { cols: parseInt(raw[0], 10), rows: parseInt(raw[1], 10) };
    }
    function bgColor() {
      var r = root.querySelector('input[name="psBg"]:checked');
      return r ? r.value : "#FFFFFF";
    }
    function guides() { var e = $("psGuides"); return !!(e && e.checked); }
    function withLabel() { var e = $("psLabel"); return !!(e && e.checked); }
    function sheetName() { var e = $("psName"); return e ? e.value.trim() : ""; }

    function setStat(id, v) { var e = $(id); if (e) e.textContent = v; }

    function buildSheet(canvas, img) {
      var s = size();
      var L = layout();
      var ctx = canvas.getContext("2d");

      // White paper
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, A4_W, A4_H);

      // Header name
      if (withLabel() && sheetName()) {
        ctx.fillStyle = "#0F2942";
        ctx.font = "700 54px 'Noto Sans Devanagari', Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(sheetName().toUpperCase(), A4_W / 2, 26);
        ctx.textAlign = "left";
        ctx.textBaseline = "alphabetic";
      }

      var top = withLabel() && sheetName() ? 110 : MARGIN;
      var usableW = A4_W - MARGIN * 2;
      var usableH = A4_H - top - MARGIN;

      var cellW = (usableW - GAP * (L.cols - 1)) / L.cols;
      var cellH = (usableH - GAP * (L.rows - 1)) / L.rows;
      // shrink to fit the smaller of width/height constraint
      var pw = Math.min(cellW, cellH * (s.w / s.h));
      var ph = pw * (s.h / s.w);

      var blockW = pw * L.cols + GAP * (L.cols - 1);
      var blockH = ph * L.rows + GAP * (L.rows - 1);
      var startX = (A4_W - blockW) / 2;
      var startY = top + (usableH - blockH) / 2;

      var bg = bgColor();
      var filter = cssFilter(gBright(), gContrast());

      for (var r = 0; r < L.rows; r++) {
        for (var c = 0; c < L.cols; c++) {
          var x = startX + c * (pw + GAP);
          var y = startY + r * (ph + GAP);

          // photo background
          ctx.fillStyle = bg;
          ctx.fillRect(x, y, pw, ph);

          if (img) {
            ctx.save();
            ctx.beginPath();
            ctx.rect(x, y, pw, ph);
            ctx.clip();
            ctx.filter = filter;
            drawCover(ctx, img, x, y, pw, ph);
            ctx.restore();
          }

          // cell border
          ctx.strokeStyle = "rgba(15,41,66,.55)";
          ctx.lineWidth = 3;
          ctx.strokeRect(x, y, pw, ph);

          // cut guides — dashed corner ticks outside the photo
          if (guides()) {
            ctx.strokeStyle = "rgba(15,41,66,.45)";
            ctx.lineWidth = 2;
            ctx.setLineDash([14, 12]);
            ctx.strokeRect(x - GAP / 2, y - GAP / 2, pw + GAP, ph + GAP);
            ctx.setLineDash([]);
          }
        }
      }

      // Footer note
      ctx.fillStyle = "rgba(15,41,66,.55)";
      ctx.font = "400 30px 'Noto Sans Devanagari', Arial, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(s.label + "  •  " + (L.cols * L.rows) + " photos  •  A4 @ 300 DPI",
                   A4_W / 2, A4_H - 48);
      ctx.textAlign = "left";

      return { pw: pw, ph: ph, count: L.cols * L.rows };
    }

    function render() {
      var canvas = mountCanvas(canvasWrap, A4_W, A4_H);
      var res = buildSheet(canvas, current);
      setStat("psCount", String(res.count));
      setStat("psDim", size().label);
      setStat("psSheets", String(Math.max(1, current ? Math.ceil(filesCount / res.count) : 1)));
      if (dl) dl.disabled = !current;
      if (pdfBtn) pdfBtn.disabled = !current;
    }

    var filesCount = 1;

    initFileInput("image/*", function (files) {
      filesCount = files.length;
      readImage(files[0]).then(function (r) {
        current = r.img;
        show(panel);
        hide($("dropZone"));
        render();
      });
    });

    ["psSize", "psLayout", "psBrightness", "psContrast", "psGuides", "psLabel", "psName"]
      .forEach(function (id) {
        var e = $(id);
        if (!e) return;
        e.addEventListener("input", render);
        e.addEventListener("change", render);
      });

    var labelWrap = $("psLabelWrap");
    var labelChk = $("psLabel");
    if (labelChk && labelWrap) {
      labelChk.addEventListener("change", function () {
        labelWrap.hidden = !labelChk.checked;
        render();
      });
    }

    root.querySelectorAll('input[name="psBg"]').forEach(function (r) {
      r.addEventListener("change", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (c) downloadCanvas(c, "rkhub-photo-sheet-a4.png", "image/png");
      });
    }

    if (pdfBtn) {
      pdfBtn.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (!c) return;
        pdfBtn.disabled = true;
        var label = pdfBtn.innerHTML;
        pdfBtn.textContent = "PDF बना रहे हैं…";

        loadScript("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js")
          .then(function () {
            var ctor = window.jspdf && window.jspdf.jsPDF;
            if (!ctor) throw new Error("jsPDF unavailable");
            var doc = new ctor({ unit: "mm", format: "a4", orientation: "portrait" });
            doc.addImage(c.toDataURL("image/jpeg", 0.92), "JPEG", 0, 0, 210, 297);
            return doc.output("blob");
          })
          .then(function (blob) {
            var url = URL.createObjectURL(blob);
            downloadURL(url, "rkhub-photo-sheet-a4.pdf");
            setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
          })
          .catch(function (err) {
            alert("PDF create failed: " + (err && err.message ? err.message : "error"));
          })
          .then(function () {
            pdfBtn.disabled = false;
            pdfBtn.innerHTML = label;
          });
      });
    }

    bindReset(function () {
      current = null; filesCount = 1;
      hide(panel); show($("dropZone"));
      canvasWrap.innerHTML = "";
      ["psCount", "psDim", "psSheets"].forEach(function (i) { setStat(i, "—"); });
      var fi = $("fileInput");
      if (fi) fi.value = "";
    });

    // Pre-render the empty sheet so the user sees the layout immediately.
    render();
  }

  /* ======================================================================
     6c. PVC CARD MAKER  —  CR80 85.6 x 54 mm @ 300 DPI
     ==================================================================== */

  function enginePvcCard() {
    var panel = panelFor("pvc-card");
    var canvasWrap = $("wsCanvas");
    var dl = $("downloadBtn");
    var photo = null;

    var CW = 1011, CH = 638;   // 85.6 x 54 mm @ 300 DPI
    var R = 46;                // corner radius

    var THEMES = {
      navy:     { bg: ["#16395C", "#0A1C2E"], fg: "#FFFFFF", muted: "rgba(255,255,255,.75)", bar: "#FFB300" },
      red:      { bg: ["#E53935", "#8E0000"], fg: "#FFFFFF", muted: "rgba(255,255,255,.78)", bar: "#FFB300" },
      green:    { bg: ["#2E9E4F", "#0B4F1E"], fg: "#FFFFFF", muted: "rgba(255,255,255,.78)", bar: "#FF9933" },
      amber:    { bg: ["#FFB300", "#E07C00"], fg: "#3A2A00", muted: "rgba(58,42,0,.78)", bar: "#0F2942" },
      tricolor: { bg: ["#FF9933", "#138808"], fg: "#FFFFFF", muted: "rgba(255,255,255,.8)", bar: "#0F2942" },
      white:    { bg: ["#FFFFFF", "#EEF2F7"], fg: "#16202C", muted: "rgba(22,32,44,.65)", bar: "#D32F2F" }
    };

    function val(id) { var e = $(id); return e ? e.value.trim() : ""; }
    function theme() { return THEMES[($("pcTheme") || {}).value] || THEMES.navy; }
    function wantQr() { var e = $("pcQr"); return !!(e && e.checked); }

    function roundRect(ctx, x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function render() {
      var canvas = mountCanvas(canvasWrap, CW, CH);
      var ctx = canvas.getContext("2d");
      var t = theme();

      // ---- background
      var g = ctx.createLinearGradient(0, 0, CW, CH);
      g.addColorStop(0, t.bg[0]);
      g.addColorStop(1, t.bg[1]);
      roundRect(ctx, 0, 0, CW, CH, R);
      ctx.fillStyle = g;
      ctx.fill();

      // subtle top accent bar
      ctx.save();
      roundRect(ctx, 0, 0, CW, CH, R);
      ctx.clip();
      ctx.fillStyle = t.bar;
      ctx.fillRect(0, 0, CW, 10);

      // ---- header
      var pad = 34;
      var org = val("pcOrg");
      var name = val("pcName");

      if (org) {
        ctx.fillStyle = t.muted;
        ctx.font = "700 26px 'Noto Sans Devanagari', Arial, sans-serif";
        ctx.textBaseline = "top";
        ctx.fillText(org.toUpperCase(), pad, 26);
      }

      // ---- photo frame
      var phW = 190, phH = 240;
      var phX = pad, phY = 96;
      ctx.fillStyle = "rgba(255,255,255,.18)";
      roundRect(ctx, phX - 6, phY - 6, phW + 12, phH + 12, 18);
      ctx.fill();

      ctx.save();
      roundRect(ctx, phX, phY, phW, phH, 14);
      ctx.clip();
      if (photo) {
        drawCover(ctx, photo, phX, phY, phW, phH);
      } else {
        ctx.fillStyle = "rgba(255,255,255,.14)";
        ctx.fillRect(phX, phY, phW, phH);
        ctx.fillStyle = t.muted;
        ctx.font = "600 20px 'Noto Sans Devanagari', Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("PHOTO", phX + phW / 2, phY + phH / 2);
        ctx.textAlign = "left";
      }
      ctx.restore();
      ctx.strokeStyle = t.bar;
      ctx.lineWidth = 3;
      roundRect(ctx, phX, phY, phW, phH, 14);
      ctx.stroke();

      // ---- name
      var tx = phX + phW + 28;
      var ty = phY + 8;
      ctx.textBaseline = "top";

      ctx.fillStyle = t.fg;
      ctx.font = "800 44px 'Noto Sans Devanagari', Arial, sans-serif";
      var shown = name || "YOUR NAME";
      // shrink to fit
      while (ctx.measureText(shown).width > CW - tx - pad && ctx.font !== "800 24px Arial") {
        var sizeNow = parseInt(ctx.font.match(/(\d+)px/)[1], 10) - 2;
        if (sizeNow <= 24) break;
        ctx.font = "800 " + sizeNow + "px 'Noto Sans Devanagari', Arial, sans-serif";
      }
      ctx.fillText(shown, tx, ty);

      var lines = [];
      var father = val("pcFather");
      if (father) lines.push("S/D/W of " + father);
      var dob = val("pcDob");
      if (dob) lines.push("DOB: " + dob);
      var gender = val("pcGender");
      var blood = val("pcBlood");
      if (gender) lines.push("Gender: " + gender);
      if (blood) lines.push("Blood: " + blood);

      ctx.fillStyle = t.muted;
      ctx.font = "600 25px 'Noto Sans Devanagari', Arial, sans-serif";
      var ly = ty + 62;
      lines.forEach(function (ln) {
        ctx.fillText(ln, tx, ly);
        ly += 34;
      });

      // ---- address
      var addr = val("pcMobile") || val("pcAddress");
      if (addr) {
        ctx.fillStyle = t.fg;
        ctx.font = "600 24px 'Noto Sans Devanagari', Arial, sans-serif";
        var ay = CH - 92;
        if (val("pcAddress") && val("pcMobile")) {
          ctx.fillText(val("pcMobile"), pad, ay);
          ctx.fillStyle = t.muted;
          ctx.font = "400 22px 'Noto Sans Devanagari', Arial, sans-serif";
          ctx.fillText(val("pcAddress"), pad, ay + 32);
        } else {
          ctx.fillText(addr, pad, ay);
        }
      }

      // ---- fake QR
      if (wantQr()) {
        var q = 78, qx = CW - q - pad, qy = CH - q - pad - 6;
        ctx.fillStyle = "rgba(255,255,255,.92)";
        roundRect(ctx, qx, qy, q, q, 8);
        ctx.fill();
        ctx.fillStyle = t.bg[1];
        var seed = 1;
        for (var i = 0; i < 7; i++) {
          for (var j = 0; j < 7; j++) {
            seed = (seed * 9301 + 49297) % 233280;
            if (seed / 233280 > 0.5) {
              ctx.fillRect(qx + 7 + i * 9.5, qy + 7 + j * 9.5, 8, 8);
            }
          }
        }
        ctx.fillStyle = t.muted;
        ctx.font = "600 15px Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("SCAN", qx + q / 2, qy - 6);
        ctx.textAlign = "left";
      }

      // ---- outer border
      ctx.restore();
      ctx.strokeStyle = "rgba(0,0,0,.35)";
      ctx.lineWidth = 3;
      roundRect(ctx, 1.5, 1.5, CW - 3, CH - 3, R);
      ctx.stroke();

      if (dl) dl.disabled = false;
    }

    // The card tool needs a photo picker inside the control panel (the main
    // drop zone is hidden the moment the panel opens, so it can't be used).
    var photoInput = document.createElement("input");
    photoInput.type = "file";
    photoInput.accept = "image/*";
    photoInput.id = "pcPhotoInput";
    photoInput.hidden = true;

    var photoBtn = document.createElement("button");
    photoBtn.type = "button";
    photoBtn.className = "btn btn--navy";
    photoBtn.style.width = "100%";
    photoBtn.style.marginBottom = "1rem";
    photoBtn.innerHTML =
      '<svg class="ico" aria-hidden="true"><use href="#i-camera"></use></svg> फोटो चुनें / Choose Photo';

    var ctl = panel && panel.querySelector(".ws-panel__controls");
    if (ctl) {
      var nameField = ctl.querySelector("#pcName");
      var anchor = nameField && nameField.closest(".field");
      if (anchor) {
        anchor.insertAdjacentElement("afterend", photoBtn);
        anchor.insertAdjacentElement("afterend", photoInput);
      } else {
        ctl.insertBefore(photoBtn, ctl.firstChild);
        ctl.insertBefore(photoInput, photoBtn);
      }
    }

    photoBtn.addEventListener("click", function () { photoInput.click(); });
    photoInput.addEventListener("change", function () {
      if (photoInput.files && photoInput.files[0]) {
        readImage(photoInput.files[0]).then(function (r) { photo = r.img; render(); });
      }
    });

    // Main file drop zone is optional for the card tool (only for the photo).
    initFileInput("image/*", function (files) {
      readImage(files[0]).then(function (r) {
        photo = r.img;
        show(panel);
        hide($("dropZone"));
        render();
      });
    });

    var fields = ["pcName", "pcFather", "pcDob", "pcGender", "pcBlood",
                  "pcMobile", "pcAddress", "pcTheme", "pcOrg", "pcQr"];
    fields.forEach(function (id) {
      var e = $(id);
      if (!e) return;
      e.addEventListener("input", render);
      e.addEventListener("change", render);
    });

    if (dl) {
      dl.addEventListener("click", function () {
        var c = canvasWrap.querySelector("canvas");
        if (c) downloadCanvas(c, "rkhub-pvc-card.png", "image/png");
      });
    }

    bindReset(function () {
      photo = null;
      hide(panel); show($("dropZone"));
      canvasWrap.innerHTML = "";
      if (dl) dl.disabled = true;
      var fi = $("fileInput");
      if (fi) fi.value = "";
      photoInput.value = "";
      ["pcName", "pcFather", "pcDob", "pcMobile", "pcAddress", "pcOrg"].forEach(function (id) {
        var e = $(id);
        if (e) e.value = "";
      });
    });

    render();
  }

  /* ======================================================================
     7. AGE CALCULATOR
     ==================================================================== */

  function engineAgeCalculator() {
    var MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
                  "जुलाई", "अगस्त", "सितंबर", "अक्तूबर", "नवंबर", "दिसंबर"];

    function pad(n) { return String(n).padStart(2, "0"); }
    function set(id, v) { var e = $(id); if (e) e.textContent = v; }

    function daysInMonth(y, m) { return new Date(y, m, 0).getDate(); }  // m is 1-based

    function today() {
      var d = new Date();
      return { y: d.getFullYear(), m: d.getMonth() + 1, d: d.getDate() };
    }

    /* ---- build one DD/MM/YYYY widget ---------------------------------- */
    function buildDateField(root2, opts) {
      var wrap = root2.querySelector('[data-datefield="' + opts.name + '"]');
      if (!wrap) return null;

      var sels = {
        d: wrap.querySelector('[data-part="d"]'),
        m: wrap.querySelector('[data-part="m"]'),
        y: wrap.querySelector('[data-part="y"]')
      };
      if (!sels.d || !sels.m || !sels.y) return null;

      // Years
      var thisYear = today().y;
      var yStart = opts.minYear || 1900;
      var yEnd = opts.maxYear || thisYear;
      sels.y.innerHTML = "";
      for (var y = yEnd; y >= yStart; y--) {
        var oy = document.createElement("option");
        oy.value = y;
        oy.textContent = y;
        sels.y.appendChild(oy);
      }

      // Months
      sels.m.innerHTML = "";
      MONTHS.forEach(function (name, i) {
        var om = document.createElement("option");
        om.value = i + 1;
        om.textContent = pad(i + 1) + " — " + name;
        sels.m.appendChild(om);
      });

      function fillDays() {
        var y = parseInt(sels.y.value, 10);
        var m = parseInt(sels.m.value, 10);
        var max = (!y || !m) ? 31 : daysInMonth(y, m);
        var prev = parseInt(sels.d.value, 10) || 0;
        sels.d.innerHTML = "";
        for (var d = 1; d <= max; d++) {
          var od = document.createElement("option");
          od.value = d;
          od.textContent = pad(d);
          sels.d.appendChild(od);
        }
        sels.d.value = (prev >= 1 && prev <= max) ? prev : 1;
      }

      sels.m.addEventListener("change", fillDays);
      sels.y.addEventListener("change", fillDays);
      [sels.d, sels.m, sels.y].forEach(function (s) {
        s.addEventListener("change", opts.onChange);
      });

      fillDays();

      return {
        set: function (y, m, d) {
          sels.y.value = y;
          sels.m.value = m;
          fillDays();
          sels.d.value = d;
        },
        clear: function () {
          sels.y.selectedIndex = 0;
          sels.m.selectedIndex = 0;
          fillDays();
        },
        get: function () {
          var y = parseInt(sels.y.value, 10);
          var m = parseInt(sels.m.value, 10);
          var d = parseInt(sels.d.value, 10);
          if (!y || !m || !d) return null;
          return new Date(y, m - 1, d);
        }
      };
    }

    var asOn = buildDateField(root, {
      name: "acAsOn",
      minYear: 1900,
      onChange: calc
    });
    var dob = buildDateField(root, {
      name: "acDob",
      minYear: 1900,
      onChange: calc
    });

    function calc() {
      var b = dob && dob.get();
      var a = asOn && asOn.get();
      var outs = ["acY", "acM", "acD", "acTM", "acTW", "acTD", "acBday"];

      if (!b || !a || a < b) {
        outs.forEach(function (i) { set(i, "—"); });
        return;
      }

      var years = a.getFullYear() - b.getFullYear();
      var months = a.getMonth() - b.getMonth();
      var days = a.getDate() - b.getDate();

      if (days < 0) {
        // borrow the length of the month the "as on" date falls in
        months -= 1;
        days = a.getDate() + daysInMonth(a.getFullYear(), a.getMonth() + 1) - b.getDate();
      }
      if (months < 0) { years -= 1; months += 12; }

      var totalDays = Math.round((a - b) / 86400000);
      var totalMonths = years * 12 + months;

      set("acY", years);
      set("acM", months);
      set("acD", days);
      set("acTM", totalMonths);
      set("acTW", Math.floor(totalDays / 7).toLocaleString("en-IN"));
      set("acTD", totalDays.toLocaleString("en-IN"));

      var nb = new Date(a.getFullYear(), b.getMonth(), b.getDate());
      if (nb < a) nb = new Date(a.getFullYear() + 1, b.getMonth(), b.getDate());
      var diff = Math.round((nb - a) / 86400000);
      var label = pad(nb.getDate()) + "/" + pad(nb.getMonth() + 1) + "/" + nb.getFullYear();
      set("acBday", label + (diff === 0 ? " — आज! 🎉" : " (" + diff + " दिन)"));
    }

    if (!dob || !asOn) return;

    var t = today();
    asOn.set(t.y, t.m, t.d);
    dob.set(t.y - 25, 1, 1);
    calc();

    var tbtn = $("acTodayBtn");
    if (tbtn) {
      tbtn.addEventListener("click", function () {
        var n = today();
        asOn.set(n.y, n.m, n.d);
        calc();
      });
    }
  }

  /* ======================================================================
     8. STAMP DUTY & FEE ESTIMATOR
     ==================================================================== */

  function engineStampDuty() {
    var val = $("sdValue"), preset = $("sdPreset");
    var regPct = $("sdRegPct"), customPct = $("sdCustomPct"), customWrap = $("sdCustomWrap");
    if (!val) return;

    function set(id, v) { var e = $(id); if (e) e.textContent = v; }

    function calc() {
      var v = parseFloat(val.value) || 0;
      var isCustom = preset.value === "custom";
      if (customWrap) customWrap.hidden = !isCustom;

      var dutyPct = isCustom ? (parseFloat(customPct.value) || 0) : parseFloat(preset.value);
      var regRate = parseFloat(regPct.value) || 0;

      var duty = v * dutyPct / 100;
      var reg = v * regRate / 100;
      set("sdDuty", inr(duty) + "  (" + dutyPct + "%)");
      set("sdReg", inr(reg) + "  (" + regRate + "%)");
      set("sdTotal", inr(duty + reg));
    }

    [val, preset, regPct, customPct].forEach(function (e) {
      if (!e) return;
      e.addEventListener("input", calc);
      e.addEventListener("change", calc);
    });
    calc();
  }

  /* ======================================================================
     9. CSC COMMISSION & TAX CALCULATOR
     ==================================================================== */

  function engineCscCommission() {
    var amount = $("ccAmount"), rate = $("ccRate");
    var tds = $("ccTds"), gst = $("ccGst"), exp = $("ccExp");
    if (!amount) return;

    function set(id, v) { var e = $(id); if (e) e.textContent = v; }

    function calc() {
      var a = parseFloat(amount.value) || 0;
      var r = parseFloat(rate.value) || 0;
      var t = parseFloat(tds.value) || 0;
      var g = parseFloat(gst.value) || 0;
      var x = parseFloat(exp.value) || 0;

      var gross = a * r / 100;
      var tdsAmt = gross * t / 100;
      var gstAmt = gross * g / 100;
      var net = gross - tdsAmt + gstAmt;
      var profit = net - x;

      set("ccGross", inr(gross));
      set("ccTdsOut", "− " + inr(tdsAmt));
      set("ccGstOut", "+ " + inr(gstAmt));
      set("ccNet", inr(net));
      set("ccProfit", inr(profit));
    }

    [amount, rate, tds, gst, exp].forEach(function (e) {
      if (!e) return;
      e.addEventListener("input", calc);
      e.addEventListener("change", calc);
    });
    calc();
  }

  /* ======================================================================
     10. FILE SIZE UNIT CONVERTER
     ==================================================================== */

  function engineFileSize() {
    var val = $("fsValue"), unit = $("fsUnit");
    if (!val) return;

    function set(id, v) { var e = $(id); if (e) e.textContent = v; }
    function show(bytes) {
      if (!isFinite(bytes)) { return; }
      var b = bytes;
      set("fsB", Math.round(b).toLocaleString("en-IN") + " B");
      set("fsKB", (b / 1024).toFixed(3) + " KB");
      set("fsMB", (b / 1048576).toFixed(4) + " MB");
      set("fsGB", (b / 1073741824).toFixed(6) + " GB");
      set("fsTB", (b / 1099511627776).toFixed(8) + " TB");
    }

    function calc() {
      show((parseFloat(val.value) || 0) * (parseFloat(unit.value) || 1));
    }

    [val, unit].forEach(function (e) {
      if (!e) return;
      e.addEventListener("input", calc);
      e.addEventListener("change", calc);
    });
    calc();
  }

  /* ============================================================= ROUTER === */

  var ENGINES = {
    "passport-photo": enginePassport,
    "pdf-compressor": enginePdfCompressor,
    "image-to-pdf": engineImageToPdf,
    "signature-extractor": engineSignature,
    "document-crop": engineDocCrop,
    "format-converter": engineFormatConverter,
    "photo-sheet": enginePhotoSheet,
    "pvc-card": enginePvcCard,
    "age-calculator": engineAgeCalculator,
    "stamp-duty": engineStampDuty,
    "csc-commission": engineCscCommission,
    "file-size-converter": engineFileSize
  };

  function boot() {
    var fn = ENGINES[SLUG];
    if (fn) {
      try {
        fn();
      } catch (err) {
        console.error("RKHUB tool engine failed:", SLUG, err);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
