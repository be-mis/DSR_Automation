from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db import connection
from .forms import FileFieldForm, ValidationForm
import traceback
from difflib import SequenceMatcher
import re
from .models import DSR, Validation
from collections import defaultdict

from django.shortcuts import get_object_or_404
import os
import re
from django.views.decorators.csrf import csrf_exempt
import logging
from DSR_APP.queries import fetch_item_code_results, fetch_bp_code_results
from DSR_APP.services.sap_query_conn import execute_query
from .mapping import chain_mapping, db_mapping
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from decimal import Decimal
from django.db import transaction #For batch processing
import uuid  # For generating unique instance identifiers
# from .views2 import validate_dsr

bp_code_results = []
item_code_results = []
ALLOWED_FILE_EXTENSIONS = ['xls', 'xlsx', 'xlsm', 'csv', 'xlsb', 'xltx', 'xltm']

logger = logging.getLogger(__name__)


# #########QUERY TO FETCH BP CODES WITH BRANCH ID 
# def fetch_bp_code_results(chain, database):
#     """Fetch the BP Code results and store them in a global list."""
#     global bp_code_results

#     query = f"""
#         SELECT 
#             a."CardCode",
#             a."CardName",
#             a."AddID"
#         FROM OCRD a
#         LEFT JOIN CPN1 b ON b."BpCode" = a."CardCode"
#         INNER JOIN OCPN c ON c."CpnNo" = b."CpnNo" AND c."U_CType" = 'SKU' AND c."U_Chain" = '{chain}'
#         WHERE a."frozenFor" = 'N'
#     """

#     try:
#         # Execute the query and fetch results
#         bp_code_results = execute_query(query, database)
#     except Exception as e:
#         # Handle any errors gracefully and leave bp_code_results empty
#         bp_code_results = []

    
# #########QUERY TO FETCH ITEM CODES WITH PRICE
# def fetch_item_code_results(chain, database):
#     global item_code_results
#     query = f"""
#         SELECT 
#             b."ItemCode",
#             b."ItemName",
#             b."U_SKU",
#             d."Price",
#             b."U_BarCode"
#         FROM OCPN a
#         JOIN CPN2 b ON a."CpnNo" = b."CpnNo"
#         JOIN OITM c ON c."ItemCode" = b."ItemCode"
#         JOIN ITM1 d ON d."ItemCode" = c."ItemCode"
#         WHERE a."U_Chain" = '{chain}' 
#         AND d."PriceList" = 2 
#         AND b."U_SKU" IS NOT NULL
#         AND c."frozenFor" = 'N';
#     """

#     try:
#         item_code_results = execute_query(query, database)
#     except Exception as e:
#         item_code_results = []



def get_headers(chain):

    DATE = ['date', 'tran date', 'date sold', 'transaction start', 'transaction date']


    if chain in ['ALLHOME', 'FISHER']:
        QTY = ['qty sold', 'qty', 'qty/kilo', 'quantity', 'units sold ty']
        DATE = ['date', 'tran date', 'date sold', 'transaction start', 'transaction date']
        GROSS = ['net sales']
        STORECODE = ['branch']

    # elif chain == 'HWORKS':
    #     QTY = ['ttl sold']
    #     DATE = ['transaction date']
    #     GROSS = ['total amount', 'gross sales amt', 'sales amount', 'gross amount', 'gross sales', 'gross sales ty']

    elif chain == 'WDS':
        QTY = ['qty sold', 'qty', 'qty/kilo', 'quantity', 'units sold ty']
        DATE = ['transaction date']
        GROSS = ['total amount', 'gross sales amt', 'sales amount', 'gross amount', 'gross sales', 'gross sales ty']
        STORECODE = ['site code']

    else:
        QTY = ['qty sold', 'qty', 'qty/kilo', 'quantity', 'units sold ty']
        DATE = ['date', 'tran date', 'date sold', 'transaction start']
        GROSS = ['total amount', 'gross sales amt', 'sales amount', 'gross amount', 'gross sales', 'gross sales ty']
        STORECODE = ['site code', 'store code', 'branch code']

    return {
        'SKU': ['matcode', 'sku#', 'sku', 'sku number', 'sku code'],
        'BRANCH': ['store name', 'branch', 'site name', 'branch name', 'store description', 'vendor name'],
        'DATE': DATE,
        'DESC': ['description', 'item description', 'item name', 'sku description', 'product', 'product description'],
        'STORE_CODE': STORECODE,
        'QTY': QTY,
        'GROSS': GROSS,
        'BPCODE': ['bp code'],
        'ITEMCODE':['item code', 'item number']
    }


