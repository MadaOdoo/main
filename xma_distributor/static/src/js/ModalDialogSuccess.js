odoo.define('xma_pos_voucher_redemption.ModalDialogSuccess', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ModalDialogSuccess extends AbstractAwaitablePopup {
        setup() {
            super.setup();
        }
    }
    ModalDialogSuccess.template = 'ModalDialogSuccess';
    ModalDialogSuccess.defaultProps = {
        confirmText: 'Ok',
        title: 'SUCCESS',
    };

    Registries.Component.add(ModalDialogSuccess);

    return ModalDialogSuccess;
});
