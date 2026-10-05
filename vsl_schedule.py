import flet as ft

COLUMNS = [
    "QC",
    "Vessel",
    "Migrations",
    "Service",
    "OWNER",
    "LOA",
    "Moves",
    "Mov. rem",
    "Arrival at Piraeus Road",
    "Working start time",
    "ETS",
]

EDITABLE_COLUMNS = [c for c in COLUMNS if c != "Migrations"]


def main(page: ft.Page):
    page.title = "Vessel Schedule"
    page.window.width = 1400
    page.scroll = ft.ScrollMode.AUTO

    migration_counter = {"n": 0}

    def blank_row():
        return {
            "selected": False,
            "migration": "",
            "fields": {c: "" for c in EDITABLE_COLUMNS},
        }

    rows = [blank_row()]

    def make_cell(row, col):
        def on_change(e, row=row, col=col):
            row["fields"][col] = e.control.value

        return ft.TextField(
            value=row["fields"][col],
            on_change=on_change,
            dense=True,
            border=ft.UnderlineInputBorder(),
            content_padding=ft.Padding(left=6, right=6, top=4, bottom=4),
            width=140 if col in ("Arrival at Piraeus Road", "Working start time", "ETS") else 110,
        )

    def rebuild():
        table.rows.clear()
        for idx, row in enumerate(rows):
            cells = [
                ft.DataCell(
                    ft.Row(
                        [
                            ft.Checkbox(
                                value=row["selected"],
                                on_change=lambda e, row=row: row.__setitem__(
                                    "selected", e.control.value
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                tooltip="Delete row",
                                on_click=lambda e, idx=idx: delete_row(idx),
                            ),
                        ],
                        spacing=0,
                    )
                )
            ]
            for col in COLUMNS:
                if col == "Migrations":
                    cells.append(
                        ft.DataCell(
                            ft.Container(
                                ft.Text(
                                    row["migration"] or "—",
                                    italic=not bool(row["migration"]),
                                    color=ft.Colors.RED_400 if row["migration"] else None,
                                    weight=ft.FontWeight.BOLD if row["migration"] else None,
                                ),
                                width=130,
                            )
                        )
                    )
                else:
                    cells.append(ft.DataCell(make_cell(row, col)))
            table.rows.append(ft.DataRow(cells=cells))
        count_text.value = f"{len(rows)} rows · {migration_counter['n']} migrations"
        page.update()

    def add_row(e=None):
        rows.append(blank_row())
        rebuild()

    def delete_row(idx):
        rows.pop(idx)
        rebuild()

    def combine_selected(e=None):
        selected = [i for i, r in enumerate(rows) if r["selected"]]
        if len(selected) < 2:
            snack.content = ft.Text("Select at least two rows to combine a migration.")
            page.open(snack)
            return
        migration_counter["n"] += 1
        tag = f"[M{migration_counter['n']}: " + " + ".join(
            f"{rows[i]['fields']['QC'] or '?'}↔{rows[i]['fields']['Vessel'] or '?'}"
            for i in selected
        ) + "]"
        for i in selected:
            rows[i]["migration"] = tag
            rows[i]["selected"] = False
        rebuild()

    def clear_selected(e=None):
        for r in rows:
            r["selected"] = False
            r["migration"] = ""
        rebuild()

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Sel.", size=12)),
            *[ft.DataColumn(ft.Text(c, size=12)) for c in COLUMNS],
        ],
        rows=[],
        heading_row_height=48,
        vertical_lines=ft.BorderSide(color=ft.Colors.GREY_300),
        horizontal_lines=ft.BorderSide(color=ft.Colors.GREY_300),
    )

    count_text = ft.Text()
    snack = ft.SnackBar(content=ft.Text(""))

    page.add(
        ft.Row(
            [
                ft.Text("Vessel Schedule", size=24, weight=ft.FontWeight.BOLD),
                count_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Row(
            [
                ft.FilledButton("Add row", icon=ft.Icons.ADD, on_click=add_row),
                ft.FilledTonalButton(
                    "Combine selected → Migration",
                    icon=ft.Icons.MERGE_TYPE,
                    on_click=combine_selected,
                ),
                ft.OutlinedButton(
                    "Clear migrations",
                    icon=ft.Icons.CLEAR_ALL,
                    on_click=clear_selected,
                ),
            ]
        ),
        ft.Card(
            ft.Container(
                ft.Column([ft.Row([table], scroll=ft.ScrollMode.AUTO)], tight=True),
                padding=10,
            )
        ),
    )

    rebuild()


ft.run(main)
