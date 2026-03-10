/**
 * Lightweight sortable tables.
 *
 * Any <table class="sortable"> gets clickable column headers.
 * Add data-sort="num" to <th> for numeric sorting (strips $, %, commas).
 * Add data-sort="none" to skip a column.
 * Default is alphabetical.
 *
 * Clicking toggles ascending / descending.  A small arrow indicator
 * is appended to the active header.
 */
(function () {
  "use strict";

  function parseNum(text) {
    // Strip $, %, commas, whitespace, + signs, then parse
    var cleaned = text.replace(/[$%,+\s]/g, "").replace(/\u2013|\u2014/g, "-");
    var n = parseFloat(cleaned);
    return isNaN(n) ? -Infinity : n;
  }

  function sortTable(table, colIndex, type, ascending) {
    var tbody = table.tBodies[0];
    if (!tbody) return;
    var rows = Array.from(tbody.rows);

    rows.sort(function (a, b) {
      var aText = (a.cells[colIndex] || {}).textContent || "";
      var bText = (b.cells[colIndex] || {}).textContent || "";
      aText = aText.trim();
      bText = bText.trim();

      var cmp;
      if (type === "num") {
        cmp = parseNum(aText) - parseNum(bText);
      } else {
        cmp = aText.localeCompare(bText, undefined, { numeric: true, sensitivity: "base" });
      }
      return ascending ? cmp : -cmp;
    });

    rows.forEach(function (row) {
      tbody.appendChild(row);
    });
  }

  function clearArrows(headerRow) {
    var ths = headerRow.querySelectorAll("th");
    ths.forEach(function (th) {
      var arrow = th.querySelector(".sort-arrow");
      if (arrow) arrow.remove();
    });
  }

  function addArrow(th, ascending) {
    var arrow = document.createElement("span");
    arrow.className = "sort-arrow";
    arrow.style.cssText = "margin-left:0.3em;font-size:0.6em;opacity:0.6;";
    arrow.textContent = ascending ? "▲" : "▼";
    th.appendChild(arrow);
  }

  function init() {
    var tables = document.querySelectorAll("table.sortable");
    tables.forEach(function (table) {
      var headerRow = table.querySelector("thead tr");
      if (!headerRow) return;

      var ths = headerRow.querySelectorAll("th");
      ths.forEach(function (th, index) {
        var sortType = th.getAttribute("data-sort");
        if (sortType === "none") return;

        // Auto-detect: if th has class "num", default to numeric
        if (!sortType && th.classList.contains("num")) {
          sortType = "num";
        }
        if (!sortType) sortType = "alpha";

        th.style.cursor = "pointer";
        th.style.userSelect = "none";
        th.title = "Click to sort";

        var ascending = true;
        th.addEventListener("click", function () {
          // If already sorted by this column, toggle direction
          if (th.querySelector(".sort-arrow")) {
            ascending = !ascending;
          } else {
            ascending = sortType === "num" ? false : true; // Numbers: descending first
          }

          clearArrows(headerRow);
          addArrow(th, ascending);
          sortTable(table, index, sortType, ascending);
        });
      });
    });
  }

  // Run on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