@csrf_exempt
def process_data(request, instance):
    """Process and extract data from the uploaded files, then save it to the database."""
    extracted_data = []  # Local variable to store extracted data.
    global item_code_results, bp_code_results

    def get_column_name(possible_names, df_columns):
        """
        Find the first matching column name from possible_names in df_columns (case-insensitive and whitespace-agnostic).
        """
        df_columns_normalized = {col.strip().lower(): col for col in df_columns}  # Normalize column names
        for name in possible_names:
            if name.strip().lower() in df_columns_normalized:
                return df_columns_normalized[name.strip().lower()]  # Return the original column name
        return None

    ###Dynamically check where the row starts for extracting the data
    def detect_header_row(df, chain):
        """
        Automatically detect the header row by scanning the first few rows for matching column names.
        """
        HEADERS = get_headers(chain)

        for i, row in df.iterrows():
            normalized_row = row.astype(str).str.strip().str.lower()
            if any(col_name.lower() in normalized_row.values for col_list in HEADERS.values() for col_name in col_list):
                print(f"Header row detected at index {i}")
                return i  # Return the row index
        return 0  # Default to the first row if no match is found

    # Fetch all files associated with the given instance
    files = DSR.objects.filter(instance=instance)
    print(f"Processing {len(files)} files for instance {instance}.")


    for file in files:

        # Add BP Code using store_name and chain ------------------------
        file_name = file.raw_file.name.lower().strip().replace(" ", "").replace("_", "")   # Remove spaces and lowercase the file name for comparison
        print(f"Processing file: {file_name}")


        # Determine the appropriate engine based on file extension
        if file_name.endswith('.xls'):
            engine = 'xlrd'  # For .xls files
        else:
            engine = 'openpyxl'  # For .xlsx files


        

        # Get file path
        file_path = file.raw_file.path  # Move file_path assignment here
        # Read the Excel file using the determined engine
        print(f"Reading file from path: {file_path}")
        df = pd.read_excel(file_path, engine=engine, header=None)
        
        database = ''
        for keyword, db_name in db_mapping.items():
            cleaned_keyword = keyword.replace(" ", "").lower()
            if cleaned_keyword in file_name:
                database = db_name


        # Ensure case-insensitive matching and remove spaces for both file name and dictionary keys
        chain = ''
        for keyword, chain_name in chain_mapping.items():
            cleaned_keyword = keyword.replace(" ", "").lower()
            if cleaned_keyword in file_name:
                chain = chain_name
        

        if database == 'EPC' and chain == 'SM':
            chain = 'SM HOMEWORLD'
        elif database == 'NBFI' and chain == 'SM':
            chain = 'SM DEPT. STORE'
        elif not chain:
            chain = None

        print(f"chain is: {chain} ")
                
        if chain and database != '':
            file.chain = chain
            file.database = database
            file.save()
            bp_code_results = fetch_bp_code_results(chain, database)
            item_code_results = fetch_item_code_results(chain, database)
            if item_code_results:
                print(f"Successful ka sa itemcodes")
            elif bp_code_results:
                print(f"Successful ka sa bpcodes")
            else:
                print(f"sad bobo ka")
                


        else:
            print(f"No valid chain found for file: {file.raw_file.name}")
            continue

        #-------------------------------------------------

        if file.chain and file.database != '':
            

            try:
                # Detect the header row dynamically
                print("Detecting header row...")
                header_row = detect_header_row(df, chain)
                HEADERS = get_headers(chain)

                df.columns = df.iloc[header_row].apply(str).str.strip()  # Set the detected header row as columns
                df = df.iloc[header_row + 1:]  # Skip the header row in the data

                # Check if the DATE column exists
                print("Checking for DATE column...")
                date_column = get_column_name(HEADERS['DATE'], df.columns)
                if not date_column:
                    print(f"File {file.raw_file.name} has no DATE column. Including all rows for processing.")

                gross_column = get_column_name(HEADERS['GROSS'], df.columns) #################################ABSOLUTE VALUE
                if not gross_column:
                    print(f"File {file.raw_file.name} has no Gross column. Including all rows for processing.")

                # Map columns dynamically for the remaining columns
                column_map = {}
                missing_headers = []  # List to store missing headers
                for key, col_list in HEADERS.items():
                    matched_col = get_column_name(col_list, df.columns)
                    if not matched_col:
                        # Only return an error for essential columns (e.g., SKU, QTY, GROSS)
                        if key in ['SKU', 'QTY']:
                            print(f"Missing required column for {key}: {', '.join(col_list)}")
                            return HttpResponse(f"Missing required column for {key}: {', '.join(col_list)}", status=400)
                        missing_headers.append(key)  # Add the missing header key to the list
                    column_map[key] = matched_col

                print(f"Column mapping: {column_map}")

                # Print the missing headers if any
                if missing_headers:
                    print(f"Missing headers: {', '.join(missing_headers)}")

                                # Process each row in the DataFrame
                if column_map['GROSS']:
                    valid_rows = df[df.iloc[:, df.columns.get_loc(column_map['DESC'])].notna()]
                    gross_sum = float(valid_rows.iloc[:, valid_rows.columns.get_loc(column_map['GROSS'])].sum())
                    file.total_amount_raw += gross_sum
                    file.total_amount_raw = round(file.total_amount_raw, 2)
                
                # Convert numeric columns if necessary
                df[column_map['SKU']] = pd.to_numeric(df[column_map['SKU']], errors='coerce', downcast='integer')
                df[column_map['QTY']] = pd.to_numeric(df[column_map['QTY']], errors='coerce', downcast='integer')

                # Process each row in the DataFrame
                print("Processing rows...")
                file_data = []


                for index, row in df[pd.notna(df[column_map['QTY']]) & (df[column_map['QTY']] != 0)].iterrows():

                    if all(pd.notna([row[column_map['BRANCH']], row[column_map['SKU']], row[column_map['DESC']],
                                    row[column_map['QTY']]])):

                        # Handle Excel date serial numbers if DATE column is available
                        if date_column:
                            date_value = row[column_map['DATE']]
                            if isinstance(date_value, (int, float)):
                                date_value = pd.to_datetime('1900-01-01') + pd.to_timedelta(date_value - 2, unit='D')
                            else:
                                date_value = pd.to_datetime(date_value, errors='coerce')

                            # Format date if valid
                            date_formatted = date_value.strftime('%m/%d/%Y') if pd.notna(date_value) else None
                        else:
                            # No DATE column, set date to today minus 1 month
                            today = datetime.today()
                            first_of_current_month = today.replace(day=1)
                            last_day_of_previous_month = first_of_current_month - relativedelta(days=1)
                            date_formatted = last_day_of_previous_month.strftime('%m/%d/%Y')

                        # Extract row data
                        row_data = {
                            'row_id': index + 1,
                            'store_name': row[column_map['BRANCH']],
                            'date': date_formatted,
                            'matcode': int(row[column_map['SKU']]) if pd.notna(row[column_map['SKU']]) else None,
                            'qty_sold': int(row[column_map['QTY']]),
                        }

                        # Add BP Code Using store code
                        if column_map.get('STORE_CODE'):
                            row_data['store_code'] = row[column_map['STORE_CODE']]
                        else:
                            row_data['store_code'] = None
                        
                        # Add Item Code
                        if chain == 'SM DEPT. STORE':
                            row_data['item_code'] = row[column_map['ITEMCODE']]
                            row_data['item_description'] = row[column_map['DESC']]
                        else:
                            if chain == 'ALLHOME':
                                row_data = add_item_barcode(row_data['matcode'], row_data)
                            else:
                                row_data = add_item_code(row_data['matcode'], row_data)
                        # Add BP Code
                        if column_map.get('BPCODE'):
                            row_data['bp_code'] = row[column_map['BPCODE']]
                        else:
                            if row_data['store_code']:
                                row_data = add_bp_store_code(row_data['store_name'], row_data['store_code'], row_data, chain)
                            else:
                                row_data = add_bp_code(row_data['store_name'], row_data, chain)
                                

                        # Add Gross Amount and Unit Amount
                        if column_map.get('GROSS'):
                            row_data['total_amount'] = row[column_map['GROSS']]
                            if row_data['qty_sold'] > 0 and row_data['total_amount'] >= 0:  # Non-negative total_amount and positive qty_sold
                                row_data['unit_amount'] = row_data['total_amount'] / row_data['qty_sold']
                            else:  # Handle negative values for qty_sold and total_amount
                                row_data['unit_amount'] = abs(row_data['total_amount']) / row_data['qty_sold']
                        else:
                            if chain == 'ALLHOME':
                                row_data = add_item_barcode(row_data['matcode'], row_data)
                            else:
                                row_data = add_item_price(row_data['matcode'], row_data)


                        if row_data['item_description'] == None:
                            row_data['item_description'] = row[column_map['DESC']]

                        file.total_qty_sold += row_data['qty_sold']
                        file.total_amount_template += row_data['total_amount']
                        file.total_amount_template = round(file.total_amount_template, 2)
                        file.total_amount_raw = file.total_amount_template
                        file_data.append(row_data)


                # Save extracted data for this file to the database
                with transaction.atomic():
                    file.extracted_data = file_data
                    if not file.extracted_data and file.chain != 'Empty' and file.database != 'Empty':
                        file.special_remarks = '------ (0 SALES)'

                    
                    file.save()
                    print(f"{file.raw_file.name} processed successfully")
                    print(f"{file.chain} is the chain")

                # Return extracted data for this file
                extracted_data.append({
                    'file_name': file.raw_file.name,  # Store file name separately
                    'data': file_data
                })
                item_code_results.clear()
                bp_code_results.clear()
            except Exception as e:
                print(f"Error processing file {file.raw_file.name}: {e}")
                print("Traceback:")
                traceback.print_exc()
                continue
        else:
            file.special_remarks = 'NO BU/CHAIN FOUND ON FILE NAME'
            continue

        # After processing all files, render the data
    #CLEANUP
    delete_processed_files(instance)
    print("Finished processing all files.")

    return redirect('generated-page', instance)



