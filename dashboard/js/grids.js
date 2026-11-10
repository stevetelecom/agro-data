/**
 * Rôle : tableau dynamique des mesures (jQWidgets) et repli local.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3)
 */

import { escapeHtml } from "./format.js";

const localization = {
  emptydatastring: "Aucune donnée",
  filterstring: "Filtrer",
  filterclearstring: "Effacer",
  filtershowrowstring: "Afficher les lignes où :",
  filterorconditionstring: "Ou",
  filterandconditionstring: "Et",
  sortascendingstring: "Tri croissant",
  sortdescendingstring: "Tri décroissant",
  sortremovestring: "Retirer le tri",
  pagergotopagestring: "Page :",
  pagershowrowsstring: "Lignes :",
  pagerrangestring: " sur ",
  pagerpreviousbuttonstring: "Précédent",
  pagernextbuttonstring: "Suivant",
  decimalseparator: ",",
  thousandsseparator: " ",
};

function jqxReady() {
  return Boolean(window.jQuery?.fn?.jqxGrid);
}

function paintJqx(holder, columns, rows, options) {
  const previous = holder.firstElementChild;
  if (previous && window.jQuery(previous).data("jqxGrid")) {
    window.jQuery(previous).jqxGrid("destroy");
  }
  holder.replaceChildren();
  const grid = document.createElement("div");
  holder.append(grid);
  const datafields = columns.map((column) => ({ name: column.field, type: column.type || "string" }));
  if (!datafields.some((field) => field.name === "id")) datafields.unshift({ name: "id", type: "string" });
  const source = {
    localdata: rows,
    datatype: "array",
    datafields,
  };
  window.jQuery(grid).jqxGrid({
    width: "100%",
    height: options.height || 520,
    source: new window.jQuery.jqx.dataAdapter(source),
    columns: columns.map((column) => {
      const spec = { text: column.label, datafield: column.field };
      if (column.width) spec.width = column.width;
      if (column.render) {
        spec.cellsrenderer = (rowIndex, dataField, value) => column.render(value, rows[rowIndex]);
      }
      return spec;
    }),
    sortable: true,
    filterable: Boolean(options.filterable),
    showfilterrow: Boolean(options.filterable),
    pageable: Boolean(options.pageable),
    pagesize: 10,
    columnsresize: true,
    altrows: true,
    selectionmode: "singlerow",
    localization,
    enablebrowserselection: true,
  });
  if (options.onSelect) {
    window.jQuery(grid).on("rowselect", (event) => {
      options.onSelect(event.args?.row || null);
    });
  }
}

function paintTable(holder, columns, rows, options) {
  holder.replaceChildren();
  const scroll = document.createElement("div");
  scroll.className = "table-scroll";
  const table = document.createElement("table");
  table.className = "data";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.scope = "col";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sort-btn";
    button.textContent = column.label;
    button.addEventListener("click", () => {
      const direction = button.dataset.dir === "asc" ? "desc" : "asc";
      button.dataset.dir = direction;
      const sorted = [...rows].sort((left, right) => {
        const a = left[column.field];
        const b = right[column.field];
        if (typeof a === "number" && typeof b === "number") return direction === "asc" ? a - b : b - a;
        return direction === "asc"
          ? String(a ?? "").localeCompare(String(b ?? ""), "fr")
          : String(b ?? "").localeCompare(String(a ?? ""), "fr");
      });
      paintTable(holder, columns, sorted, options);
    });
    th.append(button);
    headRow.append(th);
  });
  thead.append(headRow);
  const tbody = document.createElement("tbody");
  if (rows.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = columns.length;
    td.textContent = "Aucune donnée";
    tr.append(td);
    tbody.append(tr);
  }
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.tabIndex = 0;
    columns.forEach((column) => {
      const td = document.createElement("td");
      if (column.render) td.innerHTML = column.render(row[column.field], row);
      else td.textContent = row[column.field] ?? "—";
      tr.append(td);
    });
    const select = () => {
      tbody.querySelectorAll("tr").forEach((item) => item.removeAttribute("aria-selected"));
      tr.setAttribute("aria-selected", "true");
      options.onSelect?.(row);
    };
    tr.addEventListener("click", select);
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter") select();
    });
    tbody.append(tr);
  });
  table.append(thead, tbody);
  scroll.append(table);
  holder.append(scroll);
}

export function mountGrid(holder, columns, rows, options = {}) {
  if (!holder) return;
  if (jqxReady()) {
    try {
      paintJqx(holder, columns, rows, options);
      return;
    } catch (error) {
      console.error(error);
    }
  }
  paintTable(holder, columns, rows, options);
}

export function cell(value) {
  return `<div class="grid-cell">${escapeHtml(value ?? "—")}</div>`;
}
