odoo.define('xma_pos_voucher_redemption.PartnerDetailsEdit', function (require) {
    'use strict';

    const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const PosPartnerDetailsEdit = (PartnerDetailsEdit) =>
        class extends PartnerDetailsEdit {
            setup() {
                super.setup();
                const partner = this.props.partner;
                this.changes.l10n_mx_edi_curp = partner.l10n_mx_edi_curp || ''
                this.changes.mobile = partner.mobile || ''
            }
        };

    Registries.Component.extend(PartnerDetailsEdit, PosPartnerDetailsEdit);

    return PartnerDetailsEdit;
});