##########IF THE RAW FILE DOES NOT HAVE COLUMN FOR THE GROSS SALES (SM BRANCHES), USE THE FETCHED EFFECTIVE PRICE FROM SAP
##########We use the U_SKU here to match the corresponding ItemCode
def add_item_price(skucode, row_data):
    """
    Add price to row_data using item_code_results if GROSS header is not present.
    Ensure total_amount and unit_amount are JSON serializable.
    """
    if not item_code_results:
        row_data["total_amount"] = 0
        row_data["unit_amount"] = 0
        return row_data

    # Ensure matcode is a string for comparison
    new_matcode = str(skucode).strip() if isinstance(skucode, (int, float, Decimal)) else row_data['matcode'].strip()

    # Search for the SKU match in item_code_results
    for record in item_code_results:
        sku = record.get("U_SKU")
        if sku:
            # Ensure SKU is a string and use only the part before the hyphen
            new_sku = str(sku).split('-')[0].strip()
            if new_matcode == new_sku:
                # Convert Decimal price to float for JSON serialization
                row_data["unit_amount"] = float(record.get("Price", 0)) if isinstance(record.get("Price"), Decimal) else record.get("Price", 0)
                row_data['total_amount'] = row_data['unit_amount'] * row_data['qty_sold']
                
                return row_data

    # If no match is found, set total_amount and unit_amount to defaults
    row_data["total_amount"] = 0
    row_data["unit_amount"] = 0

    return row_data

##########IF THE RAW FILE DOES NOT HAVE COLUMN FOR THE GROSS SALES (SM BRANCHES), USE THE FETCHED EFFECTIVE PRICE FROM SAP
##########Some chain uses barcode instead of sku so we use the U_BarCode column in SAP to match with the ItemCode
def add_item_barcode(skucode, row_data):
    if not item_code_results:
        row_data["item_code"] = 'no item code'
        return row_data
    
    # Ensure matcode is a string for comparison
    if isinstance(skucode, (int, float)):
        new_matcode = str(skucode).strip()  # Convert number to string and strip whitespace
    else:
        new_matcode = row_data['matcode'].strip()  # Assume it's already a string and strip whitespace

    # Look for the exact match in item_code_results
    for record in item_code_results:
        sku = record.get("U_BarCode")
        if sku:
            # Ensure SKU is a string for comparison
            new_sku = str(sku).split('-')[0].strip()

            if new_matcode == new_sku:
                # Exact match found, assign the item code
                row_data["item_code"] = record.get("ItemCode")
                row_data["item_description"] = record.get("ItemName") if record.get("ItemName") else row_data.get("item_description")
                return row_data

    # If no match is found, set item_code to None
    row_data["item_code"] = "no item code"
    row_data["item_description"] = None

    return row_data


