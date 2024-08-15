odoo.define('xma_pos_voucher_redemption.PSNumpadInputButton', function(require) {
    'use strict';

    const PSNumpadInputButton = require('point_of_sale.PSNumpadInputButton');
    const Registries = require('point_of_sale.Registries');

    const PosPSNumpadInputButton = PSNumpadInputButton =>
        class extends PSNumpadInputButton {
            get _class() {
                var selected_paymentline = this.currentOrder.selected_paymentline
                var journal = {}
                if(selected_paymentline != undefined){
                    if(selected_paymentline.payment_method.journal_id){
                        journal = this.env.pos.journal_by_id[selected_paymentline.payment_method.journal_id[0]]
                    }
                }
                if(journal.is_vale){
                    return 'button next'
                } else {
                    super._class;
                }
            }
            get currentOrder() {
                return this.env.pos.get_order();
            }
        };
    Registries.Component.extend(PSNumpadInputButton, PosPSNumpadInputButton);
    return PSNumpadInputButton;
});
