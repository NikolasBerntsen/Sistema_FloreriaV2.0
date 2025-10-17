from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Mapping, MutableMapping, Sequence

from tkinter import ttk

from app.services import customer_service
from app.ui import theme
from app.utils import csv_export

from .validators import normalise_status, validate_customer_payload

__all__ = ["CustomerListView"]


class CustomerListView(tk.Frame):
    """Listado de clientes con filtros, paginación y utilitarios CSV."""

    PAGE_SIZE = 20

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_select: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(master, bg=theme.SURFACE_COLOR)
        self._on_select = on_select
        self._current_page = 1
        self._total_pages = 1
        self._search_term: str | None = None
        self._active_filters: dict[str, Any] = {}
        self._rows: dict[str, Mapping[str, Any]] = {}

        self._search_var = tk.StringVar()
        self._status_var = tk.StringVar(value="all")

        self._build_filters()
        self._build_table()
        self._build_footer()

        self.refresh()

    # ------------------------------------------------------------------
    # Construcción de UI
    # ------------------------------------------------------------------
    def _build_filters(self) -> None:
        container = tk.Frame(self, bg=theme.SURFACE_COLOR)
        container.pack(fill=tk.X, pady=(0, 12))

        search_label = tk.Label(container, text="Buscar", bg=theme.SURFACE_COLOR)
        search_label.pack(side=tk.LEFT, padx=(0, 8))
        search_entry = tk.Entry(container, textvariable=self._search_var, width=32)
        search_entry.pack(side=tk.LEFT, padx=(0, 12))
        search_entry.bind("<Return>", lambda _event: self._apply_filters())

        status_label = tk.Label(container, text="Estado", bg=theme.SURFACE_COLOR)
        status_label.pack(side=tk.LEFT, padx=(0, 8))
        status_menu = ttk.Combobox(
            container,
            textvariable=self._status_var,
            width=14,
            values=self._status_options(),
            state="readonly",
        )
        status_menu.pack(side=tk.LEFT, padx=(0, 12))

        apply_button = tk.Button(container, text="Aplicar", command=self._apply_filters)
        theme.style_primary_button(apply_button)
        apply_button.pack(side=tk.LEFT, padx=4)

        clear_button = tk.Button(container, text="Limpiar", command=self._clear_filters)
        theme.style_secondary_button(clear_button)
        clear_button.pack(side=tk.LEFT, padx=4)

        new_button = tk.Button(container, text="Nuevo cliente", command=self._open_create_dialog)
        theme.style_primary_button(new_button)
        new_button.pack(side=tk.RIGHT, padx=(4, 0))

        export_button = tk.Button(container, text="Exportar CSV", command=self._export_csv)
        theme.style_secondary_button(export_button)
        export_button.pack(side=tk.RIGHT, padx=4)

        import_commit_button = tk.Button(
            container, text="Importar (commit)", command=lambda: self._import_customers("commit")
        )
        theme.style_secondary_button(import_commit_button)
        import_commit_button.pack(side=tk.RIGHT, padx=4)

        import_preview_button = tk.Button(
            container, text="Importar (preview)", command=lambda: self._import_customers("preview")
        )
        theme.style_secondary_button(import_preview_button)
        import_preview_button.pack(side=tk.RIGHT, padx=4)

    def _build_table(self) -> None:
        table_container = tk.Frame(self, bg=theme.SURFACE_COLOR)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "email", "phone", "status")
        self._tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "name": "Nombre",
            "email": "Email",
            "phone": "Teléfono",
            "status": "Estado",
        }
        widths = {"name": 220, "email": 180, "phone": 120, "status": 90}
        for column in columns:
            self._tree.heading(column, text=headings[column])
            self._tree.column(column, width=widths[column], anchor=tk.W)

        vsb = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.bind("<<TreeviewSelect>>", self._handle_selection)
        self._tree.bind("<Double-1>", self._handle_double_click)

    def _build_footer(self) -> None:
        footer = tk.Frame(self, bg=theme.SURFACE_COLOR)
        footer.pack(fill=tk.X, pady=(12, 0))

        self._pagination_label = tk.Label(footer, text="Página 1 de 1", bg=theme.SURFACE_COLOR)
        self._pagination_label.pack(side=tk.LEFT)

        prev_button = tk.Button(footer, text="Anterior", command=lambda: self._change_page(-1))
        theme.style_secondary_button(prev_button)
        prev_button.pack(side=tk.RIGHT, padx=4)

        next_button = tk.Button(footer, text="Siguiente", command=lambda: self._change_page(1))
        theme.style_secondary_button(next_button)
        next_button.pack(side=tk.RIGHT, padx=4)

        self._pagination_buttons = {"prev": prev_button, "next": next_button}

    # ------------------------------------------------------------------
    # Acciones y helpers
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        result = customer_service.list_customers(
            page=self._current_page,
            size=self.PAGE_SIZE,
            sort="created_at,DESC",
            filters=self._active_filters or None,
            search=self._search_term,
        )
        self._populate(result)

    def _populate(self, result: Any) -> None:
        self._tree.delete(*self._tree.get_children())
        self._rows.clear()

        for row in result.data:
            customer_id = str(row.get("id"))
            full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            status = row.get("status", "").capitalize()
            values = (
                full_name or "(Sin nombre)",
                row.get("email", ""),
                row.get("phone", ""),
                status,
            )
            self._tree.insert("", tk.END, iid=customer_id, values=values)
            self._rows[customer_id] = row

        meta = result.meta
        self._total_pages = max(1, int(meta.get("totalPages", 1)))
        self._current_page = max(1, min(self._current_page, self._total_pages))
        page = self._current_page
        total = int(meta.get("total", len(result.data)))
        size = int(meta.get("size", self.PAGE_SIZE))
        start = (page - 1) * size + 1 if total else 0
        end = min(page * size, total) if total else 0
        self._pagination_label.configure(
            text=f"Página {page} de {self._total_pages} · Mostrando {start}-{end} de {total}"
        )

        self._pagination_buttons["prev"].configure(state=tk.NORMAL if page > 1 else tk.DISABLED)
        self._pagination_buttons["next"].configure(
            state=tk.NORMAL if page < self._total_pages else tk.DISABLED
        )

    def _apply_filters(self) -> None:
        self._search_term = self._search_var.get().strip() or None
        status = self._status_var.get()
        filters: dict[str, Any] = {}
        if status and status not in {"all", "todos"}:
            filters["status"] = normalise_status(status)
        self._active_filters = filters
        self._current_page = 1
        self.refresh()

    def _clear_filters(self) -> None:
        self._search_var.set("")
        self._status_var.set("all")
        self._search_term = None
        self._active_filters.clear()
        self._current_page = 1
        self.refresh()

    def _change_page(self, delta: int) -> None:
        new_page = self._current_page + delta
        if new_page < 1 or new_page > self._total_pages:
            return
        self._current_page = new_page
        self.refresh()

    def _handle_selection(self, _event: tk.Event) -> None:
        if not self._on_select:
            return
        selection = self._tree.selection()
        if not selection:
            return
        customer_id = selection[0]
        try:
            self._on_select(int(customer_id))
        except ValueError:
            self._on_select(customer_id)  # type: ignore[arg-type]

    def _handle_double_click(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        customer_id = selection[0]
        row = self._rows.get(customer_id)
        if not row:
            return
        self._open_edit_dialog(row)

    def _open_create_dialog(self) -> None:
        CustomerFormDialog(
            self.winfo_toplevel(),
            title="Nuevo cliente",
            on_submit=self._create_customer,
        )

    def _open_edit_dialog(self, customer: Mapping[str, Any]) -> None:
        CustomerFormDialog(
            self.winfo_toplevel(),
            title="Editar cliente",
            on_submit=lambda data: self._update_customer(int(customer.get("id")), data),
            initial=customer,
        )

    def _create_customer(self, data: Mapping[str, str]) -> None:
        try:
            payload = validate_customer_payload(data)
            record = customer_service.create_customer(payload)
            messagebox.showinfo("Clientes", "Cliente creado correctamente")
            self.refresh()
            if self._on_select:
                try:
                    self._on_select(int(record.get("id")))
                except Exception:
                    pass
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo crear el cliente: {exc}")

    def _update_customer(self, customer_id: int, data: Mapping[str, str]) -> None:
        try:
            payload = validate_customer_payload(data)
            customer_service.update_customer(customer_id, payload)
            messagebox.showinfo("Clientes", "Cliente actualizado correctamente")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo actualizar el cliente: {exc}")

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Exportar clientes",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            rows: list[Mapping[str, Any]] = []
            page = 1
            while True:
                result = customer_service.list_customers(
                    page=page,
                    size=200,
                    sort="created_at,DESC",
                    filters=self._active_filters or None,
                    search=self._search_term,
                )
                rows.extend(result.data)
                if page >= int(result.meta.get("totalPages", 1)):
                    break
                page += 1

            headers = [
                ("id", "ID"),
                ("first_name", "Nombre"),
                ("last_name", "Apellido"),
                ("email", "Email"),
                ("phone", "Teléfono"),
                ("status", "Estado"),
                ("tax_id", "Identificación"),
            ]
            csv_export.export_csv(Path(path), rows, headers)
            messagebox.showinfo("Clientes", f"Exportación completada en {path}")
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo exportar: {exc}")

    def _import_customers(self, mode: str) -> None:
        path = filedialog.askopenfilename(
            title="Importar clientes",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            return

        valid_rows = 0
        created = 0
        updated = 0
        preview_created = 0
        preview_updated = 0
        errors: list[str] = []

        try:
            with open(path, newline="", encoding="utf-8") as handler:
                reader = csv.DictReader(handler)
                if not reader.fieldnames:
                    raise ValueError("El archivo no contiene encabezados")

                for line_number, row in enumerate(reader, start=2):
                    try:
                        mapped = self._map_csv_row(row)
                        payload = validate_customer_payload(mapped)
                        customer_id = payload.get("id")
                        if mode == "commit":
                            payload.pop("id", None)
                            if customer_id:
                                customer_service.update_customer(int(customer_id), payload)
                                updated += 1
                            else:
                                customer_service.create_customer(payload)
                                created += 1
                        else:
                            if customer_id:
                                preview_updated += 1
                            else:
                                preview_created += 1
                        valid_rows += 1
                    except Exception as exc:
                        # Acumulamos errores para mostrar un resumen al finalizar.
                        errors.append(f"Línea {line_number}: {exc}")

            if mode == "preview":
                message = (
                    f"Filas válidas: {valid_rows}\n"
                    f"Posibles creaciones: {preview_created}\n"
                    f"Posibles actualizaciones: {preview_updated}\n"
                    f"Errores: {len(errors)}"
                )
                if errors:
                    message += "\n\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        message += "\n..."
                messagebox.showinfo("Preview importación", message)
            else:
                summary = (
                    f"Importación finalizada. Creados: {created}, Actualizados: {updated}, "
                    f"Errores: {len(errors)}"
                )
                if errors:
                    summary += "\n\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        summary += "\n..."
                messagebox.showinfo("Importación", summary)
                self.refresh()
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo importar: {exc}")

    def _map_csv_row(self, row: Mapping[str, Any]) -> MutableMapping[str, Any]:
        mapped: MutableMapping[str, Any] = {}
        for key, value in row.items():
            if not key:
                continue
            normalised_key = key.strip().lower()
            cleaned_value = (value or "").strip()
            if normalised_key in {"id"}:
                mapped["id"] = cleaned_value
            elif normalised_key in {"first_name", "nombre"}:
                mapped["first_name"] = cleaned_value
            elif normalised_key in {"last_name", "apellido"}:
                mapped["last_name"] = cleaned_value
            elif normalised_key in {"email", "correo"}:
                mapped["email"] = cleaned_value
            elif normalised_key in {"phone", "telefono"}:
                mapped["phone"] = cleaned_value
            elif normalised_key in {"tax_id", "identificacion"}:
                mapped["tax_id"] = cleaned_value
            elif normalised_key in {"status", "estado"}:
                mapped["status"] = cleaned_value
        return mapped

    def _status_options(self) -> Sequence[str]:
        return ("all", customer_service.ACTIVE_STATUS, customer_service.INACTIVE_STATUS)


class CustomerFormDialog(tk.Toplevel):
    """Diálogo reutilizable para altas/ediciones de clientes."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        on_submit: Callable[[Mapping[str, str]], None],
        initial: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self._on_submit = on_submit

        self._first_name_var = tk.StringVar(value=(initial or {}).get("first_name", ""))
        self._last_name_var = tk.StringVar(value=(initial or {}).get("last_name", ""))
        self._email_var = tk.StringVar(value=(initial or {}).get("email", ""))
        self._phone_var = tk.StringVar(value=(initial or {}).get("phone", ""))
        self._tax_id_var = tk.StringVar(value=(initial or {}).get("tax_id", ""))
        self._status_var = tk.StringVar(value=(initial or {}).get("status", customer_service.ACTIVE_STATUS))

        self._build_form()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.resizable(False, False)
        self.wait_visibility()
        self.focus_set()

    def _build_form(self) -> None:
        container = tk.Frame(self, padx=20, pady=16, bg=theme.SURFACE_COLOR)
        container.pack(fill=tk.BOTH, expand=True)

        self._add_field(container, "Nombre", self._first_name_var, row=0)
        self._add_field(container, "Apellido", self._last_name_var, row=1)
        self._add_field(container, "Email", self._email_var, row=2)
        self._add_field(container, "Teléfono", self._phone_var, row=3)
        self._add_field(container, "Identificación", self._tax_id_var, row=4)

        status_label = tk.Label(container, text="Estado")
        status_label.grid(row=5, column=0, sticky=tk.W, pady=4)
        status_combo = ttk.Combobox(
            container,
            textvariable=self._status_var,
            values=(customer_service.ACTIVE_STATUS, customer_service.INACTIVE_STATUS),
            state="readonly",
        )
        status_combo.grid(row=5, column=1, sticky=tk.EW, pady=4)

        container.columnconfigure(1, weight=1)

        button_frame = tk.Frame(container, bg=theme.SURFACE_COLOR)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(12, 0))

        cancel_button = tk.Button(button_frame, text="Cancelar", command=self.destroy)
        theme.style_secondary_button(cancel_button)
        cancel_button.pack(side=tk.RIGHT, padx=4)

        submit_button = tk.Button(button_frame, text="Guardar", command=self._submit)
        theme.style_primary_button(submit_button)
        submit_button.pack(side=tk.RIGHT, padx=4)

    def _add_field(self, master: tk.Misc, label: str, variable: tk.StringVar, *, row: int) -> None:
        lbl = tk.Label(master, text=label)
        lbl.grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = tk.Entry(master, textvariable=variable)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=4)

    def _submit(self) -> None:
        data = {
            "first_name": self._first_name_var.get(),
            "last_name": self._last_name_var.get(),
            "email": self._email_var.get(),
            "phone": self._phone_var.get(),
            "tax_id": self._tax_id_var.get(),
            "status": self._status_var.get(),
        }
        try:
            # Antes de invocar el servicio validamos manualmente los campos
            # obligatorios y el formato de email/teléfono para ofrecer feedback
            # inmediato en la interfaz sin tocar la base de datos.
            payload = validate_customer_payload(data)
            self._on_submit(payload)
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Clientes", str(exc))
