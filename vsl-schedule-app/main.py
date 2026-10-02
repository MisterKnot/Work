from typing import Optional

import flet as ft

from database import (
    connect, seed_if_empty, list_entries, get_entry,
    add_entry, update_entry, delete_entry, ScheduleEntry,
)

SHIFT_ORDER = ["MORNING", "AFTERNOON", "NIGHT"]
SHIFT_ICONS = {"MORNING": ft.Icons.WB_SUNNY, "AFTERNOON": ft.Icons.WB_CLOUDY, "NIGHT": ft.Icons.NIGHTLIGHT}


def fmt(value, dt_fmt="%d/%m %H:%M"):
    if value is None:
        return "-"
    if isinstance(value, str) and "T" in value:
        date_part, time_part = value.split("T")
        d = date_part.split("-")
        return f"{d[2]}/{d[1]} {time_part[:5]}"
    return str(value)


class VesselScheduleApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.conn = connect()
        seed_if_empty(self.conn)
        self.filter_text = ""
        self.build_ui()

    def build_ui(self):
        self.search_field = ft.TextField(
            hint_text="Search vessel or service...",
            on_change=self.on_search, prefix_icon=ft.Icons.SEARCH, dense=True
        )
        self.table_areas = {
            shift: ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
            for shift in SHIFT_ORDER
        }
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            length=len(SHIFT_ORDER),
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label=shift, icon=SHIFT_ICONS[shift])
                            for shift in SHIFT_ORDER
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[self.table_areas[shift] for shift in SHIFT_ORDER],
                    ),
                ],
            ),
        )
        self.add_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, content=ft.Text("Add Vessel"), on_click=self.on_add
        )
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [self.search_field, self.tabs],
                    spacing=10, expand=True,
                ),
                padding=20, expand=True,
            ),
            self.add_button,
        )
        self.refresh_table()

    def current_shift(self):
        return SHIFT_ORDER[self.tabs.selected_index]

    def on_search(self, e):
        self.filter_text = self.search_field.value.strip().upper()
        self.refresh_table()

    def on_tab_change(self, e):
        self.refresh_table()

    def refresh_table(self):
        for shift, area in self.table_areas.items():
            entries = [
                x for x in list_entries(self.conn, shift)
                if not self.filter_text
                or self.filter_text in x.vessel.upper()
                or (x.service or "").upper().startswith(self.filter_text)
            ]
            area.controls = [self.build_table(entries)]
        self.page.update()

    def build_table(self, entries):
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("QC")), ft.DataColumn(ft.Text("Vessel")),
                ft.DataColumn(ft.Text("Service")), ft.DataColumn(ft.Text("Owner")),
                ft.DataColumn(ft.Text("LOA")), ft.DataColumn(ft.Text("Moves")),
                ft.DataColumn(ft.Text("Mov. rem.")),
                ft.DataColumn(ft.Text("Arrival Road")),
                ft.DataColumn(ft.Text("Working Start")),
                ft.DataColumn(ft.Text("ETS")),
                ft.DataColumn(ft.Text("")),
            ],
            rows=[self.entry_row(x) for x in entries],
            heading_row_height=40, data_row_min_height=40,
        )

    def entry_row(self, entry: ScheduleEntry):
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(str(entry.qc))),
                ft.DataCell(ft.Text(entry.vessel, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(entry.service or "-")),
                ft.DataCell(ft.Text(entry.owner or "-")),
                ft.DataCell(ft.Text(fmt(entry.loa))),
                ft.DataCell(ft.Text(str(entry.moves) if entry.moves is not None else "-")),
                ft.DataCell(ft.Text(str(entry.moves_remaining) if entry.moves_remaining is not None else "-")),
                ft.DataCell(ft.Text(fmt(entry.arrival_road))),
                ft.DataCell(ft.Text(fmt(entry.working_start))),
                ft.DataCell(ft.Text(fmt(entry.ets))),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                                      on_click=lambda _, i=entry.id: self.on_edit(i)),
                        ft.IconButton(ft.Icons.DELETE, icon_size=18, tooltip="Delete",
                                      on_click=lambda _, i=entry.id: self.on_delete(i)),
                    ], spacing=0)
                ),
            ]
        )

    def entry_dialog(self, entry: Optional[ScheduleEntry] = None):
        is_new = entry is None
        if is_new:
            entry = ScheduleEntry(id=None, shift=self.current_shift(), qc=0, vessel="")

        def parse_dt(s):
            if not s:
                return None
            try:
                return s.replace("T", " ")
            except Exception:
                return s

        qc_field = ft.TextField(label="QC", value=str(entry.qc) if entry.qc is not None else "")
        vessel_field = ft.TextField(label="Vessel", value=entry.vessel)
        service_field = ft.TextField(label="Service", value=entry.service or "")
        owner_field = ft.TextField(label="Owner", value=entry.owner or "")
        loa_field = ft.TextField(label="LOA (m)", value=str(entry.loa) if entry.loa is not None else "")
        moves_field = ft.TextField(label="Moves", value=str(entry.moves) if entry.moves is not None else "")
        moves_rem_field = ft.TextField(label="Moves remaining", value=str(entry.moves_remaining) if entry.moves_remaining is not None else "")
        arrival_field = ft.TextField(label="Arrival at Piraeus Road (YYYY-MM-DD HH:MM)", value=parse_dt(entry.arrival_road) or "")
        working_field = ft.TextField(label="Working start (YYYY-MM-DD HH:MM)", value=parse_dt(entry.working_start) or "")
        ets_field = ft.TextField(label="ETS (YYYY-MM-DD HH:MM)", value=parse_dt(entry.ets) or "")
        shift_dropdown = ft.Dropdown(
            label="Shift", value=entry.shift, options=[ft.dropdown.Option(s) for s in SHIFT_ORDER]
        )
        error_text = ft.Text("", color=ft.Colors.RED, size=12)

        def save(_):
            if not vessel_field.value.strip():
                error_text.value = "Vessel name is required."
                dlg.open = False
                self.page.open(dlg)
                return
            try:
                qc_val = int(qc_field.value or 0)
                loa_val = float(loa_field.value) if loa_field.value.strip() else None
                moves_val = int(moves_field.value) if moves_field.value.strip() else None
                moves_rem_val = int(moves_rem_field.value) if moves_rem_field.value.strip() else None
            except ValueError:
                error_text.value = "QC/Moves must be integers, LOA a number."
                self.page.update()
                return

            def norm_dt(v):
                if not v.strip():
                    return None
                return v.strip().replace(" ", "T")

            new_entry = ScheduleEntry(
                id=entry.id, shift=shift_dropdown.value, qc=qc_val,
                vessel=vessel_field.value.strip(), service=service_field.value.strip() or None,
                owner=owner_field.value.strip() or None, loa=loa_val, moves=moves_val,
                moves_remaining=moves_rem_val, arrival_road=norm_dt(arrival_field.value),
                working_start=norm_dt(working_field.value), ets=norm_dt(ets_field.value),
            )
            if is_new:
                add_entry(self.conn, new_entry)
            else:
                update_entry(self.conn, new_entry)
            self.page.close(dlg)
            self.refresh_table()

        def cancel(_):
            self.page.close(dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Vessel" if is_new else f"Edit {entry.vessel}"),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    [
                        shift_dropdown, qc_field, vessel_field, service_field, owner_field,
                        loa_field, moves_field, moves_rem_field, arrival_field,
                        working_field, ets_field, error_text,
                    ],
                    tight=True, spacing=12, scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Save", on_click=save),
                ft.TextButton("Cancel", on_click=cancel),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

    def on_add(self, e):
        self.entry_dialog(None)

    def on_edit(self, entry_id):
        entry = get_entry(self.conn, entry_id)
        if entry:
            self.entry_dialog(entry)

    def on_delete(self, entry_id):
        entry = get_entry(self.conn, entry_id)

        def confirm(_):
            delete_entry(self.conn, entry_id)
            self.page.close(dlg)
            self.refresh_table()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete entry?"),
            content=ft.Text(f"Delete {entry.vessel} (QC {entry.qc}) from {entry.shift}?"),
            actions=[
                ft.TextButton("Delete", on_click=confirm),
                ft.TextButton("Cancel", on_click=lambda _: self.page.close(dlg)),
            ],
        )
        self.page.open(dlg)


def main(page: ft.Page):
    page.title = "Vessel Schedule — PCT"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    VesselScheduleApp(page)


if __name__ == "__main__":
    ft.run(main)
