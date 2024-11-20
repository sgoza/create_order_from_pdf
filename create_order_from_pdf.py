#!/usr/bin/env python3
"""
ddsafdsaf
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
#INPUT_FOLDER = r"C:\LX\import\apotea"
#OUTPUT_FOLDER = r"C:\LX\import\apotea\pyramid"
INPUT_FOLDER = r"."
OUTPUT_FOLDER = r"./output"

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
            page = pdf_file.pages[0]

            bounding_box_no_header = (
                0,  # x0
                0.4 * float(page.height),  # top
                page.width,  # x1
                page.height,  # bottom
            )
            page_no_header = page.within_bbox(bounding_box_no_header)

            table = page_no_header.extract_table(
                table_settings={
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": [38, 68, 349, 415, 465, 510, 564],
                }
            )

            return table

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
