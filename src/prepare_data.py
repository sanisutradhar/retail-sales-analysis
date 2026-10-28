from pathlib import Path

import pandas as pd


SOURCE_FILE = Path("data/raw/online_retail_II.xlsx")
OUTPUT_FILE = Path("data/processed/retail_lines.csv")


def normalize_column_name(column: str) -> str:
    """Convert a column name to lowercase snake_case."""
    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found at {SOURCE_FILE}. "
            "Download the UCI workbook and save it there."
        )

    workbook = pd.ExcelFile(SOURCE_FILE)
    dataframes = [
        pd.read_excel(SOURCE_FILE, sheet_name=sheet_name)
        for sheet_name in workbook.sheet_names
    ]

    data = pd.concat(dataframes, ignore_index=True)
    data.columns = [normalize_column_name(column) for column in data.columns]

    data = data.rename(
        columns={
            "price": "unit_price",
            "invoiceno": "invoice_no",
            "stockcode": "stock_code",
            "invoicedate": "invoice_date",
        }
    )

    required_columns = {
        "invoice_no",
        "stock_code",
        "quantity",
        "unit_price",
        "invoice_date",
        "customer_id",
        "country",
    }

    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(
            "The workbook is missing expected columns: "
            + ", ".join(sorted(missing_columns))
        )

    data["invoice_date"] = pd.to_datetime(
        data["invoice_date"],
        errors="coerce",
    )
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_FILE, index=False)

    print(f"Rows prepared: {len(data):,}")
    print(f"Saved file: {OUTPUT_FILE}")
    print("\nMissing values by column:")
    print(data.isna().sum().sort_values(ascending=False).head(10))


if __name__ == "__main__":
    main()