########ADDING THE ITEM CODE USING THE RAW FILE'S SKU (SKU MATCHING)
def add_item_code(skucode, row_data):
    if not item_code_results:
        row_data["item_code"] = None
        return row_data
    
    # Ensure matcode is a string for comparison
    if isinstance(skucode, (int, float)):
        new_matcode = str(skucode).strip()  # Convert number to string and strip whitespace
    else:
        new_matcode = row_data['matcode'].strip()  # Assume it's already a string and strip whitespace

    # Look for the exact match in item_code_results
    for record in item_code_results:
        sku = record.get("U_SKU")
        if sku:
            # Ensure SKU is a string for comparison
            new_sku = str(sku).split('-')[0].strip()

            if new_matcode == new_sku:
                # Exact match found, assign the item code
                row_data["item_code"] = record.get("ItemCode")
                row_data["item_description"] = record.get("ItemName") if record.get("ItemName") else row_data.get("item_description")
                return row_data

    # If no match is found, set item_code to None
    row_data["item_code"] = "no item code"
    row_data["item_description"] = None
    return row_data

#########ADD BP CODE USING THE RAW FILE'S STORE CODE IF ANY
def add_bp_store_code(store_name, store_code, row_data, chain):
    if not bp_code_results:  # If no results are fetched, return the row_data without a bp_code
        row_data["bp_code"] = None
        return row_data

    if isinstance(store_code, (int,float)):
        new_storecode = str(store_code).strip()  # Convert number to string and strip whitespace
    else:
        new_storecode = row_data['store_code'].strip()

    for record in bp_code_results:
        scode = record.get("AddID")
        if scode:
            new_scode = str(scode).strip()
            if new_storecode == new_scode:
                row_data['bp_code'] = record.get("CardCode")
                return row_data
    row_data["bp_code"] = None
    return row_data
    




##EDIT FIELDS DYNAMICALLY....THIS FUNCTION IS REUSABLE
##Function for editing specific cells will be generalized using this one. You do not need to create one for each column
@csrf_exempt
def edit_field(request, field_name, row_id, file_id):
    try:
        # Get the specific DSR object
        dsr = get_object_or_404(DSR, id=file_id)

        # Extract the row from extracted_data using row_id
        extracted_data = dsr.extracted_data or []
        row = next((item for item in extracted_data if item.get('row_id') == row_id), None)

        if not row:
            return JsonResponse({'success': False, 'error': 'Row not found'}, status=404)

        if request.method == 'POST' and request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            # Update the field dynamically based on `field_name`
            new_value = request.POST.get(field_name)
            if new_value:
                row[field_name] = new_value
                dsr.extracted_data = extracted_data
                dsr.save()
                return JsonResponse({'success': True, field_name: new_value})
            else:
                return JsonResponse({'success': False, 'error': f'{field_name} is missing'}, status=400)

        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    except Exception as e:
        logger.error(f"Error editing {field_name}: {str(e)}")  # Log the error for debugging
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)






#-----------------------------------------MATCH USING Regular Expressions (REGEX)---------------------------

#### ADDING OF BP CODE USING REGEX ONLY(CREATE A SPECIAL CASE MAPPING TO AVOID CONFUSION FOR BRANCHES WITH COMMON WORDS)
## PUT THE LONGER BRANCH NAME WITH COMMON WORD AT THE TOP TO KEEP THE COMMON WORD FROM OVERRIDING THE MATCHING
def count_strict_order_matches(store_name, card_name):
    """Count the number of characters that match in strict order (no jumbling) between store_name and card_name."""
    store_name = store_name.lower()
    card_name = card_name.lower()
    
    # Initialize counters for matches
    match_count = 0
    store_index = 0
    card_index = 0

    while store_index < len(store_name) and card_index < len(card_name):
        if store_name[store_index] == card_name[card_index]:
            match_count += 1
            store_index += 1
        card_index += 1  # Move through the card_name regardless of match

    return match_count

def add_bp_code(store_name, row_data, chain):
    """Add BP Code based on the store_name using strict order matching and special case mapping."""
    
    # Special case mapping for exact matches (manually added)
    # Some characters have multiple match (DAVAO to DAVAO and LANANG DAVAO) so we prioritize the longer one at the top line
    # The system will read LANANG DAVAO first so it will not be a match for DAVAO only
    # The same logic is applied for characters with multiple matches
    if chain == 'OUR HOME':
        special_case_mapping = {
            "LANANG DAVAO": "OUR HOME LANANG DAVAO",
            "CDO 2 PREMIER": "OUR HOME CDO 2 DOWNTOWN PREMIER",
            "DAVAO": "OUR HOME DAVAO",
            "SEASIDE CEBU": "OUR HOME SEASIDE CEBU",
            "CEBU": "OUR HOME CEBU",
        }


    elif chain == 'SM DEPT. STORE':
        special_case_mapping = {
            "SM BALANGA BATAAN": "SM DEPT STORE BATAAN",
            "SM DEPT STORE BATAAN":"SM DEPT STORE BATAAN",
        }

    elif chain == 'ALLHOME':
        special_case_mapping = {
            # "Quezon City": "ALL HOME LIBIS",
            "North Molino": "ALL HOME MOLINO",
            # "Santiago": "ALL HOME BULACAN",
            # "Las Piñas": "ALL HOME MOLINO",
            # "General Trias": "ALL HOME IMUS",
            # "Tanza": "ALL HOME IMUS",
        }
    else:
        # Default special case mapping for other chains
        special_case_mapping = {}

    if not bp_code_results:  # If no results are fetched, return the row_data without a bp_code
        row_data["bp_code"] = None
        return row_data

    store_name_lower = store_name.lower()

    # Check for a special case match first
    for key, value in special_case_mapping.items():
        if key.lower() in store_name_lower:
            # Find the exact record in the results
            best_match = next((record for record in bp_code_results if record.get("CardName") == value), None)
            if best_match:
                row_data["bp_code"] = best_match.get("CardCode")
                return row_data

    # Default to strict order matching if no special case matches for 'OUR HOME' or 'ALLHOME'
    best_match = None
    highest_match_count = 0

    for record in bp_code_results:
        card_name = record.get("CardName")
        if card_name:
            # Calculate the strict order match count
            match_count = count_strict_order_matches(store_name_lower, card_name.lower())
            if match_count > highest_match_count:  # Keep the record with the highest match count
                highest_match_count = match_count
                best_match = record

    # If there was a valid match with strict order, return that result
    if best_match and highest_match_count > 0:
        row_data["bp_code"] = best_match.get("CardCode")
    else:
        # Continue with normal logic (regex matching) if no matches found
        best_match = None
        highest_match_count = 0

        # Use regex to match the store_name with the CardName in bp_code_results
        for record in bp_code_results:
            card_name = record.get("CardName")
            if card_name:
                # Apply regex matching, ensuring that store_name appears within card_name
                if re.search(re.escape(store_name_lower), card_name.lower()):
                    match_count = count_strict_order_matches(store_name_lower, card_name.lower())
                    if match_count > highest_match_count:  # Keep the highest match count
                        highest_match_count = match_count
                        best_match = record

        # Assign the BP Code from the best match if found
        if best_match and highest_match_count > 0:
            row_data["bp_code"] = best_match.get("CardCode")
        else:
            row_data["bp_code"] = None

    return row_data



