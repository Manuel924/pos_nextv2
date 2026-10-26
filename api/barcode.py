import io

import frappe
from frappe.utils.file_manager import save_file


def _render_qr(item_code):
	"""QR code (PNG bytes)."""
	import segno

	buf = io.BytesIO()
	segno.make(item_code, error="m").save(buf, kind="png", scale=6)
	buf.seek(0)
	return buf.getvalue()


def _render_barcode(item_code):
	"""Code 39 barcode (PNG bytes), solo las barras + zona de silencio."""
	import barcode
	from barcode.writer import ImageWriter

	bc = barcode.get("code39", item_code.upper(), writer=ImageWriter())
	buf = io.BytesIO()
	bc.write(buf, options={"write_text": False, "module_width": 0.35, "module_height": 15, "quiet_zone": 6.5})
	buf.seek(0)
	return buf.getvalue()


@frappe.whitelist()
def generate_item_barcode(item_code, code_type="barcode"):
	"""Genera QR y/o código de barras (Code 39) para un Item y adjunta la(s)
	imagen(es) POR SEPARADO.

	code_type: "qr" | "barcode" | "both" (default "barcode")
	"""
	item_code = (item_code or "").strip()
	if not item_code:
		frappe.throw("item_code is required")

	item = frappe.get_doc("Item", item_code)

	results = []
	try:
		if code_type in ("qr", "both"):
			png = _render_qr(item_code)
			fname = item_code + "_qr.png"
			fd = save_file(fname, png, "Item", item_code, is_private=0)
			results.append({"type": "qr", "file_url": fd.file_url if hasattr(fd, "file_url") else "/files/" + fname})

		if code_type in ("barcode", "both"):
			png = _render_barcode(item_code)
			fname = item_code + "_barcode.png"
			fd = save_file(fname, png, "Item", item_code, is_private=0)
			results.append({"type": "barcode", "file_url": fd.file_url if hasattr(fd, "file_url") else "/files/" + fname})
	except Exception as e:
		frappe.log_error(title="POSNext barcode generation failed", message=str(e))
		frappe.throw("Could not generate barcode image: " + str(e))

	# Agregar la fila de código de barras al child table (con dedupe)
	exists = any((r.barcode or "").strip() == item_code for r in (item.barcodes or []))
	if not exists:
		item.append("barcodes", {"barcode": item_code, "barcode_type": "CODE-39"})
		item.save(ignore_permissions=True)
		frappe.db.commit()

	return {"barcode": item_code, "files": results}
