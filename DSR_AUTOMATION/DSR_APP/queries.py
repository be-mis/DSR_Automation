from DSR_APP.services.sap_query_conn import execute_query



#########QUERY TO FETCH BP CODES WITH BRANCH ID 
def fetch_bp_code_results(chain, database):
    """Fetch the BP Code results and store them in a global list."""

    query = f"""
        SELECT 
            a."CardCode",
            a."CardName",
            a."AddID"
        FROM OCRD a
        LEFT JOIN CPN1 b ON b."BpCode" = a."CardCode"
        INNER JOIN OCPN c ON c."CpnNo" = b."CpnNo" AND c."U_CType" = 'SKU' AND c."U_Chain" = '{chain}'
        WHERE a."frozenFor" = 'N'
    """

    try:
        # Execute the query and fetch results
        return execute_query(query, database)
    except Exception as e:
        # Handle any errors gracefully and leave bp_code_results empty
        return []

    
#########QUERY TO FETCH ITEM CODES WITH PRICE
def fetch_item_code_results(chain, database):
    query = f"""
        SELECT 
            b."ItemCode",
            b."ItemName",
            b."U_SKU",
            d."Price",
            b."U_BarCode"
        FROM OCPN a
        JOIN CPN2 b ON a."CpnNo" = b."CpnNo"
        JOIN OITM c ON c."ItemCode" = b."ItemCode"
        JOIN ITM1 d ON d."ItemCode" = c."ItemCode"
        WHERE a."U_Chain" = '{chain}' 
        AND d."PriceList" = 2 
        AND b."U_SKU" IS NOT NULL
        AND c."frozenFor" = 'N';
    """

    try:
        return execute_query(query, database)
    except Exception as e:
        return []
