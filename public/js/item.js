frappe.ui.form.on("Item", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Generar QR"), () => generateCode(frm, "qr"), __("Barcodes"));
		frm.add_custom_button(__("Generar Código de barras"), () => generateCode(frm, "barcode"), __("Barcodes"));
	},
});

function generateCode(frm, codeType) {
	frappe.call({
		method: "pos_next.api.barcode.generate_item_barcode",
		args: { item_code: frm.doc.name, code_type: codeType },
		freeze: true,
		freeze_message: __("Generando código..."),
		callback(r) {
			if (r.message) {
				frappe.show_alert({ message: __("Código generado y adjuntado"), indicator: "green" });
				frm.reload_doc();
			}
		},
	});
}
