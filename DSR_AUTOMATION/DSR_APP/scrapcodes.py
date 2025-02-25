# EDITING THE ITEM CODE IF NO ITEM CODE FOUND
        # def edit_item_code(request, row_id, file_id):
        #     # Get the specific DSR object
        #     dsr = DSR.objects.get(id=file_id)
            
        #     # Extract the row from extracted_data using row_id
        #     extracted_data = dsr.extracted_data or []
        #     row = next((item for item in extracted_data if item.get('row_id') == row_id), None)

        #     if not row:
        #         return HttpResponse("Row not found", status=404)

        #     if request.method == 'POST':
        #         # Update the item_code in the row and save the DSR object
        #         new_item_code = request.POST.get('item_code')
        #         if new_item_code:
        #             row['item_code'] = new_item_code
        #             dsr.extracted_data = extracted_data
        #             dsr.save()
        #             return redirect('generated-page', instance=dsr.instance)  # Update as per your redirection logic

        #     # Render the form with pre-filled data
        #     return render(request, 'app/edit_item_code.html', {'row': row, 'file_id': file_id})



            # query = f"""
    # SELECT
    #     LEFT(b."U_SKU", LOCATE(b."U_SKU", '-') - 1) AS "U_SKU",
    #     a."ItemCode", 
    #     a."ItemName", 
    #     b."U_SKU", 
    #     b."U_BarCode", 
    #     b."U_UPC", 
    #     b."U_VendorPartNumber"
    # FROM OITM a
    # LEFT JOIN (
    #     SELECT 
    #         b1."ItemCode", 
    #         b1."U_SKU", 
    #         T0."U_Chain", 
    #         b1."U_BarCode", 
    #         b1."U_UPC", 
    #         b1."U_VendorPartNumber"
    #     FROM OCPN T0
    #     INNER JOIN CPN2 b1 ON T0."CpnNo" = b1."CpnNo"
    #     WHERE T0."U_CType" = 'SKU'
    #         AND IFNULL(b1."U_SKU", '') <> ''
    #         AND IFNULL(T0."U_CType",'') = 'SKU'
    # ) b ON a."ItemCode" = b."ItemCode" 
    #     AND b."U_Chain" = '{chain}'
    # WHERE a."ItmsGrpCod" = 100 
    #     AND b."U_SKU" IS NOT NULL;
    #         """


# FOR THE PRICE (SM)

#             query = f"""
#             SELECT 
#                 b."ItemCode", 
#                 b."U_SKU"
#             FROM OCPN a
#             JOIN CPN2 b ON a."CpnNo" = b."CpnNo"
#             JOIN OITM c ON c."ItemCode" = b."ItemCode"
#             WHERE a."U_Chain" = '{chain}';
#         """
















# @csrf_exempt
# def edit_item_code(request, row_id, file_id):
#     try:
#         # Get the specific DSR object
#         dsr = get_object_or_404(DSR, id=file_id)

#         # Extract the row from extracted_data using row_id
#         extracted_data = dsr.extracted_data or []
#         row = next((item for item in extracted_data if item.get('row_id') == row_id), None)

#         if not row:
#             return JsonResponse({'success': False, 'error': 'Row not found'}, status=404)

#         if request.method == 'POST' and request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
#             # Update the item_code in the row and save the DSR object
#             new_item_code = request.POST.get('item_code')
#             if new_item_code:
#                 row['item_code'] = new_item_code
#                 dsr.extracted_data = extracted_data
#                 dsr.save()
#                 return JsonResponse({'success': True, 'item_code': new_item_code})
#             else:
#                 return JsonResponse({'success': False, 'error': 'Item code is missing'}, status=400)

#         return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
#     except Exception as e:
#         logger.error(f"Error editing item code: {str(e)}")  # Log the error for debugging
#         return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)


# @csrf_exempt
# def edit_bp_code(request, row_id, file_id):
#     try:
#         # Get the specific DSR object
#         dsr = get_object_or_404(DSR, id=file_id)

#         # Extract the row from extracted_data using row_id
#         extracted_data = dsr.extracted_data or []
#         row = next((item for item in extracted_data if item.get('row_id') == row_id), None)

#         if not row:
#             return JsonResponse({'success': False, 'error': 'Row not found'}, status=404)

#         if request.method == 'POST' and request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
#             # Update the item_code in the row and save the DSR object
#             new_bp_code = request.POST.get('bp_code')
#             if new_bp_code:
#                 row['bp_code'] = new_bp_code
#                 dsr.extracted_data = extracted_data
#                 dsr.save()
#                 return JsonResponse({'success': True, 'bp_code': new_bp_code})
#             else:
#                 return JsonResponse({'success': False, 'error': 'Item code is missing'}, status=400)

