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
        return {"selected": False, "mid": None, "fields": {c: "" for c in EDITABLE_COLUMNS}}

    rows = [blank_row()]

    # ---- migration bookkeeping -------------------------------------------

    def normalize():
        for r in rows:
            r["selected"] = False
        for i, r in enumerate(rows):
            if r["mid"] is not None:
                if i == 0 or rows[i - 1]["mid"] != r["mid"]:
                    j = i
                    while j + 1 < len(rows) and rows[j + 1]["mid"] == r["mid"]:
                        j += 1
                    if j == i:
                        r["mid"] = None
        labels = {}
        for r in rows:
            if r["mid"] is not None and r["mid"] not in labels:
                labels[r["mid"]] = f"M{len(labels) + 1}"

    def migration_runs():
        runs = []
        i = 0
        while i < len(rows):
            if rows[i]["mid"] is None:
                i += 1
                continue
            j = i
            while j + 1 < len(rows) and rows[j + 1]["mid"] == rows[i]["mid"]:
                j += 1
            runs.append((i, j))
            i = j + 1
        return runs

    # ---- actions ----------------------------------------------------------

    def add_row(e=None):
        rows.append(blank_row())
        rebuild()

    def delete_row(idx):
        rows.pop(idx)
        normalize()
        rebuild()

    def move_row(idx, step):
        row = rows[idx]
        if row["mid"] is None:
            k = idx + step
            while 0 <= k < len(rows) and rows[k]["mid"] is not None:
                k += step
            if not 0 <= k < len(rows):
                return
            rows[idx], rows[k] = rows[k], rows[idx]
        else:
            j = idx + step
            if not 0 <= j < len(rows):
                return
            other = rows[j]
            rows[idx], rows[j] = rows[j], rows[idx]
            if other["mid"] != row["mid"]:
                row["mid"] = None
        normalize()
        rebuild()

    def combine_selected(e=None):
        selected = [i for i, r in enumerate(rows) if r["selected"]]
        if len(selected) < 2:
            return
        migration_counter["n"] += 1
        mid = migration_counter["n"]
        group = [rows[i] for i in selected]
        insert_at = selected[0]
        for i in reversed(selected):
            rows.pop(i)
        for offset, r in enumerate(group):
            r["mid"] = mid
            r["selected"] = False
            rows.insert(insert_at + offset, r)
        normalize()
        rebuild()

    def clear_selected(e=None):
        for r in rows:
            r["mid"] = None
        normalize()
        rebuild()

    def delete_selected_migrations(e=None):
        selected_mids = {
            r["mid"] for r in rows if r["selected"] and r["mid"] is not None
        }
        if not selected_mids:
            return
        for r in rows:
            if r["mid"] in selected_mids:
                r["mid"] = None
        normalize()
        rebuild()

    # ---- table ------------------------------------------------------------

    def make_cell(row, col):
        def on_change(e, row=row, col=col):
            row["fields"][col] = e.control.value

        return ft.TextField(
            value=row["fields"][col],
            on_change=on_change,
            dense=True,
            border=ft.UnderlineInputBorder(),
            content_padding=ft.Padding(left=6, right=6, top=0, bottom=0),                  
        )

    def migration_cell(idx):
        row = rows[idx]
        if row["mid"] is None:
            return ft.Container(ft.Text("", italic=True, color=ft.Colors.GREY_400))
        runs = migration_runs()
        run = next((a, b) for a, b in runs if a <= idx <= b)
        a, b = run
        seq = [rows[k]["fields"]["QC"] or "?" for k in range(a, b + 1)]
        label = f"M{[r for r in runs].index(run) + 1}"
        piece = ("]─╮ " if idx == a else "  │") if idx < b else "]─╯ "
        return ft.Container(
            ft.Text(
                f"{piece}",
                color=ft.Colors.RED_400,
                weight=ft.FontWeight.BOLD,
                size=13,
            ),
            tooltip=f"{label}: " + " → ".join(seq),
        )

    def rebuild():
        table.rows.clear()
        runs = migration_runs()
        for idx, row in enumerate(rows):
            cells = [
                ft.DataCell(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_DROP_UP,
                                        icon_size=16,
                                        tooltip="Move up",
                                        on_click=lambda e, idx=idx: move_row(idx, -1),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_DROP_DOWN,
                                        icon_size=16,
                                        tooltip="Move down",
                                        on_click=lambda e, idx=idx: move_row(idx, 1),
                                    ),
                                ],
                                spacing=0,
                                tight=True,
                            ),
                            ft.Row(
                                [
                                    ft.Checkbox(
                                        value=row["selected"],
                                        on_change=lambda e, row=row: row.__setitem__(
                                            "selected", e.control.value
                                        ),
                                        scale=0.8,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_size=16,
                                        tooltip="Delete row",
                                        on_click=lambda e, idx=idx: delete_row(idx),
                                    ),
                                ],
                                spacing=0,
                                tight=True,
                            ),
                        ],
                        spacing=0,
                        tight=True,
                    )
                )
            ]
            for col in COLUMNS:
                if col == "Migrations":
                    cells.append(ft.DataCell(migration_cell(idx)))
                else:
                    cells.append(ft.DataCell(make_cell(row, col)))
            table.rows.append(ft.DataRow(cells=cells))
        count_text.value = f"{len(rows)} rows · {len(runs)} migrations"
        page.update()

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Sel. / Move", size=12, width=60, max_lines=2)),
            *[
                ft.DataColumn(
                    ft.Text(
                        "" if c == "Migrations" else c,
                        size=12,
                        width=18 if c == "Migrations" else (90 if c in ("QC", "LOA", "Moves", "Mov. rem", "ETS", "Service", "OWNER") else 110),
                        max_lines=2,
                    )
                )
                for c in COLUMNS
            ],
        ],
        rows=[],
        heading_row_height=48,
        data_row_min_height=48,
        data_row_max_height=float("inf"),
        column_spacing=24,
        horizontal_margin=12,
        horizontal_lines=ft.BorderSide(width=0),
        vertical_lines=ft.BorderSide(width=0),
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
                ft.OutlinedButton(
                    "Delete selected migration",
                    icon=ft.Icons.DELETE,
                    on_click=delete_selected_migrations,
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