@csrf_exempt
def render_processed_data(request, instance):
    """Render the processed data to the template in an accordion format with pagination."""
    try:
        # Fetch the extracted data for the given instance
        files = DSR.objects.filter(instance=instance)

        # Initialize variables
        files_with_missing_date_ids = []

        # Process each file
        for file in files:
            # Keep database values unchanged, only format for display
            file.f_total_qty_sold = "{:,}".format(float(file.total_qty_sold))
            file.f_total_amount_template = "{:,.2f}".format(float(file.total_amount_template))
            file.f_total_amount_raw = "{:,.2f}".format(float(file.total_amount_raw))

            if file.extracted_data:
                # Sort the extracted data
                file.extracted_data = sorted(file.extracted_data, key=lambda row: (
                    row.get("item_code", "no item code") != "no item code",  # Prioritize "no item code" first
                    row.get("bp_code") is not None  # Then prioritize rows where bp_code is None
                ))

                # Check for missing dates in rows
                has_missing_date = any("date" not in row or not row["date"] for row in file.extracted_data)
                if has_missing_date:
                    files_with_missing_date_ids.append(file.id)

        has_data = any(file.extracted_data for file in files)

        # Pagination
        page = request.GET.get("page", 1)  # Get page number from request
        paginator = Paginator(files, 10)  # Show 10 files per page (adjust as needed)

        try:
            paginated_files = paginator.page(page)
        except PageNotAnInteger:
            paginated_files = paginator.page(1)  # If page is not an integer, show first page
        except EmptyPage:
            paginated_files = paginator.page(paginator.num_pages)  # If page is out of range, show last page

        # Prepare the context for rendering
        context = {
            "files": paginated_files,  # Paginated files
            "instance": instance,
            "files_with_missing_date_ids": files_with_missing_date_ids,  # File IDs with missing dates
            "has_data": has_data
        }

        # Render the template with the context
        return render(request, "app/generated.html", context)

    except Exception as e:
        # Log the error for debugging purposes
        logger.error(f"Error processing data for instance {instance}: {e}", exc_info=True)

        # Provide a user-friendly error message
        return HttpResponse("Error in rendering", status=500)












#####CLEANUP FUNCTION (Uploading files will populate the database so we need to delete them after processing)
#####Information on the files will be saved in text which will be much lighter for our database
def delete_processed_files(instance):
    """
    Deletes files in the uploads directory after processing them
    and ensures database entries are cleaned up.
    """
    # Query for processed DSR objects (customize this logic based on your processing criteria)
    processed_files = DSR.objects.filter(instance=instance)  # Example filter

    for file_obj in processed_files:
        file_obj.raw_file.delete()


def delete_validation_files(instance):
    """
    Deletes files in the uploads directory after processing them
    and ensures database entries are cleaned up.
    """
    # Query for processed DSR objects (customize this logic based on your processing criteria)
    processed_files = Validation.objects.filter(instance=instance)  # Example filter

    for file_obj in processed_files:
        file_obj.generated_file.delete()


###########FOR FUTURE IMPROVEMENTS, FILE NAMES WOULD BE LINKS THAT REDIRECTS TO ANOTHER PAGE THAT RENDERS THE DATA DYNAMICALLY
###########This is currently for tracking the generation of templates and who generated them along with the date of generation(per batch)
def display_filenames(request, instance):
    files = DSR.objects.filter(instance=instance)
    pass



###########HANDLES THE FILE UPLOAD
@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = FileFieldForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract remarks and uploader from the form data
            remarks = request.POST.get('remarks')
            uploader = request.POST.get('uploader')
            
            # Get uploaded files
            files = request.FILES.getlist('file_field')

            # Check each file extension
            for file in files:
                # Get file extension
                file_extension = os.path.splitext(file.name)[1][1:].lower()  # Strip the dot and convert to lowercase
                if file_extension not in ALLOWED_FILE_EXTENSIONS:
                    # Raise a validation error if the file extension is not allowed
                    print(f"File type '{file_extension}' is not allowed. Only .xls, .xlsx, .xlsm, and .csv files are accepted.")
                    continue
            
            # Generate a unique instance ID (e.g., UUID)
            instance = str(uuid.uuid4())

            # Call the save_file function to handle the saving logic
            save_file(files, remarks, uploader, instance) #Add uploader here if needed

            # Redirect to process the uploaded files
            return redirect('process-data', instance=instance)
    else:
        form = FileFieldForm()

    return render(request, 'app/upload.html', {"form": form})