#         return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
#     except Exception as e:
#         logger.error(f"Error editing item code: {str(e)}")  # Log the error for debugging
#         return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)



















# {% comment %} <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Processed Data</title>
#     <style>
#         body {
#             font-family: Arial, sans-serif;
#             margin: 20px;
#             background-color: #f4f4f9;
#         }
#         h1 {
#             text-align: center;
#             color: #333;
#         }
#         .file-header {
#             font-size: 1.5em;
#             margin-top: 30px;
#             text-align: center;
#             color: #444;
#         }
#         .download-btn {
#             display: block;
#             margin: 10px auto;
#             padding: 10px 20px;
#             background-color: #4CAF50;
#             color: white;
#             text-align: center;
#             font-size: 16px;
#             cursor: pointer;
#             border: none;
#             border-radius: 5px;
#         }
#         .download-btn:hover {
#             background-color: #45a049;
#         }
#     </style>
# </head>
# <body>
#     <h1>Processed Data</h1>

#     {% for file in files %}
#         <div class="file-header">
#             <p>File {{ file.raw_file.name }} is now ready for download</p>
#             <form action="{% url 'download-excel' file.id %}" method="get">
#                 <button type="submit" class="download-btn">Download Excel</button>
#             </form>
#         </div>
#     {% endfor %}

#     {% comment %} <div class="download-all">
#         <form action="{% url 'download-all' instance %}" method="get">
#             <button type="submit" class="download-btn" >Download All</button>
#         </form>
#     </div> 
# </body>
# </html> {% endcomment %}









































# {% comment %} 

# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Processed Data</title>
#     <style>
#         body {
#             font-family: Arial, sans-serif;
#             margin: 20px;
#             background-color: #f4f4f9;
#         }
#         h1 {
#             text-align: center;
#             color: #333;
#         }
#         table {
#             width: 100%;
#             border-collapse: collapse;
#             margin: 20px 0;
#         }
#         th, td {
#             padding: 10px;
#             text-align: left;
#             border: 1px solid #ddd;
#         }
#         th {
#             background-color: #f2f2f2;
#             color: #333;
#         }
#         tr:nth-child(even) {
#             background-color: #f9f9f9;
#         }
#         tr:hover {
#             background-color: #f1f1f1;
#         }
#         .file-header {
#             font-size: 1.5em;
#             margin-top: 30px;
#             text-align: center;
#             color: #444;
#         }
#         .filter-input {
#             width: 100%;
#             padding: 5px;
#             margin-top: 5px;
#         }
#     </style>
# </head>
# <body>
#     <h1>Processed Data</h1>
#     {% for file in extracted_data %}
#         <div class="file-header">
#             <h2>{{ file.file_name }}</h2>
#         </div>
#         <table id="dataTable">
#             <thead>
#                 <tr>
#                     <th>
#                         SKU
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                     <th>
#                         Item Description
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                     <th>
#                         Branch Name
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                     <th>
#                         Date
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                     <th>
#                         Quantity Sold
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                     <th>
#                         Gross Amount
#                         <input type="text" class="filter-input" placeholder="Filter..." onkeyup="filterTable()">
#                     </th>
#                 </tr>
#             </thead>
#             <tbody>
#                 {% for data in file.data %}
#                     <tr>
#                         <td>{{ data.matcode }}</td>
#                         <td>{{ data.item_description }}</td>
#                         <td>{{ data.store_name }}</td>
#                         <td>{{ data.date }}</td>
#                         <td>{{ data.qty_sold }}</td>
#                         <td>{{ data.total_amount }}</td>
#                     </tr>
#                 {% endfor %}
#             </tbody>
#         </table>
#     {% endfor %}

#     <script>
#         // Function to filter data by multiple columns
#         function filterTable() {
#             var table = document.getElementById("dataTable");
#             var rows = table.getElementsByTagName("tr");
#             var filters = [];
            
#             // Collect all filter values from input fields
#             var inputs = document.querySelectorAll('.filter-input');
#             inputs.forEach(function(input) {
#                 filters.push(input.value.toLowerCase());
#             });

#             // Loop through table rows and apply the filters
#             for (var i = 1; i < rows.length; i++) {
#                 var cells = rows[i].getElementsByTagName("td");
#                 var match = true;
                
#                 for (var j = 0; j < filters.length; j++) {
#                     if (filters[j] && cells[j]) {
#                         var cellText = cells[j].textContent || cells[j].innerText;
#                         if (cellText.toLowerCase().indexOf(filters[j]) === -1) {
#                             match = false;
#                             break;
#                         }
#                     }
#                 }

