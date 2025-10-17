from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from app.services import customer_service
from app.ui import theme

from .validators import validate_customer_payload

__all__ = ["CustomerDetailView"]


class CustomerDetailView(tk.Frame):
    """Vista de detalle con formulario editable y resumen financiero."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=theme.SURFACE_COLOR)
        self._customer_id: Optional[int] = None

        self._first_name_var = tk.StringVar()
        self._last_name_var = tk.StringVar()
        self._email_var = tk.StringVar()
        self._phone_var = tk.StringVar()
        self._tax_id_var = tk.StringVar()
        self._status_var = tk.StringVar(value=customer_service.ACTIVE_STATUS)

        self._orders_count = tk.StringVar(value="0")
        self._orders_total = tk.StringVar(value="$0.00")
        self._orders_balance = tk.StringVar(value="$0.00")
        self._payments_count = tk.StringVar(value="0")
        self._payments_total = tk.StringVar(value="$0.00")
        self._outstanding = tk.StringVar(value="$0.00")

        self._build_layout()

    # ------------------------------------------------------------------
    # Construcción UI
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        header = tk.Label(
            self,
            text="Detalle del cliente",
            font=theme.font(14, "bold"),
            bg=theme.SURFACE_COLOR,
        )
        header.pack(anchor=tk.W, pady=(0, 12))

        form_frame = tk.LabelFrame(
            self, text="Información básica", padx=16, pady=12, bg=theme.SURFACE_COLOR
        )
        form_frame.pack(fill=tk.X, pady=(0, 16))
        form_frame.columnconfigure(1, weight=1)

        self._add_field(form_frame, "Nombre", self._first_name_var, row=0)
        self._add_field(form_frame, "Apellido", self._last_name_var, row=1)
        self._add_field(form_frame, "Email", self._email_var, row=2)
        self._add_field(form_frame, "Teléfono", self._phone_var, row=3)
        self._add_field(form_frame, "Identificación", self._tax_id_var, row=4)

        status_label = tk.Label(form_frame, text="Estado")
        status_label.grid(row=5, column=0, sticky=tk.W, pady=4)
        status_combo = ttk.Combobox(
            form_frame,
            textvariable=self._status_var,
            values=(customer_service.ACTIVE_STATUS, customer_service.INACTIVE_STATUS),
            state="readonly",
        )
        status_combo.grid(row=5, column=1, sticky=tk.EW, pady=4)

        button_frame = tk.Frame(form_frame, bg=theme.SURFACE_COLOR)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky=tk.E)

        deactivate_button = tk.Button(button_frame, text="Desactivar", command=self._deactivate)
        theme.style_secondary_button(deactivate_button)
        deactivate_button.pack(side=tk.RIGHT, padx=4)

        save_button = tk.Button(button_frame, text="Guardar cambios", command=self._save)
        theme.style_primary_button(save_button)
        save_button.pack(side=tk.RIGHT, padx=4)

        summary_frame = tk.LabelFrame(
            self, text="Resumen financiero", padx=16, pady=12, bg=theme.SURFACE_COLOR
        )
        summary_frame.pack(fill=tk.X)
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)

        self._add_summary_row(summary_frame, "Pedidos registrados", self._orders_count, 0)
        self._add_summary_row(summary_frame, "Monto total de pedidos", self._orders_total, 1)
        self._add_summary_row(summary_frame, "Saldo pendiente (pedidos)", self._orders_balance, 2)
        self._add_summary_row(summary_frame, "Pagos registrados", self._payments_count, 3)
        self._add_summary_row(summary_frame, "Monto total pagado", self._payments_total, 4)
        self._add_summary_row(summary_frame, "Saldo por cobrar", self._outstanding, 5)

        refresh_button = tk.Button(summary_frame, text="Actualizar resumen", command=self._refresh_summary)
        theme.style_secondary_button(refresh_button)
        refresh_button.grid(row=6, column=0, columnspan=2, pady=(12, 0))

    def _add_field(self, master: tk.Misc, label: str, variable: tk.StringVar, *, row: int) -> None:
        lbl = tk.Label(master, text=label)
        lbl.grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = tk.Entry(master, textvariable=variable)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=4)

    def _add_summary_row(self, master: tk.Misc, label: str, variable: tk.StringVar, row: int) -> None:
        lbl = tk.Label(master, text=label)
        lbl.grid(row=row, column=0, sticky=tk.W, pady=2)
        value = tk.Label(master, textvariable=variable, font=theme.font(11, "bold"))
        value.grid(row=row, column=1, sticky=tk.E, pady=2)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def load_customer(self, customer_id: int) -> None:
        """Carga los datos del cliente indicado en el formulario."""

        record = customer_service.get_customer(customer_id)
        if not record:
            messagebox.showwarning("Clientes", "No se encontró el cliente solicitado")
            return

        self._customer_id = customer_id
        self._first_name_var.set(record.get("first_name", ""))
        self._last_name_var.set(record.get("last_name", ""))
        self._email_var.set(record.get("email", ""))
        self._phone_var.set(record.get("phone", ""))
        self._tax_id_var.set(record.get("tax_id", ""))
        self._status_var.set(record.get("status", customer_service.ACTIVE_STATUS))

        self._refresh_summary()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _save(self) -> None:
        if self._customer_id is None:
            return

        data = {
            "first_name": self._first_name_var.get(),
            "last_name": self._last_name_var.get(),
            "email": self._email_var.get(),
            "phone": self._phone_var.get(),
            "tax_id": self._tax_id_var.get(),
            "status": self._status_var.get(),
        }
        try:
            # Validamos en la capa de interfaz para mostrar errores antes de
            # invocar el servicio que persiste cambios en la base de datos.
            payload = validate_customer_payload(data)
            customer_service.update_customer(self._customer_id, payload)
            messagebox.showinfo("Clientes", "Datos actualizados correctamente")
            self.load_customer(self._customer_id)
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo actualizar: {exc}")

    def _deactivate(self) -> None:
        if self._customer_id is None:
            return
        if not messagebox.askyesno(
            "Clientes",
            "¿Desea desactivar a este cliente?",
        ):
            return
        try:
            customer_service.deactivate_customer(self._customer_id)
            messagebox.showinfo("Clientes", "Cliente desactivado")
            self.load_customer(self._customer_id)
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo desactivar: {exc}")

    def _refresh_summary(self) -> None:
        if self._customer_id is None:
            return
        try:
            summary = customer_service.get_financial_summary(self._customer_id)
            orders = summary.get("orders", {})
            payments = summary.get("payments", {})
            self._orders_count.set(str(orders.get("count", 0)))
            self._orders_total.set(self._format_currency(orders.get("totalAmount", 0.0)))
            self._orders_balance.set(self._format_currency(orders.get("balanceDue", 0.0)))
            self._payments_count.set(str(payments.get("count", 0)))
            self._payments_total.set(self._format_currency(payments.get("totalPaid", 0.0)))
            self._outstanding.set(self._format_currency(summary.get("outstandingBalance", 0.0)))
        except Exception as exc:
            messagebox.showerror("Clientes", f"No se pudo obtener el resumen: {exc}")

    # ------------------------------------------------------------------
    # Utilitarios
    # ------------------------------------------------------------------
    @staticmethod
    def _format_currency(value: Any) -> str:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            amount = 0.0
        return f"${amount:,.2f}"
