import flet as ft

COLORS = {
    "vessel": ["#1e88e5", "#43a047", "#e53935", "#8e24aa", "#fb8c00", "#00897b"],
    "qc": "#455a64",
    "chain": "#90a4ae",
}


def vessel_color(name, mapping):
    if name not in mapping:
        mapping[name] = COLORS["vessel"][len(mapping) % len(COLORS["vessel"])]
    return mapping[name]


# ---------------------------------------------------------------------------
# The data model: a migration sequence is an ORDERED chain of (qc, vessel) steps.
# Order matters; the same vessel can appear at multiple positions.
# ---------------------------------------------------------------------------
STEPS = [
    {"position": 1, "qc": 43, "vessel": "BG BLUE"},
    {"position": 2, "qc": 42, "vessel": "BG BLUE"},
    {"position": 3, "qc": 39, "vessel": "JAN"},
]
NEXT_STEPS = [
    {"position": 1, "qc": 38, "vessel": "JAN"},
    {"position": 2, "qc": 41, "vessel": "BG BLUE"},
]


def main(page: ft.Page):
    page.title = "QC Migration Demo"
    page.padding = 30
    color_map = {}

    def step_badge(step, first=False, last=False):
        c = vessel_color(step["vessel"], color_map)
        return ft.Container(
            content=ft.Row(
                [
                    ft.CircleAvatar(
                        content=ft.Text(str(step["position"]), size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=c, width=24, height=24,
                    ),
                    ft.Container(
                        padding=ft.Padding(10, 6, 10, 6),
                        border=ft.Border(
                            left=ft.BorderSide(1.5, c), top=ft.BorderSide(1.5, c),
                            right=ft.BorderSide(1.5, c), bottom=ft.BorderSide(1.5, c),
                        ),
                        border_radius=8,
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.PRECISION_MANUFACTURING, size=15, color=c),
                                ft.Text(f"QC {step['qc']}", size=13, color=c, weight=ft.FontWeight.BOLD),
                                ft.Container(width=1, height=14, bgcolor=c),
                                ft.Icon(ft.Icons.DIRECTIONS_BOAT, size=15, color=c),
                                ft.Text(step["vessel"], size=13, color=c),
                            ], spacing=6,
                        ),
                    ),
                ], spacing=8,
            ),
        )

    def arrow_down():
        return ft.Container(
            content=ft.Column(
                [ft.Icon(ft.Icons.ARROW_DOWNWARD, size=16, color=COLORS["chain"])],
                alignment=ft.Alignment(0, 0),
            ),
            margin=ft.Margin(11, 0, 0, 0),
        )

    def sequence_flow(title, steps):
        chain = []
        for i, s in enumerate(steps):
            chain.append(step_badge(s))
            if i < len(steps) - 1:
                chain.append(arrow_down())
        return ft.Container(
            padding=15,
            border=ft.Border(
                left=ft.BorderSide(1, "#cfd8dc"), top=ft.BorderSide(1, "#cfd8dc"),
                right=ft.BorderSide(1, "#cfd8dc"), bottom=ft.BorderSide(1, "#cfd8dc"),
            ),
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 15),
            content=ft.Column(
                [
                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color="#607d8b"),
                    ft.Column(chain, spacing=4),
                ], spacing=10,
            ),
        )

    # ---------------------------------------------------------------
    # Bracket ("}") style: the Excel-like view. Rows of a table; a
    # leading bracket spans the joined steps, drawn as stacked borders.
    # ---------------------------------------------------------------
    def bracket_rows(steps):
        rows = []
        for i, s in enumerate(steps):
            n = len(steps)
            joined = n > 1
            left = ft.Container(
                width=18,
                height=34,
                border=ft.Border(
                    left=ft.BorderSide(2, COLORS["chain"]) if joined else ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    top=ft.BorderSide(2, COLORS["chain"]) if joined and i == 0 else ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    bottom=ft.BorderSide(2, COLORS["chain"]) if joined and i == n - 1 else ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    right=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                ),
            )
            rows.append(
                ft.Row(
                    [
                        left,
                        ft.Container(width=4),
                        ft.Text(str(s["position"]), size=12, width=20, color="#90a4ae"),
                        ft.Text(f"QC {s['qc']}", size=13, weight=ft.FontWeight.BOLD, width=70),
                        ft.Text(s["vessel"], size=13, width=110,
                                color=vessel_color(s["vessel"], color_map),
                                weight=ft.FontWeight.W_600),
                    ],
                    spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return rows

    # ---------------------------------------------------------------
    # Interactive: click a row -> highlight the whole sequence
    # ---------------------------------------------------------------
    highlight = {"seq": None}

    def seq_table(title, steps, seq_id):
        rows = []
        for s in steps:
            selected = highlight["seq"] == seq_id
            rows.append(
                ft.DataRow(
                    color=ft.Colors.with_opacity(0.12, vessel_color(s["vessel"], color_map)) if selected else None,
                    on_select_change=lambda e, sid=seq_id: toggle(sid),
                    cells=[
                        ft.DataCell(ft.Text(str(s["position"]), size=12)),
                        ft.DataCell(ft.Text(f"QC {s['qc']}", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(s["vessel"],
                                             color=vessel_color(s["vessel"], color_map))),
                        ft.DataCell(ft.Icon(
                            ft.Icons.LINK if highlight["seq"] == seq_id else ft.Icons.LINK_OFF,
                            size=14, color=COLORS["chain"],
                        )),
                    ],
                )
            )
        return ft.DataTable(
            heading_row_height=32,
            data_row_min_height=34,
            columns=[
                ft.DataColumn(ft.Text("#")),
                ft.DataColumn(ft.Text("QC")),
                ft.DataColumn(ft.Text("Vessel")),
                ft.DataColumn(ft.Text("")),
            ],
            rows=rows,
        )

    def toggle(seq_id):
        highlight["seq"] = None if highlight["seq"] == seq_id else seq_id
        rebuild()

    interactive_tables = {}

    def rebuild():
        interactive_tables.clear()
        col = interactive.content.controls = [
            ft.Text("3. Click a row to highlight its sequence", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Sequence A", size=12, color="#607d8b"),
            seq_table("A", STEPS, "A"),
            ft.Text("Sequence B", size=12, color="#607d8b"),
            seq_table("B", NEXT_STEPS, "B"),
        ]
        page.update()

    page.add(
        ft.Column(
            [
                ft.Text("QC Migration — three ways to show joined sequences",
                        size=22, weight=ft.FontWeight.BOLD),
                ft.Text("QC 43/BG BLUE → QC 42/BG BLUE → QC 39/JAN   (same vessel can appear twice)",
                        size=13, color="#607d8b"),
                ft.Divider(height=20),

                ft.Text("1. Flow view — explicit order, top to bottom", size=16, weight=ft.FontWeight.BOLD),
                sequence_flow("Sequence A", STEPS),
                sequence_flow("Sequence B", NEXT_STEPS),
                ft.Divider(height=20),

                ft.Text("2. Bracket view — Excel-style \"}\" spanning joined steps", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=10,
                    border=ft.Border(
                        left=ft.BorderSide(1, "#cfd8dc"), top=ft.BorderSide(1, "#cfd8dc"),
                        right=ft.BorderSide(1, "#cfd8dc"), bottom=ft.BorderSide(1, "#cfd8dc"),
                    ),
                    border_radius=10,
                    content=ft.Row(
                        [
                            ft.Column(bracket_rows(STEPS)),
                            ft.VerticalDivider(width=30),
                            ft.Column(bracket_rows(NEXT_STEPS)),
                        ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ),
                ft.Divider(height=20),
            ],
            spacing=8, scroll=ft.ScrollMode.AUTO, expand=True,
        )
    )
    interactive = ft.Container(content=ft.Column())
    page.controls[0].controls.append(interactive)
    rebuild()


if __name__ == "__main__":
    ft.run(main)
