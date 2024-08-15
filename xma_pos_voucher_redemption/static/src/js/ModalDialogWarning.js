odoo.define('xma_pos_voucher_redemption.ModalDialogWarningPopup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ModalDialogWarningPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            owl.onMounted(this.onMounted);
        }
        onMounted() {
            this.playSound('error');
        }
    }
    ModalDialogWarningPopup.template = 'ModalDialogWarningPopup';
    ModalDialogWarningPopup.defaultProps = {
        confirmText: 'Ok',
        title: '!WARNING',
    };

    Registries.Component.add(ModalDialogWarningPopup);

    return ModalDialogWarningPopup;
});
