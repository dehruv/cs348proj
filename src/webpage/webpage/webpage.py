from rxconfig import config

import sqlite3
import plotly.figure_factory as ff
import scipy as sc
import reflex as rx
import pandas as pd

f = open("data/consts.txt", "r")
last_median = float(f.read())
f.close()

con = sqlite3.connect("data/shortages.db")
cur = con.cursor()
cur.execute("""
SELECT DISTINCT ` Therapeutic Category` 
FROM shortages
WHERE ` Status` = "Current"
GROUP BY ` Therapeutic Category`
""")
res = cur.fetchall()
res = {r for row in res for r in row[0].split("; ")}
table = pd.read_sql(
    """
SELECT `Generic Name`, 
`Company Name`, 
`Date of Update`, 
` Reason for Shortage`, 
` Therapeutic Category`, 
`Payment Limit` FROM shortages
WHERE ` Status` = "Current"
""",
    con
)

cur.execute("""
DROP INDEX IF EXISTS category                    
""")

cur.execute("""
CREATE INDEX category
ON shortages(` Therapeutic Category`);    
""")


class SelectionState(rx.State):
    names: list[str] = list(res)
    checks: dict[str, bool] = {r: False for r in res}
    df: pd.DataFrame = table

    def handle_checkbox(self, name, state):
        self.checks[name] = state
        therapies = [
            f"` Therapeutic Category` LIKE \"%{name}%\"" for name, s in self.checks.items() if s]

        self.df = pd.read_sql(f"""
SELECT `Generic Name`, 
`Company Name`, 
`Date of Update`, 
` Reason for Shortage`, 
` Therapeutic Category`, 
`Payment Limit` FROM shortages
WHERE ` Status` = "Current"
{'AND' if therapies else ''} {" OR ".join(therapies)}
""", con)


class FormState(rx.State):
    form_data: dict = {}
    df: pd.DataFrame = table

    def handle_submit(self, form_data: dict):
        self.form_data = form_data
        self.df.loc[len(self.df)] = list(self.form_data.values())
        self.df.index = self.df.index + 1
        self.df = self.df.sort_index()


class Cond(rx.State):
    show: bool = False
    checks: dict[str, bool] = {r: False for r in res}

    def change1(self):
        self.show = not (self.show)


class TickerState(rx.State):
    price: float = last_median
    diff: float = 0
    increase: str = "increase"

    def increase_or_decrease(self, curr):
        if (curr-self.price) >= 0:
            self.increase = "increase"
            self.diff = (curr-self.price)/100
        else:
            self.increase = "decrease"
            self.diff = (self.price-curr)/100


def price_dist(df):
    x = df[df["Payment Limit"] < 20]["Payment Limit"]
    fig = ff.create_distplot(
        [x], group_labels=['Price'],
        bin_size=0.25,
        show_rug=False,
        show_hist=False)
    return fig


style = {
    "background_color": "#C7C8F7",
    "font_family": "Libre Franklin",
    rx.section: {
        "padding_left": "3em",
        "padding_right": "1em",
        "padding_bottom": "1em",
        "padding_top": "1em",
    },
    rx.card: {
        "background_color": "#F4F4FF"
    },
    rx.plotly: {
        "font_family": "Libre Franklin"
    }
}


def index() -> rx.Component:
    TickerState.increase_or_decrease(table["Payment Limit"].median())
    return rx.box(
        rx.box(
            rx.text("Current US Generic Drugs in Shortage",
                    font_weight="bold",
                    font_size="2.5em",
                    padding_bottom=".5em"),
            rx.text(
                "This dashboard is updated daily on FDA published data."
            ),
            rx.text(
                "Created by: ",
                rx.link(
                    "Dhruv Narayanan",
                    href="https://github.com/dehruv",
                    is_external=True
                ),
            ),
            rx.text(
                "For any questions or comments please reach out to: dhruv.n80@gmail.com"),
            padding_top="2em",
            padding_bottom="1em",
            padding_left="2em",
        ),
        rx.flex(
            rx.vstack(
                rx.card(
                    rx.chakra.stat(
                        rx.chakra.stat_label(
                            "Median Reimbursement Price", color="#6A6A6A"),
                        rx.chakra.stat_number(
                            "$" + str(table["Payment Limit"].median())),
                        rx.chakra.stat_help_text(
                            table["Payment Limit"].median() - TickerState.diff, rx.chakra.stat_arrow(
                                type_=TickerState.increase)
                        ),
                    ),
                    size="5"
                ),
                flew_grow="1",
            ),
            rx.vstack(
                rx.card(
                    rx.plotly(data=price_dist(table), layout=dict(
                        title="Distribution of Reimbursement Prices",
                        showlegend=False,
                        plot_bgcolor="#F4F4FF",
                        paper_bgcolor="#F4F4FF",
                        xaxis=dict(title="Price($)"),
                        yaxis=dict(title="Density"),
                    ), config=dict(
                        displayModeBar=False,
                    ), height="800px",
                        width="4000px"
                    ),
                    font_family="Libre Franklin",
                    size="3",
                    flex_grow="1"
                ),
            ),
            flex_wrap="wrap",
            justify="center",
            align="stretch",
            spacing="9",
        ),
        rx.box(
            rx.heading("Select Therapeutic Category:"),
            padding_left="0",
            padding_bottom="0.5em",
            padding_top="0.5em",
            padding_right="0.5em"
        ),
        rx.grid(
            rx.foreach(
                SelectionState.names,
                lambda name: rx.checkbox(
                    name, on_change=lambda state: SelectionState.handle_checkbox(
                        name, state)
                )
            ),
            columns="4"),
        rx.heading("Insert a new shortage:",
                   padding_top="0.5em",
                   padding_bottom="0.5em"),
        rx.form(
            rx.flex(
                rx.input(placeholder="Generic Name", name="drug name"),
                rx.input(placeholder="Company Name", name="company name"),
                rx.input(placeholder="Date of Update", name="date"),
                rx.input(placeholder="Reason for Shortage", name="reason"),
                rx.input(placeholder="Therapeutic Category", name="category"),
                rx.input(placeholder="Payment Limit", name="payment limit"),
                rx.button("Submit", type="submit"),
                spacing='4',
                padding_bottom="0.5em",
            ),
            on_submit=FormState.handle_submit,
        ),
        rx.button("Inserted Data or Subsetted Data", on_click=Cond.change1),
        rx.cond(
            Cond.show,
            rx.data_table(
                data=SelectionState.df,
                pagination=True,
                search=False,
                sort=True,
                resizable=True,
                font_size='50%',
                padding_right="0",
                padding_left="2.5em",
                padding_top="2.5em",
                padding_bottom="2.5em"
            ),
            rx.data_table(
                data=FormState.df,
                pagination=True,
                search=False,
                sort=True,
                resizable=True,
                font_size='50%',
                padding_right="0",
                padding_left="2.5em",
                padding_top="2.5em",
                padding_bottom="2.5em"
            ),
        )
    )


app = rx.App(
    style=style,
    stylesheets=[
        "/styles.css",
    ],
)

app.add_page(index)