#                 if (match) {
#                     rows[i].style.display = "";
#                 } else {
#                     rows[i].style.display = "none";
#                 }
#             }
#         }

#         // Initialize table filter on page load
#         window.onload = function() {
#             filterTable(); // Initial filter application
#         }
#     </script>
# </body>
# </html> {% endcomment %}



# def download_all(file_id):
#     # Retrieve the file object by its ID
#     file = DSR.objects.get(id=file_id)
#     data = file.extracted_data
#     rows = []
    
#     # Iterate over extracted data to create rows for the Excel sheet
#     for item in data:
#         rows.append({
#             'Item Code': item.get('item_code', ''),
#             'SKU': item.get('matcode', ''),
#             'Item Description': item.get('item_description', ''),
#             'Branch': item.get('store_name', ''),
#             'Date': item.get('date', ''),
#             'Quantity Sold': item.get('qty_sold', 0),
#             'Total Amount': item.get('total_amount', 0),
#             'Unit Amount': item.get('unit_amount', 0),
#             'BP Code': item.get('bp_code', '')
#         })
    
#     # Create a DataFrame from the rows list
#     df = pd.DataFrame(rows)
    
#     # Create a BytesIO buffer to hold the Excel data
#     excel_buffer = BytesIO()
    
#     # Write the DataFrame to the buffer as an Excel file
#     with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name='Uploading')
    
#     # Move the buffer position to the beginning
#     excel_buffer.seek(0)

#     # Create a response to return the Excel file
#     response = HttpResponse(
#         excel_buffer.read(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = f'attachment; filename="{file.raw_file.name}.xlsx"'

#     return response







# @csrf_exempt
# def validatedsr(request):
#     if request.method == 'POST':
#         doc_date = request.POST.get('doc_date')
#         doc_remarks = request.POST.get('doc_remarks')
#         database_type = request.POST.get('database_type')

#         if not doc_date or not doc_remarks:
#             return render(request, 'app/dsr_input.html', {
#                 'error_message': "All fields are required."
#             })

#         try:
#             datetime.strptime(doc_date, "%Y-%m-%d")
#             return redirect('display-dsr', doc_date=doc_date, doc_remarks=doc_remarks, database_type=database_type)
#         except ValueError:
#             logging.error(f"Invalid date format provided: {doc_date}")
#             return render(request, 'app/dsr_input.html', {
#                 'error_message': f"Invalid date format: {doc_date}. Please use YYYY-MM-DD."
#             })
#     return render(request, 'app/dsr_input.html')




