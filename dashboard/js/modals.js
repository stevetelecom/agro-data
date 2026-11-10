/**
 * Rôle : fenêtres modales de création, modification et suppression.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3)
 */

function closeModal(root, onKey, result, resolve) {
  document.body.classList.remove("modal-open");
  document.removeEventListener("keydown", onKey);
  root.replaceChildren();
  resolve(result);
}

function trapTab(dialog, event) {
  if (event.key !== "Tab") return;
  const items = [...dialog.querySelectorAll("button, input, select, textarea")].filter((item) => !item.disabled);
  const first = items[0];
  const last = items[items.length - 1];
  if (!first || !last) return;
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function showFieldErrors(slots, errors) {
  slots.forEach((slot, name) => {
    const message = errors?.[name];
    slot.hidden = !message;
    slot.textContent = message || "";
  });
}

export function openForm({ title, submitLabel, fields, onSubmit }) {
  const root = document.querySelector("#modal-root");
  return new Promise((resolve) => {
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";
    const dialog = document.createElement("div");
    dialog.className = "modal";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-labelledby", "modal-title");

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "icon-btn modal-close";
    closeBtn.setAttribute("aria-label", "Fermer");
    const closeIcon = document.createElement("span");
    closeIcon.className = "material-symbols-outlined";
    closeIcon.setAttribute("aria-hidden", "true");
    closeIcon.textContent = "close";
    closeBtn.append(closeIcon);

    const heading = document.createElement("h2");
    heading.id = "modal-title";
    heading.textContent = title;
    const form = document.createElement("form");
    const slots = new Map();

    fields.forEach((field) => {
      const wrap = document.createElement("label");
      wrap.className = "field";
      const span = document.createElement("span");
      span.textContent = field.label;
      let input;
      if (field.type === "select") {
        input = document.createElement("select");
        field.options.forEach((option) => {
          const node = document.createElement("option");
          node.value = option.value;
          node.textContent = option.label;
          if (String(option.value) === String(field.value ?? "")) node.selected = true;
          input.append(node);
        });
      } else {
        input = document.createElement("input");
        input.type = field.type || "text";
        input.value = field.value ?? "";
        if (field.step) input.step = field.step;
        if (field.min !== undefined) input.min = String(field.min);
        if (field.autocomplete) input.autocomplete = field.autocomplete;
      }
      input.name = field.name;
      input.required = true;
      wrap.append(span, input);
      if (field.hint) {
        const hint = document.createElement("small");
        hint.className = "hint";
        hint.textContent = field.hint;
        wrap.append(hint);
      }
      const error = document.createElement("small");
      error.className = "field-error";
      error.hidden = true;
      wrap.append(error);
      slots.set(field.name, error);
      form.append(wrap);
    });

    const actions = document.createElement("div");
    actions.className = "modal-actions";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn btn-ghost";
    cancel.textContent = "Annuler";
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "btn btn-primary";
    submit.textContent = submitLabel;
    actions.append(cancel, submit);
    form.append(actions);
    dialog.append(closeBtn, heading, form);
    backdrop.append(dialog);
    root.replaceChildren(backdrop);
    document.body.classList.add("modal-open");

    const onKey = (event) => {
      if (event.key === "Escape") closeModal(root, onKey, false, resolve);
      trapTab(dialog, event);
    };
    document.addEventListener("keydown", onKey);
    cancel.addEventListener("click", () => closeModal(root, onKey, false, resolve));
    closeBtn.addEventListener("click", () => closeModal(root, onKey, false, resolve));
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeModal(root, onKey, false, resolve);
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submit.disabled = true;
      const values = Object.fromEntries(new FormData(form).entries());
      try {
        const errors = await onSubmit(values);
        if (errors) {
          showFieldErrors(slots, errors);
          submit.disabled = false;
          return;
        }
        closeModal(root, onKey, true, resolve);
      } catch (error) {
        submit.disabled = false;
        if (error.errors) showFieldErrors(slots, error.errors);
        else {
          const first = slots.values().next().value;
          if (first) {
            first.hidden = false;
            first.textContent = error.message || "Enregistrement impossible.";
          }
        }
      }
    });
    form.querySelector("input, select")?.focus();
  });
}

export function openConfirm({ title, message, confirmLabel }) {
  const root = document.querySelector("#modal-root");
  return new Promise((resolve) => {
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";
    const dialog = document.createElement("div");
    dialog.className = "modal";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-labelledby", "modal-title");
    const heading = document.createElement("h2");
    heading.id = "modal-title";
    heading.textContent = title;
    const paragraph = document.createElement("p");
    paragraph.textContent = message;
    const actions = document.createElement("div");
    actions.className = "modal-actions";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "btn btn-ghost";
    cancel.textContent = "Annuler";
    const confirm = document.createElement("button");
    confirm.type = "button";
    confirm.className = "btn btn-danger";
    confirm.textContent = confirmLabel;
    actions.append(cancel, confirm);
    dialog.append(heading, paragraph, actions);
    backdrop.append(dialog);
    root.replaceChildren(backdrop);
    document.body.classList.add("modal-open");
    const onKey = (event) => {
      if (event.key === "Escape") closeModal(root, onKey, false, resolve);
      trapTab(dialog, event);
    };
    document.addEventListener("keydown", onKey);
    cancel.addEventListener("click", () => closeModal(root, onKey, false, resolve));
    confirm.addEventListener("click", () => closeModal(root, onKey, true, resolve));
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeModal(root, onKey, false, resolve);
    });
    cancel.focus();
  });
}
