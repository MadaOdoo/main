odoo.define('xma_pos_voucher_redemption.TransactionPopUp', function(require) {
    'use strict';

    var {Payment} = require('point_of_sale.models');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class TransactionPopUp extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            this.transaction_id = false
        }
        async confirm() {
            super.confirm();
        }
        async cancel() {
            super.cancel()
            return false
        }
        async getPayload() {
            return this.transaction_id;
        }
    }
    TransactionPopUp.template = 'TransactionPopUp';
    TransactionPopUp.defaultProps = {
        payment_cid: 0,
        payment_method_id: 0,
    };

    Registries.Component.add(TransactionPopUp);

    return TransactionPopUp;
});