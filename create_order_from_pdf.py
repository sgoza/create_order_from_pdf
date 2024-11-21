#!/usr/bin/env python3
"""
Extracts order tables from PDF files and generates an order file formatted for
integration into the business system.
"""

import sys
import os
import datetime
import logging
import pdfplumber

CUSTOMER_CODE = "1112L"
DELIVERY_DAYS = 10
TABLE_COLUMNS = {
    "article": 2,
    "quantity": 3,
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def extract_table_from_order_pdf(infile):
    """
    Extracts a table from the given order PDF file.

    Args:
        infile (str): Path to the input PDF file.

    Returns:
        list or None: Extracted table data, or None if no table is found.
    """

    try:
        with pdfplumber.open(infile) as pdf_file:
            tables = []
            for index, page in enumerate(pdf_file.pages):
                if index == 0:
                    bounding_box_no_header = (
                        0,  # x0
                        0.4 * float(page.height),  # top
                        page.width,  # x1
                        0.92 * float(page.height)  # bottom
                    )
                    page = page.within_bbox(bounding_box_no_header)

                else:
                    bounding_box_no_top = (
                        0,  # x0
                        0.12 * float(page.height),  # top
                        page.width,  # x1
                        0.92 * float(page.height)  # bottom
                    )
                    page = page.within_bbox(bounding_box_no_top)

                table = page.extract_table(
                    table_settings={
                        "vertical_strategy": "explicit",
                        "explicit_vertical_lines": [38, 68, 349, 415, 465, 510, 564],
                    }
                )

                if table:
                    tables.extend(table)

            return tables

    except Exception as e:
        logging.error("Error processing PDF file: %s", e)
        return None


def create_order_file(table):
    """
    Generates an order file based on the extracted table data.

    Args:
        table (list): A list of rows extracted from the PDF table.
    """

    date_today = datetime.date.today().strftime("%Y-%m-%d")
    date_delivery = (
        datetime.date.today() + datetime.timedelta(days=DELIVERY_DAYS)
    ).strftime("%Y-%m-%d")

    number = "10_1"
    order_filename = f"O{CUSTOMER_CODE}_{date_today}_{number}"

    if os.path.exists(order_filename):
        logging.warning(
            "The file '%s' already exists and will be overwritten.", order_filename
        )

    order_info = [
        "01",
        "#12211;O",
        f"#12205;{CUSTOMER_CODE}",
        "#12225;",
        "#12213;GN",
        f"#12312;{date_today}",
        f"#12313;{date_delivery}",
    ]

    for row in table[1:]:
        if len(row) >= max(TABLE_COLUMNS.values()):
            if row[2]:
                order_article = [
                    "11",
                    f"#12401;{row[TABLE_COLUMNS['article']]}",
                    f"#12441;{row[TABLE_COLUMNS['quantity']]}",
                ]
                order_info.extend(order_article)

        else:
            logging.warning("Malformed row skipped: %s", row)
            continue

    order_info = "\n".join(order_info)

    try:
        with open(order_filename, "w", encoding="utf-8") as order_file:
            order_file.write(order_info)
        logging.info("Order file '%s' successfully created.", order_filename)

    except IOError as e:
        logging.error("Failed to write the order file: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <order-pdf-file>")
        sys.exit(1)

    infile = sys.argv[1]
    if not os.path.exists(infile):
        print(f"File '{infile}' does not exist.")
        sys.exit(2)

    if not infile.lower().endswith(".pdf"):
        logging.warning(
            "The file does not have a '.pdf' extension. Attempting to process it anyway."
        )

    table = extract_table_from_order_pdf(infile)
    if not table:
        print("No table found in the PDF. Please check the input file.")
        sys.exit(3)

    create_order_file(table)