def save_validation(files, instance):
    """ Save uploaded files with proper naming """
    for f in files:
        validation_entry = Validation.objects.create(
            generated_file=f,
            instance=instance,
            original_name=f.name
        )
        print(f"Saved file: {validation_entry.generated_file.path}")

@csrf_exempt
def upload_validation(request):
    if request.method == 'POST':
        form = ValidationForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file_field')
            print(f"Files received: {[file.name for file in files]}")  # Debugging output

            instance = str(uuid.uuid4())
            save_validation(files, instance)  # Save files
            print(f"Request method: {request.method}")
            print(f"POST data: {request.POST}")
            print(f"FILES data: {request.FILES}")  # This should contain files

            return redirect('comparison-function', instance=instance)

    else:
        form = ValidationForm()

    return render(request, 'app/upload_validation.html', {"form": form})



def comparison_view(request, instance):
    files = Validation.objects.filter(instance=instance)
    extracted_data = []

    for file in files:
        if file.generated_file:  # Ensure file exists
            file_path = file.generated_file.path  # Correct file path
            print(f"Processing file: {file_path}")  # Debugging output

            try:
                df = pd.read_excel(file_path, skiprows=3)  # Read file

                # Convert all column names to lowercase for case-insensitive comparison
                df.columns = df.columns.str.lower()

                # Define expected columns in lowercase
                bp_code_col = 'bp code'
                quantity_sold_col = 'quantity sold'
                gross_sales_col = 'gross sales'
                net_sales_col = 'net sales'

                # Determine the correct sales column
                if gross_sales_col in df.columns:
                    sales_column = gross_sales_col
                elif net_sales_col in df.columns:
                    sales_column = net_sales_col
                else:
                    raise ValueError("Neither 'Gross Sales' nor 'Net Sales' found in the file.")

                # Select required columns
                df = df[[bp_code_col, quantity_sold_col, sales_column]]
                df.columns = ['BP_CODE', 'Quantity_Sold', 'Sales']  # Rename columns
                df = df.sort_values(by=['BP_CODE'], ascending=True)  # Sort data
                
                json_data = df.to_dict(orient='records')  # Convert to JSON
                
                # Store data in database as a string
                file.data_from_generated_file = json_data
                file.save(update_fields=['data_from_generated_file'])

                extracted_data.extend(json_data)  # Append data for rendering

                delete_validation_files(instance=instance)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    return render(request, 'app/comparison.html', {'data': extracted_data})



###########SAVING THE UPLOADED FILES
def save_file(files, remarks, uploader, instance):  # Add uploader if needed
    for f in files:
        original_name = f.name  # Retain the original file name
        base_name, ext = os.path.splitext(original_name)
        count = 1

        # Ensure uniqueness of original_name
        while DSR.objects.filter(original_name=original_name).exists():
            original_name = f"{base_name} {count}{ext}"
            count += 1

        # Save the file with the unique original_name
        DSR.objects.create(
            raw_file=f,
            remarks=remarks,
            uploader=uploader,
            instance=instance,  # Save instance with each file for identification
            original_name=original_name  # Store the unique original name
        )
###########DOWNLOADING ALL PROCESSED DATA TO EXCEL (ZIP IF MULTIPLE FILES) ALSO INCLUDES A SEPARATE FILE CONTAINING NO ITEM CODES
def download_excel(request, instance):
    # Filter DSR records by the instance
    files = DSR.objects.filter(instance=instance)

    # Create a list to hold the "No Item Code" data across all files
    all_no_item_code_rows = []

    if len(files) > 1:
        # Create a BytesIO buffer to hold the ZIP file
        zip_buffer = BytesIO()

        # Create a ZipFile object
        with ZipFile(zip_buffer, 'w') as zip_file:
            for file in files:
                response, no_item_code_rows = download_all(file.id)
                file_name = f"GENERATED --{file.original_name}"
                # Write each Excel file to the zip archive
                zip_file.writestr(file_name, response.content)

                # Collect "No Item Code" rows for a separate Excel file
                all_no_item_code_rows.append(no_item_code_rows)

            # Check if there are "No Item Code" rows and add a separate Excel file for them
            if any(all_no_item_code_rows):  # Check if there are any "No Item Code" rows
                no_item_code_excel_response = create_no_item_code_excel(all_no_item_code_rows, files)
                zip_file.writestr(f"{file.chain}_no_item_code_files.xlsx", no_item_code_excel_response.read())

        # Set the position of the BytesIO buffer to the beginning
        zip_buffer.seek(0)

        # Create a response to return the ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="DSR.zip"'
    elif len(files) == 1:
        # Download a single file directly
        file = files.first()
        response, no_item_code_rows = download_all(file.id)
        all_no_item_code_rows.append(no_item_code_rows)
        
        # Check if there are "No Item Code" rows and add a separate Excel file for them
        if any(all_no_item_code_rows):  # Check if there are any "No Item Code" rows
            no_item_code_excel_response = create_no_item_code_excel(all_no_item_code_rows, files)
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, 'w') as zip_file:
                # Add the regular Excel file
                zip_file.writestr(f"GENERATED --{file.original_name}", response.content)
                # Add the "No Item Code" Excel file
                zip_file.writestr(f"{file.chain}_no_item_code_files.xlsx", no_item_code_excel_response.read())
            
            zip_buffer.seek(0)
            return HttpResponse(zip_buffer.read(), content_type='application/zip', headers={
                'Content-Disposition': f'attachment; filename="DSR.zip"'
            })
        else:
            return response  # Return the regular file directly
    else:
        # Handle case with no files
        return HttpResponse("No files available to download.", status=404)

    return response



