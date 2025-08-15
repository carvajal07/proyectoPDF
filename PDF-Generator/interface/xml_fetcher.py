from infra.db import get_connection

def get_layout_xml(customer, product):
    conn = get_connection("PruebaMapeo")
    cursor = conn.cursor()

    query = """
        SELECT [schema]
        FROM SchemeXml
        WHERE customer = ? AND product = ?
    """
    try:
        cursor.execute(query, (customer, product))
    except Exception as e:
        conn.close()
        raise ValueError(f"Error al ejecutar la consulta: {e}")
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    else:
        raise ValueError(f"No se encontró layout para {customer}-{product}")