uploaded_items = []
def detaileddsr(request, doc_date, doc_remarks, database_type):
    global item_result, uploaded_items
    uploaded_items = []  # Reset global list
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
        AND T0."DocDate" ='{doc_date}'
        AND  T0."U_Remarks" LIKE '%%{doc_remarks}%%' 

        GROUP BY T0."TaxDate",T0."DocDate", T0."DocNum", T0."CardCode", T1."AddID", T0."DocTotal", T0."U_Remarks"  

        ORDER BY T0."CardCode"
    """

    try:
        database = database_type
        uploaded_items = execute_query(query, database)  # Store fetched data

        # Format DocDate and TaxDate
        for item in uploaded_items:
            if isinstance(item["DocDate"], datetime):
                item["DocDate"] = item["DocDate"].strftime("%Y-%m-%d")
            if isinstance(item["TaxDate"], datetime):
                item["TaxDate"] = item["TaxDate"].strftime("%Y-%m-%d")
            if "DocTotal" in item:
                item["DocTotal"] = "PHP {:,.2f}".format(float(item["DocTotal"]))

        headers = ['Document Date', 'Posting Date', 'Document Number', 'BP Code', 'Store Code', 'Quantity', 'Document Total', 'Remarks']
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        uploaded_items = []  # Clear on error
        return render(request, 'app/detailed_dsr.html', {'items': [], 'headers': []})

    context = {'items': uploaded_items, 'headers': headers}
    item_result = []
    return render(request, 'app/detailed_dsr.html', context)






# # def create_connection(database):
# def create_connection(database):
#     server = settings.DB_SERVER
#     user = settings.DB_USER
#     password = settings.DB_PASSWORD
#     if database == 'NBFI':
#         database = settings.DB_DATABASE_NBFI
#     elif database == 'EPC':
#         database = settings.DB_DATABASE_EPC
#     else:
#         print("No valid database found!")

#     driver = "HDBODBC" if platform.architecture()[0] == "64bit" else "HDBODBC32"
#     connection_string = (
#         f"DRIVER={{{driver}}};"
#         f"SERVERNODE={server};"
#         f"UID={user};"
#         f"PWD={password};"
#         f"CS={database};"
#     )

#     try:
#         connection = pyodbc.connect(connection_string)
#         print("Connection successful!")
#         return connection
#     except pyodbc.Error as e:
#         print(f"Failed to connect to the database: {e}")
#         return None

# # def execute_query(query, database):
# #     connection = create_connection(database)
    

# def execute_query(query, database):
#     connection = create_connection(database)

#     if connection:
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute(query)
#                 columns = [column[0] for column in cursor.description]  # Get column names
#                 results = cursor.fetchall()  # Fetch all rows
#                 # Convert results to a list of dictionaries
#                 data = [dict(zip(columns, row)) for row in results]
#                 return data  # Return the data without closing prematurely
#         except Exception as e:
#             print(f"Database operation failed: {e}")
#             return None
#         finally:
#             connection.close()  # Ensure connection is closed after the query
#     return None




# @csrf_exempt
# def validate_dsr(doc_date, doc_remarks, database_type):
#     dsr_records = DSR.objects.filter(instance=instance)
#     selected_file = request.GET.get("selected_file", None)
#     totalqty = 0 
#     processed_data = []

#     remarks = dsr_records.first().remarks if dsr_records.exists() else ""

#     for file in dsr_records:
#         if not file.extracted_data:
#             continue

#         # Filter by selected file name
#         if selected_file and file.original_name != selected_file:
#             continue  

#         aggregated_data = defaultdict(lambda: {"total_qty_sold": 0})

#         for row in file.extracted_data:
#             bp_code = row.get("bp_code")
#             qty_sold = row.get("qty_sold", 0)
#             if bp_code:
#                 aggregated_data[bp_code]["total_qty_sold"] += qty_sold  

#         totalqty += file.total_qty_sold  

#         for bp, details in aggregated_data.items():
#             processed_data.append({"bp_code": bp, "total_qty_sold": details["total_qty_sold"]})  


#     processed_data.sort(key=lambda x: x["bp_code"])  

#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse({"processed_data": processed_data, "total_qty_sold": totalqty}, safe=False)

#     original_names = list(dsr_records.values_list("original_name", flat=True).distinct())
#     print(f"DocDate: ")
#     return render(request, "app/dsr_template.html", {
#         "processed_data": processed_data,
#         "original_names": original_names,
#         "totalqty": totalqty,
#         "instance": instance,
#         "remarks": remarks,
#     })


##########RENDERING THE DATA TO THE TEMPLATE AND CREATING THE SUMMARY OF THE FILES
##########Data is rendered by batch (using the file's instance or uuid)
# @csrf_exempt
# def render_processed_data(request, instance):
#     """Render the processed data to the template in an accordion format."""
#     try:
#         # Fetch the extracted data for the given instance
#         files = DSR.objects.filter(instance=instance)

#         # Initialize variables
#         files_with_missing_date_ids = []

#         # Process each file
#         for file in files:
#             # Keep database values unchanged, only format for display
#             file.f_total_qty_sold = "{:,}".format(float(file.total_qty_sold))
#             file.f_total_amount_template = "{:,.2f}".format(float(file.total_amount_template))
#             file.f_total_amount_raw = "{:,.2f}".format(float(file.total_amount_raw))

#             if file.extracted_data:
#                 # Sort the extracted data
#                 file.extracted_data = sorted(file.extracted_data, key=lambda row: (
#                     row.get("item_code", "no item code") != "no item code",  # Prioritize "no item code" first
#                     row.get("bp_code") is not None  # Then prioritize rows where bp_code is None
#                 ))

#                 # Check for missing dates in rows
#                 has_missing_date = any("date" not in row or not row["date"] for row in file.extracted_data)
#                 if has_missing_date:
#                     files_with_missing_date_ids.append(file.id)


#         has_data = any(file.extracted_data for file in files)
#         # Prepare the context for rendering
#         context = {
#             "files": files,
#             "instance": instance,
#             "files_with_missing_date_ids": files_with_missing_date_ids,  # File IDs with missing dates
#             "has_data": has_data
#         }
#         # Render the template with the context
#         return render(request, 'app/generated.html', context)

#     except Exception as e:
#         # Log the error for debugging purposes
#         logger.error(f"Error processing data for instance {instance}: {e}", exc_info=True)

#         # Provide a user-friendly error message
#         error_message = "Error in rendering"
#         return HttpResponse(error_message, status=500)