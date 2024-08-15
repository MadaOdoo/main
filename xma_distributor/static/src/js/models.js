odoo.define('xma_pos_voucher_redemption.pos', function (require) {
    "use strict";

    var { PosGlobalState, Payment, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');


    const XmaPosVoucherRedemtionPosGlobalState = (PosGlobalState) => class XmaPosVoucherRedemtionPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.journal_by_id = loadedData['journal_by_id'];
        }
    }
    Registries.Model.extend(PosGlobalState, XmaPosVoucherRedemtionPosGlobalState);

    const XmaPosVoucherRedemtionPayment = (Payment) => class XmaPosVoucherRedemtionPayment extends Payment {
        // @Override
        constructor() {
            super(...arguments);
            this.folio_de_vale = this.folio_de_vale || null;
        }
        //@Override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.folio_de_vale = json.folio_de_vale;
        }
        export_as_JSON() {
            var json = super.export_as_JSON(...arguments);

            var to_return = _.extend(json, {
                'folio_de_vale': this.folio_de_vale,
            });
            return to_return;
        }
    }
    Registries.Model.extend(Payment, XmaPosVoucherRedemtionPayment);

    const XmaPosVoucherRedemtionOrder = (Order) => class XmaPosVoucherRedemtionOrder extends Order {
        // @Override
        constructor() {
            super(...arguments);
            this.is_vale = this.is_vale || null;
            this.folio_de_vale = this.folio_de_vale || null;
            this.state_de_vale = this.state_de_vale || null;
            this.distribuidora_id = this.distribuidora_id || null;
        }
        //@Override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.is_vale = json.is_vale;
            this.folio_de_vale = json.folio_de_vale;
            this.state_de_vale = json.state_de_vale;
        }
        export_as_JSON() {
            var json = super.export_as_JSON(...arguments);

            var to_return = _.extend(json, {
                'is_vale': this.is_vale,
                'folio_de_vale': this.folio_de_vale,
                'state_de_vale': this.state_de_vale,
                'distribuidora_id': this.distribuidora_id,
            });
            return to_return;
        }
    }
    Registries.Model.extend(Order, XmaPosVoucherRedemtionOrder);
});