###############PROCESSING OF DATA TO BE DOWNLOADED ON EXCEL
def download_all(file_id):
    try:
        # Retrieve the file object by its ID
        file = DSR.objects.get(id=file_id)
        data = file.extracted_data
        rows = []
        none_bp_code_rows = [] 
        no_item_code_rows = []  # Rows with no item code

        # Iterate over extracted data to create rows for the Excel sheet
        for item in data:
            sales_column = 'Net Sales' if file.chain in ['ALLHOME', 'FISHER'] else 'Gross Sales'
            if file.chain in ['RDS', 'FISHER']:
                code_column = 'STORE CODE'
                code_value = item.get('store_code', '')
            elif file.chain == 'ALLHOME':
                code_column = 'STORE'
                code_value = item.get('store_name', '')
            elif file.chain in ['WDS', 'URATEX', 'OUR HOME', 'SM HOMEWORLD']:
                code_column = 'BP CODE'
                code_value = item.get('bp_code', '')
            else:
                code_column = 'BP CODE'
                code_value = 'None'
            


            # Ensure all values are strings and replace empty or missing values with an empty string
            row = {
                'Item Code': str(item.get('item_code', '') or ''),
                'SKU': str(item.get('matcode', '') or ''),
                'Item Description': str(item.get('item_description', '') or ''),
                code_column: str(code_value or ''),
                'Date': str(item.get('date', '') or ''),
                'Quantity Sold': str(item.get('qty_sold', 0)),  # Ensure 0 is converted to "0"
                sales_column: str(abs(float(item.get('total_amount', 0)))),  # Ensure 0 is converted to "0"
                'Unit Price': str(abs(float(item.get('unit_amount', 0)))),  # Ensure 0 is converted to "0"
                'BP CODE': item.get('bp_code', ''),
                'BRANCH NAME': item.get('store_name','')
            }
            

            # Categorize rows based on conditions
            if not item.get('item_code') or item.get('item_code') == "no item code":
                no_item_code_rows.append(row)
            elif item.get('bp_code') is None or item.get('bp_code') == '':
                none_bp_code_rows.append(row)

            rows.append(row)

        # Combine "No Item Code" rows at the top, followed by other rows
        sorted_rows = no_item_code_rows + [row for row in rows if row not in no_item_code_rows]

        # Create a DataFrame from the sorted rows list
        df = pd.DataFrame(sorted_rows)

        # Ensure all data in DataFrame is of type string and replace NaN with empty strings
        df = df.fillna("").astype(str)

        # Create a BytesIO buffer to hold the Excel data
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Write the data with headers, skipping three rows
            df.to_excel(writer, index=False, sheet_name='Uploading', startrow=3)

        # Move the buffer position to the beginning
        excel_buffer.seek(0)

        # Set the correct content type and filename
        response = HttpResponse(
            excel_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="GENERATED --{file.original_name}"'

        return response, no_item_code_rows

    except DSR.DoesNotExist:
        return HttpResponse("File not found", status=404), []
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500), []


#########REMOVING SPECIAL CHARACTERS FOR FILE NAMING
def sanitize_sheet_name(name):
    # Remove invalid characters in sheet names (e.g., '/', '\\', ':', '?', etc.)
    sanitized_name = re.sub(r'[\\/*?:"<>|]', '_', name)  # Replace invalid characters with underscores
    return sanitized_name[:31]  # Excel sheet names are limited to 31 characters



#########PROCESS FOR THE SEPARATE FILE CONTAINING THE NO ITEM CODES
def create_no_item_code_excel(all_no_item_code_rows, files):
    # Create a new Excel file where each sheet corresponds to a file with "No Item Code" rows
    no_item_code_excel_buffer = BytesIO()

    with pd.ExcelWriter(no_item_code_excel_buffer, engine='openpyxl') as writer:
        for i, file in enumerate(files):
            # Get the corresponding "No Item Code" rows for the current file
            file_no_item_code_rows = all_no_item_code_rows[i]
            
            if file_no_item_code_rows:  # Only write a sheet if there are "No Item Code" rows
                sanitized_file_name = sanitize_sheet_name(f"File_{i + 1} ({file.original_name})")
                no_item_code_df = pd.DataFrame(file_no_item_code_rows)
                no_item_code_df.to_excel(writer, index=False, sheet_name=sanitized_file_name)
            else:
                print(f"No 'No Item Code' data for file: {file.original_name}")

    no_item_code_excel_buffer.seek(0)
    return no_item_code_excel_buffer


def delete_data(request, instance):
    # Fetch all DSR records
    item = DSR.objects.filter(instance=instance)
    item.delete()
    return redirect('data')



@csrf_exempt
def delete_selected(request):
    if request.method == 'POST':
        selected_instances = request.POST.getlist('delete[]')
        # Delete all selected instances
        DSR.objects.filter(instance__in=selected_instances).delete()
        return redirect('data')





def displayuploadeddsr(request, doc_date, doc_remarks, database_type):
    global item_result
    query = f"""
        SELECT
        T0."DocDate", SUM(T0."DocTotal") AS "Total Amount", T0."U_Remarks"
        FROM ODLN T0 
        WHERE T0."CANCELED" NOT IN ('Y', 'C')
        AND T0."DocDate" = '{doc_date}'
        AND T0."U_Remarks" LIKE '%%{doc_remarks}%%'
        GROUP BY T0."DocDate", T0."U_Remarks"
    """
    try:
        database = database_type
        item_result = execute_query(query, database)
        items = item_result
        # Format DocDate to 'yyyy-mm-dd'
        for item in items:
            if isinstance(item["DocDate"], datetime):
                item["DocDate"] = item["DocDate"].strftime("%Y-%m-%d")
            if "Total Amount" in item:
                item["Total Amount"] = "PHP {:,.2f}".format(float(item["Total Amount"]))

        headers = ['DocDate', 'Total Amount', 'Remarks']
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return render(request, 'app/result.html', {'items': [], 'headers': []})

    context = {'items': items, 'headers': headers, 'doc_date':doc_date, 'doc_remarks':doc_remarks, 'database_type':database_type}
    print(doc_date)
    return render(request, 'app/result.html', context)



