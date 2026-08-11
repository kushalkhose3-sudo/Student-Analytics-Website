from flask import Flask, render_template, request
import pandas as pd
import os
import plotly.express as px

app = Flask(__name__, template_folder="templates")

# =========================================================
# CONFIGURATION
# =========================================================

app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# FEATURES
# =========================================================

@app.route("/features")
def features():
    return render_template("features.html")


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():
    return render_template("About.html")


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact")
def contact():
    return render_template("Contact.html")


# =========================================================
# UPLOAD PAGE
# =========================================================

@app.route("/uploadpage")
def uploadpage():
    return render_template("upload.html")


# =========================================================
# UPLOAD DATASET
# =========================================================

@app.route("/upload", methods=["POST"])
def upload():

    try:

        # -------------------------------------------------
        # Check file
        # -------------------------------------------------

        file = request.files.get("file")

        if not file or file.filename == "":
            return render_template(
                "Error.html",
                message="⚠️ No file selected. Please upload a CSV or Excel file."
            )

        # -------------------------------------------------
        # Check extension
        # -------------------------------------------------

        filename = file.filename.lower()

        if not filename.endswith((".csv", ".xlsx", ".xls")):
            return render_template(
                "Error.html",
                message="⚠️ Invalid file type. Please upload CSV or Excel file."
            )

        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(filepath)

        # -------------------------------------------------
        # Read dataset
        # -------------------------------------------------

        if filename.endswith(".csv"):

            df = pd.read_csv(filepath)

        elif filename.endswith((".xlsx", ".xls")):

            df = pd.read_excel(filepath)

        # -------------------------------------------------
        # Check dataset
        # -------------------------------------------------

        if df.empty:

            return render_template(
                "Error.html",
                message="⚠️ The uploaded dataset is empty."
            )

        # -------------------------------------------------
        # Remove completely empty rows/columns
        # -------------------------------------------------

        df = df.dropna(axis=1, how="all")
        df = df.dropna(axis=0, how="all")

        # -------------------------------------------------
        # Clean column names
        # -------------------------------------------------

        df.columns = [
            str(col).strip()
            for col in df.columns
        ]

        # -------------------------------------------------
        # Dataset information
        # -------------------------------------------------

        total_records = len(df)

        total_columns = len(df.columns)

        columns = df.columns.tolist()

        # -------------------------------------------------
        # Create complete HTML table
        # -------------------------------------------------

        table_html = df.to_html(
            classes="data-table",
            index=False,
            border=0,
            justify="center"
        )

        # -------------------------------------------------
        # Save latest dataset
        # -------------------------------------------------

        last_dataset_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            "last_dataset.csv"
        )

        df.to_csv(
            last_dataset_path,
            index=False
        )

        # =================================================
        # AUTOMATIC CHART
        # =================================================

        numeric_cols = df.select_dtypes(
            include="number"
        ).columns.tolist()

        chart_html = ""

        if len(numeric_cols) >= 1:

            avg_values = (
                df[numeric_cols]
                .mean()
                .reset_index()
            )

            avg_values.columns = [
                "Column",
                "Average Value"
            ]

            fig = px.bar(
                avg_values,
                x="Column",
                y="Average Value",
                title="Average Values per Numeric Column",
                text_auto=".2f"
            )

            fig.update_layout(
                template="plotly_white",
                margin=dict(
                    l=40,
                    r=40,
                    t=70,
                    b=40
                )
            )

            chart_html = fig.to_html(
                full_html=False,
                include_plotlyjs="cdn"
            )

        else:

            chart_html = """
            <div class="no-chart-message">
                No numeric columns were found for automatic chart generation.
            </div>
            """

        # =================================================
        # RETURN DASHBOARD
        # =================================================

        return render_template(
            "dashboard.html",
            table=table_html,
            columns=columns,
            total_records=total_records,
            total_columns=total_columns,
            chart_html=chart_html
        )

    except Exception as e:

        return render_template(
            "Error.html",
            message=f"⚠️ Unexpected error: {str(e)}"
        )


# =========================================================
# CHART BUILDER
# =========================================================

@app.route("/chartbuilder")
def chartbuilder():

    dataset_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "last_dataset.csv"
    )

    columns = []

    if os.path.exists(dataset_path):

        try:

            df = pd.read_csv(dataset_path)

            columns = df.columns.tolist()

        except Exception:

            columns = []

    return render_template(
        "charts.html",
        columns=columns
    )


# =========================================================
# CUSTOM CHART
# =========================================================

@app.route("/custom_chart", methods=["POST"])
def custom_chart():

    try:

        dataset_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            "last_dataset.csv"
        )

        # -------------------------------------------------
        # Check dataset
        # -------------------------------------------------

        if not os.path.exists(dataset_path):

            return render_template(
                "Error.html",
                message="⚠️ No dataset found. Please upload a dataset first."
            )

        # -------------------------------------------------
        # Read dataset
        # -------------------------------------------------

        df = pd.read_csv(dataset_path)

        # -------------------------------------------------
        # Form values
        # -------------------------------------------------

        x_col = request.form.get("x_col")

        y_col = request.form.get("y_col")

        chart_type = request.form.get("chart_type")

        filter_type = request.form.get("rowFilter")

        row_count = request.form.get("rowCount")

        # -------------------------------------------------
        # Validate columns
        # -------------------------------------------------

        if not x_col or x_col not in df.columns:

            return render_template(
                "Error.html",
                message="⚠️ Invalid X-axis column selection."
            )

        if not y_col or y_col not in df.columns:

            return render_template(
                "Error.html",
                message="⚠️ Invalid Y-axis column selection."
            )

        # -------------------------------------------------
        # Top / Bottom N
        # -------------------------------------------------

        if row_count:

            try:

                n = int(row_count)

                if n > 0:

                    if filter_type == "top":

                        df = df.head(n)

                    elif filter_type == "bottom":

                        df = df.tail(n)

            except ValueError:

                pass

        # =================================================
        # CREATE CHART
        # =================================================

        if chart_type == "bar":

            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} by {x_col}"
            )

        elif chart_type == "line":

            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} Trend by {x_col}"
            )

        elif chart_type == "scatter":

            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} vs {x_col}"
            )

        elif chart_type == "pie":

            fig = px.pie(
                df,
                names=x_col,
                values=y_col,
                title=f"{y_col} Distribution by {x_col}"
            )

        else:

            return render_template(
                "Error.html",
                message="⚠️ Unsupported chart type."
            )

        # -------------------------------------------------
        # Chart styling
        # -------------------------------------------------

        fig.update_layout(
            template="plotly_white",
            margin=dict(
                l=40,
                r=40,
                t=70,
                b=40
            ),
            font=dict(
                family="Arial"
            )
        )

        # -------------------------------------------------
        # Convert to HTML
        # -------------------------------------------------

        chart_html = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn"
        )

        # -------------------------------------------------
        # Return
        # -------------------------------------------------

        return render_template(
            "charts.html",
            columns=df.columns.tolist(),
            chart_html=chart_html
        )

    except Exception as e:

        return render_template(
            "Error.html",
            message=f"⚠️ Chart builder error: {str(e)}"
        )


# =========================================================
# 404 ERROR
# =========================================================

@app.errorhandler(404)
def page_not_found(e):

    return render_template(
        "Error.html",
        message="404 - Page Not Found"
    ), 404


# =========================================================
# 500 ERROR
# =========================================================

@app.errorhandler(500)
def internal_error(e):

    return render_template(
        "Error.html",
        message="500 - Internal Server Error"
    ), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )








