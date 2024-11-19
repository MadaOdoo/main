odoo.define('xma_pos_voucher_redemption.ClosePosPopup', function (require) {
    'use strict';

    const ClosePosPopup = require('point_of_sale.ClosePosPopup');
    const Registries = require('point_of_sale.Registries');

    const PosVoucherRedemptionClosePopup = (ClosePosPopup) =>
        class extends ClosePosPopup {
            async confirm() {
                let validation_partners = await this.getValidateCustomerData(this.env.pos.pos_session.id);
                if (validation_partners.respuesta) {
                    await this.showPopup('ModalDialogWarningPopup', {
                        title: this.env._t('¡Validacion!'),
                        body1: this.env._t("Es necesario que los clientes: "+validation_partners.partners_name+" tenga llenos los campos de nombre, curp y celular antes de cerrar el PDV."),
                    })
                    return;
                }
                return super.confirm();
            }

            async getValidateCustomerData(session) {
                return await this.rpc({
                    model: 'pos.session',
                    method: 'get_validate_customer_data',
                    args: [session],
                });
            }
        };

    Registries.Component.extend(ClosePosPopup, PosVoucherRedemptionClosePopup);

    return ClosePosPopup;
});