def show_data(request):
    # Fetch all DSR records ordered by instance
    dsr_list = DSR.objects.all().order_by('instance', '-date_of_generation')

    formatted_dsr = []
    previous_instance = None  # Track the previous instance

    for item in dsr_list:
        formatted_dsr.append({
            'dsr': item,
            'chain': item.chain,
            'database': item.database,
            'instance': item.instance,
            'date_of_generation': item.date_of_generation,
            'remarks': item.remarks,
            'original_name': item.original_name,
            'uploader': item.uploader,
            'is_new_instance': item.instance != previous_instance  # Flag for template
        })
        previous_instance = item.instance  # Update previous instance

    return render(request, 'app/sample2.html', {'dsr_list': formatted_dsr})





def fetch_remarks(request):
    doc_date = request.GET.get('doc_date')  # Get the date parameter
    database_type = request.GET.get('database_type')  # Get the database type

    # Fetch remarks based on the parameters
    remarks = fetch_remarks_from_database(doc_date, database_type)

    return JsonResponse({'remarks': remarks})


def fetch_remarks_from_database(doc_date, database_type):
    query = f"""
        SELECT
        T0."DocDate", SUM(T0."DocTotal") AS "Total Amount", T0."U_Remarks"
        FROM ODLN T0 
        WHERE T0."CANCELED" NOT IN ('Y', 'C')
        AND T0."DocDate" = '{doc_date}'
        GROUP BY T0."DocDate", T0."U_Remarks"
    """
    
    database = database_type
    result = execute_query(query, database)  
    

    if result is None:  # Handle the case where no data is returned
        print("No data returned from the query.")
        return []  # Return an empty list instead of None

    remarks = [row.get('U_Remarks', '') for row in result]  # Ensure key exists
    print("Extracted Remarks:", remarks)  # Debugging statement

    return remarks


######################################################################
@csrf_exempt
def input_info(request, chain, original_name, database):
    if request.method == 'POST':
        doc_date = request.POST.get('doc_date')
        doc_remarks = request.POST.get('doc_remarks')
        database_type = request.POST.get('database_type')

        # Retrieve SAP Data
        sap_result = validate_dsr(doc_date, doc_remarks, database_type, chain, original_name)

        # Retrieve extracted data from the model
        dsr_entry = DSR.objects.filter(original_name=original_name, chain=chain).first()
        extracted_data = dsr_entry.extracted_data if dsr_entry else []

        # Prepare comparison list
        comparison_result = []
        for extracted in extracted_data:
            matched_sap = next(
                (sap for sap in sap_result if sap["bp_code"] == extracted["bp_code"]), None
            )

            comparison_result.append({
                "generated_store_name": extracted["store_name"],
                "store_code": extracted["store_code"],
                "date": extracted["date"],
                "bp_code": extracted["bp_code"],
                "qty_sold_extracted": extracted["qty_sold"],
                "qty_sold_sap": matched_sap["qty_sold"] if matched_sap else "N/A",
                "total_amount_extracted": extracted["total_amount"],
                "total_amount_sap": matched_sap["total_amount"] if matched_sap else "N/A",
                "remarks_extracted": extracted.get("remarks", ""),
                "remarks_sap": matched_sap["remarks"] if matched_sap else "N/A"
            })

        context = {
            'comparison_result': comparison_result
        }
        return render(request, 'app/validatedsr.html', context)

    return render(request, 'app/dsr_input.html')







######################## Fix this!!
def validate_dsr(doc_date, doc_remarks, database_type, chain, original_name):
    document_date = doc_date
    db = database_type
    document_remarks = doc_remarks

    query = f"""
        SELECT 
        T0."TaxDate", 
        T0."DocDate",
        T0."DocNum", 
        T0."CardCode", 
        T1."AddID" AS "Store Code", 
        TO_INT(SUM(T2."Quantity")) AS "Quantity", 
        T0."DocTotal",
        T0."U_Remarks" AS "Remarks" 
        FROM ODLN T0 
        INNER JOIN OCRD T1 ON T0."CardCode" = T1."CardCode" 
        INNER JOIN DLN1 T2 ON T0."DocEntry" = T2."DocEntry" 
        WHERE T0."CANCELED" NOT IN ('Y','C') 
        AND T0."DocDate" ='{document_date}'
        AND  T0."U_Remarks" LIKE '%{document_remarks}%' 
        GROUP BY T0."TaxDate",T0."DocDate", T0."DocNum", T0."CardCode", T1."AddID", T0."DocTotal", T0."U_Remarks"  
        ORDER BY T0."CardCode"
    """


    try:
        query_result = execute_query(query, db)  # Execute the query

        total_quantity = 0
        total_doc_total = 0
        total_per_cardcode = {}  # Dictionary to store [total quantity, total DocTotal] per CardCode

        for row in query_result:
            card_code = row["CardCode"]
            quantity = row["Quantity"]
            doc_total = row["DocTotal"]

            total_quantity += quantity
            total_doc_total += doc_total

            # Store [total quantity, total DocTotal] per CardCode
            if card_code in total_per_cardcode:
                total_per_cardcode[card_code][0] += quantity  # Update quantity
                total_per_cardcode[card_code][1] += doc_total  # Update DocTotal
            else:
                total_per_cardcode[card_code] = [quantity, doc_total]  # Initialize with quantity and DocTotal

        total_doc_total = round(total_doc_total, 2)

        print(f"Total Quantity: {total_quantity}")
        print(f"Total DocTotal: {total_doc_total}")
        print("Total per CardCode:")

        for card_code, values in total_per_cardcode.items():
            print(f"{card_code}: Quantity = {values[0]}, DocTotal = {round(values[1], 2)}")
        
        return total_quantity, total_doc_total, total_per_cardcode


    except Exception as e:
        print(f"Error executing query: {e}")
