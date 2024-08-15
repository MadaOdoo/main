odoo.define('xma_pos_voucher_redemption.PartnerListScreen', function (require) {
    'use strict';

    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
    const Registries = require('point_of_sale.Registries');

    const PosPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {
            async saveChanges(event) {
                try {
                    let curp = event.detail.processedChanges.curp != undefined
                    if(curp){
                        let partner_id = event.detail.processedChanges.id
                        curp = event.detail.processedChanges.curp.toUpperCase()
                        if(curp.length > 0){
                            let result = await this.rpc({
                                model: 'res.partner',
                                method: 'validar_curp',
                                args: [curp,partner_id],
                            });
                            if(result){
                                await this.showPopup('ModalDialogWarningPopup', {
                                    title: this.env._t('¡ADVERTENCIA!'),
                                    body1: this.env._t('Ya existe un cliente con esta CURP.'),
                                })
                                return false;
                            }
                        }
                    }
                } catch (error) {
                    console.log(error);
                }
                super.saveChanges(event);
            }
        };

    Registries.Component.extend(PartnerListScreen, PosPartnerListScreen);

    return PartnerListScreen;
});
